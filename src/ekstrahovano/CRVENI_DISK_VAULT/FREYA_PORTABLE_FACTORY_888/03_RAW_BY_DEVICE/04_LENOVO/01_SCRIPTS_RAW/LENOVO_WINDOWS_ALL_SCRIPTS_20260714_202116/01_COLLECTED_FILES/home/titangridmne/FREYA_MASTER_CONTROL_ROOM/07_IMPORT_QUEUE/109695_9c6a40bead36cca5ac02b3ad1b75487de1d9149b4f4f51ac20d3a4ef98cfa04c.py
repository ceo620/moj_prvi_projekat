# ============================================================
# TITAN_KERNEL: 63_report_cross_reference_builder.py
# PURPOSE: Cross-reference JSON/JSONL/XLSX/TXT reports by filename and status
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from collections import Counter
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

EXTS = {".json", ".jsonl", ".xlsx", ".csv", ".txt", ".md", ".html"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def infer_status_json(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN"))) if isinstance(data, dict) else "JSON_LIST"
    except Exception:
        return "UNREADABLE"

def infer_status_jsonl(path):
    c = Counter()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    c[obj.get("status", "UNKNOWN")] += 1
                except json.JSONDecodeError:
                    c["INVALID_JSON"] += 1
        return json.dumps(dict(c), ensure_ascii=False)
    except Exception:
        return "UNREADABLE"

def infer_status(path):
    if path.suffix.lower() == ".json":
        return infer_status_json(path)
    if path.suffix.lower() == ".jsonl":
        return infer_status_jsonl(path)
    return "REVIEW_REQUIRED"

def collect(root):
    root = Path(root)
    rows = []
    if not root.exists():
        return rows

    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTS:
            rows.append({
                "Report_ID": f"RPT-{len(rows)+1:05d}",
                "Name": p.name,
                "Path": str(p),
                "Extension": p.suffix.lower(),
                "Inferred_Status": infer_status(p),
                "Size_Bytes": p.stat().st_size,
                "Modified_UTC": datetime.utcfromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                "Review_Status": "REVIEW_REQUIRED",
                "Final_Use_Allowed": "NO"
            })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report Cross Reference"
    headers = ["Report_ID", "Name", "Path", "Extension", "Inferred_Status", "Size_Bytes", "Modified_UTC", "Review_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["reports"]:
        ws.append([row.get(h, "") for h in headers])
    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])
    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build TITAN report cross-reference")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    reports = collect(args.reports_root)
    payload = {
        "timestamp": now_iso(),
        "component": "REPORT_CROSS_REFERENCE_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "report_count": len(reports),
        "reports": reports,
        "decision": "Cross-reference is navigation only. It does not validate or approve reports.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Report cross-reference built: {len(reports)} reports")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
