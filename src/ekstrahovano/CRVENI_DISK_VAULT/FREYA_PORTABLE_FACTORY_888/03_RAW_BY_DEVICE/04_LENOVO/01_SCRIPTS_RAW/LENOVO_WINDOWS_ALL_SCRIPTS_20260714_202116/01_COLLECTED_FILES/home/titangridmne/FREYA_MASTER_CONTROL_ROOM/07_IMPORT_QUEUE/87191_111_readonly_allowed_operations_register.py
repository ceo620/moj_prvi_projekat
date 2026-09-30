# ============================================================
# TITAN_KERNEL: 111_readonly_allowed_operations_register.py
# PURPOSE: Register operations allowed only in read-only review/audit mode
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
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
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

ALLOWED = [
    ("RO-001", "Read reports", "Open existing JSON/XLSX/MD/TXT reports", "READ_ONLY", "YES"),
    ("RO-002", "Regenerate audit reports", "Run scripts that produce review reports only", "AUDIT_ONLY", "YES"),
    ("RO-003", "Create backups", "Copy files to backup folders", "SAFETY_ONLY", "YES"),
    ("RO-004", "Build denial archives", "Package no-release evidence", "DOCUMENTATION_ONLY", "YES"),
    ("RO-005", "Run negative tests", "Confirm unsafe transitions remain blocked", "SAFETY_TEST_ONLY", "YES"),
    ("RO-006", "Manual review notes", "Record reviewer notes without approval effect", "REVIEW_ONLY", "YES"),
    ("RO-007", "Hash/seal artifacts", "Create hashes/seals of locked reports", "INTEGRITY_ONLY", "YES"),
    ("RO-008", "Reconcile archives", "Compare archives and duplicate hashes", "INVENTORY_ONLY", "YES"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ReadOnly Allowed Ops"
    headers = ["Operation_ID", "Operation", "Description", "Mode", "Allowed_ReadOnly", "Can_Approve", "Can_Close_Gate", "Can_Write_SSoT", "Can_Unlock_STEP102", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["operations"]:
        ws.append([row.get(h, "") for h in headers])
    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])
    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build read-only allowed operations register")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    operations = []
    for op_id, op, desc, mode, allowed in ALLOWED:
        operations.append({
            "Operation_ID": op_id,
            "Operation": op,
            "Description": desc,
            "Mode": mode,
            "Allowed_ReadOnly": allowed,
            "Can_Approve": "NO",
            "Can_Close_Gate": "NO",
            "Can_Write_SSoT": "NO",
            "Can_Unlock_STEP102": "NO",
            "Final_Use_Allowed": "NO",
        })

    payload = {
        "timestamp": now_iso(),
        "component": "READONLY_ALLOWED_OPERATIONS_REGISTER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "operation_count": len(operations),
        "operations": operations,
        "decision": "Only read-only/review operations are allowed. This register grants no production permission.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Read-only allowed operations register built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
