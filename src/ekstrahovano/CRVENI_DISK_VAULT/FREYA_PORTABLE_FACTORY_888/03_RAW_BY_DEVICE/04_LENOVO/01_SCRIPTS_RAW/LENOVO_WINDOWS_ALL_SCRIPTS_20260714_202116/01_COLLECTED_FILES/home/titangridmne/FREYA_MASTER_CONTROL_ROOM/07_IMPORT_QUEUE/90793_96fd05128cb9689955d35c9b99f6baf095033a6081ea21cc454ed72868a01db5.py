# ============================================================
# TITAN_KERNEL: 91_incident_reporter.py
# PURPOSE: Create incident report when validators produce BLOCK
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

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def read_jsonl(path):
    events = []
    if not os.path.exists(path):
        return events, f"Missing report: {path}"
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                row["_source_file"] = path
                row["_line"] = idx
                events.append(row)
            except json.JSONDecodeError:
                events.append({"status": "INVALID_JSON", "message": line, "_source_file": path, "_line": idx})
    return events, None

def main():
    parser = argparse.ArgumentParser(description="TITAN incident reporter")
    parser.add_argument("--reports", nargs="+", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    events = []
    missing = []

    for report in args.reports:
        rows, error = read_jsonl(report)
        events.extend(rows)
        if error:
            missing.append(error)

    blockers = [e for e in events if e.get("status") == "BLOCK"]
    invalid = [e for e in events if e.get("status") == "INVALID_JSON"]

    incident_id = f"INC-{stamp()}"
    incident = {
        "incident_id": incident_id,
        "timestamp": now_iso(),
        "component": "INCIDENT_REPORTER",
        "version": "1.0",
        "status": "OPEN" if blockers or invalid or missing else "NO_BLOCK_EVENTS_FOUND",
        "severity": "CRITICAL" if blockers else "REVIEW_REQUIRED",
        "summary": "Control Tower blockers detected" if blockers else "No BLOCK events detected, but final use remains NO",
        "block_event_count": len(blockers),
        "invalid_json_count": len(invalid),
        "missing_reports": missing,
        "blockers": blockers,
        "invalid_events": invalid,
        **CANON,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"incident_report_{incident_id}.json"
    txt_path = out_dir / f"incident_report_{incident_id}.txt"

    json_path.write_text(json.dumps(incident, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"TITAN INCIDENT REPORT {incident_id}",
        f"Timestamp: {incident['timestamp']}",
        f"Status: {incident['status']}",
        f"Severity: {incident['severity']}",
        f"Summary: {incident['summary']}",
        f"Block Events: {len(blockers)}",
        f"Invalid JSON Events: {len(invalid)}",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "Blocking Events:"
    ]

    for e in blockers:
        lines.append(f"- {e.get('component', e.get('tool','UNKNOWN'))} | {e.get('rule_id', e.get('check_id','UNKNOWN'))} | {e.get('message','')}")

    txt_path.write_text("\n".join(lines), encoding="utf-8")

    result = {"incident_id": incident_id, "json": str(json_path), "txt": str(txt_path), **CANON}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"✅ Incident report written: {txt_path}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
