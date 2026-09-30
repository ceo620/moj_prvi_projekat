# ============================================================
# TITAN_KERNEL: 46_validation_report_reader.py
# PURPOSE: Read control_tower_validation_report.jsonl and produce summary
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def main():
    parser = argparse.ArgumentParser(description="Read TITAN validation JSONL report")
    parser.add_argument("--report", required=True)
    parser.add_argument("--out", help="Optional TXT summary output")
    args = parser.parse_args()

    if not os.path.exists(args.report):
        print(f"❌ Report ne postoji: {args.report}")
        return 1

    events = []
    with open(args.report, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                events.append({"status": "INVALID_JSON", "message": line})

    counts = Counter(e.get("status", "UNKNOWN") for e in events)
    summary_lines = [
        "TITAN VALIDATION REPORT SUMMARY",
        f"Generated_At: {now_iso()}",
        f"Report: {args.report}",
        f"Events_Total: {len(events)}",
        f"Status_Counts: {dict(counts)}",
        "Canonical_Status: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "Blocking Events:"
    ]

    for e in events:
        if e.get("status") == "BLOCK":
            summary_lines.append(f"- {e.get('rule_id','UNKNOWN')} | {e.get('rule_name','UNKNOWN')} | {e.get('message','')}")

    text = "\n".join(summary_lines)
    print(text)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")

    return 0

if __name__ == "__main__":
    sys.exit(main())
