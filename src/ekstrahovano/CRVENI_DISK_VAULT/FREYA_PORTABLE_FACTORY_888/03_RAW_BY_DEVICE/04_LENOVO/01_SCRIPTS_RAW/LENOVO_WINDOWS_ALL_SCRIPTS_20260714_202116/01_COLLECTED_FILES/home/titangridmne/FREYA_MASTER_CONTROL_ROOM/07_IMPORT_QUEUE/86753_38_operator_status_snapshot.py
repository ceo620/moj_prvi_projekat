# ============================================================
# TITAN_KERNEL: 38_operator_status_snapshot.py
# PURPOSE: Generate single current operator status snapshot from key reports
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

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

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

def read_json(path):
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as exc:
        return {"status": "UNREADABLE", "error": str(exc), "path": path}

def read_jsonl_status_counts(path):
    counts = Counter()
    if not path or not os.path.exists(path):
        return {"exists": False, "counts": {}, "events": 0}
    events = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events += 1
            try:
                obj = json.loads(line)
                counts[obj.get("status", "UNKNOWN")] += 1
            except json.JSONDecodeError:
                counts["INVALID_JSON"] += 1
    return {"exists": True, "counts": dict(counts), "events": events}

def main():
    parser = argparse.ArgumentParser(description="TITAN operator status snapshot")
    parser.add_argument("--release-readiness")
    parser.add_argument("--freeze-report")
    parser.add_argument("--self-test")
    parser.add_argument("--dry-run")
    parser.add_argument("--control-report-jsonl")
    parser.add_argument("--audit-timeline-jsonl")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-txt", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    snapshot = {
        "timestamp": now_iso(),
        "component": "OPERATOR_STATUS_SNAPSHOT",
        "version": "1.0",
        "status": "SYSTEM_RED_LOCKED",
        "summary": "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "release_readiness": read_json(args.release_readiness),
        "freeze_report": read_json(args.freeze_report),
        "self_test": read_json(args.self_test),
        "dry_run": read_json(args.dry_run),
        "control_report_counts": read_jsonl_status_counts(args.control_report_jsonl),
        "audit_timeline_counts": read_jsonl_status_counts(args.audit_timeline_jsonl),
        "operator_decision": "Continue evidence review and remediation. Do not release.",
        **CANON
    }

    lines = [
        "TITAN OPERATOR STATUS SNAPSHOT",
        f"Generated_At: {snapshot['timestamp']}",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "Canonical Locks:"
    ]

    for k, v in CANON.items():
        lines.append(f"- {k}: {v}")

    lines.extend([
        "",
        "Key Signals:",
        f"- Release Readiness: {snapshot['release_readiness'].get('release_status', snapshot['release_readiness'].get('status','MISSING')) if snapshot['release_readiness'] else 'MISSING'}",
        f"- Freeze Status: {snapshot['freeze_report'].get('freeze_status', snapshot['freeze_report'].get('status','MISSING')) if snapshot['freeze_report'] else 'MISSING'}",
        f"- Control Report Counts: {snapshot['control_report_counts']}",
        f"- Audit Timeline Counts: {snapshot['audit_timeline_counts']}",
        "",
        "Decision: Continue evidence review and remediation. Do not release."
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_txt).write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(snapshot, ensure_ascii=False, indent=2) if args.json else f"✅ Operator snapshot: {args.out_txt}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
