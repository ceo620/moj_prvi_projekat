# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 79_decision_ledger_builder.py
# PURPOSE: Build append-style decision ledger from current review state
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
    openpyxl = None

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

DECISIONS = [
    ("DEC-00001", "SYSTEM_STATUS", "KEEP_SYSTEM_RED", "SYSTEM RED remains hard locked"),
    ("DEC-00002", "STEP102", "KEEP_LOCKED", "STEP102 remains LOCKED / NOT ACCEPTED"),
    ("DEC-00003", "FINAL_USE", "DENY_FINAL_USE", "FINAL_USE_ALLOWED remains NO"),
    ("DEC-00004", "EVIDENCE", "NO_EVIDENCE_APPROVAL", "Evidence approval remains blocked"),
    ("DEC-00005", "GATES", "NO_GATE_CLOSURE", "Gate closure remains blocked"),
    ("DEC-00006", "SSOT", "NO_SSOT_WRITE", "Canonical SSoT write remains blocked"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Decision Ledger"
    headers = ["Decision_ID", "Decision_Area", "Decision", "Reason", "Timestamp", "Decision_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["decisions"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build TITAN decision ledger")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    timestamp = now_iso()
    decisions = []
    for decision_id, area, decision, reason in DECISIONS:
        decisions.append({
            "Decision_ID": decision_id,
            "Decision_Area": area,
            "Decision": decision,
            "Reason": reason,
            "Timestamp": timestamp,
            "Decision_Status": "ACTIVE_DENIAL",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": timestamp,
        "component": "DECISION_LEDGER_BUILDER",
        "version": "1.0",
        "status": "ACTIVE_DENIAL",
        "decisions": decisions,
        "decision": "Decision ledger records active denial state only. It does not grant approval.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        Path(args.out_jsonl).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_jsonl, "a", encoding="utf-8") as f:
            for d in decisions:
                event = {"component": "DECISION_LEDGER_BUILDER", **d, **CANON}
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)

    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Decision ledger built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
