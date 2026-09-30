# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 51_archive_index_builder.py
# PURPOSE: Build archive index of reports, audit packs and evidence bundles
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
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
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

ARCHIVE_EXTS = {".json", ".jsonl", ".xlsx", ".csv", ".txt", ".html", ".md", ".zip"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(path):
    s = str(path).lower()
    if "audit_pack" in s:
        return "AUDIT_PACK"
    if "evidence_bundle" in s:
        return "EVIDENCE_BUNDLE"
    if "incident" in s:
        return "INCIDENT"
    if "report" in s or "reports" in s:
        return "REPORT"
    if path.suffix.lower() == ".zip":
        return "ZIP_PACKAGE"
    return "ARCHIVE_ARTIFACT"

def collect(paths):
    rows = []
    for root in paths:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and item.suffix.lower() in ARCHIVE_EXTS:
                rows.append({
                    "Archive_ID": f"ARC-{len(rows)+1:05d}",
                    "Category": classify(item),
                    "Name": item.name,
                    "Path": str(item),
                    "Extension": item.suffix.lower(),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Retention_Status": "REVIEW_REQUIRED",
                    "Final_Use_Allowed": "NO"
                })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Archive Index"
    headers = ["Archive_ID", "Category", "Name", "Path", "Extension", "SHA256", "Size_Bytes", "Modified_UTC", "Retention_Status", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="TITAN archive index builder")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = collect(args.roots)

    payload = {
        "timestamp": now_iso(),
        "component": "ARCHIVE_INDEX_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(rows),
        "records": rows,
        "decision": "Archive index is evidence of files only; not evidence approval.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Archive index built: {len(rows)} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
