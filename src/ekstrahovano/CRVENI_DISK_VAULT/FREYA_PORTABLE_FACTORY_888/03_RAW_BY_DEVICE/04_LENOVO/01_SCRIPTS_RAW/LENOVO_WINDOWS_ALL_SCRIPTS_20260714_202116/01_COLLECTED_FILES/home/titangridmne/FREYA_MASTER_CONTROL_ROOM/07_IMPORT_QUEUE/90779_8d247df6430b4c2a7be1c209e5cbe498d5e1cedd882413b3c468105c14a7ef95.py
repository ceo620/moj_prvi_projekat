#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30_post_release_audit_and_receipt_register.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 30 — Post-Release Audit & Receipt Register
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Create a post-release audit register after a human-authorized external release
has been prepared and/or manually distributed.

This script does NOT send emails.
This script does NOT upload files.
This script does NOT verify that a recipient actually opened the package.
This script records release package identity, checksums, release decision,
intended recipients, manual distribution metadata, conditions, and receipt
status for audit evidence.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.
Freeze precedes distribution.
Gatekeeping precedes external release.
Release package precedes transmission.
Receipt register follows transmission.

Inputs
------
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_MANIFEST.json
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_INDEX.csv
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_CHECKSUMS.csv
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_DECISION_SNAPSHOT.json
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_COVER_NOTE.md
05_reports/distribution_readiness/TITAN_DISTRIBUTION_READINESS_DECISION.json
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json

Outputs
-------
05_reports/post_release_audit/TITAN_POST_RELEASE_AUDIT_REGISTER.md
05_reports/post_release_audit/TITAN_POST_RELEASE_AUDIT_REGISTER.json
05_reports/post_release_audit/TITAN_RELEASE_RECEIPT_REGISTER.csv
05_reports/post_release_audit/TITAN_RELEASE_RECIPIENT_REGISTER.csv
05_reports/post_release_audit/TITAN_RELEASE_FILE_AUDIT.csv
05_reports/post_release_audit/TITAN_POST_RELEASE_AUDIT_MANIFEST.json
06_logs/post_release_audit_and_receipt_register_audit.jsonl
06_logs/post_release_audit_and_receipt_register_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\30_post_release_audit_and_receipt_register.py" --target EBRD --print

With manual distribution metadata:
----------------------------------
python ".\\08_scripts\\30_post_release_audit_and_receipt_register.py" ^
  --target EBRD ^
  --distribution-method "Manual email / secure link" ^
  --distributed-by "Danijela" ^
  --recipient "EBRD team <team@example.com>" ^
  --recipient "Legal counsel <legal@example.com>" ^
  --print

Internal dry-run:
-----------------
python ".\\08_scripts\\30_post_release_audit_and_receipt_register.py" --target EBRD --dry-run --print
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "30_post_release_audit_and_receipt_register.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "post_release_audit"

INPUT_RELEASE_MANIFEST = Path("05_reports") / "external_release_package" / "TITAN_EXTERNAL_RELEASE_MANIFEST.json"
INPUT_RELEASE_INDEX = Path("05_reports") / "external_release_package" / "TITAN_EXTERNAL_RELEASE_INDEX.csv"
INPUT_RELEASE_CHECKSUMS = Path("05_reports") / "external_release_package" / "TITAN_EXTERNAL_RELEASE_CHECKSUMS.csv"
INPUT_RELEASE_DECISION_SNAPSHOT = Path("05_reports") / "external_release_package" / "TITAN_EXTERNAL_RELEASE_DECISION_SNAPSHOT.json"
INPUT_RELEASE_COVER_NOTE = Path("05_reports") / "external_release_package" / "TITAN_EXTERNAL_RELEASE_COVER_NOTE.md"
INPUT_DISTRIBUTION_DECISION = Path("05_reports") / "distribution_readiness" / "TITAN_DISTRIBUTION_READINESS_DECISION.json"
INPUT_FREEZE_MANIFEST = Path("05_reports") / "investor_data_room_freeze" / "TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json"

OUTPUT_REGISTER_MD = "TITAN_POST_RELEASE_AUDIT_REGISTER.md"
OUTPUT_REGISTER_JSON = "TITAN_POST_RELEASE_AUDIT_REGISTER.json"
OUTPUT_RECEIPT_CSV = "TITAN_RELEASE_RECEIPT_REGISTER.csv"
OUTPUT_RECIPIENT_CSV = "TITAN_RELEASE_RECIPIENT_REGISTER.csv"
OUTPUT_FILE_AUDIT_CSV = "TITAN_RELEASE_FILE_AUDIT.csv"
OUTPUT_MANIFEST_JSON = "TITAN_POST_RELEASE_AUDIT_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "post_release_audit_and_receipt_register_audit.jsonl"
ERROR_LOG = Path("06_logs") / "post_release_audit_and_receipt_register_errors.jsonl"

POST_RELEASE_READY = "POST_RELEASE_AUDIT_READY"
POST_RELEASE_DRY_RUN = "POST_RELEASE_AUDIT_DRY_RUN"
POST_RELEASE_CONDITIONAL = "POST_RELEASE_AUDIT_CONDITIONAL"
POST_RELEASE_BLOCKED = "POST_RELEASE_AUDIT_BLOCKED"
POST_RELEASE_INCOMPLETE = "POST_RELEASE_AUDIT_INCOMPLETE"

RECEIPT_PENDING = "PENDING_CONFIRMATION"
RECEIPT_CONFIRMED = "CONFIRMED_EXTERNALLY"
RECEIPT_NOT_REQUESTED = "NOT_REQUESTED"
RECEIPT_INTERNAL = "INTERNAL_DRY_RUN"


@dataclass(frozen=True)
class PostReleasePaths:
    base_dir: Path
    output_dir: Path
    release_manifest: Path
    release_index: Path
    release_checksums: Path
    release_decision_snapshot: Path
    release_cover_note: Path
    distribution_decision: Path
    freeze_manifest: Path
    register_md: Path
    register_json: Path
    receipt_csv: Path
    recipient_csv: Path
    file_audit_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in [None, ""]:
            return default
        return int(float(value))
    except Exception:
        return default


def bool_from_cell(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def read_text_if_exists(path: Path, max_chars: int = 10000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:max_chars]


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="", errors="ignore") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> PostReleasePaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return PostReleasePaths(
        base_dir=base_dir,
        output_dir=output_dir,
        release_manifest=base_dir / INPUT_RELEASE_MANIFEST,
        release_index=base_dir / INPUT_RELEASE_INDEX,
        release_checksums=base_dir / INPUT_RELEASE_CHECKSUMS,
        release_decision_snapshot=base_dir / INPUT_RELEASE_DECISION_SNAPSHOT,
        release_cover_note=base_dir / INPUT_RELEASE_COVER_NOTE,
        distribution_decision=base_dir / INPUT_DISTRIBUTION_DECISION,
        freeze_manifest=base_dir / INPUT_FREEZE_MANIFEST,
        register_md=output_dir / OUTPUT_REGISTER_MD,
        register_json=output_dir / OUTPUT_REGISTER_JSON,
        receipt_csv=output_dir / OUTPUT_RECEIPT_CSV,
        recipient_csv=output_dir / OUTPUT_RECIPIENT_CSV,
        file_audit_csv=output_dir / OUTPUT_FILE_AUDIT_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def determine_post_release_status(release_manifest: dict[str, Any] | None, args: argparse.Namespace) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if release_manifest is None:
        return POST_RELEASE_INCOMPLETE, ["Missing Step 29 external release manifest."]

    release_status = str(release_manifest.get("release_status") or "")

    if args.dry_run:
        return POST_RELEASE_DRY_RUN, ["Dry-run mode: post-release record prepared for internal test only."]

    if release_status == "EXTERNAL_RELEASE_PACKAGE_READY":
        reasons.append("External release package status is READY.")
        return POST_RELEASE_READY, reasons

    if release_status == "EXTERNAL_RELEASE_PACKAGE_CONDITIONAL":
        reasons.append("External release package is conditional; receipt register requires condition tracking.")
        return POST_RELEASE_CONDITIONAL, reasons

    if release_status == "EXTERNAL_RELEASE_INTERNAL_PREP_ONLY":
        reasons.append("Release package was internal-prep-only; not valid as external distribution receipt.")
        return POST_RELEASE_DRY_RUN, reasons

    if release_status == "EXTERNAL_RELEASE_INCOMPLETE":
        reasons.append("Release package incomplete.")
        return POST_RELEASE_INCOMPLETE, reasons

    reasons.append(f"Release package blocks post-release external audit: {release_status}")
    return POST_RELEASE_BLOCKED, reasons


def build_recipient_register(args: argparse.Namespace, post_status: str) -> list[dict[str, Any]]:
    recipients = args.recipient or []
    if not recipients:
        return [{
            "Recipient_ID": "RECIPIENT-NOT-SPECIFIED",
            "Target": args.target.upper(),
            "Recipient": "",
            "Recipient_Type": "UNSPECIFIED",
            "Receipt_Status": RECEIPT_INTERNAL if args.dry_run else RECEIPT_NOT_REQUESTED,
            "Receipt_Timestamp_UTC": "",
            "Receipt_Method": "",
            "Notes": "No recipients supplied. Add --recipient entries to create auditable recipient register.",
        }]

    rows = []
    for idx, recipient in enumerate(recipients, start=1):
        rid = "RECIPIENT-" + hashlib.sha256(f"{args.target}|{recipient}|{idx}".encode("utf-8")).hexdigest()[:12]
        rows.append({
            "Recipient_ID": rid,
            "Target": args.target.upper(),
            "Recipient": recipient,
            "Recipient_Type": args.recipient_type,
            "Receipt_Status": RECEIPT_INTERNAL if args.dry_run else RECEIPT_PENDING,
            "Receipt_Timestamp_UTC": "",
            "Receipt_Method": args.receipt_method,
            "Notes": "Await manual confirmation. This script does not verify receipt.",
        })
    return rows


def build_receipt_register(args: argparse.Namespace, release_manifest: dict[str, Any] | None, recipient_rows: list[dict[str, Any]], post_status: str) -> list[dict[str, Any]]:
    release_manifest_hash = (release_manifest or {}).get("external_release_manifest_sha256")
    release_status = (release_manifest or {}).get("release_status")
    release_dir = (release_manifest or {}).get("release_files_dir")
    distributed_at = args.distributed_at or ""

    rows = []
    for rec in recipient_rows:
        raw = f"{args.target}|{rec.get('Recipient_ID')}|{release_manifest_hash}|{distributed_at}|{args.distribution_method}"
        rows.append({
            "Receipt_ID": "RECEIPT-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:14],
            "Release_Target": args.target.upper(),
            "Release_Status": release_status,
            "Post_Release_Status": post_status,
            "Release_Manifest_SHA256": release_manifest_hash,
            "Release_Directory": release_dir,
            "Distribution_Method": args.distribution_method,
            "Distributed_By": args.distributed_by,
            "Distributed_At": distributed_at,
            "Recipient_ID": rec.get("Recipient_ID"),
            "Recipient": rec.get("Recipient"),
            "Receipt_Status": rec.get("Receipt_Status"),
            "Receipt_Method": rec.get("Receipt_Method"),
            "External_Transmission_Verified_By_Script": False,
            "Notes": args.notes or "Manual receipt confirmation pending.",
        })
    return rows


def build_file_audit_rows(release_rows: list[dict[str, Any]], checksum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checksum_by_id = {row.get("Release_Item_ID"): row for row in checksum_rows}
    rows = []

    for row in release_rows:
        rid = row.get("Release_Item_ID")
        checksum = checksum_by_id.get(rid, {})
        release_path = Path(str(row.get("Release_Path") or ""))
        release_path_exists = release_path.exists() if str(release_path) not in {"", "."} else False
        current_sha = sha256_file(release_path) if release_path_exists else None
        expected_sha = row.get("Release_SHA256") or checksum.get("Release_SHA256")

        rows.append({
            "Release_Item_ID": rid,
            "Name": row.get("Name"),
            "Category": row.get("Category"),
            "Release_Status": row.get("Release_Status"),
            "Release_Path": row.get("Release_Path"),
            "Release_Path_Exists_Now": release_path_exists,
            "Expected_Release_SHA256": expected_sha,
            "Current_Release_SHA256": current_sha,
            "Current_Hash_OK": current_sha == expected_sha if current_sha and expected_sha else None,
            "Frozen_SHA256": row.get("Frozen_SHA256") or checksum.get("Frozen_SHA256"),
            "Source_SHA256": row.get("Source_SHA256") or checksum.get("Source_SHA256"),
            "Original_Hash_OK": row.get("Hash_OK") or checksum.get("Hash_OK"),
        })

    return rows


def build_source_manifest(paths: PostReleasePaths) -> list[dict[str, Any]]:
    source_paths = {
        "release_manifest": paths.release_manifest,
        "release_index": paths.release_index,
        "release_checksums": paths.release_checksums,
        "release_decision_snapshot": paths.release_decision_snapshot,
        "release_cover_note": paths.release_cover_note,
        "distribution_decision": paths.distribution_decision,
        "freeze_manifest": paths.freeze_manifest,
    }

    rows = []
    for name, path in source_paths.items():
        exists = path.exists() and path.is_file()
        rows.append({
            "Name": name,
            "Path": str(path),
            "Exists": exists,
            "Size_Bytes": path.stat().st_size if exists else None,
            "Modified_UTC": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if exists else None,
            "SHA256": sha256_file(path) if exists else None,
        })
    return rows


def build_manifest(paths: PostReleasePaths, args: argparse.Namespace, source_manifest: list[dict[str, Any]], register: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "base_dir": str(paths.base_dir),
        "output_dir": str(paths.output_dir),
        "target": args.target.upper(),
        "source_manifest": source_manifest,
        "register_sha256": register.get("post_release_audit_register_sha256"),
        "governance_rule": {
            "script_does_not_send_files": True,
            "script_does_not_upload_files": True,
            "script_does_not_verify_external_receipt": True,
            "manual_receipt_confirmation_required": True,
            "release_manifest_remains_authoritative": True,
            "audit_precedes_decision": True,
            "receipt_register_follows_transmission": True,
        },
    }
    manifest["post_release_audit_manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_register(
    paths: PostReleasePaths,
    args: argparse.Namespace,
    release_manifest: dict[str, Any] | None,
    distribution_decision: dict[str, Any] | None,
    freeze_manifest: dict[str, Any] | None,
    decision_snapshot: dict[str, Any] | None,
    release_rows: list[dict[str, Any]],
    checksum_rows: list[dict[str, Any]],
    recipient_rows: list[dict[str, Any]],
    receipt_rows: list[dict[str, Any]],
    file_audit_rows: list[dict[str, Any]],
    post_status: str,
    post_reasons: list[str],
) -> dict[str, Any]:
    summary = {
        "release_rows": len(release_rows),
        "checksum_rows": len(checksum_rows),
        "recipient_rows": len(recipient_rows),
        "receipt_rows": len(receipt_rows),
        "file_audit_rows": len(file_audit_rows),
        "current_file_hash_ok": sum(1 for r in file_audit_rows if r.get("Current_Hash_OK") is True),
        "current_file_hash_fail": sum(1 for r in file_audit_rows if r.get("Current_Hash_OK") is False),
        "missing_release_files_now": sum(1 for r in file_audit_rows if r.get("Release_Path_Exists_Now") is False),
        "pending_receipts": sum(1 for r in receipt_rows if r.get("Receipt_Status") == RECEIPT_PENDING),
        "confirmed_receipts": sum(1 for r in receipt_rows if r.get("Receipt_Status") == RECEIPT_CONFIRMED),
    }

    register = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "POST_RELEASE_AUDIT_RECEIPT_REGISTER_AUDIT_LOCKED",
        "target": args.target.upper(),
        "post_release_status": post_status,
        "post_release_status_reasons": post_reasons,
        "dry_run": bool(args.dry_run),
        "distribution_method": args.distribution_method,
        "distributed_by": args.distributed_by,
        "distributed_at": args.distributed_at,
        "receipt_method": args.receipt_method,
        "notes": args.notes,
        "release_identity": {
            "release_status": (release_manifest or {}).get("release_status"),
            "external_release_manifest_sha256": (release_manifest or {}).get("external_release_manifest_sha256"),
            "release_files_dir": (release_manifest or {}).get("release_files_dir"),
            "source_distribution_decision": (release_manifest or {}).get("source_distribution_decision"),
            "source_distribution_decision_sha256": (release_manifest or {}).get("source_distribution_decision_sha256"),
            "source_freeze_manifest_sha256": (release_manifest or {}).get("source_freeze_manifest_sha256"),
        },
        "distribution_decision_snapshot": {
            "distribution_decision": (distribution_decision or {}).get("distribution_decision"),
            "target": (distribution_decision or {}).get("target"),
            "decision_sha256": (distribution_decision or {}).get("distribution_readiness_decision_sha256"),
            "recommended_action": (distribution_decision or {}).get("recommended_action"),
            "summary": (distribution_decision or {}).get("summary"),
        },
        "freeze_identity": {
            "freeze_status": (freeze_manifest or {}).get("freeze_status"),
            "freeze_manifest_sha256": (freeze_manifest or {}).get("freeze_manifest_sha256"),
        },
        "release_decision_snapshot_sha256": (decision_snapshot or {}).get("decision_snapshot_sha256"),
        "summary": summary,
        "recipient_register": recipient_rows,
        "receipt_register": receipt_rows,
        "file_audit": file_audit_rows,
        "governance_rule": {
            "does_not_send_files": True,
            "does_not_upload_files": True,
            "does_not_verify_external_receipt": True,
            "manual_receipt_confirmation_required": True,
            "release_manifest_remains_authoritative": True,
            "original_sources_remain_authoritative": True,
            "audit_precedes_decision": True,
            "receipt_register_follows_transmission": True,
        },
        "outputs": {
            "register_md": str(paths.register_md),
            "register_json": str(paths.register_json),
            "receipt_csv": str(paths.receipt_csv),
            "recipient_csv": str(paths.recipient_csv),
            "file_audit_csv": str(paths.file_audit_csv),
            "manifest_json": str(paths.manifest_json),
        },
    }
    register["post_release_audit_register_sha256"] = sha256_json(register)
    return register


def write_recipient_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Recipient_ID",
        "Target",
        "Recipient",
        "Recipient_Type",
        "Receipt_Status",
        "Receipt_Timestamp_UTC",
        "Receipt_Method",
        "Notes",
    ])


def write_receipt_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Receipt_ID",
        "Release_Target",
        "Release_Status",
        "Post_Release_Status",
        "Release_Manifest_SHA256",
        "Release_Directory",
        "Distribution_Method",
        "Distributed_By",
        "Distributed_At",
        "Recipient_ID",
        "Recipient",
        "Receipt_Status",
        "Receipt_Method",
        "External_Transmission_Verified_By_Script",
        "Notes",
    ])


def write_file_audit_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Release_Item_ID",
        "Name",
        "Category",
        "Release_Status",
        "Release_Path",
        "Release_Path_Exists_Now",
        "Expected_Release_SHA256",
        "Current_Release_SHA256",
        "Current_Hash_OK",
        "Frozen_SHA256",
        "Source_SHA256",
        "Original_Hash_OK",
    ])


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def recipients_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No recipients."
    lines = ["| Recipient | Type | Receipt Status | Method | Notes |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Recipient'))} | "
            f"{md_escape(row.get('Recipient_Type'))} | "
            f"{md_escape(row.get('Receipt_Status'))} | "
            f"{md_escape(row.get('Receipt_Method'))} | "
            f"{md_escape(row.get('Notes'))} |"
        )
    return "\n".join(lines)


def receipts_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No receipts."
    lines = ["| Receipt ID | Recipient | Status | Distributed At | Method |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Receipt_ID'))} | "
            f"{md_escape(row.get('Recipient'))} | "
            f"{md_escape(row.get('Receipt_Status'))} | "
            f"{md_escape(row.get('Distributed_At'))} | "
            f"{md_escape(row.get('Distribution_Method'))} |"
        )
    return "\n".join(lines)


def file_audit_md(rows: list[dict[str, Any]], limit: int = 80) -> str:
    if not rows:
        return "No file audit rows."
    lines = ["| Hash OK | Exists Now | Category | Name | Release Path |", "|---:|---:|---|---|---|"]
    for row in rows[:limit]:
        lines.append(
            f"| {row.get('Current_Hash_OK')} | "
            f"{row.get('Release_Path_Exists_Now')} | "
            f"{md_escape(row.get('Category'))} | "
            f"{md_escape(row.get('Name'))} | "
            f"`{md_escape(row.get('Release_Path'))}` |"
        )
    return "\n".join(lines)


def register_to_markdown(register: dict[str, Any], manifest: dict[str, Any]) -> str:
    summary = register.get("summary", {}) if isinstance(register.get("summary"), dict) else {}
    identity = register.get("release_identity", {}) if isinstance(register.get("release_identity"), dict) else {}

    summary_lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in summary.items():
        summary_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    return f"""# TITAN Post-Release Audit & Receipt Register

## 1. Register Identity

| Field | Value |
|---|---|
| Created At | {register.get("created_at")} |
| Target | {register.get("target")} |
| Post-Release Status | {register.get("post_release_status")} |
| Dry Run | {register.get("dry_run")} |
| Register SHA-256 | `{register.get("post_release_audit_register_sha256")}` |
| Manifest SHA-256 | `{manifest.get("post_release_audit_manifest_sha256")}` |

**Status reasons**

```json
{json.dumps(register.get("post_release_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Release Identity

| Field | Value |
|---|---|
| Release Status | {identity.get("release_status")} |
| External Release Manifest SHA-256 | `{identity.get("external_release_manifest_sha256")}` |
| Release Files Directory | `{identity.get("release_files_dir")}` |
| Source Distribution Decision | {identity.get("source_distribution_decision")} |
| Source Distribution Decision SHA-256 | `{identity.get("source_distribution_decision_sha256")}` |
| Source Freeze Manifest SHA-256 | `{identity.get("source_freeze_manifest_sha256")}` |

---

## 3. Distribution Metadata

| Field | Value |
|---|---|
| Distribution Method | {md_escape(register.get("distribution_method"))} |
| Distributed By | {md_escape(register.get("distributed_by"))} |
| Distributed At | {md_escape(register.get("distributed_at"))} |
| Receipt Method | {md_escape(register.get("receipt_method"))} |
| Notes | {md_escape(register.get("notes"))} |

---

## 4. Summary

{chr(10).join(summary_lines)}

---

## 5. Recipient Register

{recipients_md(register.get("recipient_register", []))}

---

## 6. Receipt Register

{receipts_md(register.get("receipt_register", []))}

---

## 7. File Audit Preview

{file_audit_md(register.get("file_audit", []))}

---

## 8. Governance Rule

```text
This script does not send files.
This script does not upload files.
This script does not verify external receipt.
Manual receipt confirmation is required.
Release manifest remains authoritative.
Original sources remain authoritative.
Audit precedes decision.
Receipt register follows transmission.
```
"""


def print_summary(register: dict[str, Any], paths: PostReleasePaths) -> None:
    summary = register.get("summary", {}) if isinstance(register.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN POST-RELEASE AUDIT & RECEIPT REGISTER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Target:                   {register.get('target')}")
    print(f"Post-release status:      {register.get('post_release_status')}")
    print(f"Recipients:               {summary.get('recipient_rows')}")
    print(f"Receipts:                 {summary.get('receipt_rows')}")
    print(f"Pending receipts:          {summary.get('pending_receipts')}")
    print(f"Missing release files now: {summary.get('missing_release_files_now')}")
    print(f"Current hash fails:        {summary.get('current_file_hash_fail')}")
    print("-" * 100)
    print(f"Register Markdown:        {paths.register_md}")
    print(f"Register JSON:            {paths.register_json}")
    print(f"Receipt CSV:              {paths.receipt_csv}")
    print(f"Recipient CSV:            {paths.recipient_csv}")
    print(f"File Audit CSV:           {paths.file_audit_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 30 — post-release audit and receipt register.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--target", default="EBRD", choices=["EBRD", "EIB", "IFC", "BOARD", "INVESTOR", "INTERNAL"], help="Release target label.")
    parser.add_argument("--distribution-method", default="Manual / not specified", help="How the package was or will be distributed manually.")
    parser.add_argument("--distributed-by", default="Danijela / TITAN Operator", help="Person/operator who performed or will perform distribution.")
    parser.add_argument("--distributed-at", default="", help="Manual distribution timestamp, if known.")
    parser.add_argument("--recipient", action="append", default=[], help="Recipient entry. Can be used multiple times.")
    parser.add_argument("--recipient-type", default="EXTERNAL_REVIEWER", help="Recipient type label.")
    parser.add_argument("--receipt-method", default="Manual confirmation", help="Expected receipt confirmation method.")
    parser.add_argument("--notes", default="", help="Free-text audit notes.")
    parser.add_argument("--dry-run", action="store_true", help="Internal dry-run record; not an external release receipt.")
    parser.add_argument("--print", action="store_true", help="Print Markdown register to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, args.output_dir)

    try:
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        paths.output_dir.mkdir(parents=True, exist_ok=True)

        release_manifest = load_json_if_exists(paths.release_manifest)
        distribution_decision = load_json_if_exists(paths.distribution_decision)
        freeze_manifest = load_json_if_exists(paths.freeze_manifest)
        decision_snapshot = load_json_if_exists(paths.release_decision_snapshot)
        release_rows = read_csv_rows(paths.release_index)
        checksum_rows = read_csv_rows(paths.release_checksums)

        post_status, post_reasons = determine_post_release_status(release_manifest, args)
        recipient_rows = build_recipient_register(args, post_status)
        receipt_rows = build_receipt_register(args, release_manifest, recipient_rows, post_status)
        file_audit_rows = build_file_audit_rows(release_rows, checksum_rows)

        register = build_register(
            paths=paths,
            args=args,
            release_manifest=release_manifest,
            distribution_decision=distribution_decision,
            freeze_manifest=freeze_manifest,
            decision_snapshot=decision_snapshot,
            release_rows=release_rows,
            checksum_rows=checksum_rows,
            recipient_rows=recipient_rows,
            receipt_rows=receipt_rows,
            file_audit_rows=file_audit_rows,
            post_status=post_status,
            post_reasons=post_reasons,
        )
        source_manifest = build_source_manifest(paths)
        manifest = build_manifest(paths, args, source_manifest, register)
        markdown = register_to_markdown(register, manifest)

        write_json(paths.register_json, register)
        write_text(paths.register_md, markdown)
        write_receipt_csv(paths.receipt_csv, receipt_rows)
        write_recipient_csv(paths.recipient_csv, recipient_rows)
        write_file_audit_csv(paths.file_audit_csv, file_audit_rows)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "POST_RELEASE_AUDIT_REGISTER_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "target": args.target,
            "post_release_status": post_status,
            "register_sha256": register.get("post_release_audit_register_sha256"),
            "manifest_sha256": manifest.get("post_release_audit_manifest_sha256"),
            "summary": register.get("summary"),
            "outputs": register.get("outputs"),
        })

        print_summary(register, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "POST_RELEASE_AUDIT_REGISTER_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "target": args.target,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN POST-RELEASE AUDIT & RECEIPT REGISTER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
