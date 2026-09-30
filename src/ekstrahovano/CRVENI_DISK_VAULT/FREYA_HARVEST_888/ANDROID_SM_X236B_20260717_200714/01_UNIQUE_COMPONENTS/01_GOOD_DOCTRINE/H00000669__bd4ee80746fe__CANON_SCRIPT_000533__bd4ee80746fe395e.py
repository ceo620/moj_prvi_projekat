# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 143_archive_of_archives_index.py
# PURPOSE: Index all terminal archive ZIPs into archive-of-archives inventory
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(path):
    n = path.name.lower()
    if "handoff_lock" in n:
        return "HANDOFF_LOCK_ARCHIVE"
    if "handoff_denial" in n:
        return "HANDOFF_DENIAL_ARCHIVE"
    if "nonacceptance" in n:
        return "NONACCEPTANCE_ARCHIVE"
    if "readonly" in n or "read_only" in n:
        return "READONLY_PROOF_ARCHIVE"
    if "final_closure" in n or "system_red_final_closure" in n:
        return "FINAL_CLOSURE_ARCHIVE"
    if "certificate" in n:
        return "CERTIFICATE_ARCHIVE"
    if "denial" in n:
        return "DENIAL_ARCHIVE"
    return "LOCKED_ARCHIVE"

def inspect_zip(path):
    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            names = z.namelist()
        return bad is None, bad or "", len(names)
    except Exception as exc:
        return False, str(exc), 0

def collect(roots):
    records = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*.zip")
        for item in iterator:
            if item.is_file() and item.suffix.lower() == ".zip":
                valid, bad, count = inspect_zip(item)
                records.append({
                    "ArchiveOfArchives_ID": f"AOA-{len(records)+1:05d}",
                    "Archive_Name": item.name,
                    "Archive_Type": classify(item),
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Valid_Zip": valid,
                    "Bad_Member": bad,
                    "Contained_Item_Count": count,
                    "Size_Bytes": item.stat().st_size,
                    "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Operational_Handoff_Allowed": "NO",
                    "Canonical_Effect": "NONE",
                    "Final_Use_Allowed": "NO",
                })
    return records

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Archive of Archives"
    headers = ["ArchiveOfArchives_ID", "Archive_Name", "Archive_Type", "Path", "SHA256", "Valid_Zip", "Bad_Member", "Contained_Item_Count", "Size_Bytes", "Modified_UTC", "Operational_Handoff_Allowed", "Canonical_Effect", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="Build archive-of-archives index")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = collect(args.roots)

    payload = {
        "timestamp": now_iso(),
        "component": "ARCHIVE_OF_ARCHIVES_INDEX",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "invalid_zip_count": sum(1 for r in records if not r["Valid_Zip"]),
        "records": records,
        "decision": "Archive-of-archives index is inventory only. It grants no release, handoff, or final use.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Archive-of-archives index built: {len(records)} ZIPs")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
