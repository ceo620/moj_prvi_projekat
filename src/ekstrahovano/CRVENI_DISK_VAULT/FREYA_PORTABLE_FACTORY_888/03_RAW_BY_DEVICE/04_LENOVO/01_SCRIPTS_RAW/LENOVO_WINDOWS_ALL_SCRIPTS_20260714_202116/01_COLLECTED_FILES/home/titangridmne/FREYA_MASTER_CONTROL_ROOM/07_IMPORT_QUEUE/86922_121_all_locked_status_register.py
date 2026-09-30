# ============================================================
# TITAN_KERNEL: 121_all_locked_status_register.py
# PURPOSE: Build final register of all NO/LOCKED/BLOCKED statuses
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
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

STATUS_FILES = [
    "nothing_accepted_memorandum.json",
    "chain_complete_locked_record.json",
    "review_only_proof.json",
    "do_not_run_notice.json",
    "final_warning_seal.json",
    "system_remains_locked_summary.json",
    "post_orchestration_denial_receipt.json",
    "final_locked_state_certificate.json",
    "no_release_memorandum.json",
    "pipeline_state.json",
    "master_orchestrator_locked_plan.json",
    "emergency_stop_ledger.json",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def infer_status(path):
    if path is None or not path.exists():
        return "MISSING"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN")))
    except Exception:
        return "UNREADABLE"

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Locked Statuses"
    headers = ["Status_ID", "Artifact", "Path", "Exists", "Inferred_Status", "Expected_Treatment", "Canonical_Effect", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["records"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build all locked status register")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = []
    for idx, name in enumerate(STATUS_FILES, start=1):
        p = find_file(args.reports_root, name)
        records.append({
            "Status_ID": f"LOCK-{idx:05d}",
            "Artifact": name,
            "Path": str(p) if p else "MISSING",
            "Exists": p is not None,
            "Inferred_Status": infer_status(p),
            "Expected_Treatment": "LOCKED_OR_DENIED_OR_REVIEW_REQUIRED",
            "Canonical_Effect": "NONE",
            "Final_Use_Allowed": "NO",
        })

    payload = {
        "timestamp": now_iso(),
        "component": "ALL_LOCKED_STATUS_REGISTER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "missing_count": sum(1 for r in records if not r["Exists"]),
        "records": records,
        "decision": "Status register confirms locked/denied/no-use posture only. It does not approve final use.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ All locked status register built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
