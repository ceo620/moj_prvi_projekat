# ============================================================
# TITAN_KERNEL: 90_pipeline_state_manager.py
# PURPOSE: Manage pipeline state as audit-only locked state record
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
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

def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def emit_jsonl(path, event):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="TITAN locked pipeline state manager")
    parser.add_argument("--readiness", help="release_readiness.json")
    parser.add_argument("--lock-verification", help="master_status_lock_verification.json")
    parser.add_argument("--handoff-precheck", help="handoff_to_90_precheck.json")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    readiness = load_json(args.readiness)
    lock_verification = load_json(args.lock_verification)
    handoff = load_json(args.handoff_precheck)

    blockers = [
        "SYSTEM RED hard lock active",
        "STEP102 LOCKED / NOT ACCEPTED",
        "FINAL_USE_ALLOWED = NO",
        "SSOT_WRITE_ALLOWED = NO",
        "EVIDENCE_APPROVAL_ALLOWED = NO",
        "GATE_CLOSURE_ALLOWED = NO",
    ]

    if readiness and readiness.get("release_status") != "READY":
        blockers.append("Release readiness is not READY")
    if lock_verification and lock_verification.get("status") == "BLOCK":
        blockers.append("Master status lock verifier returned BLOCK")
    if handoff and handoff.get("execute_90_now") == "NO":
        blockers.append("Handoff precheck says execute_90_now = NO")

    state = {
        "timestamp": now_iso(),
        "component": "PIPELINE_STATE_MANAGER",
        "version": "1.0",
        "state": "LOCKED_AUDIT_ONLY",
        "status": "SYSTEM_RED_LOCKED",
        "blockers": blockers,
        "inputs": {
            "readiness_present": readiness is not None,
            "lock_verification_present": lock_verification is not None,
            "handoff_precheck_present": handoff is not None,
        },
        "allowed_next_actions": [
            "Continue remediation",
            "Continue manual review",
            "Regenerate reports",
            "Archive denial state"
        ],
        "forbidden_actions": [
            "approve evidence",
            "close gates",
            "write canonical SSoT",
            "unlock STEP102",
            "allow final use",
            "production release"
        ],
        "decision": "Pipeline state is locked. This manager records state only and grants no approval.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        emit_jsonl(args.out_jsonl, state)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(state, ensure_ascii=False, indent=2) if args.json else "🔒 Pipeline state recorded as locked")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    sys.exit(main())
