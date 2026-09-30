# ============================================================
# TITAN_KERNEL: 92_state_transition_denial_validator.py
# PURPOSE: Validate requested pipeline transitions are denied under active canon
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
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

ALLOWED_TRANSITIONS = {
    "LOCKED_AUDIT_ONLY": ["LOCKED_AUDIT_ONLY", "REVIEW_REQUIRED", "REMEDIATION_REQUIRED"],
    "SYSTEM_RED_LOCKED": ["SYSTEM_RED_LOCKED", "REVIEW_REQUIRED", "REMEDIATION_REQUIRED"],
}

FORBIDDEN_TARGETS = {
    "READY",
    "APPROVED",
    "RELEASED",
    "FINAL_USE_ALLOWED",
    "PRODUCTION",
    "SYSTEM_GREEN",
    "SYSTEM_GOLDEN",
    "STEP102_ACCEPTED",
    "GATE_CLOSED",
    "SSOT_WRITE_ALLOWED"
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Validate denied state transitions")
    parser.add_argument("--state-json", required=True)
    parser.add_argument("--requested-target", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    state = load_json(args.state_json)
    if state is None:
        result = {
            "timestamp": now_iso(),
            "component": "STATE_TRANSITION_DENIAL_VALIDATOR",
            "status": "BLOCK",
            "message": "State JSON missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    current = state.get("state", state.get("status", "UNKNOWN"))
    target = args.requested_target.strip().upper()

    violations = []
    allowed = False

    if target in FORBIDDEN_TARGETS:
        violations.append(f"Requested forbidden target: {target}")

    allowed_targets = ALLOWED_TRANSITIONS.get(current, [])
    if target not in allowed_targets:
        violations.append(f"Transition from {current} to {target} is not allowed")

    if not violations:
        allowed = True

    payload = {
        "timestamp": now_iso(),
        "component": "STATE_TRANSITION_DENIAL_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "current_state": current,
        "requested_target": target,
        "transition_allowed": "YES" if allowed else "NO",
        "violations": violations,
        "decision": "Forbidden transitions are denied. This validator does not approve any state change.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Transition denied" if violations else "✅ Transition remains safe/non-final"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
