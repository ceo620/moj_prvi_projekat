# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 163_review_only_chain_frozen_receipt.py
# PURPOSE: Generate final receipt that review-only chain archive state is frozen
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
    parser = argparse.ArgumentParser(description="Generate review-only chain frozen receipt")
    parser.add_argument("--chain-index", required=True)
    parser.add_argument("--freeze-validation", required=True)
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.chain_index)
    validation = load_json(args.freeze_validation)

    if index is None or validation is None:
        print("❌ Missing chain index or freeze validation JSON")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_CHAIN_FROZEN_RECEIPT",
        "version": "1.0",
        "status": "REVIEW_ONLY_CHAIN_FROZEN_LOCKED",
        "operator": args.operator,
        "chain_index_records": index.get("record_count", "UNKNOWN"),
        "chain_index_hash": index.get("index_hash", "UNKNOWN"),
        "freeze_validation_status": validation.get("status", "UNKNOWN"),
        "freeze_validation_violations": validation.get("violation_count", "UNKNOWN"),
        "allowed_scope": "READ_ONLY_REVIEW_OR_AUDIT_ONLY",
        "receipt_statement": "Review-only chain archive state is frozen and locked. No operational action, approval, SSoT write, STEP102 unlock, or final use is authorized.",
        "decision": "Frozen receipt is documentary only and grants no authority.",
        **CANON,
    }

    payload["review_only_chain_frozen_receipt_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Review-Only Chain Frozen Receipt",
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
        "## Freeze Summary",
        "",
        f"- Chain index records: `{payload['chain_index_records']}`",
        f"- Chain index hash: `{payload['chain_index_hash']}`",
        f"- Freeze validation status: `{payload['freeze_validation_status']}`",
        f"- Freeze validation violations: `{payload['freeze_validation_violations']}`",
        f"- Allowed scope: `{payload['allowed_scope']}`",
        "",
        "## Receipt Statement",
        "",
        payload["receipt_statement"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Receipt Hash",
        "",
        f"`{payload['review_only_chain_frozen_receipt_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Review-only chain frozen receipt generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
