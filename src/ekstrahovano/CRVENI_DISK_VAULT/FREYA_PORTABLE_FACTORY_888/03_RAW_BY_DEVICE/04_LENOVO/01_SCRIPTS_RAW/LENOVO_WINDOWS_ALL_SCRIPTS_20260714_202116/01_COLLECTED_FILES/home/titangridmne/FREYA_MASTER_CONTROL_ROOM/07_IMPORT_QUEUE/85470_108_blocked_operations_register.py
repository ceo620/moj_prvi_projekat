# ============================================================
# TITAN_KERNEL: 108_blocked_operations_register.py
# PURPOSE: Build register of operations that remain blocked under active canon
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

BLOCKED_OPS = [
    ("BOP-001", "Production execution", "Run 99 as production", "SYSTEM RED hard lock", "CRITICAL"),
    ("BOP-002", "Final use activation", "Set FINAL_USE_ALLOWED=YES", "FINAL_USE_ALLOWED=NO", "CRITICAL"),
    ("BOP-003", "Evidence approval", "Approve evidence automatically", "EVIDENCE_APPROVAL_ALLOWED=NO", "CRITICAL"),
    ("BOP-004", "Gate closure", "Close P0 gates automatically", "GATE_CLOSURE_ALLOWED=NO", "CRITICAL"),
    ("BOP-005", "Canonical SSoT write", "Write to canonical SSoT", "SSOT_WRITE_ALLOWED=NO", "CRITICAL"),
    ("BOP-006", "STEP102 unlock", "Mark STEP102 accepted/unlocked", "STEP102 LOCKED / NOT ACCEPTED", "CRITICAL"),
    ("BOP-007", "Freeze approval", "Treat preproduction freeze as allowed", "Freeze denied under canon", "HIGH"),
    ("BOP-008", "Exception override", "Use policy exception as approval", "Policy verifier blocks overrides", "HIGH"),
    ("BOP-009", "Reviewer attestation as release", "Treat reviewer note as final approval", "Reviewer templates default to NO", "HIGH"),
    ("BOP-010", "Duplicate deletion", "Delete duplicate artifacts automatically", "Duplicates are review-only", "MEDIUM"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Blocked Operations"
    headers = ["Blocked_Operation_ID", "Operation", "Attempt", "Block_Reason", "Severity", "Status", "Can_Override_Automatically", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="Build TITAN blocked operations register")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    operations = []
    for op_id, operation, attempt, reason, severity in BLOCKED_OPS:
        operations.append({
            "Blocked_Operation_ID": op_id,
            "Operation": operation,
            "Attempt": attempt,
            "Block_Reason": reason,
            "Severity": severity,
            "Status": "BLOCKED",
            "Can_Override_Automatically": "NO",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "BLOCKED_OPERATIONS_REGISTER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "operation_count": len(operations),
        "operations": operations,
        "decision": "Register documents blocked operations only. It does not approve exceptions.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Blocked operations register built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
