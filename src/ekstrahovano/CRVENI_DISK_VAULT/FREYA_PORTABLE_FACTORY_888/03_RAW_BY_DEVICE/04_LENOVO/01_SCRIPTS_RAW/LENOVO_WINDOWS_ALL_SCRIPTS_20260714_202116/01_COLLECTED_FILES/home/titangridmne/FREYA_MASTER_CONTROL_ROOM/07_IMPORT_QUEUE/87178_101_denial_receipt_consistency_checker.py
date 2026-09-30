# ============================================================
# TITAN_KERNEL: 101_denial_receipt_consistency_checker.py
# PURPOSE: Validate post-orchestration denial receipt against active canon
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

FORBIDDEN = {
    "release_status": {"READY", "APPROVED", "RELEASED"},
    "freeze_status": {"FREEZE_ALLOWED", "APPROVED"},
    "status": {"APPROVED", "RELEASED", "FINAL_USE_ALLOWED", "UNLOCKED", "READY"},
    "FINAL_USE_ALLOWED": {"YES", True},
    "SSOT_WRITE_ALLOWED": {"YES", True},
    "EVIDENCE_APPROVAL_ALLOWED": {"YES", True},
    "GATE_CLOSURE_ALLOWED": {"YES", True},
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Validate post-orchestration denial receipt consistency")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    receipt = load_json(args.receipt)
    if receipt is None:
        result = {
            "timestamp": now_iso(),
            "component": "DENIAL_RECEIPT_CONSISTENCY_CHECKER",
            "status": "BLOCK",
            "message": "Receipt missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []

    for key, expected in CANON.items():
        actual = receipt.get(key)
        if actual != expected:
            violations.append({
                "field": key,
                "expected": expected,
                "actual": actual,
                "violation": "Canon mismatch in denial receipt"
            })

    for key, bad_values in FORBIDDEN.items():
        actual = receipt.get(key)
        if actual in bad_values:
            violations.append({
                "field": key,
                "actual": actual,
                "violation": "Forbidden approval/unlock value in receipt"
            })

    if receipt.get("status") != "ORCHESTRATION_DENIED":
        violations.append({
            "field": "status",
            "expected": "ORCHESTRATION_DENIED",
            "actual": receipt.get("status"),
            "violation": "Post-orchestration receipt must remain denied"
        })

    result = {
        "timestamp": now_iso(),
        "component": "DENIAL_RECEIPT_CONSISTENCY_CHECKER",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "receipt": args.receipt,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Receipt validation is audit-only. It does not approve release or final use.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Denial receipt inconsistency" if violations else "✅ Denial receipt consistent"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
