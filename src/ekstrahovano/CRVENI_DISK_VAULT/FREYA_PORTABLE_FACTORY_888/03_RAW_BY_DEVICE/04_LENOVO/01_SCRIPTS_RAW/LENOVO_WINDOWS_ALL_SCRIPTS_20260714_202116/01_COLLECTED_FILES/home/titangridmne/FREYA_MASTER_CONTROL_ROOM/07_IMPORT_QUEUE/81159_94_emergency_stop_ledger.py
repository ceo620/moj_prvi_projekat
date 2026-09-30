# ============================================================
# TITAN_KERNEL: 94_emergency_stop_ledger.py
# PURPOSE: Record emergency stop state as append-only audit ledger
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_STOP_ACTIVE = 1
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

def emit_jsonl(path, event):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="TITAN emergency stop ledger")
    parser.add_argument("--reason", default="SYSTEM RED active; final use denied")
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    event = {
        "timestamp": now_iso(),
        "component": "EMERGENCY_STOP_LEDGER",
        "version": "1.0",
        "status": "EMERGENCY_STOP_ACTIVE",
        "stop_active": True,
        "operator": args.operator,
        "reason": args.reason,
        "forbidden_actions": [
            "production execution",
            "final use",
            "evidence approval",
            "gate closure",
            "canonical SSoT write",
            "STEP102 unlock"
        ],
        "decision": "Emergency stop remains active under current canon.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
        emit_jsonl(args.out_jsonl, event)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(event, ensure_ascii=False, indent=2) if args.json else "⛔ Emergency stop active")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_STOP_ACTIVE

if __name__ == "__main__":
    sys.exit(main())
