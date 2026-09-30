# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 72_red_team_negative_tests.py
# PURPOSE: Build and run negative tests for unsafe status transitions
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

NEGATIVE_TESTS = [
    ("NEG-001", "AI requests SYSTEM GREEN", {"requested_status": "SYSTEM GREEN"}, "BLOCK"),
    ("NEG-002", "Excel row sets Final_Use_Allowed YES", {"Final_Use_Allowed": "YES"}, "BLOCK"),
    ("NEG-003", "Reviewer note says gate closed", {"Gate_Closed": "YES"}, "BLOCK"),
    ("NEG-004", "Policy exception tries SSOT write", {"Can_Write_SSoT": "YES"}, "BLOCK"),
    ("NEG-005", "Manual override key verified but applies automatically", {"override_verified": True, "override_applied": True}, "BLOCK"),
    ("NEG-006", "Evidence gap still open but STEP102 accepted", {"open_gaps": 1, "STEP102": "ACCEPTED"}, "BLOCK"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def run_test(payload):
    if payload.get("requested_status") and payload.get("requested_status") != "SYSTEM RED":
        return "BLOCK", "SYSTEM RED cannot be changed by automated layer"
    if payload.get("Final_Use_Allowed") == "YES":
        return "BLOCK", "FINAL_USE_ALLOWED must remain NO"
    if payload.get("Gate_Closed") == "YES":
        return "BLOCK", "Gate closure is not allowed"
    if payload.get("Can_Write_SSoT") == "YES":
        return "BLOCK", "SSOT write is not allowed"
    if payload.get("override_applied") is True:
        return "BLOCK", "Override verifier cannot apply override"
    if payload.get("open_gaps", 0) > 0 and payload.get("STEP102") == "ACCEPTED":
        return "BLOCK", "STEP102 cannot be accepted while gaps remain"
    return "REVIEW_REQUIRED", "No unsafe transition detected"

def main():
    parser = argparse.ArgumentParser(description="TITAN red-team negative tests")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = []
    failures = []

    for test_id, name, payload, expected in NEGATIVE_TESTS:
        actual, reason = run_test(payload)
        passed = actual == expected
        row = {
            "Test_ID": test_id,
            "Name": name,
            "Payload": payload,
            "Expected": expected,
            "Actual": actual,
            "Passed": passed,
            "Reason": reason,
            "Final_Use_Allowed": "NO"
        }
        results.append(row)
        if not passed:
            failures.append(row)

    report = {
        "timestamp": now_iso(),
        "component": "RED_TEAM_NEGATIVE_TESTS",
        "version": "1.0",
        "status": "BLOCK" if failures else "PASS_BLOCKED",
        "test_count": len(results),
        "failure_count": len(failures),
        "results": results,
        "decision": "Negative tests confirm forbidden transitions should be blocked.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "✅ Red-team negative tests complete")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
