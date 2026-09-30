# ============================================================
# TITAN_KERNEL: 124_final_reconciliation_memorandum.py
# PURPOSE: Generate final reconciliation memorandum for all locked archive sets
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

EXIT_LOCKED = 1
EXIT_FILE_ERROR = 2
EXIT_WRITE_ERROR = 3

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "RISK_BASELINE": 890,
    "P0_GATES": "10/10 BLOCKED",
    "EVIDENCE_GAPS_REMAINING": 6,
    "EVIDENCE_APPROVED": 0,
    "GATES_CLOSED": 0,
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Generate final reconciliation memorandum")
    parser.add_argument("--archive-set", required=True)
    parser.add_argument("--content-index", required=True)
    parser.add_argument("--locked-status-register", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    archive_set = load_json(args.archive_set)
    content_index = load_json(args.content_index)
    status_register = load_json(args.locked_status_register)

    if archive_set is None or content_index is None or status_register is None:
        print("❌ Missing required reconciliation inputs")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_RECONCILIATION_MEMORANDUM",
        "version": "1.0",
        "status": "FINAL_RECONCILIATION_LOCKED",
        "archive_count": archive_set.get("archive_count", "UNKNOWN"),
        "invalid_archive_count": archive_set.get("invalid_count", "UNKNOWN"),
        "content_count": content_index.get("content_count", "UNKNOWN"),
        "duplicate_group_count": content_index.get("duplicate_group_count", "UNKNOWN"),
        "locked_status_record_count": status_register.get("record_count", "UNKNOWN"),
        "memorandum": "Final archive sets reconcile to a locked, non-accepted, review-only posture.",
        "decision": "Reconciliation does not approve evidence, close gates, write SSoT, unlock STEP102, or allow final use.",
        **CANON,
    }

    payload["reconciliation_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Final Reconciliation Memorandum",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "## Final Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Reconciliation Summary",
        "",
        f"- Archive count: `{payload['archive_count']}`",
        f"- Invalid archive count: `{payload['invalid_archive_count']}`",
        f"- Content count: `{payload['content_count']}`",
        f"- Duplicate group count: `{payload['duplicate_group_count']}`",
        f"- Locked status records: `{payload['locked_status_record_count']}`",
        "",
        "## Memorandum",
        "",
        payload["memorandum"],
        "",
        "## Decision",
        "",
        payload["decision"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Reconciliation Hash",
        "",
        f"`{payload['reconciliation_hash']}`",
        "",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Final reconciliation memorandum generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
