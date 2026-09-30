#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_safety_filter.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 02 — Safety Filter Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Read the discovery index from Step 01 and produce a strict extraction-safe file
index for Step 03.

This script does NOT extract text.
This script does NOT execute files.
This script does NOT open documents semantically.
This script only classifies discovered files into safety categories.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Input
-----
01_index/file_index.jsonl

Outputs
-------
01_index/safe_file_index.jsonl
01_index/safe_file_index.csv
01_index/rejected_file_index.jsonl
01_index/review_required_file_index.jsonl
05_reports/safety_filter_summary.json
06_logs/safety_filter_audit.jsonl
06_logs/safety_filter_errors.jsonl

Designed for compatibility with:
03_extract_text.py
09_incremental_refresh.py
19_night_run_orchestrator.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\02_safety_filter.py"

Strict mode
-----------
python ".\\08_scripts\\02_safety_filter.py" --strict

Allow sensitive review into REVIEW_REQUIRED only, not extraction:
default behavior.

Force only specific extensions:
python ".\\08_scripts\\02_safety_filter.py" --allowed ".pdf" --allowed ".docx" --allowed ".xlsx"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_NAME = "02_safety_filter.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

CONFIG_RELATIVE = Path("00_config") / "config.json"
INPUT_FILE_INDEX = Path("01_index") / "file_index.jsonl"

OUTPUT_SAFE_JSONL = Path("01_index") / "safe_file_index.jsonl"
OUTPUT_SAFE_CSV = Path("01_index") / "safe_file_index.csv"
OUTPUT_REJECTED_JSONL = Path("01_index") / "rejected_file_index.jsonl"
OUTPUT_REVIEW_JSONL = Path("01_index") / "review_required_file_index.jsonl"

SUMMARY_JSON = Path("05_reports") / "safety_filter_summary.json"
AUDIT_LOG = Path("06_logs") / "safety_filter_audit.jsonl"
ERROR_LOG = Path("06_logs") / "safety_filter_errors.jsonl"

DISCOVERY_READY = "READY_FOR_EXTRACTION"
DISCOVERY_SENSITIVE_REVIEW = "SENSITIVE_REVIEW"

SAFE_FOR_EXTRACTION = "SAFE_FOR_EXTRACTION"
SENSITIVE_SKIP = "SENSITIVE_SKIP"
REJECTED = "REJECTED"
EXCLUDED = "EXCLUDED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
DUPLICATE_SKIPPED = "DUPLICATE_SKIPPED"

DEFAULT_ALLOWED_EXTENSIONS = [
    ".txt", ".md", ".csv", ".json", ".jsonl",
    ".docx", ".xlsx", ".xlsm", ".pptx", ".pdf",
    ".py", ".sql", ".yaml", ".yml", ".log",
]

DEFAULT_BLOCKED_EXTENSIONS = [
    ".exe", ".dll", ".bat", ".cmd", ".ps1", ".psm1",
    ".msi", ".scr", ".com", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".jar", ".bin", ".dat", ".iso", ".img",
    ".sys", ".drv", ".lnk", ".tmp", ".db", ".sqlite", ".sqlite3",
]

DEFAULT_HIGH_RISK_EXTENSIONS = [
    ".pem", ".key", ".pfx", ".p12", ".crt", ".cer",
]

DEFAULT_SENSITIVE_MARKERS = [
    ".env",
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "private-key",
    "credential",
    "credentials",
    "wallet",
    "seed",
    "recovery",
    "mnemonic",
    "auth",
    "login",
    "cookie",
    "session",
    "ssh",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "guardian_secret",
    "missing_guardian_secret",
]

DEFAULT_EXCLUDED_PATH_MARKERS = [
    r"\windows\\",
    r"\program files\\",
    r"\program files (x86)\\",
    r"\programdata\\",
    r"\appdata\\",
    r"\node_modules\\",
    r"\.git\\",
    r"\.venv\\",
    r"\venv\\",
    r"\__pycache__\\",
    r"\$recycle.bin\\",
    r"\system volume information\\",
    r"\cache\\",
    r"\caches\\",
    r"\temp\\",
    r"\tmp\\",
]

HIGH_RISK_PATTERNS = [
    r"\.env$",
    r"\.pem$",
    r"\.key$",
    r"\.pfx$",
    r"\.p12$",
    r"id_rsa",
    r"id_dsa",
    r"id_ecdsa",
    r"id_ed25519",
    r"password",
    r"passwd",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"private[_-]?key",
    r"credential",
    r"credentials",
    r"wallet",
    r"seed[_-]?phrase",
    r"recovery[_-]?phrase",
    r"mnemonic",
    r"cookie",
    r"session",
]

DEFAULT_MAX_FILE_SIZE_MB = 500

DEFAULT_CONFIG = {
    "allowed_extensions": DEFAULT_ALLOWED_EXTENSIONS,
    "blocked_extensions": DEFAULT_BLOCKED_EXTENSIONS,
    "high_risk_extensions": DEFAULT_HIGH_RISK_EXTENSIONS,
    "sensitive_name_markers": DEFAULT_SENSITIVE_MARKERS,
    "excluded_path_markers": DEFAULT_EXCLUDED_PATH_MARKERS,
    "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB,
    "allow_source_code": True,
    "allow_logs": True,
    "allow_json": True,
    "strict_mode": False,
}


@dataclass(frozen=True)
class SafetyPaths:
    base_dir: Path
    config_path: Path
    input_file_index: Path
    output_safe_jsonl: Path
    output_safe_csv: Path
    output_rejected_jsonl: Path
    output_review_jsonl: Path
    summary_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_ext(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text and not text.startswith("."):
        return "." + text
    return text


def normalize_path_text(value: Any) -> str:
    return str(value or "").lower().replace("/", "\\")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file index: {path}")

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue

            try:
                item = json.loads(raw)
                if isinstance(item, dict):
                    records.append(item)
                else:
                    records.append({
                        "file_path": None,
                        "rag_status": "INVALID_JSONL",
                        "status_reason": f"Line {line_no} is not a JSON object",
                    })
            except Exception as exc:
                records.append({
                    "file_path": None,
                    "rag_status": "INVALID_JSONL",
                    "status_reason": f"Invalid JSONL line {line_no}: {exc}",
                })

    return records


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "safety_checked_at",
        "safety_status",
        "safety_reason",
        "risk_level",
        "extraction_allowed",
        "discovered_at",
        "rag_status",
        "status_reason",
        "file_path",
        "file_name",
        "extension",
        "parent_folder",
        "size_bytes",
        "size_mb",
        "created_time_utc",
        "modified_time_utc",
        "accessed_time_utc",
        "is_symlink",
        "is_hidden",
        "sha256",
        "hash_status",
        "script",
        "script_version",
        "safety_script",
        "safety_script_version",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def resolve_paths(base_dir: Path, config_arg: str | None, input_arg: str | None) -> SafetyPaths:
    return SafetyPaths(
        base_dir=base_dir,
        config_path=Path(config_arg) if config_arg else base_dir / CONFIG_RELATIVE,
        input_file_index=Path(input_arg) if input_arg else base_dir / INPUT_FILE_INDEX,
        output_safe_jsonl=base_dir / OUTPUT_SAFE_JSONL,
        output_safe_csv=base_dir / OUTPUT_SAFE_CSV,
        output_rejected_jsonl=base_dir / OUTPUT_REJECTED_JSONL,
        output_review_jsonl=base_dir / OUTPUT_REVIEW_JSONL,
        summary_json=base_dir / SUMMARY_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def ensure_config(config_path: Path) -> dict[str, Any]:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")
        return dict(DEFAULT_CONFIG)

    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("config root must be an object")

        merged = dict(DEFAULT_CONFIG)
        merged.update(loaded)

        for key in [
            "allowed_extensions",
            "blocked_extensions",
            "high_risk_extensions",
            "sensitive_name_markers",
            "excluded_path_markers",
        ]:
            if not isinstance(merged.get(key), list):
                merged[key] = DEFAULT_CONFIG[key]

        return merged

    except Exception:
        return dict(DEFAULT_CONFIG)


def path_has_excluded_marker(file_path: Any, markers: list[str]) -> tuple[bool, str | None]:
    path_text = normalize_path_text(file_path)

    for marker in markers:
        value = normalize_path_text(marker)
        if not value:
            continue
        if value in path_text:
            return True, marker

    return False, None


def path_has_sensitive_marker(file_path: Any, markers: list[str]) -> tuple[bool, str | None]:
    lower = str(file_path or "").lower()

    for marker in markers:
        value = str(marker or "").lower().strip()
        if not value:
            continue
        if value in lower:
            return True, marker

    for pattern in HIGH_RISK_PATTERNS:
        try:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                return True, pattern
        except re.error:
            continue

    return False, None


def is_source_code_extension(ext: str) -> bool:
    return ext in {".py", ".sql", ".yaml", ".yml"}


def is_log_extension(ext: str) -> bool:
    return ext == ".log"


def is_json_extension(ext: str) -> bool:
    return ext in {".json", ".jsonl"}


def classify_record(
    record: dict[str, Any],
    config: dict[str, Any],
    strict_mode: bool,
    allowed_override: set[str] | None,
    reject_unhashed: bool,
) -> dict[str, Any]:
    out = dict(record)
    out["safety_checked_at"] = utc_now_iso()
    out["safety_script"] = SCRIPT_NAME
    out["safety_script_version"] = SCRIPT_VERSION

    file_path = out.get("file_path")
    file_name = str(out.get("file_name") or "")
    ext = normalize_ext(out.get("extension") or Path(str(file_path or "")).suffix)
    rag_status = str(out.get("rag_status") or "")
    status_reason = str(out.get("status_reason") or "")
    hash_status = str(out.get("hash_status") or "")

    allowed_extensions = {normalize_ext(x) for x in config.get("allowed_extensions", [])}
    blocked_extensions = {normalize_ext(x) for x in config.get("blocked_extensions", [])}
    high_risk_extensions = {normalize_ext(x) for x in config.get("high_risk_extensions", [])}
    sensitive_markers = list(config.get("sensitive_name_markers", []))
    excluded_markers = list(config.get("excluded_path_markers", []))
    max_file_size_mb = safe_float(config.get("max_file_size_mb"), DEFAULT_MAX_FILE_SIZE_MB)

    if allowed_override is not None:
        allowed_extensions = allowed_override

    def finish(status: str, reason: str, risk_level: str, extraction_allowed: bool) -> dict[str, Any]:
        out["safety_status"] = status
        out["safety_reason"] = reason
        out["risk_level"] = risk_level
        out["extraction_allowed"] = extraction_allowed
        return out

    if not file_path:
        return finish(REJECTED, "Missing file_path", "HIGH", False)

    if rag_status in {
        "ROOT_MISSING",
        "ERROR_DISCOVERY",
        "SYMLINK_SKIPPED",
        "HIDDEN_SKIPPED",
        "DUPLICATE_PATH",
        "UNSUPPORTED_EXTENSION",
        "EXCLUDED_PATH",
        "TOO_LARGE",
        "INVALID_JSONL",
    }:
        return finish(EXCLUDED, f"Discovery stage excluded record: {rag_status} | {status_reason}", "LOW", False)

    excluded, excluded_marker = path_has_excluded_marker(file_path, excluded_markers)
    if excluded:
        return finish(EXCLUDED, f"Path marker excluded by safety filter: {excluded_marker}", "LOW", False)

    if file_name.startswith("~$"):
        return finish(EXCLUDED, "Temporary Office lock file", "LOW", False)

    if ext in blocked_extensions:
        return finish(REJECTED, f"Blocked extension: {ext}", "HIGH", False)

    if ext in high_risk_extensions:
        return finish(SENSITIVE_SKIP, f"High-risk credential/certificate extension: {ext}", "CRITICAL", False)

    if ext not in allowed_extensions:
        return finish(REJECTED, f"Extension not allowed by safety config: {ext or '[no extension]'}", "MEDIUM", False)

    size_mb = safe_float(out.get("size_mb"), 0.0)
    if size_mb > max_file_size_mb:
        return finish(REJECTED, f"File exceeds max_file_size_mb={max_file_size_mb}", "MEDIUM", False)

    sensitive, marker = path_has_sensitive_marker(file_path, sensitive_markers)
    if sensitive:
        return finish(SENSITIVE_SKIP, f"Sensitive filename/path marker detected: {marker}", "CRITICAL", False)

    if rag_status == DISCOVERY_SENSITIVE_REVIEW:
        return finish(SENSITIVE_SKIP, "Discovery marked file as sensitive review", "HIGH", False)

    if strict_mode:
        if is_source_code_extension(ext) and not bool(config.get("allow_source_code", True)):
            return finish(REVIEW_REQUIRED, "Strict mode requires source-code review before extraction", "MEDIUM", False)

        if is_log_extension(ext) and not bool(config.get("allow_logs", True)):
            return finish(REVIEW_REQUIRED, "Strict mode requires log review before extraction", "MEDIUM", False)

        if is_json_extension(ext) and not bool(config.get("allow_json", True)):
            return finish(REVIEW_REQUIRED, "Strict mode requires JSON review before extraction", "MEDIUM", False)

    if reject_unhashed and hash_status not in {"HASHED", "HASH_NOT_REQUESTED"}:
        return finish(REVIEW_REQUIRED, f"Hash required or hash status not acceptable: {hash_status}", "MEDIUM", False)

    if rag_status != DISCOVERY_READY:
        return finish(REVIEW_REQUIRED, f"Unexpected discovery status: {rag_status}", "MEDIUM", False)

    return finish(SAFE_FOR_EXTRACTION, "Passed safety filter", "LOW", True)


def deduplicate_safe_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    safe: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []

    seen_sha: set[str] = set()
    seen_paths: set[str] = set()

    for record in records:
        if record.get("safety_status") != SAFE_FOR_EXTRACTION:
            continue

        path_key = normalize_path_text(record.get("file_path"))
        sha = str(record.get("sha256") or "").strip()

        if path_key in seen_paths:
            dup = dict(record)
            dup["safety_status"] = DUPLICATE_SKIPPED
            dup["safety_reason"] = "Duplicate file_path in safety output"
            dup["extraction_allowed"] = False
            duplicates.append(dup)
            continue

        if sha and sha in seen_sha:
            dup = dict(record)
            dup["safety_status"] = DUPLICATE_SKIPPED
            dup["safety_reason"] = "Duplicate SHA-256 in safety output"
            dup["extraction_allowed"] = False
            duplicates.append(dup)
            continue

        seen_paths.add(path_key)
        if sha:
            seen_sha.add(sha)

        safe.append(record)

    return safe, duplicates


def split_records(classified: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    safe_pre, duplicates = deduplicate_safe_records(classified)

    rejected: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    for record in classified:
        status = record.get("safety_status")

        if status == SAFE_FOR_EXTRACTION:
            continue

        if status in {REVIEW_REQUIRED, SENSITIVE_SKIP}:
            review.append(record)
        else:
            rejected.append(record)

    rejected.extend(duplicates)

    return safe_pre, rejected, review


def summarize(
    input_count: int,
    safe: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    review: list[dict[str, Any]],
    classified: list[dict[str, Any]],
    started_at: str,
    ended_at: str,
    paths: SafetyPaths,
    strict_mode: bool,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    extension_counts_safe: dict[str, int] = {}
    rejected_reason_counts: dict[str, int] = {}

    total_safe_size_bytes = 0

    for record in classified:
        status = str(record.get("safety_status") or "UNKNOWN")
        risk = str(record.get("risk_level") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

        if status != SAFE_FOR_EXTRACTION:
            reason = str(record.get("safety_reason") or "UNKNOWN")
            reason_key = reason[:120]
            rejected_reason_counts[reason_key] = rejected_reason_counts.get(reason_key, 0) + 1

    for record in safe:
        ext = str(record.get("extension") or "[no extension]")
        extension_counts_safe[ext] = extension_counts_safe.get(ext, 0) + 1

        size = record.get("size_bytes")
        if isinstance(size, int):
            total_safe_size_bytes += size

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "SAFETY_FILTER_AUDIT_LOCKED",
        "strict_mode": strict_mode,
        "input_file_index": str(paths.input_file_index),
        "input_records": input_count,
        "classified_records": len(classified),
        "safe_for_extraction": len(safe),
        "quarantine_or_rejected": len(rejected),
        "review_required": len(review),
        "safe_size_bytes": total_safe_size_bytes,
        "safe_size_mb": round(total_safe_size_bytes / (1024 * 1024), 2),
        "status_counts": dict(sorted(status_counts.items())),
        "risk_counts": dict(sorted(risk_counts.items())),
        "safe_extension_counts": dict(sorted(extension_counts_safe.items())),
        "top_rejected_or_review_reasons": dict(
            sorted(rejected_reason_counts.items(), key=lambda item: item[1], reverse=True)[:30]
        ),
        "outputs": {
            "safe_jsonl": str(paths.output_safe_jsonl),
            "safe_csv": str(paths.output_safe_csv),
            "rejected_jsonl": str(paths.output_rejected_jsonl),
            "review_jsonl": str(paths.output_review_jsonl),
            "summary_json": str(paths.summary_json),
        },
        "governance_rule": {
            "discovery_index_not_directly_extractable": True,
            "safe_file_index_required_for_extraction": True,
            "sensitive_files_never_extracted_by_default": True,
            "source_file_remains_authoritative": True,
        },
    }


def print_summary(summary: dict[str, Any]) -> None:
    print("=" * 100)
    print("TITAN RAG SAFETY FILTER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Started:                 {summary['started_at']}")
    print(f"Ended:                   {summary['ended_at']}")
    print(f"Policy:                  {summary['policy']}")
    print(f"Strict mode:             {summary['strict_mode']}")
    print(f"Input records:            {summary['input_records']}")
    print(f"Safe for extraction:      {summary['safe_for_extraction']}")
    print(f"Rejected/quarantine:      {summary['quarantine_or_rejected']}")
    print(f"Review required:          {summary['review_required']}")
    print(f"Safe size MB:             {summary['safe_size_mb']}")
    print("-" * 100)
    print("Safety status counts:")
    for key, value in summary["status_counts"].items():
        print(f" - {key}: {value}")
    print("-" * 100)
    for key, value in summary["outputs"].items():
        print(f"{key}: {value}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 02 — Safety filter for discovered files."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--config",
        default=None,
        help="Optional config.json path.",
    )

    parser.add_argument(
        "--input",
        default=None,
        help="Optional input file_index.jsonl path.",
    )

    parser.add_argument(
        "--allowed",
        action="append",
        default=None,
        help="Override allowed extension. Can be repeated, e.g. --allowed .pdf --allowed .docx",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use stricter filtering rules.",
    )

    parser.add_argument(
        "--reject-unhashed",
        action="store_true",
        help="Send records with failed/skipped hash to review/reject logic.",
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap for testing.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Classify and print summary without writing indexes.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, config_arg=args.config, input_arg=args.input)

    started_at = utc_now_iso()

    try:
        config = ensure_config(paths.config_path)
        strict_mode = bool(args.strict or config.get("strict_mode", False))

        allowed_override = None
        if args.allowed:
            allowed_override = {normalize_ext(x) for x in args.allowed}

        records = read_jsonl(paths.input_file_index)
        if args.max_records is not None:
            records = records[: int(args.max_records)]

        classified = [
            classify_record(
                record=record,
                config=config,
                strict_mode=strict_mode,
                allowed_override=allowed_override,
                reject_unhashed=bool(args.reject_unhashed),
            )
            for record in records
        ]

        safe, rejected, review = split_records(classified)

        ended_at = utc_now_iso()

        summary = summarize(
            input_count=len(records),
            safe=safe,
            rejected=rejected,
            review=review,
            classified=classified,
            started_at=started_at,
            ended_at=ended_at,
            paths=paths,
            strict_mode=strict_mode,
        )

        if not args.dry_run:
            write_jsonl(paths.output_safe_jsonl, safe)
            write_csv(paths.output_safe_csv, safe)
            write_jsonl(paths.output_rejected_jsonl, rejected)
            write_jsonl(paths.output_review_jsonl, review)
            write_json(paths.summary_json, summary)

            append_jsonl(paths.audit_log, {
                "timestamp": utc_now_iso(),
                "event": "SAFETY_FILTER_COMPLETED",
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "config_path": str(paths.config_path),
                "input_file_index": str(paths.input_file_index),
                "summary": summary,
            })
        else:
            print(json.dumps(summary, indent=2, ensure_ascii=False))

        print_summary(summary)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "SAFETY_FILTER_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "input_file_index": str(paths.input_file_index),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG SAFETY FILTER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
