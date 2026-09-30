# ============================================================
# TITAN_KERNEL: 48_release_readiness_checker.py
# PURPOSE: Check release readiness under active canon
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_NOT_READY = 1
EXIT_FILE_ERROR = 2

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

def read_jsonl(path):
    events = []
    if not os.path.exists(path):
        return events
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                events.append({"status": "INVALID_JSON"})
    return events

def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="TITAN release readiness checker")
    parser.add_argument("--reports", nargs="*", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    all_events = []
    for report in args.reports:
        all_events.extend(read_jsonl(report))

    block_count = sum(1 for e in all_events if e.get("status") == "BLOCK")
    invalid_count = sum(1 for e in all_events if e.get("status") == "INVALID_JSON")

    blockers = [
        "SYSTEM_STATUS is SYSTEM RED",
        "P0_GATES are 10/10 BLOCKED",
        "EVIDENCE_GAPS_REMAINING > 0",
        "EVIDENCE_APPROVED = 0",
        "GATES_CLOSED = 0",
        "STEP102 is LOCKED / NOT ACCEPTED",
        "FINAL_USE_ALLOWED = NO",
        "SSOT_WRITE_ALLOWED = NO",
        "EVIDENCE_APPROVAL_ALLOWED = NO",
        "GATE_CLOSURE_ALLOWED = NO",
    ]

    if block_count > 0:
        blockers.append(f"Validation reports contain BLOCK events: {block_count}")

    if invalid_count > 0:
        blockers.append(f"Validation reports contain invalid JSON lines: {invalid_count}")

    payload = {
        "timestamp": now_iso(),
        "component": "RELEASE_READINESS_CHECKER",
        "version": "1.0",
        "release_status": "NOT_READY",
        "status": "BLOCK",
        "blockers": blockers,
        "report_events_checked": len(all_events),
        "block_event_count": block_count,
        "invalid_json_count": invalid_count,
        "decision": "Release cannot proceed under active canon.",
        **CANON,
    }

    write_json(args.out_json, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "⛔ RELEASE NOT READY")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_NOT_READY

if __name__ == "__main__":
    sys.exit(main())
