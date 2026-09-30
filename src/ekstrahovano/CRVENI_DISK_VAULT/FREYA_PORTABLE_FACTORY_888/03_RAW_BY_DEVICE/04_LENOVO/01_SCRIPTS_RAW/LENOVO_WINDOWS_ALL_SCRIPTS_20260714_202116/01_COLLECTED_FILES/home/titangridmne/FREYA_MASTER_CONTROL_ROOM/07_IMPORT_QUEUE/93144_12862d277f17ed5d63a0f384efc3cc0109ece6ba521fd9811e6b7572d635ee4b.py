#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09_incremental_refresh.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 09 — Incremental Refresh Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Compare the current discovery index against the previous snapshot and produce
incremental worklists for only NEW / MODIFIED / RECHECK_REQUIRED files.

This script does NOT extract text.
This script does NOT build embeddings.
This script does NOT modify source files.
This script only compares metadata and writes audit-grade incremental indexes.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
01_index/file_index.jsonl
01_index/safe_file_index.jsonl
01_index/state/file_index_snapshot.jsonl          # previous state, if available

Outputs
-------
01_index/incremental_file_index.jsonl
01_index/incremental_file_index.csv
01_index/incremental_safe_file_index.jsonl
01_index/incremental_deleted_files.jsonl
01_index/state/file_index_snapshot.jsonl
05_reports/incremental_refresh_summary.json
06_logs/incremental_refresh_audit.jsonl
06_logs/incremental_refresh_errors.jsonl

Designed for compatibility with:
02_safety_filter.py
03_extract_text.py
19_night_run_orchestrator.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\09_incremental_refresh.py"

First run
---------
If no snapshot exists, all current files are classified as NEW.

Use after fresh discovery/safety:
---------------------------------
python ".\\08_scripts\\01_discover_files.py"
python ".\\08_scripts\\02_safety_filter.py"
python ".\\08_scripts\\09_incremental_refresh.py"

Then extract incrementally:
---------------------------
python ".\\08_scripts\\03_extract_text.py" --input ".\\01_index\\incremental_safe_file_index.jsonl" --overwrite
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_NAME = "09_incremental_refresh.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_FILE_INDEX = Path("01_index") / "file_index.jsonl"
INPUT_SAFE_INDEX = Path("01_index") / "safe_file_index.jsonl"

STATE_DIR = Path("01_index") / "state"
PREVIOUS_SNAPSHOT = STATE_DIR / "file_index_snapshot.jsonl"
SNAPSHOT_BACKUP_DIR = STATE_DIR / "snapshots_archive"

OUTPUT_INCREMENTAL_INDEX = Path("01_index") / "incremental_file_index.jsonl"
OUTPUT_INCREMENTAL_CSV = Path("01_index") / "incremental_file_index.csv"
OUTPUT_INCREMENTAL_SAFE = Path("01_index") / "incremental_safe_file_index.jsonl"
OUTPUT_DELETED = Path("01_index") / "incremental_deleted_files.jsonl"

SUMMARY_JSON = Path("05_reports") / "incremental_refresh_summary.json"
AUDIT_LOG = Path("06_logs") / "incremental_refresh_audit.jsonl"
ERROR_LOG = Path("06_logs") / "incremental_refresh_errors.jsonl"

CHANGE_NEW = "NEW"
CHANGE_MODIFIED = "MODIFIED"
CHANGE_UNCHANGED = "UNCHANGED"
CHANGE_DELETED = "DELETED"
CHANGE_RECHECK_REQUIRED = "RECHECK_REQUIRED"

SAFE_FOR_EXTRACTION = "SAFE_FOR_EXTRACTION"

HASH_MISSING = "[NO_HASH]"


@dataclass(frozen=True)
class RefreshPaths:
    base_dir: Path
    file_index: Path
    safe_index: Path
    previous_snapshot: Path
    snapshot_backup_dir: Path
    incremental_index: Path
    incremental_csv: Path
    incremental_safe: Path
    deleted_index: Path
    summary_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def normalize_path(value: Any) -> str:
    return str(value or "").strip().lower().replace("/", "\\")


def normalize_ext(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text and not text.startswith("."):
        return "." + text
    return text


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

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
            except Exception:
                records.append({
                    "file_path": None,
                    "record_error": f"Invalid JSONL line {line_no}",
                    "raw": raw[:500],
                })

    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "refresh_checked_at",
        "change_status",
        "change_reason",
        "file_path",
        "file_name",
        "extension",
        "size_bytes",
        "size_mb",
        "modified_time_utc",
        "sha256",
        "rag_status",
        "safety_status",
        "extraction_allowed",
        "previous_size_bytes",
        "previous_modified_time_utc",
        "previous_sha256",
        "previous_rag_status",
        "previous_safety_status",
        "script",
        "script_version",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for record in records:
            writer.writerow(record)


def resolve_paths(
    base_dir: Path,
    file_index_arg: str | None,
    safe_index_arg: str | None,
    snapshot_arg: str | None,
) -> RefreshPaths:
    return RefreshPaths(
        base_dir=base_dir,
        file_index=Path(file_index_arg) if file_index_arg else base_dir / INPUT_FILE_INDEX,
        safe_index=Path(safe_index_arg) if safe_index_arg else base_dir / INPUT_SAFE_INDEX,
        previous_snapshot=Path(snapshot_arg) if snapshot_arg else base_dir / PREVIOUS_SNAPSHOT,
        snapshot_backup_dir=base_dir / SNAPSHOT_BACKUP_DIR,
        incremental_index=base_dir / OUTPUT_INCREMENTAL_INDEX,
        incremental_csv=base_dir / OUTPUT_INCREMENTAL_CSV,
        incremental_safe=base_dir / OUTPUT_INCREMENTAL_SAFE,
        deleted_index=base_dir / OUTPUT_DELETED,
        summary_json=base_dir / SUMMARY_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def record_key(record: dict[str, Any]) -> str:
    return normalize_path(record.get("file_path"))


def fingerprint(record: dict[str, Any]) -> dict[str, Any]:
    """
    Stable comparison fingerprint.
    Prefer SHA-256 if present; otherwise use size + mtime + extension.
    """
    return {
        "file_path": normalize_path(record.get("file_path")),
        "size_bytes": record.get("size_bytes"),
        "modified_time_utc": record.get("modified_time_utc"),
        "sha256": record.get("sha256") or HASH_MISSING,
        "extension": normalize_ext(record.get("extension")),
        "rag_status": record.get("rag_status"),
        "safety_status": record.get("safety_status"),
    }


def index_by_path(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}

    for record in records:
        key = record_key(record)
        if not key:
            continue

        # Last record wins, but preserve duplicate signal.
        if key in output:
            existing = output[key]
            existing["_duplicate_seen_in_index"] = True

        output[key] = record

    return output


def backup_previous_snapshot(paths: RefreshPaths) -> str | None:
    if not paths.previous_snapshot.exists():
        return None

    paths.snapshot_backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = paths.snapshot_backup_dir / f"file_index_snapshot_{stamp}.jsonl"
    shutil.copy2(paths.previous_snapshot, backup_path)
    return str(backup_path)


def same_file_state(current: dict[str, Any], previous: dict[str, Any]) -> bool:
    cur = fingerprint(current)
    prev = fingerprint(previous)

    # If both have real hash, hash dominates.
    if cur.get("sha256") != HASH_MISSING and prev.get("sha256") != HASH_MISSING:
        return cur.get("sha256") == prev.get("sha256")

    return (
        cur.get("size_bytes") == prev.get("size_bytes")
        and cur.get("modified_time_utc") == prev.get("modified_time_utc")
        and cur.get("extension") == prev.get("extension")
        and cur.get("rag_status") == prev.get("rag_status")
    )


def needs_recheck_due_to_status(current: dict[str, Any], previous: dict[str, Any]) -> tuple[bool, str | None]:
    current_rag = str(current.get("rag_status") or "")
    previous_rag = str(previous.get("rag_status") or "")
    current_safe = str(current.get("safety_status") or "")
    previous_safe = str(previous.get("safety_status") or "")

    if current_rag != previous_rag:
        return True, f"rag_status changed: {previous_rag} -> {current_rag}"

    if current_safe and previous_safe and current_safe != previous_safe:
        return True, f"safety_status changed: {previous_safe} -> {current_safe}"

    # If hash became available, recheck to improve audit trail.
    if not previous.get("sha256") and current.get("sha256"):
        return True, "SHA-256 became available"

    return False, None


def attach_safe_status(current_records: list[dict[str, Any]], safe_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe_by_path = index_by_path(safe_records)
    output: list[dict[str, Any]] = []

    for record in current_records:
        item = dict(record)
        safe = safe_by_path.get(record_key(record))

        if safe:
            item["safety_status"] = safe.get("safety_status")
            item["safety_reason"] = safe.get("safety_reason")
            item["risk_level"] = safe.get("risk_level")
            item["extraction_allowed"] = safe.get("extraction_allowed")
        else:
            item["safety_status"] = item.get("safety_status")
            item["safety_reason"] = item.get("safety_reason")
            item["risk_level"] = item.get("risk_level")
            item["extraction_allowed"] = item.get("extraction_allowed", False)

        output.append(item)

    return output


def compare_indexes(
    current_records: list[dict[str, Any]],
    previous_records: list[dict[str, Any]],
    force_all: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    previous_by_path = index_by_path(previous_records)
    current_by_path = index_by_path(current_records)

    incremental: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []

    for current in current_records:
        key = record_key(current)
        if not key:
            continue

        previous = previous_by_path.get(key)

        item = dict(current)
        item["refresh_checked_at"] = utc_now_iso()
        item["script"] = SCRIPT_NAME
        item["script_version"] = SCRIPT_VERSION

        if previous is None:
            item["change_status"] = CHANGE_NEW
            item["change_reason"] = "File not present in previous snapshot"
            add_previous_fields(item, None)
            incremental.append(item)
            continue

        add_previous_fields(item, previous)

        if force_all:
            item["change_status"] = CHANGE_RECHECK_REQUIRED
            item["change_reason"] = "Forced full recheck requested"
            incremental.append(item)
            continue

        recheck, reason = needs_recheck_due_to_status(item, previous)
        if recheck:
            item["change_status"] = CHANGE_RECHECK_REQUIRED
            item["change_reason"] = reason
            incremental.append(item)
            continue

        if same_file_state(item, previous):
            item["change_status"] = CHANGE_UNCHANGED
            item["change_reason"] = "No relevant metadata/hash change"
            unchanged.append(item)
        else:
            item["change_status"] = CHANGE_MODIFIED
            item["change_reason"] = "File hash, modified time, size or extension changed"
            incremental.append(item)

    for key, previous in previous_by_path.items():
        if key in current_by_path:
            continue

        item = dict(previous)
        item["refresh_checked_at"] = utc_now_iso()
        item["script"] = SCRIPT_NAME
        item["script_version"] = SCRIPT_VERSION
        item["change_status"] = CHANGE_DELETED
        item["change_reason"] = "File present in previous snapshot but not in current discovery index"
        add_previous_fields(item, previous)
        deleted.append(item)

    return incremental, unchanged, deleted


def add_previous_fields(item: dict[str, Any], previous: dict[str, Any] | None) -> None:
    item["previous_size_bytes"] = previous.get("size_bytes") if previous else None
    item["previous_modified_time_utc"] = previous.get("modified_time_utc") if previous else None
    item["previous_sha256"] = previous.get("sha256") if previous else None
    item["previous_rag_status"] = previous.get("rag_status") if previous else None
    item["previous_safety_status"] = previous.get("safety_status") if previous else None


def build_incremental_safe(incremental_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []

    for record in incremental_records:
        if record.get("safety_status") == SAFE_FOR_EXTRACTION and bool(record.get("extraction_allowed", True)):
            output.append(record)

    return output


def summarize(
    started_at: str,
    ended_at: str,
    paths: RefreshPaths,
    current_records: list[dict[str, Any]],
    previous_records: list[dict[str, Any]],
    incremental: list[dict[str, Any]],
    unchanged: list[dict[str, Any]],
    deleted: list[dict[str, Any]],
    incremental_safe: list[dict[str, Any]],
    snapshot_backup_path: str | None,
    force_all: bool,
    update_snapshot: bool,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    extension_counts_incremental: dict[str, int] = {}
    safety_counts: dict[str, int] = {}

    for record in incremental + unchanged + deleted:
        status = str(record.get("change_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    for record in incremental:
        ext = str(record.get("extension") or "[no extension]")
        extension_counts_incremental[ext] = extension_counts_incremental.get(ext, 0) + 1

    for record in current_records:
        status = str(record.get("safety_status") or "UNKNOWN")
        safety_counts[status] = safety_counts.get(status, 0) + 1

    refresh_counts = {
        CHANGE_NEW: sum(1 for x in incremental if x.get("change_status") == CHANGE_NEW),
        CHANGE_MODIFIED: sum(1 for x in incremental if x.get("change_status") == CHANGE_MODIFIED),
        CHANGE_RECHECK_REQUIRED: sum(1 for x in incremental if x.get("change_status") == CHANGE_RECHECK_REQUIRED),
        CHANGE_UNCHANGED: len(unchanged),
        CHANGE_DELETED: len(deleted),
    }

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "INCREMENTAL_REFRESH_AUDIT_LOCKED",
        "force_all": force_all,
        "snapshot_updated": update_snapshot,
        "snapshot_backup_path": snapshot_backup_path,
        "inputs": {
            "file_index": str(paths.file_index),
            "safe_index": str(paths.safe_index),
            "previous_snapshot": str(paths.previous_snapshot),
        },
        "current_records": len(current_records),
        "previous_records": len(previous_records),
        "incremental_records": len(incremental),
        "incremental_safe_records": len(incremental_safe),
        "unchanged_records": len(unchanged),
        "deleted_records": len(deleted),
        "refresh_counts": refresh_counts,
        "status_counts": dict(sorted(status_counts.items())),
        "safety_counts": dict(sorted(safety_counts.items())),
        "incremental_extension_counts": dict(sorted(extension_counts_incremental.items())),
        "outputs": {
            "incremental_file_index": str(paths.incremental_index),
            "incremental_file_index_csv": str(paths.incremental_csv),
            "incremental_safe_file_index": str(paths.incremental_safe),
            "deleted_files": str(paths.deleted_index),
            "snapshot": str(paths.previous_snapshot),
            "summary_json": str(paths.summary_json),
        },
        "governance_rule": {
            "incremental_refresh_only_compares_metadata": True,
            "no_text_extraction": True,
            "no_embedding_build": True,
            "snapshot_required_for_future_comparison": True,
            "incremental_safe_file_index_feeds_step_03": True,
        },
    }


def print_summary(summary: dict[str, Any]) -> None:
    print("=" * 100)
    print("TITAN RAG INCREMENTAL REFRESH v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Started:                    {summary['started_at']}")
    print(f"Ended:                      {summary['ended_at']}")
    print(f"Policy:                     {summary['policy']}")
    print(f"Current records:             {summary['current_records']}")
    print(f"Previous records:            {summary['previous_records']}")
    print(f"Incremental records:         {summary['incremental_records']}")
    print(f"Incremental safe records:    {summary['incremental_safe_records']}")
    print(f"Unchanged records:           {summary['unchanged_records']}")
    print(f"Deleted records:             {summary['deleted_records']}")
    print("-" * 100)
    print("Refresh counts:")
    for key, value in summary["refresh_counts"].items():
        print(f" - {key}: {value}")
    print("-" * 100)
    for key, value in summary["outputs"].items():
        print(f"{key}: {value}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 09 — incremental refresh engine."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--file-index",
        default=None,
        help="Optional current file_index.jsonl path.",
    )

    parser.add_argument(
        "--safe-index",
        default=None,
        help="Optional current safe_file_index.jsonl path.",
    )

    parser.add_argument(
        "--snapshot",
        default=None,
        help="Optional previous snapshot path.",
    )

    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Treat all current records as RECHECK_REQUIRED.",
    )

    parser.add_argument(
        "--no-snapshot-update",
        action="store_true",
        help="Do not update snapshot after comparison.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compare indexes but do not write outputs/snapshot.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        file_index_arg=args.file_index,
        safe_index_arg=args.safe_index,
        snapshot_arg=args.snapshot,
    )

    started_at = utc_now_iso()

    try:
        current_raw = read_jsonl(paths.file_index)
        safe_records = read_jsonl(paths.safe_index)
        previous_records = read_jsonl(paths.previous_snapshot)

        current_records = attach_safe_status(current_raw, safe_records)

        incremental, unchanged, deleted = compare_indexes(
            current_records=current_records,
            previous_records=previous_records,
            force_all=bool(args.force_all),
        )

        incremental_safe = build_incremental_safe(incremental)

        update_snapshot = not bool(args.no_snapshot_update) and not bool(args.dry_run)
        snapshot_backup_path = None

        if update_snapshot:
            snapshot_backup_path = backup_previous_snapshot(paths)

        ended_at = utc_now_iso()

        summary = summarize(
            started_at=started_at,
            ended_at=ended_at,
            paths=paths,
            current_records=current_records,
            previous_records=previous_records,
            incremental=incremental,
            unchanged=unchanged,
            deleted=deleted,
            incremental_safe=incremental_safe,
            snapshot_backup_path=snapshot_backup_path,
            force_all=bool(args.force_all),
            update_snapshot=update_snapshot,
        )

        if args.dry_run:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return

        write_jsonl(paths.incremental_index, incremental)
        write_csv(paths.incremental_csv, incremental)
        write_jsonl(paths.incremental_safe, incremental_safe)
        write_jsonl(paths.deleted_index, deleted)
        write_json(paths.summary_json, summary)

        if update_snapshot:
            write_jsonl(paths.previous_snapshot, current_records)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "INCREMENTAL_REFRESH_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "summary": summary,
            "summary_sha256": sha256_json(summary),
        })

        print_summary(summary)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "INCREMENTAL_REFRESH_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "file_index": str(paths.file_index),
            "safe_index": str(paths.safe_index),
            "snapshot": str(paths.previous_snapshot),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG INCREMENTAL REFRESH FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
