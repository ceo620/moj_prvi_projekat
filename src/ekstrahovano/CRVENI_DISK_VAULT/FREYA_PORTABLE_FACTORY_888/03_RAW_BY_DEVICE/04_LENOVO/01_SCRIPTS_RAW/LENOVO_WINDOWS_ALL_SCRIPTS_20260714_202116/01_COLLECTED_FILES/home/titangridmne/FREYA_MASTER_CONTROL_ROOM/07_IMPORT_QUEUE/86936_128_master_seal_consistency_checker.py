# ============================================================
# TITAN_KERNEL: 128_master_seal_consistency_checker.py
# PURPOSE: Validate final master seal record preserves locked/non-final canon
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Validate final master seal consistency")
    parser.add_argument("--master-seal", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    seal = load_json(args.master_seal)
    if seal is None:
        result = {
            "timestamp": now_iso(),
            "component": "MASTER_SEAL_CONSISTENCY_CHECKER",
            "status": "BLOCK",
            "message": "Master seal JSON missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []

    for key, expected in CANON.items():
        actual = seal.get(key)
        if actual != expected:
            violations.append({
                "field": key,
                "expected": expected,
                "actual": actual,
                "violation": "Master seal canon mismatch"
            })

    if seal.get("status") != "FINAL_MASTER_SEAL_LOCKED":
        violations.append({
            "field": "status",
            "expected": "FINAL_MASTER_SEAL_LOCKED",
            "actual": seal.get("status"),
            "violation": "Unexpected master seal status"
        })

    decision = str(seal.get("decision", "")).lower()
    forbidden_words = ["approval granted", "release approved", "final use allowed", "step102 accepted"]
    for phrase in forbidden_words:
        if phrase in decision:
            violations.append({
                "field": "decision",
                "violation": f"Forbidden decision wording: {phrase}"
            })

    result = {
        "timestamp": now_iso(),
        "component": "MASTER_SEAL_CONSISTENCY_CHECKER",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Consistency check confirms locked seal metadata only. It does not approve final use.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Master seal inconsistency" if violations else "✅ Master seal consistent"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
