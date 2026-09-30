# ============================================================
# TITAN_KERNEL: 90_pipeline_state_manager.py
# PURPOSE: Append-only pipeline state events without canonical SSOT write
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def append_state(path, step, status, exit_code, message):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": now_iso(),
        "component": "PIPELINE_STATE_MANAGER",
        "step": step,
        "status": status,
        "exit_code": exit_code,
        "message": message,
        "system_status": "SYSTEM RED",
        "step102": "LOCKED / NOT ACCEPTED",
        "final_use_allowed": "NO",
        "ssot_write_allowed": "NO",
        "note": "Append-only operational state; not canonical SSOT approval"
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event

def main():
    parser = argparse.ArgumentParser(description="Append TITAN pipeline state event")
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--step", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--message", default="")
    args = parser.parse_args()

    event = append_state(args.state_file, args.step, args.status, args.exit_code, args.message)
    print(json.dumps(event, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
