# ============================================================
# TITAN_KERNEL: 99_master_orchestrator.py
# PURPOSE: Safe chronological runner for TITAN validation chain
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def run_step(name, cmd, state_file, stop_on_fail=True):
    print(f"\n▶ {name}")
    print(" ".join(cmd))
    started = now_iso()

    result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    event = {
        "timestamp": now_iso(),
        "component": "MASTER_ORCHESTRATOR",
        "step": name,
        "command": cmd,
        "exit_code": result.returncode,
        "started_at": started,
        "ended_at": now_iso(),
        "status": "PASS" if result.returncode == 0 else "BLOCK",
        "system_status": "SYSTEM RED",
        "step102": "LOCKED / NOT ACCEPTED",
        "final_use_allowed": "NO",
        "ssot_write_allowed": "NO"
    }

    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    if stop_on_fail and result.returncode != 0:
        print("⛔ Pipeline stopped by safe blocker.")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="TITAN safe master orchestrator")
    parser.add_argument("--root", default=r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL")
    parser.add_argument("--excel", required=True)
    parser.add_argument("--scan-root", default=r"C:\DANIJELA")
    args = parser.parse_args()

    root = Path(args.root)
    scripts = root / "SCRIPTS"
    config = root / "CORE" / "config.json"
    state_file = root / "REPORTS" / "pipeline_state.jsonl"
    report_file = root / "REPORTS" / "control_tower_validation_report.jsonl"

    py = sys.executable

    steps = [
        ("00C_runtime_env_checker", [py, str(scripts / "00C_runtime_env_checker.py"), "--root", str(root), "--json"], True),
        ("00B_config_schema_validator", [py, str(scripts / "00B_config_schema_validator.py"), "--config", str(config), "--json"], True),
        ("00_guardian_v2", [py, str(scripts / "00_guardian_v2.py")], True),
        ("15_filefinding_register_builder", [py, str(scripts / "15_filefinding_register_builder.py"), "--excel", args.excel, "--scan-root", args.scan_root, "--recursive"], False),
        ("16_evidence_gap_loader", [py, str(scripts / "16_evidence_gap_loader.py"), "--excel", args.excel], False),
        ("45_control_tower_validator", [py, str(scripts / "45_control_tower_validator.py"), "--excel", args.excel, "--report", str(report_file), "--clear-report"], False),
        ("46_validation_report_reader", [py, str(scripts / "46_validation_report_reader.py"), "--report", str(report_file), "--out", str(root / "REPORTS" / "validation_summary.txt")], False),
    ]

    print("=====================================================")
    print("🧭 TITAN MASTER ORCHESTRATOR v1.0")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    print("=====================================================")

    for name, cmd, stop in steps:
        ok = run_step(name, cmd, state_file, stop_on_fail=stop)
        if not ok:
            return 1

    print("\n✅ Safe validation chain completed.")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
