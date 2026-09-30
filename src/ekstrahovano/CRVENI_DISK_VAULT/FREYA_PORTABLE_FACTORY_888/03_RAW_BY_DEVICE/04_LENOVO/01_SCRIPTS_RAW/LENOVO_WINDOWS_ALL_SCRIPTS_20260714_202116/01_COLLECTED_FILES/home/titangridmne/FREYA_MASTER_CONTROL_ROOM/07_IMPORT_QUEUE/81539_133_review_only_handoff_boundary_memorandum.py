# ============================================================
# TITAN_KERNEL: 133_review_only_handoff_boundary_memorandum.py
# PURPOSE: Generate final memorandum defining review-only handoff boundary
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
    parser = argparse.ArgumentParser(description="Generate review-only handoff boundary memorandum")
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--review-recipient", default="REVIEW_ONLY_RECIPIENT")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_HANDOFF_BOUNDARY_MEMORANDUM",
        "version": "1.0",
        "status": "REVIEW_ONLY_HANDOFF_BOUNDARY_LOCKED",
        "operator": args.operator,
        "review_recipient": args.review_recipient,
        "allowed_handoff_scope": "READ_ONLY_REVIEW_AND_AUDIT",
        "forbidden_handoff_scope": "PRODUCTION_FINAL_USE_APPROVAL_GATE_CLOSURE_SSOT_WRITE_STEP102_UNLOCK",
        "memorandum": "Any handoff is limited to read-only review/audit. No operational, production, approval, gate closure, SSoT write, STEP102 unlock, or final-use handoff is authorized.",
        "decision": "Review-only boundary is documentation only and grants no operational authority.",
        **CANON
    }

    payload["boundary_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Review-Only Handoff Boundary Memorandum",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        f"Review Recipient: {payload['review_recipient']}",
        "",
        "## Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Allowed Scope",
        "",
        f"`{payload['allowed_handoff_scope']}`",
        "",
        "## Forbidden Scope",
        "",
        f"`{payload['forbidden_handoff_scope']}`",
        "",
        "## Memorandum",
        "",
        payload["memorandum"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Boundary Hash",
        "",
        f"`{payload['boundary_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Review-only handoff boundary memorandum generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
