#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_discover_files.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 01 — File Discovery Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Create a deterministic, audit-grade inventory of candidate files for the TITAN
Local Evidence RAG pipeline.

This script does NOT extract text.
This script does NOT execute files.
This script does NOT open documents semantically.
This script only discovers files and writes metadata.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Outputs
-------
01_index/file_index.jsonl
01_index/file_index.csv
05_reports/discovery_summary.json
06_logs/discovery_audit.jsonl
06_logs/discovery_errors.jsonl

Designed for compatibility with:
02_safety_filter.py
03_extract_text.py
09_incremental_refresh.py
20_rag_control_tower_export.py

Default base directory
----------------------
C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG

Recommended command
-------------------
python ".\\08_scripts\\01_discover_files.py"

Full user-profile scan
----------------------
python ".\\08_scripts\\01_discover_files.py" --root "C:\\Users\\Korisnik"

Hash metadata for smaller files
-------------------------------
python ".\\08_scripts\\01_discover_files.py" --hash --hash-limit-mb 50
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_NAME = "01_discover_files.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

CONFIG_RELATIVE = Path("00_config") / "config.json"

OUTPUT_INDEX_JSONL = Path("01_index") / "file_index.jsonl"
OUTPUT_INDEX_CSV = Path("01_index") / "file_index.csv"
OUTPUT_SUMMARY_JSON = Path("05_reports") / "discovery_summary.json"
AUDIT_LOG = Path("06_logs") / "discovery_audit.jsonl"
ERROR_LOG = Path("06_logs") / "discovery_errors.jsonl"

DEFAULT_HASH_LIMIT_MB = 50
DEFAULT_MAX_FILE_SIZE_MB = 500

STATUS_READY_FOR_EXTRACTION = "READY_FOR_EXTRACTION"
STATUS_SENSITIVE_REVIEW = "SENSITIVE_REVIEW"
STATUS_UNSUPPORTED_EXTENSION = "UNSUPPORTED_EXTENSION"
STATUS_EXCLUDED_PATH = "EXCLUDED_PATH"
STATUS_TOO_LARGE = "TOO_LARGE"
STATUS_ROOT_MISSING = "ROOT_MISSING"
STATUS_ERROR_DISCOVERY = "ERROR_DISCOVERY"
STATUS_SYMLINK_SKIPPED = "SYMLINK_SKIPPED"
STATUS_HIDDEN_SKIPPED = "HIDDEN_SKIPPED"
STATUS_DUPLICATE_PATH = "DUPLICATE_PATH"

DEFAULT_ALLOWED_EXTENSIONS = [
    ".txt", ".md", ".csv", ".json", ".jsonl",
    ".docx", ".xlsx", ".xlsm", ".pptx", ".pdf",
    ".py", ".sql", ".yaml", ".yml", ".log",
]

DEFAULT_BLOCKED_EXTENSIONS = [
    ".exe", ".dll", ".bat", ".cmd", ".ps1", ".psm1",
    ".msi", ".scr", ".com", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".jar", ".bin", ".dat", ".iso", ".img",
    ".sys", ".drv", ".lnk", ".tmp",
]

DEFAULT_EXCLUDE_DIRS = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
    "AppData",
    "node_modules",
    ".git",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "$Recycle.Bin",
    "System Volume Information",
    "Recovery",
    "Temporary Internet Files",
    "INetCache",
    "Cache",
    "Caches",
]

DEFAULT_SENSITIVE_NAME_MARKERS = [
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
    ".pem",
    ".pfx",
    ".p12",
    ".key",
]

HIGH_RISK_NAME_PATTERNS = [
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

DEFAULT_CONFIG = {
    "project_name": "TITAN_LOCAL_EVIDENCE_RAG_ENGINE",
    "version": "v2.0_AUDIT_LOCKED",
    "scan_roots": [
        r"C:\Users\Korisnik\Desktop",
        r"C:\Users\Korisnik\Documents",
        r"C:\Users\Korisnik\Downloads",
        r"C:\Users\Korisnik\OneDrive",
    ],
    "allowed_extensions": DEFAULT_ALLOWED_EXTENSIONS,
    "blocked_extensions": DEFAULT_BLOCKED_EXTENSIONS,
    "exclude_dirs": DEFAULT_EXCLUDE_DIRS,
    "sensitive_name_markers": DEFAULT_SENSITIVE_NAME_MARKERS,
    "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB,
    "include_hidden": False,
    "follow_symlinks": False,
    "hash_enabled_default": False,
    "hash_limit_mb": DEFAULT_HASH_LIMIT_MB,
}


@dataclass(frozen=True)
class DiscoveryPaths:
    base_dir: Path
    config_path: Path
    output_jsonl: Path
    output_csv: Path
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


def normalize_path_for_match(path: Path | str) -> str:
    return str(path).lower().replace("/", "\\")


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


def iso_from_timestamp(ts: float | int | None) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat()
    except Exception:
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def ensure_config(config_path: Path) -> dict[str, Any]:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        config_path.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return dict(DEFAULT_CONFIG)

    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("config.json root must be an object")

        merged = dict(DEFAULT_CONFIG)
        merged.update(loaded)

        # Normalize list fields.
        for key in [
            "scan_roots",
            "allowed_extensions",
            "blocked_extensions",
            "exclude_dirs",
            "sensitive_name_markers",
        ]:
            if not isinstance(merged.get(key), list):
                merged[key] = DEFAULT_CONFIG[key]

        return merged

    except Exception:
        backup_path = config_path.with_suffix(".invalid.json")
        try:
            backup_path.write_text(config_path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        except Exception:
            pass

        config_path.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return dict(DEFAULT_CONFIG)


def resolve_paths(base_dir: Path, config_arg: str | None = None) -> DiscoveryPaths:
    config_path = Path(config_arg) if config_arg else base_dir / CONFIG_RELATIVE

    return DiscoveryPaths(
        base_dir=base_dir,
        config_path=config_path,
        output_jsonl=base_dir / OUTPUT_INDEX_JSONL,
        output_csv=base_dir / OUTPUT_INDEX_CSV,
        summary_json=base_dir / OUTPUT_SUMMARY_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def is_hidden_path(path: Path) -> bool:
    # Cross-platform conservative hidden check.
    try:
        for part in path.parts:
            if part.startswith(".") and part not in {".", ".."}:
                return True

        if platform.system().lower() == "windows":
            try:
                import ctypes  # Windows attribute check.
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attrs == -1:
                    return False
                return bool(attrs & 2)
            except Exception:
                return False

        return False
    except Exception:
        return False


def is_excluded_path(path: Path, exclude_dirs: list[str]) -> tuple[bool, str | None]:
    full = normalize_path_for_match(path)
    parts = {p.lower() for p in path.parts}

    for item in exclude_dirs:
        marker = str(item or "").strip().lower().replace("/", "\\")
        if not marker:
            continue

        # Absolute Windows path prefix.
        if ":\\" in marker:
            if full.startswith(marker):
                return True, item

        # Folder-name match.
        if marker in parts:
            return True, item

        # Defensive noisy match.
        marker_no_space = marker.replace(" ", "")
        full_no_space = full.replace(" ", "")
        if marker_no_space in {
            "node_modules",
            "__pycache__",
            "systemvolumeinformation",
            "$recycle.bin",
        } and marker_no_space in full_no_space:
            return True, item

    return False, None


def path_matches_sensitive_marker(path: Path, markers: list[str]) -> tuple[bool, str | None]:
    lower = str(path).lower()

    for marker in markers:
        value = str(marker or "").lower().strip()
        if not value:
            continue
        if value in lower:
            return True, marker

    for pattern in HIGH_RISK_NAME_PATTERNS:
        try:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                return True, pattern
        except re.error:
            continue

    return False, None


def safe_stat(path: Path) -> os.stat_result | None:
    try:
        return path.stat()
    except Exception:
        return None


def sha256_file(path: Path, max_mb: int) -> tuple[str | None, str]:
    try:
        stat_obj = path.stat()
        max_bytes = int(max_mb) * 1024 * 1024

        if stat_obj.st_size > max_bytes:
            return None, "HASH_SKIPPED_TOO_LARGE"

        digest = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(block)

        return digest.hexdigest(), "HASHED"

    except Exception as exc:
        return None, f"HASH_ERROR:{exc}"


def determine_rag_status(
    path: Path,
    stat_obj: os.stat_result | None,
    config: dict[str, Any],
    include_hidden: bool,
    follow_symlinks: bool,
) -> tuple[str, str]:
    if stat_obj is None:
        return STATUS_ERROR_DISCOVERY, "Could not read file metadata"

    if path.is_symlink() and not follow_symlinks:
        return STATUS_SYMLINK_SKIPPED, "Symlink skipped by default"

    if not include_hidden and is_hidden_path(path):
        return STATUS_HIDDEN_SKIPPED, "Hidden file/path skipped by default"

    excluded, matched_rule = is_excluded_path(path, list(config.get("exclude_dirs", [])))
    if excluded:
        return STATUS_EXCLUDED_PATH, f"Path matches excluded directory rule: {matched_rule}"

    if path.name.startswith("~$"):
        return STATUS_EXCLUDED_PATH, "Temporary Office lock file"

    ext = normalize_ext(path.suffix)
    allowed = {normalize_ext(x) for x in config.get("allowed_extensions", [])}
    blocked = {normalize_ext(x) for x in config.get("blocked_extensions", [])}

    if ext in blocked:
        return STATUS_UNSUPPORTED_EXTENSION, f"Blocked extension: {ext or '[no extension]'}"

    if ext not in allowed:
        return STATUS_UNSUPPORTED_EXTENSION, f"Unsupported extension: {ext or '[no extension]'}"

    max_mb = safe_float(config.get("max_file_size_mb"), DEFAULT_MAX_FILE_SIZE_MB)
    size_mb = stat_obj.st_size / (1024 * 1024)

    if size_mb > max_mb:
        return STATUS_TOO_LARGE, f"File exceeds max_file_size_mb={max_mb}"

    sensitive, marker = path_matches_sensitive_marker(path, list(config.get("sensitive_name_markers", [])))
    if sensitive:
        return STATUS_SENSITIVE_REVIEW, f"Sensitive filename/path marker detected: {marker}"

    return STATUS_READY_FOR_EXTRACTION, "File is ready for safety filter"


def build_record(
    path: Path,
    root: Path,
    config: dict[str, Any],
    include_hidden: bool,
    follow_symlinks: bool,
    compute_hash: bool,
    hash_limit_mb: int,
) -> dict[str, Any]:
    stat_obj = safe_stat(path)
    rag_status, status_reason = determine_rag_status(
        path=path,
        stat_obj=stat_obj,
        config=config,
        include_hidden=include_hidden,
        follow_symlinks=follow_symlinks,
    )

    file_hash = None
    hash_status = "HASH_NOT_REQUESTED"

    if compute_hash and stat_obj is not None and rag_status in {
        STATUS_READY_FOR_EXTRACTION,
        STATUS_SENSITIVE_REVIEW,
    }:
        file_hash, hash_status = sha256_file(path, max_mb=hash_limit_mb)

    size_bytes = stat_obj.st_size if stat_obj else None
    size_mb = round(size_bytes / (1024 * 1024), 4) if size_bytes is not None else None

    try:
        relative_path = str(path.relative_to(root))
    except Exception:
        relative_path = None

    return {
        "discovered_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "scan_root": str(root),
        "file_path": str(path),
        "relative_path": relative_path,
        "file_name": path.name,
        "stem": path.stem,
        "extension": normalize_ext(path.suffix),
        "parent_folder": str(path.parent),
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "created_time_utc": iso_from_timestamp(stat_obj.st_ctime if stat_obj else None),
        "modified_time_utc": iso_from_timestamp(stat_obj.st_mtime if stat_obj else None),
        "accessed_time_utc": iso_from_timestamp(stat_obj.st_atime if stat_obj else None),
        "is_symlink": path.is_symlink(),
        "is_hidden": is_hidden_path(path),
        "rag_status": rag_status,
        "status_reason": status_reason,
        "sha256": file_hash,
        "hash_status": hash_status,
    }


def root_missing_record(root: Path) -> dict[str, Any]:
    return {
        "discovered_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "scan_root": str(root),
        "file_path": str(root),
        "relative_path": None,
        "file_name": root.name,
        "stem": root.stem,
        "extension": "",
        "parent_folder": str(root.parent),
        "size_bytes": None,
        "size_mb": None,
        "created_time_utc": None,
        "modified_time_utc": None,
        "accessed_time_utc": None,
        "is_symlink": False,
        "is_hidden": False,
        "rag_status": STATUS_ROOT_MISSING,
        "status_reason": "Configured scan root does not exist",
        "sha256": None,
        "hash_status": "HASH_NOT_APPLICABLE",
    }


def discovery_error_record(root: Path, path: Path, exc: Exception) -> dict[str, Any]:
    return {
        "discovered_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "scan_root": str(root),
        "file_path": str(path),
        "relative_path": None,
        "file_name": path.name,
        "stem": path.stem,
        "extension": normalize_ext(path.suffix),
        "parent_folder": str(path.parent),
        "size_bytes": None,
        "size_mb": None,
        "created_time_utc": None,
        "modified_time_utc": None,
        "accessed_time_utc": None,
        "is_symlink": path.is_symlink() if path.exists() else False,
        "is_hidden": False,
        "rag_status": STATUS_ERROR_DISCOVERY,
        "status_reason": str(exc),
        "sha256": None,
        "hash_status": "HASH_NOT_APPLICABLE",
    }


def iter_files(
    root: Path,
    config: dict[str, Any],
    include_hidden: bool,
    follow_symlinks: bool,
) -> Iterable[Path]:
    exclude_dirs = list(config.get("exclude_dirs", []))

    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        current_dir = Path(dirpath)

        kept_dirnames = []
        for dirname in dirnames:
            candidate = current_dir / dirname

            excluded, _ = is_excluded_path(candidate, exclude_dirs)
            if excluded:
                continue

            if not include_hidden and is_hidden_path(candidate):
                continue

            if candidate.is_symlink() and not follow_symlinks:
                continue

            kept_dirnames.append(dirname)

        dirnames[:] = kept_dirnames

        for filename in filenames:
            yield current_dir / filename


def discover_files(
    roots: list[Path],
    config: dict[str, Any],
    include_hidden: bool,
    follow_symlinks: bool,
    compute_hash: bool,
    hash_limit_mb: int,
    max_files: int | None,
    error_log: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    discovered_count = 0

    for root in roots:
        if not root.exists():
            records.append(root_missing_record(root))
            continue

        try:
            root = root.resolve() if root.exists() else root
        except Exception:
            pass

        for path in iter_files(
            root=root,
            config=config,
            include_hidden=include_hidden,
            follow_symlinks=follow_symlinks,
        ):
            try:
                norm = normalize_path_for_match(path)
                if norm in seen_paths:
                    record = build_record(
                        path=path,
                        root=root,
                        config=config,
                        include_hidden=include_hidden,
                        follow_symlinks=follow_symlinks,
                        compute_hash=False,
                        hash_limit_mb=hash_limit_mb,
                    )
                    record["rag_status"] = STATUS_DUPLICATE_PATH
                    record["status_reason"] = "Duplicate path discovered through multiple roots"
                    records.append(record)
                    continue

                seen_paths.add(norm)

                record = build_record(
                    path=path,
                    root=root,
                    config=config,
                    include_hidden=include_hidden,
                    follow_symlinks=follow_symlinks,
                    compute_hash=compute_hash,
                    hash_limit_mb=hash_limit_mb,
                )
                records.append(record)
                discovered_count += 1

                if discovered_count % 1000 == 0:
                    print(f"[DISCOVERY] scanned files={discovered_count} records={len(records)}")

                if max_files is not None and discovered_count >= max_files:
                    return records

            except Exception as exc:
                err_record = discovery_error_record(root=root, path=path, exc=exc)
                records.append(err_record)
                append_jsonl(error_log, {
                    "timestamp": utc_now_iso(),
                    "event": "FILE_DISCOVERY_RECORD_FAILED",
                    "script": SCRIPT_NAME,
                    "script_version": SCRIPT_VERSION,
                    "root": str(root),
                    "path": str(path),
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                })

                if max_files is not None and discovered_count >= max_files:
                    return records

    return records


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "discovered_at",
        "script",
        "script_version",
        "scan_root",
        "file_path",
        "relative_path",
        "file_name",
        "stem",
        "extension",
        "parent_folder",
        "size_bytes",
        "size_mb",
        "created_time_utc",
        "modified_time_utc",
        "accessed_time_utc",
        "is_symlink",
        "is_hidden",
        "rag_status",
        "status_reason",
        "sha256",
        "hash_status",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def summarize_records(
    records: list[dict[str, Any]],
    started_at: str,
    ended_at: str,
    config_path: Path,
    roots: list[Path],
    compute_hash: bool,
    hash_limit_mb: int,
    include_hidden: bool,
    follow_symlinks: bool,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    extension_counts: dict[str, int] = {}
    root_counts: dict[str, int] = {}
    hash_counts: dict[str, int] = {}

    total_size_bytes = 0
    ready_for_extraction = 0
    sensitive_review = 0

    largest_files: list[dict[str, Any]] = []

    for record in records:
        status = str(record.get("rag_status") or "UNKNOWN")
        ext = str(record.get("extension") or "[no extension]")
        root = str(record.get("scan_root") or "[unknown root]")
        hash_status = str(record.get("hash_status") or "UNKNOWN")

        status_counts[status] = status_counts.get(status, 0) + 1
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
        root_counts[root] = root_counts.get(root, 0) + 1
        hash_counts[hash_status] = hash_counts.get(hash_status, 0) + 1

        if status == STATUS_READY_FOR_EXTRACTION:
            ready_for_extraction += 1

        if status == STATUS_SENSITIVE_REVIEW:
            sensitive_review += 1

        size_bytes = record.get("size_bytes")
        if isinstance(size_bytes, int):
            total_size_bytes += size_bytes
            largest_files.append({
                "file_path": record.get("file_path"),
                "size_mb": record.get("size_mb"),
                "extension": record.get("extension"),
                "rag_status": status,
            })

    largest_files.sort(key=lambda x: safe_float(x.get("size_mb")), reverse=True)

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "DISCOVERY_ONLY_READ_ONLY_AUDIT_LOCKED",
        "config_path": str(config_path),
        "scan_roots": [str(root) for root in roots],
        "parameters": {
            "compute_hash": compute_hash,
            "hash_limit_mb": hash_limit_mb,
            "include_hidden": include_hidden,
            "follow_symlinks": follow_symlinks,
        },
        "total_records": len(records),
        "ready_for_extraction": ready_for_extraction,
        "sensitive_review": sensitive_review,
        "excluded_or_unsupported": (
            status_counts.get(STATUS_EXCLUDED_PATH, 0)
            + status_counts.get(STATUS_UNSUPPORTED_EXTENSION, 0)
            + status_counts.get(STATUS_TOO_LARGE, 0)
            + status_counts.get(STATUS_HIDDEN_SKIPPED, 0)
            + status_counts.get(STATUS_SYMLINK_SKIPPED, 0)
        ),
        "error_records": status_counts.get(STATUS_ERROR_DISCOVERY, 0),
        "root_missing_records": status_counts.get(STATUS_ROOT_MISSING, 0),
        "total_size_bytes": total_size_bytes,
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "status_counts": dict(sorted(status_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "root_counts": dict(sorted(root_counts.items())),
        "hash_counts": dict(sorted(hash_counts.items())),
        "largest_files_top_20": largest_files[:20],
        "governance_rule": {
            "discovery_only": True,
            "no_text_extraction": True,
            "no_file_execution": True,
            "source_file_remains_authoritative": True,
            "safety_filter_required_next": True,
        },
    }


def print_summary(summary: dict[str, Any], paths: DiscoveryPaths) -> None:
    print("=" * 100)
    print("TITAN RAG FILE DISCOVERY v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Started:                {summary['started_at']}")
    print(f"Ended:                  {summary['ended_at']}")
    print(f"Policy:                 {summary['policy']}")
    print(f"Total records:           {summary['total_records']}")
    print(f"Ready for extraction:    {summary['ready_for_extraction']}")
    print(f"Sensitive review:        {summary['sensitive_review']}")
    print(f"Excluded/unsupported:    {summary['excluded_or_unsupported']}")
    print(f"Error records:           {summary['error_records']}")
    print(f"Root missing records:    {summary['root_missing_records']}")
    print(f"Total size MB:           {summary['total_size_mb']}")
    print("-" * 100)
    print("Status counts:")
    for key, value in summary["status_counts"].items():
        print(f" - {key}: {value}")
    print("-" * 100)
    print(f"Index JSONL:             {paths.output_jsonl}")
    print(f"Index CSV:               {paths.output_csv}")
    print(f"Summary JSON:            {paths.summary_json}")
    print(f"Audit log:               {paths.audit_log}")
    print(f"Error log:               {paths.error_log}")
    print("=" * 100)


def parse_roots(args: argparse.Namespace, config: dict[str, Any]) -> list[Path]:
    roots_from_args = args.root or []
    roots_raw = roots_from_args if roots_from_args else config.get("scan_roots", [])

    roots: list[Path] = []
    for item in roots_raw:
        text = str(item or "").strip()
        if not text:
            continue
        roots.append(Path(text))

    return roots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 01 — Audit-grade file discovery engine."
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
        "--root",
        action="append",
        default=None,
        help="Scan root. Can be repeated. Overrides config scan_roots.",
    )

    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional maximum number of files to discover for test runs.",
    )

    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files/folders. Default is false.",
    )

    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symlinks. Default is false.",
    )

    parser.add_argument(
        "--hash",
        action="store_true",
        help="Compute SHA-256 for eligible files up to --hash-limit-mb.",
    )

    parser.add_argument(
        "--hash-limit-mb",
        type=int,
        default=None,
        help="Maximum file size for hashing in MB.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load config and print planned roots, but do not scan.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, config_arg=args.config)

    started_at = utc_now_iso()

    try:
        config = ensure_config(paths.config_path)
        roots = parse_roots(args, config)

        include_hidden = bool(args.include_hidden or config.get("include_hidden", False))
        follow_symlinks = bool(args.follow_symlinks or config.get("follow_symlinks", False))
        compute_hash = bool(args.hash or config.get("hash_enabled_default", False))
        hash_limit_mb = int(args.hash_limit_mb or config.get("hash_limit_mb", DEFAULT_HASH_LIMIT_MB))

        if args.dry_run:
            summary = {
                "started_at": started_at,
                "ended_at": utc_now_iso(),
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "policy": "DRY_RUN_NO_SCAN",
                "config_path": str(paths.config_path),
                "planned_scan_roots": [str(root) for root in roots],
                "parameters": {
                    "include_hidden": include_hidden,
                    "follow_symlinks": follow_symlinks,
                    "compute_hash": compute_hash,
                    "hash_limit_mb": hash_limit_mb,
                    "max_files": args.max_files,
                },
            }

            write_json(paths.summary_json, summary)
            append_jsonl(paths.audit_log, {
                "timestamp": utc_now_iso(),
                "event": "DISCOVERY_DRY_RUN_COMPLETED",
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "summary": summary,
            })

            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return

        records = discover_files(
            roots=roots,
            config=config,
            include_hidden=include_hidden,
            follow_symlinks=follow_symlinks,
            compute_hash=compute_hash,
            hash_limit_mb=hash_limit_mb,
            max_files=args.max_files,
            error_log=paths.error_log,
        )

        ended_at = utc_now_iso()

        summary = summarize_records(
            records=records,
            started_at=started_at,
            ended_at=ended_at,
            config_path=paths.config_path,
            roots=roots,
            compute_hash=compute_hash,
            hash_limit_mb=hash_limit_mb,
            include_hidden=include_hidden,
            follow_symlinks=follow_symlinks,
        )

        write_jsonl(paths.output_jsonl, records)
        write_csv(paths.output_csv, records)
        write_json(paths.summary_json, summary)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "DISCOVERY_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "outputs": {
                "file_index_jsonl": str(paths.output_jsonl),
                "file_index_csv": str(paths.output_csv),
                "summary_json": str(paths.summary_json),
                "error_log": str(paths.error_log),
            },
            "summary": summary,
        })

        print_summary(summary, paths)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "DISCOVERY_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG FILE DISCOVERY FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
