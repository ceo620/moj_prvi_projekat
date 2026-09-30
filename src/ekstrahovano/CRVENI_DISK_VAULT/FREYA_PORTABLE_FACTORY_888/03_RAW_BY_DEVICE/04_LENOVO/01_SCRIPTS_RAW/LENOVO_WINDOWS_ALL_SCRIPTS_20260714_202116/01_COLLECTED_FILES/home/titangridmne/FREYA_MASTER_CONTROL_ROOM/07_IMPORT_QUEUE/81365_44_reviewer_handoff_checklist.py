# ============================================================
# TITAN_KERNEL: 44_reviewer_handoff_checklist.py
# PURPOSE: Build reviewer handoff checklist from known audit artifacts
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("❌ Nedostaje openpyxl. Instaliraj: pip install openpyxl")
    sys.exit(5)

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

DEFAULT_ITEMS = [
    ("HND-001", "Review Control Tower validation report", "control_tower_validation_report.jsonl", "CRITICAL"),
    ("HND-002", "Review Script integrity report", "script_integrity_report.jsonl", "CRITICAL"),
    ("HND-003", "Review Evidence link report", "evidence_link_report.jsonl", "CRITICAL"),
    ("HND-004", "Review Evidence weight report", "evidence_weight_report.jsonl", "HIGH"),
    ("HND-005", "Review Gap closure candidates", "gap_closure_candidates.json", "CRITICAL"),
    ("HND-006", "Review Manual review queue", "manual_review_queue.xlsx", "CRITICAL"),
    ("HND-007", "Review Gate evidence matrix", "gate_evidence_matrix.xlsx", "CRITICAL"),
    ("HND-008", "Review Gap remediation tracker", "gap_remediation_tracker.xlsx", "HIGH"),
    ("HND-009", "Review Release readiness report", "release_readiness.json", "CRITICAL"),
    ("HND-010", "Review Preproduction freeze denial", "preproduction_freeze_denied.json", "CRITICAL"),
    ("HND-011", "Review Audit pack ZIP", "AUDIT_PACKS", "HIGH"),
    ("HND-012", "Review Chain of custody log", "chain_of_custody.jsonl", "HIGH"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def find_artifact(root, name):
    root = Path(root)
    if not root.exists():
        return "MISSING"
    matches = list(root.rglob(name))
    if matches:
        return str(matches[0])
    # for folders like AUDIT_PACKS
    folder = root / name
    if folder.exists():
        return str(folder)
    return "MISSING"

def main():
    parser = argparse.ArgumentParser(description="Build TITAN reviewer handoff checklist")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out-xlsx", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = []
    for item_id, task, artifact_name, priority in DEFAULT_ITEMS:
        path = find_artifact(args.root, artifact_name)
        records.append({
            "Checklist_ID": item_id,
            "Task": task,
            "Expected_Artifact": artifact_name,
            "Artifact_Path": path,
            "Priority": priority,
            "Artifact_Present": "YES" if path != "MISSING" else "NO",
            "Reviewer": "",
            "Review_Status": "PENDING",
            "Can_Approve_Evidence": "NO",
            "Can_Close_Gate": "NO",
            "Final_Use_Allowed": "NO",
        })

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEWER_HANDOFF_CHECKLIST",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "records": records,
        "decision": "Checklist is for human review handoff only.",
        **CANON
    }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reviewer Handoff"
    headers = ["Checklist_ID", "Task", "Expected_Artifact", "Artifact_Path", "Priority", "Artifact_Present", "Reviewer", "Review_Status", "Can_Approve_Evidence", "Can_Close_Gate", "Final_Use_Allowed"]
    ws.append(headers)
    for row in records:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    try:
        Path(args.out_xlsx).parent.mkdir(parents=True, exist_ok=True)
        wb.save(args.out_xlsx)
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Reviewer checklist: {args.out_xlsx}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
