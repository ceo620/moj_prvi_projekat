# ============================================================
# TITAN_KERNEL: 95_rollback_readiness_verifier.py
# PURPOSE: Verify rollback plan and backup references before any freeze attempt
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
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
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
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as exc:
        return {"__error__": str(exc)}

def count_files(path):
    p = Path(path)
    if not p.exists():
        return 0
    return sum(1 for x in p.rglob("*") if x.is_file())

def main():
    parser = argparse.ArgumentParser(description="Verify rollback readiness without executing rollback")
    parser.add_argument("--rollback-plan", required=True)
    parser.add_argument("--backup-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = load_json(args.rollback_plan)
    backup_count = count_files(args.backup_root)

    blockers = []
    if plan is None:
        blockers.append("rollback_plan missing")
    elif "__error__" in plan:
        blockers.append(f"rollback_plan unreadable: {plan['__error__']}")
    else:
        steps = plan.get("rollback_steps", [])
        if not steps:
            blockers.append("rollback_plan has no rollback_steps")
        for step in steps:
            if step.get("Auto_Execute") == "YES":
                blockers.append(f"{step.get('Step_ID','UNKNOWN')} attempts Auto_Execute=YES")
            if step.get("Final_Use_Allowed") == "YES":
                blockers.append(f"{step.get('Step_ID','UNKNOWN')} attempts Final_Use_Allowed=YES")

    if backup_count == 0:
        blockers.append("backup_root has no files or does not exist")

    payload = {
        "timestamp": now_iso(),
        "component": "ROLLBACK_READINESS_VERIFIER",
        "version": "1.0",
        "status": "BLOCK" if blockers else "REVIEW_REQUIRED",
        "backup_root": args.backup_root,
        "backup_file_count": backup_count,
        "blockers": blockers,
        "rollback_ready_for_manual_review": "YES" if not blockers else "NO",
        "rollback_auto_execute_allowed": "NO",
        "decision": "Rollback readiness is manual-review only. No restore or approval is performed.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Rollback readiness BLOCK" if blockers else "✅ Rollback ready for manual review"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if blockers else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
