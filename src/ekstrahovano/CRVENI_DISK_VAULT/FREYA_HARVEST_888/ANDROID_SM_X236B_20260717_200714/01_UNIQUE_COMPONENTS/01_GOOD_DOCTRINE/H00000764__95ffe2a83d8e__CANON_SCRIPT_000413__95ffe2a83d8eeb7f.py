# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 165_review_only_frozen_receipt_validator.py
# PURPOSE: Validate review-only chain frozen receipt remains canonical
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
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

FORBIDDEN_PHRASES = [
    "final use allowed",
    "production authorized",
    "operational action authorized",
    "handoff authorized",
    "step102 accepted",
    "release approved",
    "evidence approved",
    "gate closed",
    "ssot write allowed",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Validate review-only frozen receipt")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    receipt = load_json(args.receipt)
    if receipt is None:
        result = {
            "timestamp": now_iso(),
            "component": "REVIEW_ONLY_FROZEN_RECEIPT_VALIDATOR",
            "status": "BLOCK",
            "message": "Receipt missing",
            **CANON,
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []

    for key, expected in CANON.items():
        actual = receipt.get(key)
        if actual != expected:
            violations.append({"field": key, "expected": expected, "actual": actual, "violation": "Canon mismatch"})

    if receipt.get("status") != "REVIEW_ONLY_CHAIN_FROZEN_LOCKED":
        violations.append({
            "field": "status",
            "expected": "REVIEW_ONLY_CHAIN_FROZEN_LOCKED",
            "actual": receipt.get("status"),
            "violation": "Unexpected receipt status"
        })

    if receipt.get("allowed_scope") != "READ_ONLY_REVIEW_OR_AUDIT_ONLY":
        violations.append({
            "field": "allowed_scope",
            "expected": "READ_ONLY_REVIEW_OR_AUDIT_ONLY",
            "actual": receipt.get("allowed_scope"),
            "violation": "Allowed scope is not review/audit-only"
        })

    text = json.dumps(receipt, ensure_ascii=False).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            violations.append({"field": "receipt_text", "violation": f"Forbidden phrase: {phrase}"})

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_FROZEN_RECEIPT_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "receipt": args.receipt,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Receipt validation confirms review-only locked state only. It grants no authority.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Review-only frozen receipt violation" if violations else "✅ Review-only frozen receipt validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
