# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 155_review_only_super_index.py
# PURPOSE: Build super-index of review-only closure archives and terminal records
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import zipfile
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

EXTS = {".zip", ".json", ".xlsx", ".md", ".txt"}
KEYWORDS = [
    "review_only",
    "closure",
    "terminal",
    "frozen",
    "locked",
    "no_further_action",
    "do_not_run",
    "nothing_accepted",
    "handoff",
    "nonacceptance",
    "final_master",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inspect_zip(path):
    if path.suffix.lower() != ".zip":
        return "N/A", "", 0
    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            names = z.namelist()
        return bad is None, bad or "", len(names)
    except Exception as exc:
        return False, str(exc), 0

def include(path):
    n = path.name.lower()
    return path.suffix.lower() in EXTS and any(k in n for k in KEYWORDS)

def classify(path):
    n = path.name.lower()
    if "review_only_closure" in n:
        return "REVIEW_ONLY_CLOSURE"
    if "terminal" in n:
        return "TERMINAL_LOCKED_RECORD"
    if "handoff" in n:
        return "HANDOFF_LOCK_RECORD"
    if "nonacceptance" in n or "nothing_accepted" in n:
        return "NONACCEPTANCE_RECORD"
    if "do_not_run" in n:
        return "DO_NOT_RUN_RECORD"
    if "final_master" in n:
        return "MASTER_SEAL_RECORD"
    return "REVIEW_ONLY_LOCKED_ARTIFACT"

def collect(roots):
    rows = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and include(item):
                valid_zip, bad_member, item_count = inspect_zip(item)
                rows.append({
                    "Super_Index_ID": f"RSUP-{len(rows)+1:05d}",
                    "Artifact_Name": item.name,
                    "Artifact_Type": classify(item),
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Valid_Zip": valid_zip,
                    "Bad_Member": bad_member,
                    "Contained_Item_Count": item_count,
                    "Review_Only": "YES",
                    "Operational_Action_Allowed": "NO",
                    "Canonical_Effect": "NONE",
                    "Final_Use_Allowed": "NO",
                })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ReviewOnly SuperIndex"
    headers = [
        "Super_Index_ID", "Artifact_Name", "Artifact_Type", "Path", "SHA256",
        "Size_Bytes", "Modified_UTC", "Valid_Zip", "Bad_Member", "Contained_Item_Count",
        "Review_Only", "Operational_Action_Allowed", "Canonical_Effect", "Final_Use_Allowed"
    ]
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
    parser = argparse.ArgumentParser(description="Build review-only super index")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = collect(args.roots)
    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_SUPER_INDEX",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "records": records,
        "decision": "Review-only super-index is inventory only. It grants no operational action or final use.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Review-only super-index built: {len(records)} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
