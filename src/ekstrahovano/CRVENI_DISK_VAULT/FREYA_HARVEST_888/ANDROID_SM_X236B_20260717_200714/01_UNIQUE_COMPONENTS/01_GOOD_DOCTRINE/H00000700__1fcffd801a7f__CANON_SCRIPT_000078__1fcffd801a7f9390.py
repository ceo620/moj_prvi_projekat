# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 166_absolute_review_only_terminal_record.py
# PURPOSE: Generate absolute terminal record for review-only state
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
    parser = argparse.ArgumentParser(description="Generate absolute review-only terminal record")
    parser.add_argument("--closeout-index", required=True)
    parser.add_argument("--receipt-validation", required=True)
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    closeout = load_json(args.closeout_index)
    validation = load_json(args.receipt_validation)

    if closeout is None or validation is None:
        print("❌ Missing closeout index or receipt validation JSON")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "ABSOLUTE_REVIEW_ONLY_TERMINAL_RECORD",
        "version": "1.0",
        "status": "ABSOLUTE_REVIEW_ONLY_TERMINAL_LOCKED",
        "operator": args.operator,
        "closeout_records": closeout.get("record_count", "UNKNOWN"),
        "closeout_hash": closeout.get("closeout_hash", "UNKNOWN"),
        "receipt_validation_status": validation.get("status", "UNKNOWN"),
        "receipt_validation_violations": validation.get("violation_count", "UNKNOWN"),
        "allowed_scope": "READ_ONLY_REVIEW_OR_AUDIT_ONLY",
        "forbidden_scope": "ALL_OPERATIONAL_PRODUCTION_FINAL_APPROVAL_GATE_SSOT_STEP102_ACTIONS",
        "terminal_statement": "The chain is terminally locked for read-only review/audit only. No operational action, production, approval, gate closure, SSoT write, STEP102 unlock, or final use is authorized.",
        "decision": "Absolute terminal record is documentary only and grants no authority.",
        **CANON,
    }

    payload["absolute_terminal_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Absolute Review-Only Terminal Record",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        "",
        "## Final Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Terminal Scope",
        "",
        f"- Allowed scope: `{payload['allowed_scope']}`",
        f"- Forbidden scope: `{payload['forbidden_scope']}`",
        "",
        "## Evidence Summary",
        "",
        f"- Closeout records: `{payload['closeout_records']}`",
        f"- Closeout hash: `{payload['closeout_hash']}`",
        f"- Receipt validation status: `{payload['receipt_validation_status']}`",
        f"- Receipt validation violations: `{payload['receipt_validation_violations']}`",
        "",
        "## Terminal Statement",
        "",
        payload["terminal_statement"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Absolute Terminal Hash",
        "",
        f"`{payload['absolute_terminal_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Absolute review-only terminal record generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
