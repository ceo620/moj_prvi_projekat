# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 37_system_index_builder.py
# PURPOSE: Build central operator index of scripts, reports and packages
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

SCRIPT_EXTS = {".py", ".ps1"}
REPORT_EXTS = {".json", ".jsonl", ".xlsx", ".csv", ".txt", ".html", ".md"}
PACKAGE_EXTS = {".zip"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def collect(root, exts, category):
    root = Path(root)
    rows = []
    if not root.exists():
        return rows

    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue

        rows.append({
            "Category": category,
            "Name": p.name,
            "Path": str(p),
            "Extension": p.suffix.lower(),
            "SHA256": sha256_file(p),
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
    ws.title = "System Index"
    headers = ["Category", "Name", "Path", "Extension", "SHA256", "Size_Bytes", "Modified_UTC", "Review_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["records"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Summary")
    ws2.append(["Metric", "Value"])
    ws2.append(["Generated_At", payload["timestamp"]])
    ws2.append(["Total_Records", len(payload["records"])])
    ws2.append(["Scripts", payload["counts"]["scripts"]])
    ws2.append(["Reports", payload["counts"]["reports"]])
    ws2.append(["Packages", payload["counts"]["packages"]])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN system index builder")
    parser.add_argument("--root", required=True)
    parser.add_argument("--packages-root", help="Optional folder containing downloaded ZIP packages")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    scripts = collect(root / "SCRIPTS", SCRIPT_EXTS, "SCRIPT")
    reports = collect(root / "REPORTS", REPORT_EXTS, "REPORT")
    packages = collect(args.packages_root, PACKAGE_EXTS, "PACKAGE") if args.packages_root else []

    payload = {
        "timestamp": now_iso(),
        "component": "SYSTEM_INDEX_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "root": str(root),
        "counts": {
            "scripts": len(scripts),
            "reports": len(reports),
            "packages": len(packages),
            "total": len(scripts) + len(reports) + len(packages)
        },
        "records": scripts + reports + packages,
        "decision": "System index is an operator/audit artifact only.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ System index built: {payload['counts']['total']} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
