# ============================================================
# TITAN_KERNEL: 130_no_operational_handoff_record.py
# PURPOSE: Generate final no-operational-handoff record
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

EXIT_LOCKED = 1
EXIT_WRITE_ERROR = 2

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

def main():
    parser = argparse.ArgumentParser(description="Generate no operational handoff record")
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--recipient", default="NO_OPERATIONAL_RECIPIENT")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {
        "timestamp": now_iso(),
        "component": "NO_OPERATIONAL_HANDOFF_RECORD",
        "version": "1.0",
        "status": "NO_OPERATIONAL_HANDOFF",
        "operator": args.operator,
        "recipient": args.recipient,
        "handoff_statement": "No operational handoff is authorized. Materials are restricted to review/audit-only use.",
        "decision": "No production, final-use, evidence approval, gate closure, SSoT write, or STEP102 unlock handoff is allowed.",
        **CANON
    }

    payload["handoff_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN No Operational Handoff Record",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        f"Recipient: {payload['recipient']}",
        "",
        "## Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Handoff Statement",
        "",
        payload["handoff_statement"],
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
        "## Handoff Hash",
        "",
        f"`{payload['handoff_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 No operational handoff record generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
