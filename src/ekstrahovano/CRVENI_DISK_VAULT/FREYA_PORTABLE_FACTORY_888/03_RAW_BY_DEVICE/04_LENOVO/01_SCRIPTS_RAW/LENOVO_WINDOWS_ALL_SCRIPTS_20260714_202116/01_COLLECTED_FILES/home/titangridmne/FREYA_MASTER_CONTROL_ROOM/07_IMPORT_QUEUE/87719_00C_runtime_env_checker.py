# ============================================================
# TITAN_KERNEL: 00C_runtime_env_checker.py
# PURPOSE: Check Python runtime, dependencies, folders and permissions
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def check_module(name):
    return importlib.util.find_spec(name) is not None

def can_write(folder):
    try:
        Path(folder).mkdir(parents=True, exist_ok=True)
        probe = Path(folder) / ".titan_write_probe.tmp"
        probe.write_text("probe", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="TITAN runtime environment checker")
    parser.add_argument("--root", default=r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    folders = {
        "CORE": root / "CORE",
        "SCRIPTS": root / "SCRIPTS",
        "UTILITIES": root / "SCRIPTS" / "UTILITIES",
        "LOGS": root / "LOGS",
        "REPORTS": root / "REPORTS",
        "BACKUPS": root / "BACKUPS",
    }

    checks = []
    checks.append({"check": "python_version", "value": sys.version.split()[0], "pass": sys.version_info >= (3, 9)})
    checks.append({"check": "openpyxl_installed", "value": check_module("openpyxl"), "pass": check_module("openpyxl")})

    for name, folder in folders.items():
        checks.append({"check": f"folder_{name}_writable", "value": str(folder), "pass": can_write(folder)})

    blocked = any(not item["pass"] for item in checks)

    result = {
        "timestamp": now_iso(),
        "component": "RUNTIME_ENV_CHECKER",
        "status": "BLOCK" if blocked else "PASS",
        "checks": checks,
        "system_status": "SYSTEM RED",
        "step102": "LOCKED / NOT ACCEPTED",
        "final_use_allowed": "NO",
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("🧪 TITAN RUNTIME ENV CHECK")
        for item in checks:
            mark = "✅" if item["pass"] else "❌"
            print(f"{mark} {item['check']}: {item['value']}")
        print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")

    return EXIT_BLOCK if blocked else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
