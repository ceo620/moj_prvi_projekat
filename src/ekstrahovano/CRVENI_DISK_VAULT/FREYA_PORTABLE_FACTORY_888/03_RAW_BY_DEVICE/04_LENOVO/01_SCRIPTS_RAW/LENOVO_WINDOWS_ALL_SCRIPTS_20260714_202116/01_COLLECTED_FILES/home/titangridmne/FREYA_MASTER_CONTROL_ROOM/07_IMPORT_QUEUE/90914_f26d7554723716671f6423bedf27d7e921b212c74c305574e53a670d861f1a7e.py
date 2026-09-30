# ============================================================
# TITAN_KERNEL: 118_nothing_accepted_memorandum.py
# PURPOSE: Generate final memorandum that nothing is accepted/final/approved
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import sys
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
    parser = argparse.ArgumentParser(description="Generate nothing accepted memorandum")
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {
        "timestamp": now_iso(),
        "component": "NOTHING_ACCEPTED_MEMORANDUM",
        "version": "1.0",
        "status": "NOTHING_ACCEPTED",
        "operator": args.operator,
        "memorandum": "No evidence is approved, no gate is closed, no SSoT write is allowed, STEP102 is not accepted, and no final use is permitted.",
        "decision": "This memorandum confirms non-acceptance only. It is not a release artifact.",
        **CANON
    }

    payload["memorandum_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Nothing Accepted Memorandum",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        "",
        "## Memorandum",
        "",
        payload["memorandum"],
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Explicit Non-Acceptance",
        "",
        "- Evidence approved: `0`",
        "- Gates closed: `0`",
        "- STEP102 accepted: `NO`",
        "- Final use allowed: `NO`",
        "- Canonical SSoT write allowed: `NO`",
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Memorandum Hash",
        "",
        f"`{payload['memorandum_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Nothing accepted memorandum generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    sys.exit(main())
