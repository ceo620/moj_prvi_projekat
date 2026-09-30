#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_discover_files_v8_1_AUDIT_LOCKED.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 01 — File Discovery Engine
Version: v8.1_COMPLIANCE_HEURISTICS_AUDIT_HARDENED

Purpose
-------
Create a deterministic, audit-grade, read-only inventory of candidate files for
TITAN Local Evidence RAG. V8 adds a bounded HeuristicsEngine for forensic
pre-screening without document parsing, OCR, embeddings, semantic extraction,
LLM visibility, or source-file modification.

Core doctrine
-------------
Evidence precedes intelligence.
Audit precedes decision.
No extraction before safety classification.
Controlled header sampling is not text extraction.

V8 additions
------------
1. Magic-byte extension verification.
2. Shannon entropy on a bounded header sample.
3. Temporal burst detection as post-processing.
4. Directory depth complexity.
5. Regex maturity vectoring from filename/path only.
6. Gini coefficient of risk concentration by directory.
7. Benford size-distribution report.
8. Orphaned asset report from access timestamps.
9. Spatial marker aggregation report.

Important boundary
------------------
Filename/path heuristics are prioritization signals only. They are not content
classification, legal verification, financial validation, or lender evidence.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import math
import os
import platform
import re
import socket
import sys
import tempfile
import time
import traceback
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCRIPT_NAME = "01_discover_files_v8_1_AUDIT_LOCKED.py"
SCRIPT_VERSION = "v8.1_COMPLIANCE_HEURISTICS_AUDIT_HARDENED"
SCHEMA_VERSION = "discovery.record.schema.v8.1"
SSOT_DOMAIN = "TITAN_LOCAL_EVIDENCE_RAG"
EVIDENCE_DOCTRINE = "EVIDENCE_PRECEDES_INTELLIGENCE"
PIPELINE_STAGE = "01_DISCOVERY"
POLICY_NAME = "DISCOVERY_ONLY_READ_ONLY_HEURISTICS_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
CONFIG_RELATIVE = Path("00_config") / "config.json"

OUTPUT_INDEX_JSONL = Path("01_index") / "file_index.jsonl"
OUTPUT_INDEX_CSV = Path("01_index") / "file_index.csv"
OUTPUT_HANDOFF_JSONL = Path("02_handoff") / "candidates_for_safety_filter.jsonl"
OUTPUT_SUMMARY_JSON = Path("05_reports") / "discovery_summary.json"
OUTPUT_MANIFEST_JSON = Path("05_reports") / "discovery_manifest.json"
OUTPUT_LATEST_MANIFEST_JSON = Path("05_reports") / "discovery_manifest.latest.json"
OUTPUT_SCHEMA_JSON = Path("05_reports") / "discovery_schema_v8_1.json"
OUTPUT_SSOT_REGISTER_JSON = Path("05_reports") / "discovery_ssot_register.json"
OUTPUT_METRICS_JSON = Path("05_reports") / "discovery_metrics.json"
OUTPUT_MERKLE_LEDGER_JSON = Path("05_reports") / "discovery_merkle_ledger.json"
OUTPUT_HEURISTICS_REPORT_JSON = Path("05_reports") / "discovery_heuristics_report.json"
OUTPUT_COMPLIANCE_ADDENDUM_JSON = Path("05_reports") / "discovery_compliance_addendum.json"
OUTPUT_RUN_LEDGER_JSONL = Path("05_reports") / "discovery_run_ledger.jsonl"
AUDIT_LOG = Path("06_logs") / "discovery_audit.jsonl"
ERROR_LOG = Path("06_logs") / "discovery_errors.jsonl"
SKIPPED_DIRS_LOG = Path("06_logs") / "skipped_directories.jsonl"

DEFAULT_HASH_LIMIT_MB = 50
DEFAULT_MAX_FILE_SIZE_MB = 500
DEFAULT_MAX_PATH_LENGTH_WARN = 240
DEFAULT_MAX_WORKERS = min(8, os.cpu_count() or 4)
READ_BLOCK_SIZE = 1024 * 1024
DEFAULT_HEADER_SAMPLE_BYTES = 256
DEFAULT_MAGIC_SAMPLE_BYTES = 4096
DEFAULT_INCREMENTAL_MTIME_TOLERANCE_SECONDS = 1.0
QUANTITATIVE_RISK_LAMBDA_DAILY = 0.0019
TEMPORAL_BURST_WINDOW_SECONDS = 3
TEMPORAL_BURST_MIN_FILES = 500
HIGH_ENTROPY_THRESHOLD = 7.50

STATUS_CANDIDATE_FOR_SAFETY_FILTER = "CANDIDATE_FOR_SAFETY_FILTER"
STATUS_SENSITIVE_NAME_REVIEW = "SENSITIVE_NAME_REVIEW"
STATUS_BLOCKED_EXTENSION = "BLOCKED_EXTENSION"
STATUS_UNSUPPORTED_EXTENSION = "UNSUPPORTED_EXTENSION"
STATUS_EXCLUDED_PATH = "EXCLUDED_PATH"
STATUS_TOO_LARGE = "TOO_LARGE"
STATUS_ROOT_MISSING = "ROOT_MISSING"
STATUS_ERROR_DISCOVERY = "ERROR_DISCOVERY"
STATUS_SYMLINK_SKIPPED = "SYMLINK_SKIPPED"
STATUS_HIDDEN_SKIPPED = "HIDDEN_SKIPPED"
STATUS_DUPLICATE_PATH = "DUPLICATE_PATH"
STATUS_OFFICE_LOCK_FILE = "OFFICE_LOCK_FILE"
STATUS_EMPTY_FILE = "EMPTY_FILE"
STATUS_ZERO_TRUST_REVIEW = "ZERO_TRUST_REVIEW"

HANDOFF_STATUSES = {STATUS_CANDIDATE_FOR_SAFETY_FILTER, STATUS_SENSITIVE_NAME_REVIEW, STATUS_ZERO_TRUST_REVIEW}

DEFAULT_ALLOWED_EXTENSIONS = [
    ".txt", ".md", ".csv", ".json", ".jsonl", ".docx", ".xlsx", ".xlsm",
    ".pptx", ".pdf", ".rtf", ".py", ".sql", ".yaml", ".yml", ".log",
]
DEFAULT_BLOCKED_EXTENSIONS = [
    ".exe", ".dll", ".bat", ".cmd", ".ps1", ".psm1", ".psd1", ".msi",
    ".scr", ".com", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
    ".jar", ".bin", ".dat", ".iso", ".img", ".sys", ".drv", ".lnk",
    ".tmp", ".apk", ".app", ".deb", ".rpm", ".dmg", ".pkg", ".so", ".dylib",
    ".ocx", ".cpl",
]
DEFAULT_EXCLUDE_DIRS = [
    r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)", r"C:\ProgramData",
    "AppData", "node_modules", ".git", ".svn", ".hg", ".venv", "venv", "env",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".idea", ".vscode",
    "$Recycle.Bin", "System Volume Information", "Recovery", "Temporary Internet Files",
    "INetCache", "Cache", "Caches",
]
DEFAULT_SENSITIVE_NAME_MARKERS = [
    ".env", "password", "passwd", "secret", "token", "api_key", "apikey", "private_key",
    "private-key", "credential", "credentials", "wallet", "seed", "recovery", "mnemonic",
    "auth", "login", "cookie", "session", "ssh", "id_rsa", "id_dsa", "id_ecdsa",
    "id_ed25519", ".pem", ".pfx", ".p12", ".key",
]
INSTITUTIONAL_MARKERS = [
    "capex", "opex", "eib", "ebrd", "ifc", "kfw", "budget", "finance", "audit",
    "invoice", "procurement", "tender", "contract", "subsidy", "transformer", "grid",
    "feasibility", "due_diligence", "risk", "esg", "environmental", "social", "governance",
    "tuzi", "vuksanlekici", "vuksanlekići",
]
SPATIAL_MARKERS = ["tuzi", "vuksanlekici", "vuksanlekići", "podgorica", "trafo", "grid", "mreza", "mreža", "zona"]

DEFAULT_CONFIG: dict[str, Any] = {
    "project_name": "TITAN_LOCAL_EVIDENCE_RAG_ENGINE",
    "version": SCRIPT_VERSION,
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
    "institutional_markers": INSTITUTIONAL_MARKERS,
    "spatial_markers": SPATIAL_MARKERS,
    "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB,
    "max_path_length_warn": DEFAULT_MAX_PATH_LENGTH_WARN,
    "include_hidden": False,
    "follow_symlinks": False,
    "hash_enabled_default": False,
    "hash_limit_mb": DEFAULT_HASH_LIMIT_MB,
    "deterministic_sort": True,
    "emit_handoff_file": True,
    "write_latest_manifest": True,
    "atomic_output_writes": True,
    "max_workers": DEFAULT_MAX_WORKERS,
    "header_heuristics_enabled_default": False,
    "header_sample_bytes": DEFAULT_HEADER_SAMPLE_BYTES,
    "magic_sample_bytes": DEFAULT_MAGIC_SAMPLE_BYTES,
    "store_sample_hex_default": False,
    "incremental_default": False,
    "incremental_mtime_tolerance_seconds": DEFAULT_INCREMENTAL_MTIME_TOLERANCE_SECONDS,
    "quantitative_risk_lambda_daily": QUANTITATIVE_RISK_LAMBDA_DAILY,
    "merkle_ledger_enabled": True,
    "temporal_burst_window_seconds": TEMPORAL_BURST_WINDOW_SECONDS,
    "temporal_burst_min_files": TEMPORAL_BURST_MIN_FILES,
    "high_entropy_threshold": HIGH_ENTROPY_THRESHOLD,
    "orphan_asset_days": 730,
}


@dataclass(frozen=True)
class DiscoveryPaths:
    base_dir: Path
    config_path: Path
    output_jsonl: Path
    output_csv: Path
    handoff_jsonl: Path
    summary_json: Path
    manifest_json: Path
    latest_manifest_json: Path
    schema_json: Path
    ssot_register_json: Path
    metrics_json: Path
    merkle_ledger_json: Path
    heuristics_report_json: Path
    compliance_addendum_json: Path
    run_ledger_jsonl: Path
    audit_log: Path
    error_log: Path
    skipped_dirs_log: Path
    config_snapshot_path: Path


@dataclass
class RuntimeCounters:
    directories_seen: int = 0
    directories_skipped: int = 0
    files_seen: int = 0
    files_recorded: int = 0
    duplicate_paths: int = 0
    errors: int = 0


class HeuristicsEngine:
    """Bounded metadata/header heuristic functions. No content parsing."""

    MATURITY_PATTERNS: list[tuple[str, str]] = [
        ("FINAL_APPROVED", r"(?i)(final|approved|signed|executed|locked)"),
        ("DRAFT", r"(?i)(draft|nacrt|working|wip|temp|tmp)"),
        ("REVISION", r"(?i)(rev(?:ision)?|revised|izmjena|correction|corrected)"),
        ("VERSIONED", r"(?i)(?:^|[_\-\s])v?\d+(?:\.\d+){0,3}(?:$|[_\-\s])"),
        ("DATED", r"(?i)(20\d{2}[-_. ]?(?:0[1-9]|1[0-2])[-_. ]?(?:0[1-9]|[12]\d|3[01]))"),
        ("COPY", r"(?i)(copy|kopija|duplicate|backup|bak)"),
    ]

    @staticmethod
    def shannon_entropy(data: bytes | None) -> float | None:
        if not data:
            return None
        length = len(data)
        counts = Counter(data)
        entropy = 0.0
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return round(entropy, 4)

    @staticmethod
    def magic_type(header: bytes | None) -> str:
        if not header:
            return "NOT_SAMPLED_OR_UNREADABLE"
        if header.startswith(b"MZ"):
            return "WINDOWS_EXECUTABLE_MZ"
        if header.startswith(b"%PDF"):
            return "PDF"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "PNG_IMAGE"
        if header[:2] == b"\xff\xd8":
            return "JPEG_IMAGE"
        if header[:4] == b"GIF8":
            return "GIF_IMAGE"
        if header[:4] == b"PK\x03\x04":
            return "ZIP_CONTAINER_OR_OFFICE_OPEN_XML"
        if header[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            return "OLE_COMPOUND_DOCUMENT"
        stripped = header.lstrip()
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            return "POSSIBLE_JSON_TEXT"
        if all((b in b"\t\n\r" or 32 <= b <= 126) for b in header[: min(128, len(header))]):
            return "POSSIBLE_PLAIN_TEXT"
        return "UNKNOWN_BINARY_OR_TEXT"

    @staticmethod
    def verify_extension_against_magic(ext: str, magic_type: str) -> dict[str, Any]:
        ext = normalize_ext(ext)
        expected = {
            ".pdf": {"PDF"},
            ".docx": {"ZIP_CONTAINER_OR_OFFICE_OPEN_XML"},
            ".xlsx": {"ZIP_CONTAINER_OR_OFFICE_OPEN_XML"},
            ".xlsm": {"ZIP_CONTAINER_OR_OFFICE_OPEN_XML"},
            ".pptx": {"ZIP_CONTAINER_OR_OFFICE_OPEN_XML"},
            ".zip": {"ZIP_CONTAINER_OR_OFFICE_OPEN_XML"},
            ".json": {"POSSIBLE_JSON_TEXT", "POSSIBLE_PLAIN_TEXT"},
            ".jsonl": {"POSSIBLE_JSON_TEXT", "POSSIBLE_PLAIN_TEXT"},
            ".txt": {"POSSIBLE_PLAIN_TEXT", "UNKNOWN_BINARY_OR_TEXT"},
            ".md": {"POSSIBLE_PLAIN_TEXT", "UNKNOWN_BINARY_OR_TEXT"},
            ".csv": {"POSSIBLE_PLAIN_TEXT", "UNKNOWN_BINARY_OR_TEXT"},
            ".log": {"POSSIBLE_PLAIN_TEXT", "UNKNOWN_BINARY_OR_TEXT"},
            ".rtf": {"POSSIBLE_PLAIN_TEXT", "UNKNOWN_BINARY_OR_TEXT"},
            ".exe": {"WINDOWS_EXECUTABLE_MZ"},
            ".dll": {"WINDOWS_EXECUTABLE_MZ"},
        }
        executable_disguised = magic_type == "WINDOWS_EXECUTABLE_MZ" and ext not in {".exe", ".dll", ".scr", ".com"}
        if executable_disguised:
            return {"magic_extension_match": False, "extension_spoofing_signal": True, "magic_verification_status": "CRITICAL_MZ_EXECUTABLE_MISMATCH"}
        if ext in expected and magic_type not in expected[ext] and magic_type != "NOT_SAMPLED_OR_UNREADABLE":
            return {"magic_extension_match": False, "extension_spoofing_signal": True, "magic_verification_status": "MISMATCH"}
        if ext in expected and magic_type in expected[ext]:
            return {"magic_extension_match": True, "extension_spoofing_signal": False, "magic_verification_status": "MATCH"}
        return {"magic_extension_match": None, "extension_spoofing_signal": False, "magic_verification_status": "NO_STRICT_RULE"}

    @staticmethod
    def maturity_vector(path: Path) -> dict[str, Any]:
        text = str(path).replace("\\", "/")
        hits = []
        for label, pattern in HeuristicsEngine.MATURITY_PATTERNS:
            if re.search(pattern, text):
                hits.append(label)
        if "FINAL_APPROVED" in hits:
            level = "FINAL_OR_APPROVED_NAME"
        elif "DRAFT" in hits:
            level = "DRAFT_OR_WORKING_NAME"
        elif "REVISION" in hits or "VERSIONED" in hits:
            level = "VERSIONED_OR_REVISED_NAME"
        elif "COPY" in hits:
            level = "COPY_OR_BACKUP_NAME"
        else:
            level = "UNSPECIFIED"
        return {"maturity_vector": sorted(set(hits)), "maturity_level": level}

    @staticmethod
    def directory_depth(path: Path, root: Path | None = None) -> int:
        try:
            rel = path.relative_to(root) if root else path
            return max(0, len(rel.parts) - 1)
        except Exception:
            return max(0, len(path.parts) - 1)

    @staticmethod
    def path_marker_hits(path: Path, markers: list[str]) -> list[str]:
        haystack = str(path).lower()
        return sorted({m.strip().lower() for m in markers if str(m).strip() and str(m).strip().lower() in haystack})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]


def normalize_ext(value: Any) -> str:
    text = str(value or "").strip().lower()
    return "." + text if text and not text.startswith(".") else text


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
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).replace(microsecond=0).isoformat() if ts is not None else None
    except Exception:
        return None


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    atomic_write_text(path, "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records))


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def stable_policy_hash(config: dict[str, Any]) -> str:
    policy_fields = {
        "allowed_extensions": sorted({normalize_ext(x) for x in config.get("allowed_extensions", [])}),
        "blocked_extensions": sorted({normalize_ext(x) for x in config.get("blocked_extensions", [])}),
        "exclude_dirs": sorted([str(x) for x in config.get("exclude_dirs", [])]),
        "sensitive_name_markers": sorted([str(x).lower() for x in config.get("sensitive_name_markers", [])]),
        "max_file_size_mb": safe_float(config.get("max_file_size_mb"), DEFAULT_MAX_FILE_SIZE_MB),
        "include_hidden": bool(config.get("include_hidden", False)),
        "follow_symlinks": bool(config.get("follow_symlinks", False)),
        "header_heuristics_enabled_default": bool(config.get("header_heuristics_enabled_default", False)),
        "header_sample_bytes": safe_int(config.get("header_sample_bytes"), DEFAULT_HEADER_SAMPLE_BYTES),
        "incremental_mtime_tolerance_seconds": safe_float(config.get("incremental_mtime_tolerance_seconds"), DEFAULT_INCREMENTAL_MTIME_TOLERANCE_SECONDS),
    }
    return hashlib.sha256(json.dumps(policy_fields, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def ensure_config(config_path: Path) -> dict[str, Any]:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        write_json(config_path, DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with config_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        config = dict(DEFAULT_CONFIG)
        config.update(loaded if isinstance(loaded, dict) else {})
        return config
    except Exception:
        backup = config_path.with_suffix(config_path.suffix + ".corrupt")
        try:
            config_path.replace(backup)
        except Exception:
            pass
        write_json(config_path, DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)


def resolve_paths(base_dir: Path, run_id: str, config_arg: str | None) -> DiscoveryPaths:
    config_path = Path(config_arg).expanduser() if config_arg else base_dir / CONFIG_RELATIVE
    return DiscoveryPaths(
        base_dir=base_dir,
        config_path=config_path,
        output_jsonl=base_dir / OUTPUT_INDEX_JSONL,
        output_csv=base_dir / OUTPUT_INDEX_CSV,
        handoff_jsonl=base_dir / OUTPUT_HANDOFF_JSONL,
        summary_json=base_dir / OUTPUT_SUMMARY_JSON,
        manifest_json=base_dir / OUTPUT_MANIFEST_JSON,
        latest_manifest_json=base_dir / OUTPUT_LATEST_MANIFEST_JSON,
        schema_json=base_dir / OUTPUT_SCHEMA_JSON,
        ssot_register_json=base_dir / OUTPUT_SSOT_REGISTER_JSON,
        metrics_json=base_dir / OUTPUT_METRICS_JSON,
        merkle_ledger_json=base_dir / OUTPUT_MERKLE_LEDGER_JSON,
        heuristics_report_json=base_dir / OUTPUT_HEURISTICS_REPORT_JSON,
        compliance_addendum_json=base_dir / OUTPUT_COMPLIANCE_ADDENDUM_JSON,
        run_ledger_jsonl=base_dir / OUTPUT_RUN_LEDGER_JSONL,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
        skipped_dirs_log=base_dir / SKIPPED_DIRS_LOG,
        config_snapshot_path=base_dir / "00_config" / f"config.snapshot.{run_id}.json",
    )


def is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts if part not in {path.anchor, path.drive})


def is_excluded_path(path: Path, exclude_rules: list[str]) -> tuple[bool, str | None]:
    normalized = normalize_path_for_match(path)
    for rule in exclude_rules:
        r = str(rule or "").strip()
        if not r:
            continue
        if normalize_path_for_match(r) in normalized:
            return True, r
    return False, None


def path_matches_sensitive_marker(path: Path, markers: list[str]) -> tuple[bool, str | None]:
    haystack = str(path).lower()
    for marker in markers:
        m = str(marker or "").strip().lower()
        if m and m in haystack:
            return True, m
    return False, None


def file_sha256(path: Path, size_mb: float, hash_limit_mb: int) -> tuple[str | None, str]:
    if size_mb > hash_limit_mb:
        return None, f"HASH_SKIPPED_OVER_LIMIT_MB:{hash_limit_mb}"
    try:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(READ_BLOCK_SIZE), b""):
                digest.update(block)
        return digest.hexdigest(), "HASHED"
    except PermissionError as exc:
        return None, f"HASH_PERMISSION_ERROR:{exc}"
    except Exception as exc:
        return None, f"HASH_ERROR:{exc}"


def read_binary_header(path: Path, sample_bytes: int) -> tuple[bytes | None, str]:
    try:
        with path.open("rb") as f:
            return f.read(max(0, int(sample_bytes))), "SAMPLED"
    except PermissionError as exc:
        return None, f"SAMPLE_PERMISSION_ERROR:{exc}"
    except Exception as exc:
        return None, f"SAMPLE_ERROR:{exc}"


def canonical_identity(path: Path) -> dict[str, Any]:
    try:
        resolved = path.resolve(strict=False)
    except Exception:
        resolved = path.absolute()
    drive = path.drive or getattr(resolved, "drive", "")
    canonical = str(resolved)
    return {
        "canonical_path": canonical,
        "path_key_sha256": hashlib.sha256(canonical.lower().encode("utf-8", errors="ignore")).hexdigest(),
        "source_volume": drive or "[unknown]",
    }


def determine_rag_status(path: Path, stat_obj: os.stat_result | None, config: dict[str, Any], include_hidden: bool, follow_symlinks: bool) -> tuple[str, str, str]:
    if stat_obj is None:
        return STATUS_ERROR_DISCOVERY, "E_METADATA_UNREADABLE", "Could not read file metadata"
    if path.is_symlink() and not follow_symlinks:
        return STATUS_SYMLINK_SKIPPED, "E_SYMLINK_SKIPPED", "Symlink skipped by policy"
    if not include_hidden and is_hidden_path(path):
        return STATUS_HIDDEN_SKIPPED, "E_HIDDEN_SKIPPED", "Hidden file/path skipped by policy"
    excluded, matched_rule = is_excluded_path(path, list(config.get("exclude_dirs", [])))
    if excluded:
        return STATUS_EXCLUDED_PATH, "E_EXCLUDED_PATH", f"Path matches excluded directory rule: {matched_rule}"
    if path.name.startswith("~$"):
        return STATUS_OFFICE_LOCK_FILE, "E_OFFICE_LOCK", "Temporary Office lock file"

    ext = normalize_ext(path.suffix)
    allowed = {normalize_ext(x) for x in config.get("allowed_extensions", [])}
    blocked = {normalize_ext(x) for x in config.get("blocked_extensions", [])}
    if ext in blocked:
        return STATUS_BLOCKED_EXTENSION, "E_BLOCKED_EXTENSION", f"Blocked extension: {ext or '[no extension]'}"
    if ext not in allowed:
        return STATUS_UNSUPPORTED_EXTENSION, "E_UNSUPPORTED_EXTENSION", f"Unsupported extension: {ext or '[no extension]'}"
    if stat_obj.st_size == 0:
        return STATUS_EMPTY_FILE, "E_EMPTY_FILE", "Empty file excluded from downstream extraction"
    max_mb = safe_float(config.get("max_file_size_mb"), DEFAULT_MAX_FILE_SIZE_MB)
    if stat_obj.st_size / (1024 * 1024) > max_mb:
        return STATUS_TOO_LARGE, "E_TOO_LARGE", f"File exceeds max_file_size_mb={max_mb}"
    sensitive, marker = path_matches_sensitive_marker(path, list(config.get("sensitive_name_markers", [])))
    if sensitive:
        return STATUS_SENSITIVE_NAME_REVIEW, "W_SENSITIVE_NAME", f"Sensitive filename/path marker detected: {marker}"
    return STATUS_CANDIDATE_FOR_SAFETY_FILTER, "OK_CANDIDATE", "Candidate for Step 02 safety filter; not approved for extraction yet"


def classify_status_severity(rag_status: str) -> str:
    if rag_status == STATUS_CANDIDATE_FOR_SAFETY_FILTER:
        return "INFO"
    if rag_status in {STATUS_SENSITIVE_NAME_REVIEW, STATUS_ZERO_TRUST_REVIEW}:
        return "WARNING"
    if rag_status in {STATUS_ERROR_DISCOVERY, STATUS_ROOT_MISSING}:
        return "ERROR"
    return "CONTROLLED_SKIP"


def classify_evidence_class(path: Path) -> str:
    ext = normalize_ext(path.suffix)
    if ext in {".xlsx", ".xlsm", ".csv", ".json", ".jsonl"}:
        return "STRUCTURED_OR_SEMI_STRUCTURED"
    if ext in {".pdf", ".docx", ".rtf", ".pptx", ".txt", ".md", ".log"}:
        return "DOCUMENT_TEXT_CANDIDATE"
    if ext in {".py", ".sql", ".yaml", ".yml"}:
        return "CODE_OR_CONFIG_REVIEW"
    return "UNCLASSIFIED_FILESYSTEM_OBJECT"


def parse_iso_datetime(value: Any) -> datetime | None:
    try:
        if not value:
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def calculate_base_risk(record: dict[str, Any]) -> int:
    score = 0
    ext = str(record.get("extension") or "").lower()
    path_text = str(record.get("file_path") or "").lower()
    size_mb = safe_float(record.get("size_mb"), 0.0)
    status = str(record.get("rag_status") or "")
    entropy = record.get("header_entropy")
    spoof = bool(record.get("extension_spoofing_signal"))
    maturity = str(record.get("maturity_level") or "")

    if any(marker in path_text for marker in ["password", "passwd", "secret", "token", "api_key", "apikey", "credential", "private_key", "wallet", "mnemonic", ".env"]):
        score += 45
    if ext in {".pem", ".key", ".pfx", ".p12", ".env"}:
        score += 30
    if ext in {".exe", ".dll", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jar", ".scr", ".msi"}:
        score += 30
    if status == STATUS_SENSITIVE_NAME_REVIEW:
        score += 25
    if status == STATUS_BLOCKED_EXTENSION:
        score += 15
    if bool(record.get("is_hidden")):
        score += 10
    if bool(record.get("is_symlink")):
        score += 10
    if size_mb > 200:
        score += 10
    if spoof:
        score += 35
    if entropy is not None and safe_float(entropy) >= HIGH_ENTROPY_THRESHOLD and ext in {".docx", ".xlsx", ".xlsm", ".pptx", ".pdf", ".txt", ".csv"}:
        score += 12
    if maturity == "DRAFT_OR_WORKING_NAME":
        score += 5
    return min(100, max(0, int(score)))


def calculate_quantitative_scores(record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    base = calculate_base_risk(record)
    modified = parse_iso_datetime(record.get("modified_time_utc"))
    now = datetime.now(timezone.utc)
    age_days = max(0.0, (now - modified).total_seconds() / 86400.0) if modified else 0.0
    lam = safe_float(config.get("quantitative_risk_lambda_daily"), QUANTITATIVE_RISK_LAMBDA_DAILY)
    time_decay = math.exp(-lam * age_days)
    institutional_hits = HeuristicsEngine.path_marker_hits(Path(str(record.get("file_path") or "")), list(config.get("institutional_markers", INSTITUTIONAL_MARKERS)))
    institutional_index = min(100.0, len(institutional_hits) * 10.0)
    quantitative = min(100, max(0, int(round((base * time_decay) + (institutional_index * 0.20)))))
    return {
        "risk_score": base,
        "base_risk_score": base,
        "quantitative_risk_score": quantitative,
        "institutional_compliance_index": round(institutional_index * time_decay, 2),
        "institutional_marker_hits": institutional_hits,
        "file_age_days": round(age_days, 2),
        "time_decay_factor": round(time_decay, 6),
        "quant_model": "PATH_METADATA_AND_OPTIONAL_HEADER_HEURISTIC_ONLY_NO_CONTENT_SEMANTICS",
    }


def build_record(
    path: Path,
    root: Path,
    config: dict[str, Any],
    include_hidden: bool,
    follow_symlinks: bool,
    compute_hash: bool,
    hash_limit_mb: int,
    run_id: str,
    policy_hash: str,
    header_heuristics: bool,
    header_sample_bytes: int,
    store_sample_hex: bool,
) -> dict[str, Any]:
    try:
        stat_obj = path.stat()
    except Exception:
        stat_obj = None
    status, status_code, status_reason = determine_rag_status(path, stat_obj, config, include_hidden, follow_symlinks)
    identity = canonical_identity(path)
    size_bytes = stat_obj.st_size if stat_obj else None
    size_mb = round((size_bytes or 0) / (1024 * 1024), 4) if size_bytes is not None else None
    ext = normalize_ext(path.suffix)

    should_access_binary = bool(header_heuristics and stat_obj is not None and status in HANDOFF_STATUSES)
    header: bytes | None = None
    sample_status = "SAMPLE_NOT_REQUESTED"
    if should_access_binary:
        header, sample_status = read_binary_header(path, max(1, int(header_sample_bytes)))

    magic_type = HeuristicsEngine.magic_type(header) if should_access_binary else "NOT_SAMPLED"
    magic_check = HeuristicsEngine.verify_extension_against_magic(ext, magic_type) if should_access_binary else {
        "magic_extension_match": None,
        "extension_spoofing_signal": False,
        "magic_verification_status": "NOT_SAMPLED",
    }
    entropy = HeuristicsEngine.shannon_entropy(header) if should_access_binary else None
    entropy_flag = bool(entropy is not None and entropy >= safe_float(config.get("high_entropy_threshold"), HIGH_ENTROPY_THRESHOLD))
    maturity = HeuristicsEngine.maturity_vector(path)
    directory_depth = HeuristicsEngine.directory_depth(path, root)
    spatial_tags = HeuristicsEngine.path_marker_hits(path, list(config.get("spatial_markers", SPATIAL_MARKERS)))

    sha256_value = None
    hash_status = "HASH_NOT_REQUESTED"
    if compute_hash and stat_obj is not None and status in HANDOFF_STATUSES:
        sha256_value, hash_status = file_sha256(path, safe_float(size_mb), hash_limit_mb)

    try:
        relative_path = str(path.relative_to(root))
    except Exception:
        relative_path = None

    record = {
        "schema_version": SCHEMA_VERSION,
        "ssot_domain": SSOT_DOMAIN,
        "evidence_doctrine": EVIDENCE_DOCTRINE,
        "run_id": run_id,
        "discovered_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "pipeline_stage": PIPELINE_STAGE,
        "policy_hash": policy_hash,
        "record_uid": hashlib.sha256(f"{run_id}|{identity['path_key_sha256']}".encode("utf-8")).hexdigest(),
        "lineage_parent_run_id": None,
        "scan_root": str(root),
        "file_path": str(path),
        "canonical_path": identity["canonical_path"],
        "path_key_sha256": identity["path_key_sha256"],
        "source_volume": identity["source_volume"],
        "relative_path": relative_path,
        "file_name": path.name,
        "stem": path.stem,
        "extension": ext,
        "parent_folder": str(path.parent),
        "path_length": len(str(path)),
        "path_length_warning": len(str(path)) >= safe_int(config.get("max_path_length_warn"), DEFAULT_MAX_PATH_LENGTH_WARN),
        "directory_depth": directory_depth,
        "directory_depth_warning": directory_depth >= 10,
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "created_time_utc": iso_from_timestamp(stat_obj.st_ctime if stat_obj else None),
        "modified_time_utc": iso_from_timestamp(stat_obj.st_mtime if stat_obj else None),
        "accessed_time_utc": iso_from_timestamp(stat_obj.st_atime if stat_obj else None),
        "is_symlink": path.is_symlink() if path.exists() else False,
        "is_hidden": is_hidden_path(path),
        "rag_status": status,
        "status_code": status_code,
        "status_reason": status_reason,
        "status_severity": classify_status_severity(status),
        "evidence_class": classify_evidence_class(path),
        "content_accessed": bool((compute_hash or should_access_binary) and stat_obj is not None and status in HANDOFF_STATUSES),
        "content_access_purpose": (
            "SHA256_AND_CONTROLLED_HEADER_HEURISTICS_ONLY" if compute_hash and should_access_binary else
            "SHA256_FINGERPRINT_ONLY" if compute_hash and stat_obj is not None and status in HANDOFF_STATUSES else
            "CONTROLLED_HEADER_HEURISTICS_ONLY" if should_access_binary else
            "NONE"
        ),
        "content_read_bytes": (len(header or b"") if should_access_binary else 0),
        "sha256": sha256_value,
        "hash_status": hash_status,
        "header_heuristics_requested": bool(header_heuristics),
        "header_sample_bytes_requested": int(header_sample_bytes) if header_heuristics else 0,
        "sample_status": sample_status,
        "magic_type": magic_type,
        "magic_extension_match": magic_check["magic_extension_match"],
        "extension_spoofing_signal": magic_check["extension_spoofing_signal"],
        "magic_verification_status": magic_check["magic_verification_status"],
        "header_entropy": entropy,
        "high_entropy_signal": entropy_flag,
        "content_sample_hex": (header[:64].hex() if store_sample_hex and header else None),
        "maturity_vector": maturity["maturity_vector"],
        "maturity_level": maturity["maturity_level"],
        "spatial_tags": spatial_tags,
        "incremental_status": "NOT_REQUESTED",
        "downstream_required_stage": "02_safety_filter_v1_AUDIT_LOCKED.py" if status in HANDOFF_STATUSES else None,
        "approved_for_extraction": False,
        "llm_visible": False,
        "embedding_allowed": False,
        "extraction_allowed": False,
    }
    record.update(calculate_quantitative_scores(record, config))
    if record["extension_spoofing_signal"]:
        record["rag_status"] = STATUS_ZERO_TRUST_REVIEW
        record["status_code"] = "W_MAGIC_EXTENSION_MISMATCH"
        record["status_reason"] = "Magic-byte signature does not match extension; requires safety review"
        record["status_severity"] = "WARNING"
        record["downstream_required_stage"] = "02_safety_filter_v1_AUDIT_LOCKED.py"
    return record


def root_missing_record(root: Path, run_id: str, policy_hash: str) -> dict[str, Any]:
    identity = canonical_identity(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "ssot_domain": SSOT_DOMAIN,
        "evidence_doctrine": EVIDENCE_DOCTRINE,
        "run_id": run_id,
        "discovered_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "pipeline_stage": PIPELINE_STAGE,
        "policy_hash": policy_hash,
        "record_uid": hashlib.sha256(f"{run_id}|{identity['path_key_sha256']}".encode("utf-8")).hexdigest(),
        "scan_root": str(root),
        "file_path": str(root),
        "canonical_path": identity["canonical_path"],
        "path_key_sha256": identity["path_key_sha256"],
        "source_volume": identity["source_volume"],
        "file_name": root.name,
        "extension": "",
        "parent_folder": str(root.parent),
        "size_bytes": None,
        "size_mb": None,
        "modified_time_utc": None,
        "rag_status": STATUS_ROOT_MISSING,
        "status_code": "E_ROOT_MISSING",
        "status_reason": "Configured scan root does not exist",
        "status_severity": "ERROR",
        "evidence_class": "SCAN_ROOT",
        "content_accessed": False,
        "content_access_purpose": "NONE",
        "content_read_bytes": 0,
        "risk_score": 0,
        "base_risk_score": 0,
        "quantitative_risk_score": 0,
        "institutional_compliance_index": 0,
        "institutional_marker_hits": [],
        "approved_for_extraction": False,
        "llm_visible": False,
        "embedding_allowed": False,
        "extraction_allowed": False,
    }


def discovery_error_record(root: Path, path: Path, exc: Exception, run_id: str, policy_hash: str) -> dict[str, Any]:
    record = root_missing_record(path, run_id, policy_hash)
    record.update({
        "scan_root": str(root),
        "rag_status": STATUS_ERROR_DISCOVERY,
        "status_code": "E_DISCOVERY_EXCEPTION",
        "status_reason": str(exc),
        "status_severity": "ERROR",
        "risk_score": 100,
        "base_risk_score": 100,
        "quantitative_risk_score": 100,
    })
    return record


def iter_files(root: Path, config: dict[str, Any], include_hidden: bool, follow_symlinks: bool, skipped_dirs_log: Path, run_id: str, counters: RuntimeCounters) -> Iterator[Path]:
    exclude_dirs = list(config.get("exclude_dirs", []))
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        current_dir = Path(dirpath)
        counters.directories_seen += 1
        kept = []
        for dirname in sorted(dirnames, key=str.lower):
            candidate = current_dir / dirname
            reason = None
            excluded, rule = is_excluded_path(candidate, exclude_dirs)
            if excluded:
                reason = f"Excluded directory rule: {rule}"
            elif not include_hidden and is_hidden_path(candidate):
                reason = "Hidden directory skipped"
            elif candidate.is_symlink() and not follow_symlinks:
                reason = "Symlink directory skipped"
            if reason:
                counters.directories_skipped += 1
                append_jsonl(skipped_dirs_log, {"timestamp": utc_now_iso(), "run_id": run_id, "event": "DIRECTORY_SKIPPED", "path": str(candidate), "reason": reason})
            else:
                kept.append(dirname)
        dirnames[:] = kept
        for filename in sorted(filenames, key=str.lower):
            counters.files_seen += 1
            yield current_dir / filename


def load_previous_index(path: Path | None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path or not path.exists():
        return out
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    key = row.get("path_key_sha256")
                    if key:
                        out[str(key)] = row
    except Exception:
        return {}
    return out


def is_unchanged(record: dict[str, Any], previous: dict[str, Any] | None, tolerance: float) -> bool:
    if not previous:
        return False
    if record.get("size_bytes") != previous.get("size_bytes"):
        return False
    a = parse_iso_datetime(record.get("modified_time_utc"))
    b = parse_iso_datetime(previous.get("modified_time_utc"))
    if not a or not b:
        return False
    return abs((a - b).total_seconds()) <= tolerance


def process_single_file(task: tuple[Any, ...]) -> dict[str, Any]:
    (path, root, config, include_hidden, follow_symlinks, compute_hash, hash_limit_mb,
     run_id, policy_hash, header_heuristics, header_sample_bytes, store_sample_hex,
     incremental, previous_index, tolerance) = task
    try:
        record = build_record(path, root, config, include_hidden, follow_symlinks, compute_hash,
                              hash_limit_mb, run_id, policy_hash, header_heuristics,
                              header_sample_bytes, store_sample_hex)
        if incremental:
            previous = previous_index.get(str(record.get("path_key_sha256"))) if previous_index else None
            if is_unchanged(record, previous, tolerance):
                record["incremental_status"] = "UNCHANGED_FROM_PREVIOUS_INDEX"
                record["lineage_parent_run_id"] = previous.get("run_id") if previous else None
            else:
                record["incremental_status"] = "NEW_OR_CHANGED"
        return record
    except Exception as exc:
        return discovery_error_record(root, path, exc, run_id, policy_hash)


def discover_files_parallel(
    roots: list[Path], config: dict[str, Any], include_hidden: bool, follow_symlinks: bool,
    compute_hash: bool, hash_limit_mb: int, max_files: int | None, paths: DiscoveryPaths,
    run_id: str, policy_hash: str, counters: RuntimeCounters, max_workers: int,
    header_heuristics: bool, header_sample_bytes: int, store_sample_hex: bool,
    incremental: bool, previous_index_path: Path | None, skip_unchanged: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    tasks: list[tuple[Any, ...]] = []
    seen: set[str] = set()
    previous_index = load_previous_index(previous_index_path) if incremental else {}
    tolerance = safe_float(config.get("incremental_mtime_tolerance_seconds"), DEFAULT_INCREMENTAL_MTIME_TOLERANCE_SECONDS)

    for raw_root in roots:
        root = raw_root.expanduser()
        if not root.exists():
            records.append(root_missing_record(root, run_id, policy_hash))
            continue
        try:
            root = root.resolve()
        except Exception:
            pass
        for path in iter_files(root, config, include_hidden, follow_symlinks, paths.skipped_dirs_log, run_id, counters):
            norm = normalize_path_for_match(path)
            if norm in seen:
                duplicate = build_record(path, root, config, include_hidden, follow_symlinks, False, hash_limit_mb, run_id, policy_hash, False, 0, False)
                duplicate.update({"rag_status": STATUS_DUPLICATE_PATH, "status_code": "E_DUPLICATE_PATH", "status_reason": "Duplicate path discovered through multiple roots", "downstream_required_stage": None})
                records.append(duplicate)
                counters.duplicate_paths += 1
                continue
            seen.add(norm)
            tasks.append((path, root, config, include_hidden, follow_symlinks, compute_hash, hash_limit_mb, run_id, policy_hash, header_heuristics, header_sample_bytes, store_sample_hex, incremental, previous_index, tolerance))
            if max_files is not None and len(tasks) >= max_files:
                break
        if max_files is not None and len(tasks) >= max_files:
            break

    workers = max(1, int(max_workers or 1))
    if workers == 1:
        for task in tasks:
            record = process_single_file(task)
            counters.files_recorded += 1
            if not (skip_unchanged and record.get("incremental_status") == "UNCHANGED_FROM_PREVIOUS_INDEX"):
                records.append(record)
        return records

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_single_file, task): task[0] for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            path = futures[future]
            counters.files_recorded += 1
            try:
                record = future.result()
                if not (skip_unchanged and record.get("incremental_status") == "UNCHANGED_FROM_PREVIOUS_INDEX"):
                    records.append(record)
            except Exception as exc:
                counters.errors += 1
                records.append(discovery_error_record(Path("."), path, exc, run_id, policy_hash))
                append_jsonl(paths.error_log, {"timestamp": utc_now_iso(), "run_id": run_id, "event": "FILE_DISCOVERY_RECORD_FAILED", "path": str(path), "error": str(exc), "traceback": traceback.format_exc()})
    return records


def csv_fieldnames() -> list[str]:
    return [
        "schema_version", "ssot_domain", "evidence_doctrine", "run_id", "discovered_at", "script", "script_version", "pipeline_stage", "policy_hash",
        "record_uid", "lineage_parent_run_id", "scan_root", "file_path", "canonical_path", "path_key_sha256", "source_volume", "relative_path", "file_name", "stem", "extension", "parent_folder",
        "path_length", "path_length_warning", "directory_depth", "directory_depth_warning", "size_bytes", "size_mb", "created_time_utc", "modified_time_utc", "accessed_time_utc", "is_symlink", "is_hidden",
        "rag_status", "status_code", "status_reason", "status_severity", "evidence_class", "content_accessed", "content_access_purpose", "content_read_bytes", "sha256", "hash_status",
        "header_heuristics_requested", "header_sample_bytes_requested", "sample_status", "magic_type", "magic_extension_match", "extension_spoofing_signal", "magic_verification_status", "header_entropy", "high_entropy_signal", "content_sample_hex",
        "maturity_vector", "maturity_level", "spatial_tags", "risk_score", "base_risk_score", "quantitative_risk_score", "institutional_compliance_index", "institutional_marker_hits", "file_age_days", "time_decay_factor", "quant_model", "incremental_status",
        "downstream_required_stage", "approved_for_extraction", "llm_visible", "embedding_allowed", "extraction_allowed",
    ]


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=csv_fieldnames(), extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow(record)
    atomic_write_text(path, "\ufeff" + buffer.getvalue())


def gini(values: list[float]) -> float:
    clean = sorted([max(0.0, float(v)) for v in values])
    n = len(clean)
    if n == 0:
        return 0.0
    total = sum(clean)
    if total == 0:
        return 0.0
    weighted = sum((i + 1) * value for i, value in enumerate(clean))
    return round((2 * weighted) / (n * total) - (n + 1) / n, 6)


def detect_temporal_bursts(records: list[dict[str, Any]], window_seconds: int, min_files: int) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        dt = parse_iso_datetime(record.get("modified_time_utc"))
        if not dt:
            continue
        bucket = int(dt.timestamp() // max(1, window_seconds))
        buckets[bucket].append(record)
    bursts = []
    for bucket, rows in buckets.items():
        if len(rows) >= min_files:
            sample = rows[:10]
            bursts.append({
                "window_start_utc": datetime.fromtimestamp(bucket * window_seconds, tz=timezone.utc).isoformat(),
                "window_seconds": window_seconds,
                "file_count": len(rows),
                "sample_paths": [r.get("file_path") for r in sample],
            })
    bursts.sort(key=lambda x: x["file_count"], reverse=True)
    return bursts[:50]


def build_heuristics_report(records: list[dict[str, Any]], config: dict[str, Any], run_id: str) -> dict[str, Any]:
    risk_by_dir: dict[str, float] = defaultdict(float)
    count_by_dir: dict[str, int] = defaultdict(int)
    for r in records:
        parent = str(r.get("parent_folder") or "[unknown]")
        risk_by_dir[parent] += safe_float(r.get("risk_score"), 0.0)
        count_by_dir[parent] += 1
    concentration_values = list(risk_by_dir.values())
    top_dirs = sorted([
        {"parent_folder": d, "risk_sum": round(v, 2), "record_count": count_by_dir[d], "avg_risk": round(v / max(1, count_by_dir[d]), 2)}
        for d, v in risk_by_dir.items()
    ], key=lambda x: x["risk_sum"], reverse=True)[:20]
    temporal_bursts = detect_temporal_bursts(
        records,
        safe_int(config.get("temporal_burst_window_seconds"), TEMPORAL_BURST_WINDOW_SECONDS),
        safe_int(config.get("temporal_burst_min_files"), TEMPORAL_BURST_MIN_FILES),
    )
    maturity_counts = Counter(str(r.get("maturity_level") or "UNKNOWN") for r in records)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "created_at": utc_now_iso(),
        "doctrine": "CONTROLLED_METADATA_AND_HEADER_HEURISTICS_ONLY",
        "header_entropy": {
            "sampled_records": sum(1 for r in records if r.get("header_entropy") is not None),
            "high_entropy_records": sum(1 for r in records if r.get("high_entropy_signal")),
            "threshold": safe_float(config.get("high_entropy_threshold"), HIGH_ENTROPY_THRESHOLD),
        },
        "magic_verification": {
            "sampled_records": sum(1 for r in records if r.get("magic_verification_status") not in {None, "NOT_SAMPLED"}),
            "extension_spoofing_signals": sum(1 for r in records if r.get("extension_spoofing_signal")),
            "critical_mz_mismatches": sum(1 for r in records if r.get("magic_verification_status") == "CRITICAL_MZ_EXECUTABLE_MISMATCH"),
        },
        "temporal_burst_detection": {
            "window_seconds": safe_int(config.get("temporal_burst_window_seconds"), TEMPORAL_BURST_WINDOW_SECONDS),
            "min_files": safe_int(config.get("temporal_burst_min_files"), TEMPORAL_BURST_MIN_FILES),
            "bursts_detected": len(temporal_bursts),
            "bursts": temporal_bursts,
        },
        "directory_depth_complexity": {
            "avg_depth": round(sum(safe_int(r.get("directory_depth"), 0) for r in records) / len(records), 2) if records else 0,
            "max_depth": max([safe_int(r.get("directory_depth"), 0) for r in records], default=0),
            "deep_records_ge_10": sum(1 for r in records if safe_int(r.get("directory_depth"), 0) >= 10),
        },
        "maturity_vectoring": dict(sorted(maturity_counts.items())),
        "risk_concentration": {
            "gini_coefficient": gini(concentration_values),
            "top_risk_directories": top_dirs,
            "interpretation": "0 means evenly distributed risk; values closer to 1 indicate risk concentration in fewer directories.",
        },
        "model_warning": "All signals are metadata/path/header heuristics. They are not document-content findings.",
    }


def first_digit(value: Any) -> str | None:
    n = abs(safe_int(value, 0))
    if n <= 0:
        return None
    return str(n)[0]


def build_compliance_addendum(records: list[dict[str, Any]], config: dict[str, Any], run_id: str) -> dict[str, Any]:
    """V8.1 post-processing only: no document parsing, no OCR, no semantic extraction."""
    orphan_days = safe_int(config.get("orphan_asset_days"), 730)
    now_ts = datetime.now(timezone.utc).timestamp()
    first_digit_counts: Counter[str] = Counter()
    size_records = 0
    for r in records:
        d = first_digit(r.get("size_bytes"))
        if d:
            first_digit_counts[d] += 1
            size_records += 1
    benford_expected = {str(i): round(math.log10(1 + 1 / i), 4) for i in range(1, 10)}
    benford_observed = {str(i): round(first_digit_counts.get(str(i), 0) / size_records, 4) if size_records else 0.0 for i in range(1, 10)}
    benford_abs_deviation = round(sum(abs(benford_observed[str(i)] - benford_expected[str(i)]) for i in range(1, 10)), 4)

    orphan_candidates = []
    for r in records:
        accessed = r.get("accessed_time_utc")
        if not accessed:
            continue
        try:
            atime_ts = datetime.fromisoformat(str(accessed).replace("Z", "+00:00")).timestamp()
            age_days = int(max(0, (now_ts - atime_ts) / 86400))
            if age_days >= orphan_days:
                orphan_candidates.append({
                    "file_path": r.get("file_path"),
                    "accessed_age_days": age_days,
                    "size_mb": r.get("size_mb"),
                    "rag_status": r.get("rag_status"),
                    "risk_score": r.get("risk_score"),
                })
        except Exception:
            continue
    orphan_candidates = sorted(orphan_candidates, key=lambda x: (safe_int(x.get("accessed_age_days")), safe_float(x.get("size_mb"))), reverse=True)[:100]

    spatial_counts: Counter[str] = Counter()
    for r in records:
        for tag in r.get("spatial_tags") or []:
            spatial_counts[str(tag)] += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "created_at": utc_now_iso(),
        "doctrine": "POST_PROCESSING_METADATA_ONLY_NO_DOCUMENT_CONTENT_ACCESS",
        "benford_file_size_distribution": {
            "records_tested": size_records,
            "observed_first_digit_distribution": benford_observed,
            "expected_benford_distribution": benford_expected,
            "absolute_deviation_sum": benford_abs_deviation,
            "interpretation": "Screening signal only. File-size Benford analysis is not fraud proof and must not be used as evidence without follow-up.",
        },
        "orphaned_asset_identification": {
            "threshold_days": orphan_days,
            "candidate_count": len(orphan_candidates),
            "top_candidates": orphan_candidates,
            "warning": "Access timestamps may be disabled or altered by OS policy, backup tools, or indexing services.",
        },
        "spatial_heuristics": {
            "marker_counts": dict(sorted(spatial_counts.items())),
            "model_warning": "Spatial tags are path/name heuristics only, not geospatial proof.",
        },
    }


def build_merkle_ledger(records: list[dict[str, Any]], run_id: str, policy_hash: str) -> dict[str, Any]:
    leaves = []
    for r in records:
        payload = {
            "path_key_sha256": r.get("path_key_sha256"),
            "sha256": r.get("sha256"),
            "size_bytes": r.get("size_bytes"),
            "modified_time_utc": r.get("modified_time_utc"),
            "rag_status": r.get("rag_status"),
            "status_code": r.get("status_code"),
            "hash_status": r.get("hash_status"),
            "risk_score": r.get("risk_score"),
        }
        leaf = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        leaves.append(leaf)
    leaves.sort()
    if not leaves:
        root = hashlib.sha256(b"EMPTY_DISCOVERY_ROOT").hexdigest()
    else:
        level = leaves[:]
        while len(level) > 1:
            if len(level) % 2:
                level.append(level[-1])
            level = [hashlib.sha256((level[i] + level[i + 1]).encode("utf-8")).hexdigest() for i in range(0, len(level), 2)]
        root = level[0]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "policy_hash": policy_hash,
        "merkle_root": root,
        "leaf_count": len(leaves),
        "scope": "DISCOVERY_OUTPUT_RECORD_STATE_NOT_ABSOLUTE_SOURCE_FILESYSTEM_STATE",
        "leaf_algorithm": "sha256(json(record_evidence_fields))",
        "created_at": utc_now_iso(),
    }


def summarize_records(records: list[dict[str, Any]], started_at: str, ended_at: str, config_path: Path, roots: list[Path], compute_hash: bool, hash_limit_mb: int, include_hidden: bool, follow_symlinks: bool, run_id: str, policy_hash: str, counters: RuntimeCounters, header_heuristics: bool, header_sample_bytes: int) -> dict[str, Any]:
    status_counts = Counter(str(r.get("rag_status") or "UNKNOWN") for r in records)
    extension_counts = Counter(str(r.get("extension") or "[no extension]") for r in records)
    hash_counts = Counter(str(r.get("hash_status") or "UNKNOWN") for r in records)
    handoff_count = sum(1 for r in records if r.get("rag_status") in HANDOFF_STATUSES)
    total_size = sum(safe_int(r.get("size_bytes"), 0) for r in records)
    largest = sorted([
        {"file_path": r.get("file_path"), "size_mb": r.get("size_mb"), "extension": r.get("extension"), "rag_status": r.get("rag_status")}
        for r in records if r.get("size_mb") is not None
    ], key=lambda x: safe_float(x.get("size_mb")), reverse=True)[:20]
    return {
        "schema_version": SCHEMA_VERSION,
        "ssot_domain": SSOT_DOMAIN,
        "evidence_doctrine": EVIDENCE_DOCTRINE,
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "pipeline_stage": PIPELINE_STAGE,
        "policy": POLICY_NAME,
        "policy_hash": policy_hash,
        "host": {"hostname": socket.gethostname(), "platform": platform.platform(), "python": sys.version.split()[0]},
        "config_path": str(config_path),
        "scan_roots": [str(r) for r in roots],
        "parameters": {
            "compute_hash": compute_hash,
            "hash_limit_mb": hash_limit_mb,
            "include_hidden": include_hidden,
            "follow_symlinks": follow_symlinks,
            "header_heuristics": header_heuristics,
            "header_sample_bytes": header_sample_bytes if header_heuristics else 0,
        },
        "runtime_counters": counters.__dict__,
        "total_records": len(records),
        "handoff_records": handoff_count,
        "candidate_for_safety_filter": status_counts.get(STATUS_CANDIDATE_FOR_SAFETY_FILTER, 0),
        "sensitive_name_review": status_counts.get(STATUS_SENSITIVE_NAME_REVIEW, 0),
        "error_records": status_counts.get(STATUS_ERROR_DISCOVERY, 0),
        "root_missing_records": status_counts.get(STATUS_ROOT_MISSING, 0),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "status_counts": dict(sorted(status_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "hash_counts": dict(sorted(hash_counts.items())),
        "largest_files_top_20": largest,
        "risk_summary": {
            "avg_risk_score": round(sum(safe_int(r.get("risk_score"), 0) for r in records) / len(records), 2) if records else 0,
            "avg_quantitative_risk_score": round(sum(safe_int(r.get("quantitative_risk_score"), 0) for r in records) / len(records), 2) if records else 0,
            "high_risk_files_gt_70": sum(1 for r in records if safe_int(r.get("risk_score"), 0) > 70),
            "medium_risk_files_40_70": sum(1 for r in records if 40 <= safe_int(r.get("risk_score"), 0) <= 70),
        },
        "institutional_priority_summary": {
            "avg_institutional_compliance_index": round(sum(safe_float(r.get("institutional_compliance_index"), 0.0) for r in records) / len(records), 2) if records else 0,
            "records_with_institutional_markers": sum(1 for r in records if r.get("institutional_marker_hits")),
            "model_warning": "Filename/path metadata heuristic only; not content-based CAPEX/OPEX classification.",
        },
        "governance_rule": {
            "discovery_only": True,
            "controlled_header_sampling_is_not_text_extraction": True,
            "no_text_extraction": True,
            "no_semantic_parsing": True,
            "no_embeddings": True,
            "no_llm_visibility": True,
            "no_file_execution": True,
            "source_file_remains_authoritative": True,
            "safety_filter_required_next": True,
        },
    }


def output_integrity(paths: DiscoveryPaths) -> dict[str, Any]:
    result = {}
    for name, path in {
        "file_index_jsonl": paths.output_jsonl,
        "file_index_csv": paths.output_csv,
        "handoff_jsonl": paths.handoff_jsonl,
        "summary_json": paths.summary_json,
        "metrics_json": paths.metrics_json,
        "heuristics_report_json": paths.heuristics_report_json,
        "merkle_ledger_json": paths.merkle_ledger_json,
        "schema_json": paths.schema_json,
        "ssot_register_json": paths.ssot_register_json,
    }.items():
        if path.exists():
            h = hashlib.sha256()
            with path.open("rb") as f:
                for block in iter(lambda: f.read(READ_BLOCK_SIZE), b""):
                    h.update(block)
            result[name] = {"path": str(path), "sha256": h.hexdigest(), "size_bytes": path.stat().st_size}
        else:
            result[name] = {"path": str(path), "sha256": None, "size_bytes": None}
    return result


def build_schema_document() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "script_version": SCRIPT_VERSION,
        "record_contract": "Discovery records include filesystem metadata plus optional bounded header heuristics. No content semantics.",
        "key_fields": csv_fieldnames(),
        "status_values": sorted([STATUS_CANDIDATE_FOR_SAFETY_FILTER, STATUS_SENSITIVE_NAME_REVIEW, STATUS_ZERO_TRUST_REVIEW, STATUS_BLOCKED_EXTENSION, STATUS_UNSUPPORTED_EXTENSION, STATUS_EXCLUDED_PATH, STATUS_TOO_LARGE, STATUS_ROOT_MISSING, STATUS_ERROR_DISCOVERY, STATUS_SYMLINK_SKIPPED, STATUS_HIDDEN_SKIPPED, STATUS_DUPLICATE_PATH, STATUS_OFFICE_LOCK_FILE, STATUS_EMPTY_FILE]),
        "next_required_stage": "02_safety_filter_v1_AUDIT_LOCKED.py",
    }


def build_manifest(summary: dict[str, Any], paths: DiscoveryPaths, merkle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": summary["run_id"],
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "audit_status": "LOCKED",
        "created_at": utc_now_iso(),
        "policy_hash": summary["policy_hash"],
        "total_records": summary["total_records"],
        "handoff_records": summary["handoff_records"],
        "merkle_audit": {"merkle_root": merkle["merkle_root"], "leaf_count": merkle["leaf_count"], "scope": merkle["scope"], "ledger_path": str(paths.merkle_ledger_json)},
        "outputs": {
            "file_index_jsonl": str(paths.output_jsonl),
            "file_index_csv": str(paths.output_csv),
            "handoff_jsonl": str(paths.handoff_jsonl),
            "summary_json": str(paths.summary_json),
            "metrics_json": str(paths.metrics_json),
            "heuristics_report_json": str(paths.heuristics_report_json),
            "merkle_ledger_json": str(paths.merkle_ledger_json),
            "schema_json": str(paths.schema_json),
            "ssot_register_json": str(paths.ssot_register_json),
        },
        "governance_warning": "Merkle root seals emitted discovery records, not an absolute external proof of the full source filesystem.",
    }


def append_run_ledger(paths: DiscoveryPaths, summary: dict[str, Any], manifest: dict[str, Any]) -> None:
    append_jsonl(paths.run_ledger_jsonl, {
        "timestamp": utc_now_iso(),
        "run_id": summary.get("run_id"),
        "script_version": SCRIPT_VERSION,
        "policy_hash": summary.get("policy_hash"),
        "total_records": summary.get("total_records"),
        "handoff_records": summary.get("handoff_records"),
        "merkle_root": manifest.get("merkle_audit", {}).get("merkle_root"),
        "manifest_path": str(paths.manifest_json),
    })


def print_summary(summary: dict[str, Any], paths: DiscoveryPaths) -> None:
    print("=" * 110)
    print("TITAN RAG FILE DISCOVERY V8 — HEURISTICS AUDIT LOCKED")
    print("=" * 110)
    print(f"Run ID:                  {summary['run_id']}")
    print(f"Total records:           {summary['total_records']}")
    print(f"Handoff records:         {summary['handoff_records']}")
    print(f"Error records:           {summary['error_records']}")
    print(f"Avg risk score:          {summary['risk_summary']['avg_risk_score']}")
    print(f"File index:              {paths.output_jsonl}")
    print(f"Heuristics report:       {paths.heuristics_report_json}")
    print(f"Manifest:                {paths.manifest_json}")
    print("=" * 110)


def parse_roots(args: argparse.Namespace, config: dict[str, Any]) -> list[Path]:
    roots_raw = args.root if args.root else config.get("scan_roots", [])
    roots: list[Path] = []
    seen: set[str] = set()
    for item in roots_raw:
        p = Path(str(item)).expanduser()
        key = normalize_path_for_match(p)
        if key not in seen:
            roots.append(p)
            seen.add(key)
    return roots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 01 — v8 heuristics audit-hardened file discovery engine.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--config", default=None, help="Optional config.json path.")
    parser.add_argument("--root", action="append", default=None, help="Scan root. Can be repeated. Overrides config scan_roots.")
    parser.add_argument("--max-files", type=int, default=None, help="Optional maximum number of files for test runs.")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files/folders. Default is false.")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks. Default is false.")
    parser.add_argument("--hash", action="store_true", help="Compute SHA-256 for eligible files up to --hash-limit-mb.")
    parser.add_argument("--hash-limit-mb", type=int, default=None, help="Maximum file size for hashing in MB.")
    parser.add_argument("--workers", type=int, default=None, help="Parallel worker threads. Use 1 for strict single-thread test mode.")
    parser.add_argument("--header-heuristics", action="store_true", help="Enable bounded header entropy and magic-byte extension verification. No text extraction.")
    parser.add_argument("--header-sample-bytes", type=int, default=None, help="Bytes read for --header-heuristics. Default 256.")
    parser.add_argument("--store-sample-hex", action="store_true", help="Store first 64 sampled bytes as hex. Default false.")
    parser.add_argument("--incremental", action="store_true", help="Compare with previous file_index.jsonl to mark unchanged/new_or_changed.")
    parser.add_argument("--previous-index", default=None, help="Previous file_index.jsonl path for incremental mode.")
    parser.add_argument("--skip-unchanged", action="store_true", help="In incremental mode, omit unchanged records from new outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Load config and print planned roots, but do not scan.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_id = make_run_id()
    base_dir = Path(args.base_dir).expanduser()
    paths = resolve_paths(base_dir, run_id, args.config)
    started_at = utc_now_iso()
    started_perf = time.perf_counter()
    counters = RuntimeCounters()

    try:
        config = ensure_config(paths.config_path)
        roots = parse_roots(args, config)
        include_hidden = bool(args.include_hidden or config.get("include_hidden", False))
        follow_symlinks = bool(args.follow_symlinks or config.get("follow_symlinks", False))
        compute_hash = bool(args.hash or config.get("hash_enabled_default", False))
        hash_limit_mb = int(args.hash_limit_mb or config.get("hash_limit_mb", DEFAULT_HASH_LIMIT_MB))
        max_workers = int(args.workers or config.get("max_workers", DEFAULT_MAX_WORKERS))
        header_heuristics = bool(args.header_heuristics or config.get("header_heuristics_enabled_default", False))
        header_sample_bytes = int(args.header_sample_bytes or config.get("header_sample_bytes", DEFAULT_HEADER_SAMPLE_BYTES))
        store_sample_hex = bool(args.store_sample_hex or config.get("store_sample_hex_default", False))
        incremental = bool(args.incremental or config.get("incremental_default", False))
        previous_index_path = Path(args.previous_index).expanduser() if args.previous_index else (paths.output_jsonl if paths.output_jsonl.exists() else None)
        skip_unchanged = bool(args.skip_unchanged)
        policy_hash = stable_policy_hash(config)

        config_snapshot = dict(config)
        config_snapshot.update({"run_id": run_id, "snapshot_created_at": utc_now_iso(), "policy_hash": policy_hash, "script_version": SCRIPT_VERSION})
        write_json(paths.config_snapshot_path, config_snapshot)
        append_jsonl(paths.audit_log, {"timestamp": utc_now_iso(), "run_id": run_id, "event": "DISCOVERY_STARTED", "script": SCRIPT_NAME, "script_version": SCRIPT_VERSION, "roots": [str(r) for r in roots], "policy_hash": policy_hash, "header_heuristics": header_heuristics})

        if args.dry_run:
            summary = {"run_id": run_id, "script": SCRIPT_NAME, "script_version": SCRIPT_VERSION, "policy": "DRY_RUN_NO_SCAN", "policy_hash": policy_hash, "planned_scan_roots": [str(r) for r in roots], "parameters": {"compute_hash": compute_hash, "hash_limit_mb": hash_limit_mb, "max_workers": max_workers, "header_heuristics": header_heuristics, "header_sample_bytes": header_sample_bytes if header_heuristics else 0, "incremental": incremental, "previous_index_path": str(previous_index_path) if previous_index_path else None}}
            write_json(paths.summary_json, summary)
            print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
            return

        records = discover_files_parallel(
            roots, config, include_hidden, follow_symlinks, compute_hash, hash_limit_mb,
            args.max_files, paths, run_id, policy_hash, counters, max_workers,
            header_heuristics, header_sample_bytes, store_sample_hex, incremental,
            previous_index_path, skip_unchanged,
        )
        if bool(config.get("deterministic_sort", True)):
            records.sort(key=lambda r: (str(r.get("scan_root", "")).lower(), str(r.get("file_path", "")).lower()))

        handoff_records = [r for r in records if r.get("rag_status") in HANDOFF_STATUSES]
        ended_at = utc_now_iso()
        summary = summarize_records(records, started_at, ended_at, paths.config_path, roots, compute_hash, hash_limit_mb, include_hidden, follow_symlinks, run_id, policy_hash, counters, header_heuristics, header_sample_bytes)
        heuristics_report = build_heuristics_report(records, config, run_id)
        compliance_addendum = build_compliance_addendum(records, config, run_id)
        merkle = build_merkle_ledger(records, run_id, policy_hash)
        elapsed = max(time.perf_counter() - started_perf, 0.0001)
        metrics = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "script_version": SCRIPT_VERSION,
            "elapsed_seconds": round(elapsed, 4),
            "files_seen": counters.files_seen,
            "files_recorded_or_processed": counters.files_recorded,
            "records_written": len(records),
            "files_per_second_processed": round(counters.files_recorded / elapsed, 2),
            "max_workers": max_workers,
            "parallel_mode": max_workers > 1,
            "header_heuristics": header_heuristics,
            "header_sample_bytes": header_sample_bytes if header_heuristics else 0,
            "extension_spoofing_signals": heuristics_report["magic_verification"]["extension_spoofing_signals"],
            "high_entropy_records": heuristics_report["header_entropy"]["high_entropy_records"],
            "temporal_bursts_detected": heuristics_report["temporal_burst_detection"]["bursts_detected"],
            "gini_risk_concentration": heuristics_report["risk_concentration"]["gini_coefficient"],
            "merkle_root": merkle["merkle_root"],
        }
        manifest = build_manifest(summary, paths, merkle)

        write_jsonl(paths.output_jsonl, records)
        write_csv(paths.output_csv, records)
        write_jsonl(paths.handoff_jsonl, handoff_records if bool(config.get("emit_handoff_file", True)) else [])
        write_json(paths.summary_json, summary)
        write_json(paths.metrics_json, metrics)
        write_json(paths.heuristics_report_json, heuristics_report)
        write_json(paths.compliance_addendum_json, compliance_addendum)
        write_json(paths.merkle_ledger_json, merkle)
        write_json(paths.schema_json, build_schema_document())
        write_json(paths.ssot_register_json, {"schema_version": SCHEMA_VERSION, "run_id": run_id, "script_version": SCRIPT_VERSION, "ssot_domain": SSOT_DOMAIN, "outputs": manifest["outputs"], "next_stage": "02_safety_filter_v1_AUDIT_LOCKED.py"})
        write_json(paths.manifest_json, manifest)
        manifest["output_integrity"] = output_integrity(paths)
        write_json(paths.manifest_json, manifest)
        if bool(config.get("write_latest_manifest", True)):
            write_json(paths.latest_manifest_json, manifest)
        append_run_ledger(paths, summary, manifest)
        append_jsonl(paths.audit_log, {"timestamp": utc_now_iso(), "run_id": run_id, "event": "DISCOVERY_COMPLETED", "script": SCRIPT_NAME, "script_version": SCRIPT_VERSION, "summary": summary, "manifest": str(paths.manifest_json)})
        print_summary(summary, paths)

    except Exception as exc:
        append_jsonl(paths.error_log, {"timestamp": utc_now_iso(), "run_id": run_id, "event": "DISCOVERY_FAILED", "script": SCRIPT_NAME, "script_version": SCRIPT_VERSION, "base_dir": str(base_dir), "error": str(exc), "traceback": traceback.format_exc()})
        print("=" * 110)
        print("TITAN RAG FILE DISCOVERY V8 FAILED")
        print("=" * 110)
        print(f"Run ID: {run_id}")
        print(f"Error:  {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 110)
        raise


if __name__ == "__main__":
    main()
