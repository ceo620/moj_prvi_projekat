# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 74_audit_replay_plan_builder.py
# PURPOSE: Build replay plan for audit steps without executing them
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

REPLAY_STEPS = [
    ("RP-001", "Runtime check", "00C_runtime_env_checker.py"),
    ("RP-002", "Config schema validation", "00B_config_schema_validator.py"),
    ("RP-003", "SSoT read-only export", "03_ssot_readonly_exporter.py"),
    ("RP-004", "SSoT integrity check", "04_ssot_integrity_checker.py"),
    ("RP-005", "Script manifest build", "05_script_manifest_builder.py"),
    ("RP-006", "Script integrity check", "06_script_integrity_checker.py"),
    ("RP-007", "Evidence link validation", "17_evidence_link_validator.py"),
    ("RP-008", "Evidence weight calculation", "18_filefinding_evidence_weight_calculator.py"),
    ("RP-009", "Control Tower validation", "45_control_tower_validator.py"),
    ("RP-010", "Release readiness check", "48_release_readiness_checker.py"),
    ("RP-011", "No-release memorandum", "55_no_release_memorandum_generator.py"),
    ("RP-012", "Approval boundary simulation", "71_approval_boundary_simulator.py"),
    ("RP-013", "Red-team negative tests", "72_red_team_negative_tests.py"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def main():
    parser = argparse.ArgumentParser(description="Build audit replay plan without execution")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    scripts_root = root / "SCRIPTS"

    steps = []
    for order, (step_id, purpose, script) in enumerate(REPLAY_STEPS, start=1):
        path = scripts_root / script
        steps.append({
            "Order": order,
            "Replay_ID": step_id,
            "Purpose": purpose,
            "Script": script,
            "Script_Path": str(path),
            "Exists": path.exists(),
            "Execute_Automatically": "NO",
            "Expected_Result": "BLOCK_OR_REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "AUDIT_REPLAY_PLAN_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "step_count": len(steps),
        "steps": steps,
        "decision": "Replay plan is documentation only. It does not execute audit steps.",
        **CANON
    }

    md = [
        "# TITAN Audit Replay Plan",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "| Order | Replay ID | Purpose | Script | Exists | Execute Automatically |",
        "|---:|---|---|---|---|---|"
    ]
    for s in steps:
        md.append(f"| {s['Order']} | {s['Replay_ID']} | {s['Purpose']} | `{s['Script']}` | {s['Exists']} | NO |")
    md.append("")
    md.append("This plan does not execute scripts and does not approve final use.")

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Audit replay plan: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
