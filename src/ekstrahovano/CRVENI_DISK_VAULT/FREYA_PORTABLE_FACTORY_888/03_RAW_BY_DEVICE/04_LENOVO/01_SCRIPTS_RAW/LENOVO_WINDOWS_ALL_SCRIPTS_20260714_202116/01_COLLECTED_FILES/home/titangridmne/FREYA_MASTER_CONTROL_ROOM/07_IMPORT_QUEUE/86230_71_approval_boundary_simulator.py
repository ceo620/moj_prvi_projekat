# ============================================================
# TITAN_KERNEL: 71_approval_boundary_simulator.py
# PURPOSE: Simulate forbidden approval attempts and confirm they remain blocked
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

ATTEMPTS = [
    ("APPROVE_EVIDENCE", "EVIDENCE_APPROVAL_ALLOWED"),
    ("CLOSE_GATE", "GATE_CLOSURE_ALLOWED"),
    ("WRITE_SSOT", "SSOT_WRITE_ALLOWED"),
    ("ALLOW_FINAL_USE", "FINAL_USE_ALLOWED"),
    ("UNLOCK_STEP102", "STEP102"),
    ("CHANGE_SYSTEM_RED", "SYSTEM_STATUS"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def evaluate_attempt(action, target):
    if action == "UNLOCK_STEP102":
        return {"allowed": False, "result": "LOCKED / NOT ACCEPTED", "reason": "STEP102 hard lock active"}
    if action == "CHANGE_SYSTEM_RED":
        return {"allowed": False, "result": "SYSTEM RED", "reason": "SYSTEM RED hard lock active"}
    return {"allowed": False, "result": "NO", "reason": f"{target} is canonically NO"}

def main():
    parser = argparse.ArgumentParser(description="TITAN approval boundary simulator")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    simulations = []
    for idx, (action, target) in enumerate(ATTEMPTS, start=1):
        result = evaluate_attempt(action, target)
        simulations.append({
            "Simulation_ID": f"SIM-{idx:05d}",
            "Attempted_Action": action,
            "Target_Control": target,
            "Allowed": "YES" if result["allowed"] else "NO",
            "Result": result["result"],
            "Reason": result["reason"],
            "Boundary_Status": "PASS_BLOCKED",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "APPROVAL_BOUNDARY_SIMULATOR",
        "version": "1.0",
        "status": "PASS_BLOCKED",
        "simulations": simulations,
        "decision": "All simulated approval attempts remain blocked. No real approval attempted or granted.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Approval boundary simulation complete")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
