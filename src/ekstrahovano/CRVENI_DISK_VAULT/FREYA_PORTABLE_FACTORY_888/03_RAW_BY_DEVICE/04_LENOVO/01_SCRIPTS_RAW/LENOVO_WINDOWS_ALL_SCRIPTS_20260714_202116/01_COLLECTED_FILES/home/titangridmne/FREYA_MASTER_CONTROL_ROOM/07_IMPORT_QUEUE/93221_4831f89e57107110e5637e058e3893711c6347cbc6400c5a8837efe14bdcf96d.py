#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
29_external_release_package_builder.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 29 — External Release Package Builder
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build a controlled external release package from the frozen investor data-room
snapshot and the distribution readiness decision.

This script does NOT email, upload, share or transmit files.
This script does NOT modify original source documents.
This script does NOT override legal/board/lender decisions.
It prepares a release folder with:
- release manifest
- release index
- release cover note
- included frozen exports
- conditions/blockers snapshot
- checksum register

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.
Freeze precedes distribution.
Gatekeeping precedes external release.
Release package precedes any transmission.

Inputs
------
05_reports/distribution_readiness/TITAN_DISTRIBUTION_READINESS_DECISION.json
05_reports/distribution_readiness/TITAN_DISTRIBUTION_RELEASE_INDEX.csv
05_reports/distribution_readiness/TITAN_DISTRIBUTION_BLOCKER_REGISTER.csv
05_reports/distribution_readiness/TITAN_DISTRIBUTION_CONDITION_REGISTER.csv
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json
05_reports/investor_data_room_freeze/FROZEN_EXPORTS/...

Outputs
-------
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_COVER_NOTE.md
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_MANIFEST.json
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_INDEX.csv
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_CHECKSUMS.csv
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_DECISION_SNAPSHOT.json
05_reports/external_release_package/RELEASE_FILES/...
06_logs/external_release_package_builder_audit.jsonl
06_logs/external_release_package_builder_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\29_external_release_package_builder.py" --target EBRD --print

Strict mode
-----------
python ".\\08_scripts\\29_external_release_package_builder.py" --target EBRD --strict --print

Internal preparation even if Step 28 is not GO:
-----------------------------------------------
python ".\\08_scripts\\29_external_release_package_builder.py" --target EBRD --internal-prep-only --print

Override gate, requires explicit reason:
----------------------------------------
python ".\\08_scripts\\29_external_release_package_builder.py" --target EBRD --override-gate --override-reason "Internal dry-run only" --print
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
from typing import Any


SCRIPT_NAME = "29_external_release_package_builder.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "external_release_package"

INPUT_DISTRIBUTION_DECISION = Path("05_reports") / "distribution_readiness" / "TITAN_DISTRIBUTION_READINESS_DECISION.json"
INPUT_DISTRIBUTION_RELEASE_INDEX = Path("05_reports") / "distribution_readiness" / "TITAN_DISTRIBUTION_RELEASE_INDEX.csv"
INPUT_DISTRIBUTION_BLOCKERS = Path("05_reports") / "distribution_readiness" / "TITAN_DISTRIBUTION_BLOCKER_REGISTER.csv"
INPUT_DISTRIBUTION_CONDITIONS = Path("05_reports") / "distribution_readiness" / "TITAN_DISTRIBUTION_CONDITION_REGISTER.csv"
INPUT_FREEZE_MANIFEST = Path("05_reports") / "investor_data_room_freeze" / "TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json"

OUTPUT_COVER_NOTE_MD = "TITAN_EXTERNAL_RELEASE_COVER_NOTE.md"
OUTPUT_MANIFEST_JSON = "TITAN_EXTERNAL_RELEASE_MANIFEST.json"
OUTPUT_INDEX_CSV = "TITAN_EXTERNAL_RELEASE_INDEX.csv"
OUTPUT_CHECKSUMS_CSV = "TITAN_EXTERNAL_RELEASE_CHECKSUMS.csv"
OUTPUT_DECISION_SNAPSHOT_JSON = "TITAN_EXTERNAL_RELEASE_DECISION_SNAPSHOT.json"

AUDIT_LOG = Path("06_logs") / "external_release_package_builder_audit.jsonl"
ERROR_LOG = Path("06_logs") / "external_release_package_builder_errors.jsonl"

RELEASE_READY = "EXTERNAL_RELEASE_PACKAGE_READY"
RELEASE_INTERNAL_PREP_ONLY = "EXTERNAL_RELEASE_INTERNAL_PREP_ONLY"
RELEASE_WITH_CONDITIONS = "EXTERNAL_RELEASE_PACKAGE_CONDITIONAL"
RELEASE_BLOCKED = "EXTERNAL_RELEASE_BLOCKED"
RELEASE_INCOMPLETE = "EXTERNAL_RELEASE_INCOMPLETE"

ALLOWED_GO_DECISIONS = {"GO_FOR_DISTRIBUTION"}
CONDITIONAL_DECISIONS = {"GO_WITH_CONDITIONS"}


@dataclass(frozen=True)
class ReleasePaths:
    base_dir: Path
    output_dir: Path
    release_files_dir: Path
    decision_json: Path
    release_index_input: Path
    blockers_input: Path
    conditions_input: Path
    freeze_manifest: Path
    cover_note_md: Path
    manifest_json: Path
    index_csv: Path
    checksums_csv: Path
    decision_snapshot_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return payload


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> ReleasePaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return ReleasePaths(
        base_dir=base_dir,
        output_dir=output_dir,
        release_files_dir=output_dir / "RELEASE_FILES",
        decision_json=base_dir / INPUT_DISTRIBUTION_DECISION,
        release_index_input=base_dir / INPUT_DISTRIBUTION_RELEASE_INDEX,
        blockers_input=base_dir / INPUT_DISTRIBUTION_BLOCKERS,
        conditions_input=base_dir / INPUT_DISTRIBUTION_CONDITIONS,
        freeze_manifest=base_dir / INPUT_FREEZE_MANIFEST,
        cover_note_md=output_dir / OUTPUT_COVER_NOTE_MD,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        index_csv=output_dir / OUTPUT_INDEX_CSV,
        checksums_csv=output_dir / OUTPUT_CHECKSUMS_CSV,
        decision_snapshot_json=output_dir / OUTPUT_DECISION_SNAPSHOT_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def determine_release_status(
    decision: dict[str, Any],
    blockers: list[dict[str, Any]],
    conditions: list[dict[str, Any]],
    args: argparse.Namespace,
) -> tuple[str, list[str], bool]:
    reasons: list[str] = []
    allowed_to_copy = False

    distribution_decision = str(decision.get("distribution_decision") or "")

    if args.internal_prep_only:
        reasons.append("Internal preparation only; package is not approved for external distribution.")
        return RELEASE_INTERNAL_PREP_ONLY, reasons, True

    if args.override_gate:
        if not args.override_reason:
            reasons.append("Override requested without override reason.")
            return RELEASE_BLOCKED, reasons, False
        reasons.append(f"Gate override used: {args.override_reason}")
        return RELEASE_INTERNAL_PREP_ONLY, reasons, True

    if distribution_decision in ALLOWED_GO_DECISIONS:
        reasons.append("Step 28 distribution decision is GO_FOR_DISTRIBUTION.")
        allowed_to_copy = True
        return RELEASE_READY, reasons, allowed_to_copy

    if distribution_decision in CONDITIONAL_DECISIONS:
        if args.allow_conditional:
            reasons.append("Step 28 decision is GO_WITH_CONDITIONS and --allow-conditional was used.")
            allowed_to_copy = True
            return RELEASE_WITH_CONDITIONS, reasons, allowed_to_copy
        reasons.append("Step 28 decision is GO_WITH_CONDITIONS; use --allow-conditional only after authorized review.")
        return RELEASE_BLOCKED, reasons, False

    if distribution_decision in {"INCOMPLETE_NO_DISTRIBUTION_DECISION"}:
        reasons.append("Step 28 distribution decision is incomplete.")
        return RELEASE_INCOMPLETE, reasons, False

    reasons.append(f"Step 28 distribution decision blocks release: {distribution_decision}")
    if blockers:
        reasons.append(f"Open blockers in Step 28: {len(blockers)}")
    if conditions:
        reasons.append(f"Open conditions in Step 28: {len(conditions)}")
    return RELEASE_BLOCKED, reasons, False


def release_target_path(release_files_dir: Path, source_path: Path, category: str, name: str) -> Path:
    safe_category = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in str(category or "UNCLASSIFIED")).strip() or "UNCLASSIFIED"
    safe_name = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in str(name or source_path.stem)).strip() or source_path.stem
    return release_files_dir / safe_category / f"{safe_name}__{source_path.name}"


def build_release_rows(release_index: list[dict[str, Any]], paths: ReleasePaths, allowed_to_copy: bool, manifest_only: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths.release_files_dir.mkdir(parents=True, exist_ok=True)

    for item in release_index:
        eligible = bool_from_cell(item.get("Release_Eligible"))
        frozen_path_raw = item.get("Frozen_Path")
        frozen_path = Path(frozen_path_raw) if frozen_path_raw else None
        source_sha = item.get("Frozen_SHA256") or item.get("Source_SHA256")
        category = item.get("Category") or "UNCLASSIFIED"
        name = item.get("Name") or item.get("Release_Item_ID")

        row = {
            "Release_Item_ID": item.get("Release_Item_ID"),
            "Name": name,
            "Category": category,
            "Eligible_From_Gate": eligible,
            "Frozen_Path": str(frozen_path) if frozen_path else None,
            "Frozen_SHA256": item.get("Frozen_SHA256"),
            "Source_SHA256": item.get("Source_SHA256"),
            "Release_Path": None,
            "Release_SHA256": None,
            "Copied_To_Release": False,
            "Hash_OK": None,
            "Release_Status": "NOT_SELECTED",
            "Reason": "",
        }

        if not eligible:
            row["Release_Status"] = "NOT_ELIGIBLE"
            row["Reason"] = "Release_Eligible is not true in Step 28 release index."
            rows.append(row)
            continue

        if not frozen_path or not frozen_path.exists():
            row["Release_Status"] = "MISSING_FROZEN_FILE"
            row["Reason"] = "Frozen file does not exist."
            rows.append(row)
            continue

        if not allowed_to_copy:
            row["Release_Status"] = "GATE_NOT_ALLOWED"
            row["Reason"] = "Distribution gate did not authorize release copy."
            rows.append(row)
            continue

        target = release_target_path(paths.release_files_dir, frozen_path, str(category), str(name))
        target.parent.mkdir(parents=True, exist_ok=True)

        if manifest_only:
            row["Release_Path"] = str(target)
            row["Release_SHA256"] = sha256_file(frozen_path)
            row["Copied_To_Release"] = False
            row["Hash_OK"] = row["Release_SHA256"] == source_sha if source_sha else None
            row["Release_Status"] = "MANIFEST_ONLY"
            row["Reason"] = "Manifest-only mode; file not copied."
            rows.append(row)
            continue

        shutil.copy2(frozen_path, target)
        release_sha = sha256_file(target)

        row["Release_Path"] = str(target)
        row["Release_SHA256"] = release_sha
        row["Copied_To_Release"] = True
        row["Hash_OK"] = release_sha == source_sha if source_sha else None
        row["Release_Status"] = "COPIED" if row["Hash_OK"] is True else "HASH_MISMATCH"
        row["Reason"] = "Copied from frozen export." if row["Hash_OK"] is True else "Release hash differs from frozen/source hash."
        rows.append(row)

    return rows


def build_checksum_rows(release_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in release_rows:
        rows.append({
            "Release_Item_ID": row.get("Release_Item_ID"),
            "Name": row.get("Name"),
            "Category": row.get("Category"),
            "Frozen_Path": row.get("Frozen_Path"),
            "Release_Path": row.get("Release_Path"),
            "Frozen_SHA256": row.get("Frozen_SHA256"),
            "Source_SHA256": row.get("Source_SHA256"),
            "Release_SHA256": row.get("Release_SHA256"),
            "Hash_OK": row.get("Hash_OK"),
            "Release_Status": row.get("Release_Status"),
        })
    return rows


def build_decision_snapshot(decision: dict[str, Any], blockers: list[dict[str, Any]], conditions: list[dict[str, Any]], release_status: str, release_reasons: list[str]) -> dict[str, Any]:
    snapshot = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "source_distribution_decision": {
            "distribution_decision": decision.get("distribution_decision"),
            "target": decision.get("target"),
            "strict_mode": decision.get("strict_mode"),
            "decision_sha256": decision.get("distribution_readiness_decision_sha256"),
            "decision_reasons": decision.get("decision_reasons"),
            "recommended_action": decision.get("recommended_action"),
            "summary": decision.get("summary"),
            "status_snapshot": decision.get("status_snapshot"),
        },
        "external_release_status": release_status,
        "external_release_status_reasons": release_reasons,
        "blocker_count": len(blockers),
        "condition_count": len(conditions),
        "blockers": blockers,
        "conditions": conditions,
    }
    snapshot["decision_snapshot_sha256"] = sha256_json(snapshot)
    return snapshot


def build_manifest(
    paths: ReleasePaths,
    args: argparse.Namespace,
    decision: dict[str, Any],
    freeze_manifest: dict[str, Any] | None,
    release_status: str,
    release_reasons: list[str],
    release_rows: list[dict[str, Any]],
    checksum_rows: list[dict[str, Any]],
    decision_snapshot: dict[str, Any],
) -> dict[str, Any]:
    copied = [r for r in release_rows if r.get("Copied_To_Release")]
    mismatches = [r for r in release_rows if r.get("Hash_OK") is False]

    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "EXTERNAL_RELEASE_PACKAGE_AUDIT_LOCKED",
        "target": args.target.upper(),
        "base_dir": str(paths.base_dir),
        "output_dir": str(paths.output_dir),
        "release_files_dir": str(paths.release_files_dir),
        "release_status": release_status,
        "release_status_reasons": release_reasons,
        "internal_prep_only": bool(args.internal_prep_only),
        "override_gate": bool(args.override_gate),
        "override_reason": args.override_reason,
        "allow_conditional": bool(args.allow_conditional),
        "manifest_only": bool(args.manifest_only),
        "strict_mode": bool(args.strict),
        "source_distribution_decision": decision.get("distribution_decision"),
        "source_distribution_decision_sha256": decision.get("distribution_readiness_decision_sha256"),
        "source_freeze_manifest_sha256": (freeze_manifest or {}).get("freeze_manifest_sha256"),
        "decision_snapshot_sha256": decision_snapshot.get("decision_snapshot_sha256"),
        "summary": {
            "release_rows": len(release_rows),
            "copied_files": len(copied),
            "manifest_only_rows": sum(1 for r in release_rows if r.get("Release_Status") == "MANIFEST_ONLY"),
            "not_eligible_rows": sum(1 for r in release_rows if r.get("Release_Status") == "NOT_ELIGIBLE"),
            "missing_frozen_files": sum(1 for r in release_rows if r.get("Release_Status") == "MISSING_FROZEN_FILE"),
            "hash_mismatch_rows": len(mismatches),
            "hash_ok_rows": sum(1 for r in release_rows if r.get("Hash_OK") is True),
        },
        "outputs": {
            "cover_note_md": str(paths.cover_note_md),
            "manifest_json": str(paths.manifest_json),
            "release_index_csv": str(paths.index_csv),
            "checksums_csv": str(paths.checksums_csv),
            "decision_snapshot_json": str(paths.decision_snapshot_json),
            "release_files_dir": str(paths.release_files_dir),
        },
        "governance_rule": {
            "builder_does_not_send_files": True,
            "builder_does_not_upload_files": True,
            "builder_does_not_modify_original_sources": True,
            "external_distribution_requires_authorized_signoff": True,
            "release_package_is_copy_of_frozen_outputs": True,
            "release_hashes_must_match_frozen_hashes": True,
            "audit_precedes_decision": True,
            "release_package_precedes_transmission": True,
        },
    }
    manifest["external_release_manifest_sha256"] = sha256_json(manifest)
    return manifest


def cover_note_markdown(manifest: dict[str, Any], decision_snapshot: dict[str, Any], release_rows: list[dict[str, Any]]) -> str:
    summary = manifest.get("summary", {}) if isinstance(manifest.get("summary"), dict) else {}
    decision = decision_snapshot.get("source_distribution_decision", {}) if isinstance(decision_snapshot.get("source_distribution_decision"), dict) else {}

    rows_preview = release_rows[:120]
    table_lines = ["| Status | Hash OK | Category | Name | Release Path |", "|---|---:|---|---|---|"]
    for row in rows_preview:
        table_lines.append(
            f"| {md_escape(row.get('Release_Status'))} | "
            f"{row.get('Hash_OK')} | "
            f"{md_escape(row.get('Category'))} | "
            f"{md_escape(row.get('Name'))} | "
            f"`{md_escape(row.get('Release_Path'))}` |"
        )

    return f"""# TITAN External Release Package Cover Note

## 1. Release Identity

| Field | Value |
|---|---|
| Created At | {manifest.get("created_at")} |
| Target | {manifest.get("target")} |
| Release Status | {manifest.get("release_status")} |
| Internal Prep Only | {manifest.get("internal_prep_only")} |
| Override Gate | {manifest.get("override_gate")} |
| Allow Conditional | {manifest.get("allow_conditional")} |
| Manifest SHA-256 | `{manifest.get("external_release_manifest_sha256")}` |
| Decision Snapshot SHA-256 | `{manifest.get("decision_snapshot_sha256")}` |

**Release status reasons**

```json
{json.dumps(manifest.get("release_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Source Distribution Decision

| Field | Value |
|---|---|
| Step 28 Decision | {decision.get("distribution_decision")} |
| Step 28 Target | {decision.get("target")} |
| Step 28 Strict Mode | {decision.get("strict_mode")} |
| Step 28 Decision SHA-256 | `{decision.get("decision_sha256")}` |
| Step 28 Recommended Action | {md_escape(decision.get("recommended_action"))} |

---

## 3. Release Package Summary

| Metric | Value |
|---|---:|
| Release Rows | {summary.get("release_rows")} |
| Copied Files | {summary.get("copied_files")} |
| Manifest-Only Rows | {summary.get("manifest_only_rows")} |
| Not Eligible Rows | {summary.get("not_eligible_rows")} |
| Missing Frozen Files | {summary.get("missing_frozen_files")} |
| Hash OK Rows | {summary.get("hash_ok_rows")} |
| Hash Mismatch Rows | {summary.get("hash_mismatch_rows")} |

---

## 4. Release Index Preview

{chr(10).join(table_lines)}

---

## 5. Mandatory Limitation

```text
This package builder does not send, upload or share files.
External transmission requires a separate authorized human action.
This package is a copy of frozen outputs only.
Original documents and JSON reports remain authoritative.
If release status is not EXTERNAL_RELEASE_PACKAGE_READY, do not distribute without formal written authorization.
```

---

## 6. Governance Rule

```text
Release package builder does not send files.
Release package builder does not upload files.
Release package builder does not modify original sources.
External distribution requires authorized sign-off.
Release package is copy of frozen outputs.
Release hashes must match frozen/source hashes.
Audit precedes decision.
Release package precedes transmission.
```
"""


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def write_release_index_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Release_Item_ID",
        "Name",
        "Category",
        "Eligible_From_Gate",
        "Frozen_Path",
        "Frozen_SHA256",
        "Source_SHA256",
        "Release_Path",
        "Release_SHA256",
        "Copied_To_Release",
        "Hash_OK",
        "Release_Status",
        "Reason",
    ])


def write_checksums_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Release_Item_ID",
        "Name",
        "Category",
        "Frozen_Path",
        "Release_Path",
        "Frozen_SHA256",
        "Source_SHA256",
        "Release_SHA256",
        "Hash_OK",
        "Release_Status",
    ])


def print_summary(manifest: dict[str, Any], paths: ReleasePaths) -> None:
    summary = manifest.get("summary", {}) if isinstance(manifest.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN EXTERNAL RELEASE PACKAGE BUILDER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Target:                   {manifest.get('target')}")
    print(f"Release status:           {manifest.get('release_status')}")
    print(f"Copied files:             {summary.get('copied_files')}")
    print(f"Hash OK rows:             {summary.get('hash_ok_rows')}")
    print(f"Hash mismatches:          {summary.get('hash_mismatch_rows')}")
    print(f"Missing frozen files:     {summary.get('missing_frozen_files')}")
    print("-" * 100)
    print(f"Cover Note:               {paths.cover_note_md}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print(f"Release Index CSV:        {paths.index_csv}")
    print(f"Checksums CSV:            {paths.checksums_csv}")
    print(f"Decision Snapshot JSON:   {paths.decision_snapshot_json}")
    print(f"Release Files:            {paths.release_files_dir}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 29 — external release package builder.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--target", default="EBRD", choices=["EBRD", "EIB", "IFC", "BOARD", "INVESTOR", "INTERNAL"], help="Release target label.")
    parser.add_argument("--allow-conditional", action="store_true", help="Allow package build when Step 28 is GO_WITH_CONDITIONS.")
    parser.add_argument("--internal-prep-only", action="store_true", help="Build package for internal prep only; not approved for external distribution.")
    parser.add_argument("--override-gate", action="store_true", help="Override Step 28 gate for internal dry-run only.")
    parser.add_argument("--override-reason", default="", help="Required reason when --override-gate is used.")
    parser.add_argument("--manifest-only", action="store_true", help="Do not copy files; create manifest/index only.")
    parser.add_argument("--strict", action="store_true", help="Strict metadata flag.")
    parser.add_argument("--print", action="store_true", help="Print cover note to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, args.output_dir)

    try:
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        paths.output_dir.mkdir(parents=True, exist_ok=True)
        paths.release_files_dir.mkdir(parents=True, exist_ok=True)

        decision = load_json(paths.decision_json)
        freeze_manifest = load_json_if_exists(paths.freeze_manifest)
        release_index = read_csv_rows(paths.release_index_input)
        blockers = read_csv_rows(paths.blockers_input)
        conditions = read_csv_rows(paths.conditions_input)

        release_status, release_reasons, allowed_to_copy = determine_release_status(
            decision=decision,
            blockers=blockers,
            conditions=conditions,
            args=args,
        )

        release_rows = build_release_rows(
            release_index=release_index,
            paths=paths,
            allowed_to_copy=allowed_to_copy,
            manifest_only=bool(args.manifest_only),
        )
        checksum_rows = build_checksum_rows(release_rows)
        decision_snapshot = build_decision_snapshot(decision, blockers, conditions, release_status, release_reasons)
        manifest = build_manifest(
            paths=paths,
            args=args,
            decision=decision,
            freeze_manifest=freeze_manifest,
            release_status=release_status,
            release_reasons=release_reasons,
            release_rows=release_rows,
            checksum_rows=checksum_rows,
            decision_snapshot=decision_snapshot,
        )
        cover_note = cover_note_markdown(manifest, decision_snapshot, release_rows)

        write_json(paths.decision_snapshot_json, decision_snapshot)
        write_json(paths.manifest_json, manifest)
        write_text(paths.cover_note_md, cover_note)
        write_release_index_csv(paths.index_csv, release_rows)
        write_checksums_csv(paths.checksums_csv, checksum_rows)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "EXTERNAL_RELEASE_PACKAGE_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "target": args.target,
            "release_status": release_status,
            "release_manifest_sha256": manifest.get("external_release_manifest_sha256"),
            "decision_snapshot_sha256": decision_snapshot.get("decision_snapshot_sha256"),
            "summary": manifest.get("summary"),
            "outputs": manifest.get("outputs"),
        })

        print_summary(manifest, paths)

        if args.print:
            print("\n" + cover_note)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "EXTERNAL_RELEASE_PACKAGE_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "target": args.target,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN EXTERNAL RELEASE PACKAGE BUILDER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
