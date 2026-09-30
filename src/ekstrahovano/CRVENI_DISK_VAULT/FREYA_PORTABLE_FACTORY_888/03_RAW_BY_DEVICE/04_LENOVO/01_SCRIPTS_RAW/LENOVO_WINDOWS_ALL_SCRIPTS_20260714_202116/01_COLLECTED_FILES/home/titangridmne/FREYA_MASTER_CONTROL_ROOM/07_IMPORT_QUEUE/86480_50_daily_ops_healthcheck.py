# ============================================================
# TITAN_KERNEL: 50_daily_ops_healthcheck.py
# PURPOSE: Daily read-only operational healthcheck
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

REQUIRED_DIRS = ["CORE", "SCRIPTS", "REPORTS", "LOGS"]
REQUIRED_FILES = [
    "CORE/config.json",
    "SCRIPTS/00_guardian_v2.py",
    "SCRIPTS/45_control_tower_validator.py",
    "SCRIPTS/99_master_orchestrator.py"
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def check_path(root, rel):
    p = Path(root) / rel
    return {
        "relative_path": rel,
        "path": str(p),
        "exists": p.exists(),
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "status": "PASS" if p.exists() else "MISSING"
    }

def count_files(folder):
    p = Path(folder)
    if not p.exists():
        return 0
    return sum(1 for x in p.rglob("*") if x.is_file())

def main():
    parser = argparse.ArgumentParser(description="TITAN daily ops healthcheck")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)

    dir_checks = [check_path(root, d) for d in REQUIRED_DIRS]
    file_checks = [check_path(root, f) for f in REQUIRED_FILES]

    missing = [x for x in dir_checks + file_checks if not x["exists"]]

    result = {
        "timestamp": now_iso(),
        "component": "DAILY_OPS_HEALTHCHECK",
        "version": "1.0",
        "status": "BLOCK" if missing else "REVIEW_REQUIRED",
        "root": str(root),
        "dir_checks": dir_checks,
        "file_checks": file_checks,
        "missing_count": len(missing),
        "report_file_count": count_files(root / "REPORTS"),
        "script_file_count": count_files(root / "SCRIPTS"),
        "decision": "Daily healthcheck is read-only and does not approve operation.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Healthcheck BLOCK" if missing else "✅ Healthcheck complete"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if missing else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
