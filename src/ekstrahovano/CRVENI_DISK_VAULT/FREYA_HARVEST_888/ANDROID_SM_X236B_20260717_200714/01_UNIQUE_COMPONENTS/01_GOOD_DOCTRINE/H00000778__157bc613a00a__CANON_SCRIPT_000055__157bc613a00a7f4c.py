# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 60_script_number_map_builder.py
# PURPOSE: Build numeric map of TITAN scripts 00-99
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import re
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def detect_number(name):
    m = re.match(r"^(\d{2}[A-Z]?)_", name, re.IGNORECASE)
    return m.group(1) if m else "UNNUMBERED"

def classify(name):
    n = name.lower()
    if n.startswith("00") or "guardian" in n or "validator" in n or "checker" in n:
        return "CONTROL"
    if n.startswith("1") or "evidence" in n or "filefinding" in n or "gap" in n:
        return "EVIDENCE"
    if n.startswith("2") or "review" in n or "audit" in n or "custody" in n:
        return "REVIEW_GOVERNANCE"
    if n.startswith("3") or "operator" in n or "runbook" in n or "dry" in n:
        return "OPERATOR"
    if n.startswith("4") or "readiness" in n or "dashboard" in n or "matrix" in n:
        return "GATE_RELEASE"
    if n.startswith("5") or "memorandum" in n or "catalog" in n or "ledger" in n:
        return "CLOSEOUT"
    if n.startswith("9"):
        return "ORCHESTRATION"
    return "UTILITY"

def main():
    parser = argparse.ArgumentParser(description="TITAN script number map builder")
    parser.add_argument("--scripts-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.scripts_root)
    rows = []
    for p in sorted(root.rglob("*.py")) if root.exists() else []:
        rows.append({
            "Script_Number": detect_number(p.name),
            "Script_Name": p.name,
            "Path": str(p),
            "Category": classify(p.name),
            "Present": "YES",
            "Run_Automatically": "NO",
            "Review_Status": "REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO"
        })

    rows.sort(key=lambda x: (x["Script_Number"], x["Script_Name"]))

    payload = {
        "timestamp": now_iso(),
        "component": "SCRIPT_NUMBER_MAP_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "script_count": len(rows),
        "scripts": rows,
        "decision": "Number map is navigation only. It does not authorize execution.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        if args.out_xlsx:
            if openpyxl is None:
                raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Script Number Map"
            headers = ["Script_Number", "Script_Name", "Path", "Category", "Present", "Run_Automatically", "Review_Status", "Final_Use_Allowed"]
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h, "") for h in headers])
            ws2 = wb.create_sheet("Canonical Locks")
            ws2.append(["Control", "Value"])
            for k, v in CANON.items():
                ws2.append([k, v])
            Path(args.out_xlsx).parent.mkdir(parents=True, exist_ok=True)
            wb.save(args.out_xlsx)

    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Script map built: {len(rows)} scripts")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
