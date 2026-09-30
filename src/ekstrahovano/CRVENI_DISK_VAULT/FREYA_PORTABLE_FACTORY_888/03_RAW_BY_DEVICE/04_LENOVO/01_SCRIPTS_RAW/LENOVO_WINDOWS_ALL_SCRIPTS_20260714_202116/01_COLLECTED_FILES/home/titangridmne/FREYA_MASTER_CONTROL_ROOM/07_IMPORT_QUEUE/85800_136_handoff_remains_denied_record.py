# ============================================================
# TITAN_KERNEL: 136_handoff_remains_denied_record.py
# PURPOSE: Generate final record that handoff remains denied
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
    parser = argparse.ArgumentParser(description="Generate handoff remains denied record")
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {
        "timestamp": now_iso(),
        "component": "HANDOFF_REMAINS_DENIED_RECORD",
        "version": "1.0",
        "status": "HANDOFF_REMAINS_DENIED",
        "operator": args.operator,
        "handoff_allowed": "NO",
        "operational_transfer_allowed": "NO",
        "review_only_allowed": "YES",
        "record_statement": "Handoff remains denied for operational/production/final-use purposes. Review-only handling remains the only allowed scope.",
        "decision": "This record does not authorize any operational handoff.",
        **CANON
    }

    payload["record_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Handoff Remains Denied Record",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        "",
        "## Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Handoff State",
        "",
        "- Operational handoff allowed: `NO`",
        "- Operational transfer allowed: `NO`",
        "- Review-only handling allowed: `YES`",
        "",
        "## Record Statement",
        "",
        payload["record_statement"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Record Hash",
        "",
        f"`{payload['record_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Handoff remains denied record generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
