# ============================================================
# TITAN_KERNEL: 52_master_package_catalog_builder.py
# PURPOSE: Build master catalog of TITAN ZIP packages and script ranges
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import re
import sys
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

def package_range(name):
    nums = re.findall(r"(?<!\d)(\d{2})(?!\d)", name)
    if nums:
        return "-".join(nums[:3]) if len(nums) > 1 else nums[0]
    return "UNKNOWN"

def inspect_package(path):
    scripts = []
    installers = []
    readmes = []
    valid = False
    error = ""

    try:
        with zipfile.ZipFile(path, "r") as z:
            valid = z.testzip() is None
            for info in z.infolist():
                base = Path(info.filename).name
                if base.endswith(".py"):
                    scripts.append(base)
                elif base.endswith(".ps1"):
                    installers.append(base)
                elif base.lower().startswith("readme"):
                    readmes.append(base)
    except Exception as exc:
        error = str(exc)

    return valid, scripts, installers, readmes, error

def collect(root, recursive):
    p = Path(root)
    if p.is_file() and p.suffix.lower() == ".zip":
        zips = [p]
    elif p.is_dir():
        zips = list(p.rglob("*.zip") if recursive else p.glob("*.zip"))
    else:
        zips = []

    rows = []
    for z in sorted(zips):
        valid, scripts, installers, readmes, error = inspect_package(z)
        rows.append({
            "Package_ID": f"PKG-{len(rows)+1:05d}",
            "Package_Name": z.name,
            "Path": str(z),
            "SHA256": sha256_file(z),
            "Valid_Zip": valid,
            "Script_Range": package_range(z.name),
            "Python_Scripts": ", ".join(scripts),
            "Installers": ", ".join(installers),
            "Readmes": ", ".join(readmes),
            "Error": error,
            "Review_Status": "REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO"
        })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master Package Catalog"
    headers = ["Package_ID", "Package_Name", "Path", "SHA256", "Valid_Zip", "Script_Range", "Python_Scripts", "Installers", "Readmes", "Error", "Review_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["packages"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN master package catalog builder")
    parser.add_argument("--packages-root", required=True)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = collect(args.packages_root, args.recursive)

    payload = {
        "timestamp": now_iso(),
        "component": "MASTER_PACKAGE_CATALOG_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "package_count": len(rows),
        "packages": rows,
        "decision": "Catalog is inventory only. Package presence is not approval.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Package catalog built: {len(rows)} packages")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
