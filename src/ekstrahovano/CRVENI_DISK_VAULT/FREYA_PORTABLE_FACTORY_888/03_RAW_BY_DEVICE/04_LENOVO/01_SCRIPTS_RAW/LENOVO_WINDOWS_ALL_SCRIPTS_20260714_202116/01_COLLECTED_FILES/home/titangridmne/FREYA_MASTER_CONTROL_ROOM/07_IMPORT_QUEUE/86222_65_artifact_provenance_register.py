# ============================================================
# TITAN_KERNEL: 65_artifact_provenance_register.py
# PURPOSE: Build provenance register for reports, scripts and evidence artifacts
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

EXTS = {".py", ".ps1", ".json", ".jsonl", ".xlsx", ".csv", ".txt", ".md", ".html", ".zip"}

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
    if "\\scripts\\" in s or "/scripts/" in s:
        return "SCRIPT"
    if "\\reports\\" in s or "/reports/" in s:
        return "REPORT"
    if "evidence" in s:
        return "EVIDENCE"
    if "audit" in s:
        return "AUDIT"
    if path.suffix.lower() == ".zip":
        return "PACKAGE"
    return "ARTIFACT"

def collect(roots):
    rows = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and item.suffix.lower() in EXTS:
                rows.append({
                    "Provenance_ID": f"PROV-{len(rows)+1:05d}",
                    "Artifact_Name": item.name,
                    "Artifact_Type": classify(item),
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Created_or_Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Source_System": "LOCAL_TITAN_KERNEL",
                    "Capture_Method": "READ_ONLY_SCAN",
                    "Reviewer": "",
                    "Review_Status": "REVIEW_REQUIRED",
                    "Canonical_Effect": "NONE",
                    "Final_Use_Allowed": "NO",
                })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Provenance Register"
    headers = ["Provenance_ID", "Artifact_Name", "Artifact_Type", "Path", "SHA256", "Size_Bytes", "Created_or_Modified_UTC", "Source_System", "Capture_Method", "Reviewer", "Review_Status", "Canonical_Effect", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="TITAN artifact provenance register")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = collect(args.roots)
    payload = {
        "timestamp": now_iso(),
        "component": "ARTIFACT_PROVENANCE_REGISTER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "records": records,
        "decision": "Provenance register records local artifact state only. It is not evidence approval.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Provenance register built: {len(records)} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
