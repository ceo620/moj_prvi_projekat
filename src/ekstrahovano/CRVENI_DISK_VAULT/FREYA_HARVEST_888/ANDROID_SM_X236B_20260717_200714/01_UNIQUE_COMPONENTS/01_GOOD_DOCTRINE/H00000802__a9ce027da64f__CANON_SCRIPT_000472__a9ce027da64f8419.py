# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 88_archive_reconciliation_reporter.py
# PURPOSE: Generate final archive reconciliation report from archive and duplicate registers
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_FILE_ERROR = 2
EXIT_WRITE_ERROR = 3

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="TITAN archive reconciliation reporter")
    parser.add_argument("--archive-reconciliation", required=True)
    parser.add_argument("--duplicate-register", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    archive = load_json(args.archive_reconciliation)
    dup = load_json(args.duplicate_register)

    if archive is None or dup is None:
        print("❌ Missing archive reconciliation or duplicate register JSON")
        return EXIT_FILE_ERROR

    archive_count = archive.get("archive_count", 0)
    invalid_count = archive.get("invalid_count", 0)
    duplicate_group_count = dup.get("duplicate_group_count", 0)
    files_scanned = dup.get("files_scanned", 0)

    status = "REVIEW_REQUIRED"
    if invalid_count > 0:
        status = "BLOCK"

    payload = {
        "timestamp": now_iso(),
        "component": "ARCHIVE_RECONCILIATION_REPORTER",
        "version": "1.0",
        "status": status,
        "archive_count": archive_count,
        "invalid_archive_count": invalid_count,
        "files_scanned_for_duplicates": files_scanned,
        "duplicate_group_count": duplicate_group_count,
        "decision": "Archive reconciliation report is operational evidence only. It does not approve final use.",
        **CANON
    }

    md = [
        "# TITAN Archive Reconciliation Report",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "## Summary",
        "",
        f"- Archives reconciled: {archive_count}",
        f"- Invalid archives: {invalid_count}",
        f"- Files scanned for duplicates: {files_scanned}",
        f"- Duplicate groups: {duplicate_group_count}",
        "",
        "## Decision",
        "",
        "This report does not approve release, evidence, gates, SSoT write, STEP102 unlock, or final use.",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
    ]

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Archive reconciliation report: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
