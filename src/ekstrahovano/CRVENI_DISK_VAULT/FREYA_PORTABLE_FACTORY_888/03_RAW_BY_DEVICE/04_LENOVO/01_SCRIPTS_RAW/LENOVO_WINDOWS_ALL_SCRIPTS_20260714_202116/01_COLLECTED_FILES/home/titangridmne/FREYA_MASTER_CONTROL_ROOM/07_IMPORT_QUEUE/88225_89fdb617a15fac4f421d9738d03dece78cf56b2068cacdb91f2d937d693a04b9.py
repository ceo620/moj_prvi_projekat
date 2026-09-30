# ============================================================
# TITAN_KERNEL: 00B_config_schema_validator.py
# PURPOSE: Validate config.json schema before Guardian
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime

EXIT_OK = 0
EXIT_CONFIG_MISSING = 1
EXIT_CONFIG_UNREADABLE = 2
EXIT_SCHEMA_INVALID = 3
EXIT_RUNTIME_ERROR = 4

REQUIRED_TOP_LEVEL = ["project_name", "version", "target_signals", "paths"]
REQUIRED_PATHS = ["monolith", "logs", "vdr_root"]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def event(status, message, extra=None):
    data = {
        "timestamp": now_iso(),
        "component": "CONFIG_SCHEMA_VALIDATOR",
        "status": status,
        "message": message,
        "final_use_allowed": "NO",
        "ssot_write_allowed": "NO",
    }
    if extra:
        data.update(extra)
    return data

def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def validate(config):
    errors = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in config:
            errors.append(f"Missing top-level key: {key}")

    if "paths" in config and not isinstance(config["paths"], dict):
        errors.append("paths must be an object")

    if isinstance(config.get("paths"), dict):
        for key in REQUIRED_PATHS:
            if key not in config["paths"]:
                errors.append(f"Missing paths key: {key}")

    if "target_signals" in config and not isinstance(config["target_signals"], int):
        errors.append("target_signals must be integer")

    return errors

def main():
    parser = argparse.ArgumentParser(description="TITAN config schema validator")
    parser.add_argument("--config", required=True, help="Path to config.json")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        output = event("BLOCK", "config.json missing", {"config": args.config})
        print(json.dumps(output, ensure_ascii=False) if args.json else output["message"])
        return EXIT_CONFIG_MISSING

    try:
        config = load_json(args.config)
    except Exception as exc:
        output = event("BLOCK", f"config.json unreadable: {exc}", {"config": args.config})
        print(json.dumps(output, ensure_ascii=False) if args.json else output["message"])
        return EXIT_CONFIG_UNREADABLE

    errors = validate(config)

    if errors:
        output = event("BLOCK", "config schema invalid", {"errors": errors})
        print(json.dumps(output, ensure_ascii=False) if args.json else "\n".join(errors))
        return EXIT_SCHEMA_INVALID

    output = event("PASS", "config schema valid", {"config": args.config})
    print(json.dumps(output, ensure_ascii=False) if args.json else "✅ config schema valid")
    return EXIT_OK

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps(event("ERROR", str(exc)), ensure_ascii=False))
        sys.exit(EXIT_RUNTIME_ERROR)
