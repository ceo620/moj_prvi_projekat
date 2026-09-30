# ============================================================
# TITAN_KERNEL: 99_master_orchestrator.py
# PURPOSE: Master orchestrator in locked dry-run mode only
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

LOCKED_PLAN = [
    ("98_safe_backup_runner.py", "backup safety"),
    ("90_pipeline_state_manager.py", "state record"),
    ("94_emergency_stop_ledger.py", "emergency stop"),
    ("96_prefreeze_denial_precheck.py", "pre-freeze denial"),
    ("97_preproduction_freeze.py", "expected freeze denial"),
    ("55_no_release_memorandum_generator.py", "no-release memorandum"),
    ("82_final_locked_state_certificate.py", "locked certificate"),
    ("100_post_orchestration_denial_receipt.py", "post-orchestration denial receipt"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def exists_under(root, script):
    path = Path(root) / "SCRIPTS" / script
    return str(path), path.exists()

def main():
    parser = argparse.ArgumentParser(description="TITAN locked master orchestrator")
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", default="LOCKED_DRY_RUN_ONLY")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    steps = []
    for idx, (script, purpose) in enumerate(LOCKED_PLAN, start=1):
        path, exists = exists_under(args.root, script)
        steps.append({
            "Order": idx,
            "Script": script,
            "Purpose": purpose,
            "Path": path,
            "Exists": exists,
            "Would_Execute": "NO",
            "Execution_Mode": "LOCKED_DRY_RUN_ONLY",
            "Expected_Result": "DENIED_OR_LOCKED",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "MASTER_ORCHESTRATOR",
        "version": "1.0",
        "status": "ORCHESTRATION_LOCKED",
        "mode": args.mode,
        "child_execution_performed": False,
        "steps": steps,
        "decision": "Master orchestrator is locked. No child script is executed and no final use is allowed.",
        **CANON
    }

    md = [
        "# TITAN Master Orchestrator Locked Plan",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "## Locked Plan",
        "",
        "| Order | Script | Exists | Would Execute | Expected Result |",
        "|---:|---|---:|---|---|",
    ]
    for s in steps:
        md.append(f"| {s['Order']} | `{s['Script']}` | {s['Exists']} | NO | DENIED_OR_LOCKED |")

    md.extend([
        "",
        "## Decision",
        "",
        "No child script executed. No evidence approved. No gate closed. No SSoT write. No STEP102 unlock. No final use.",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```"
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Master orchestrator locked")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    sys.exit(main())
