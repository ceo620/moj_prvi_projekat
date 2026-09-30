# ============================================================
# TITAN_KERNEL: 05_script_manifest_builder.py
# PURPOSE: Build manifest of scripts with hashes, versions and categories
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import csv
import hashlib
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
EXIT_SOURCE_ERROR = 1
EXIT_WRITE_ERROR = 2
EXIT_DEPENDENCY_ERROR = 5

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

SCRIPT_EXTS = {".py", ".ps1", ".bat", ".cmd"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def detect_version(text):
    patterns = [
        r"VERSION:\s*([A-Za-z0-9._\-]+)",
        r"version\s*=\s*[\"']([^\"']+)[\"']",
        r"VERSION\s*=\s*[\"']([^\"']+)[\"']",
        r"v(\d+\.\d+(?:\.\d+)?)"
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return "UNKNOWN"

def classify_script(path):
    name = path.name.lower()
    if name.startswith("00") or "guardian" in name or "validator" in name or "checker" in name:
        return "CONTROL"
    if name.startswith("util_") or "utility" in str(path).lower():
        return "UTILITY"
    if name.startswith("dev_"):
        return "ADMIN"
    if name.startswith("ui_"):
        return "UI"
    if "orchestrator" in name:
        return "ORCHESTRATION"
    if "manifest" in name or "integrity" in name or "ssot" in name:
        return "INTEGRITY"
    if "evidence" in name or "filefinding" in name:
        return "EVIDENCE"
    return "SCRIPT"

def run_order_from_name(path):
    m = re.match(r"^(\d+[A-Z]?)", path.name, re.IGNORECASE)
    return m.group(1) if m else "UNKNOWN"

def read_sample(path):
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")[:12000]
    except Exception:
        return ""

def build_manifest(root, recursive):
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(str(root))

    iterator = root.rglob("*") if recursive else root.glob("*")
    rows = []

    for path in iterator:
        if not path.is_file() or path.suffix.lower() not in SCRIPT_EXTS:
            continue

        sample = read_sample(path)
        stat = path.stat()

        rows.append({
            "Script_ID": f"SCR-{len(rows)+1:04d}",
            "Script_Name": path.name,
            "Path": str(path),
            "SHA256": sha256_file(path),
            "Version": detect_version(sample),
            "Category": classify_script(path),
            "Run_Order": run_order_from_name(path),
            "Size_Bytes": stat.st_size,
            "Modified_UTC": datetime.utcfromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "Status": "REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO",
            "SSOT_Write_Allowed": "NO",
        })

    return rows

def write_json(rows, out_json):
    payload = {
        "metadata": {
            "created_at": now_iso(),
            "component": "SCRIPT_MANIFEST_BUILDER",
            "version": "1.0",
            "record_count": len(rows),
            "canonical_status": CANON,
            "note": "Manifest is audit artifact only. It is not evidence approval and not production approval."
        },
        "scripts": rows
    }
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def write_csv(rows, out_csv):
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        headers = ["Script_ID", "Script_Name", "Path", "SHA256", "Version", "Category", "Run_Order", "Size_Bytes", "Modified_UTC", "Status", "Final_Use_Allowed", "SSOT_Write_Allowed"]
    else:
        headers = list(rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def write_xlsx(rows, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Script Manifest"
    headers = list(rows[0].keys()) if rows else ["Script_ID", "Script_Name", "Path", "SHA256", "Version", "Category", "Run_Order", "Size_Bytes", "Modified_UTC", "Status", "Final_Use_Allowed", "SSOT_Write_Allowed"]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN script manifest builder")
    parser.add_argument("--scripts-root", required=True)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-csv")
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        rows = build_manifest(args.scripts_root, args.recursive)
    except Exception as exc:
        status = {
            "timestamp": now_iso(),
            "component": "SCRIPT_MANIFEST_BUILDER",
            "status": "BLOCK",
            "message": f"Could not build manifest: {exc}",
            **CANON,
        }
        print(json.dumps(status, ensure_ascii=False) if args.json else status["message"])
        return EXIT_SOURCE_ERROR

    try:
        write_json(rows, args.out_json)
        if args.out_csv:
            write_csv(rows, args.out_csv)
        if args.out_xlsx:
            write_xlsx(rows, args.out_xlsx)
    except Exception as exc:
        status = {
            "timestamp": now_iso(),
            "component": "SCRIPT_MANIFEST_BUILDER",
            "status": "BLOCK",
            "message": f"Could not write manifest outputs: {exc}",
            **CANON,
        }
        print(json.dumps(status, ensure_ascii=False) if args.json else status["message"])
        return EXIT_WRITE_ERROR

    status = {
        "timestamp": now_iso(),
        "component": "SCRIPT_MANIFEST_BUILDER",
        "status": "PASS",
        "message": "Script manifest built",
        "record_count": len(rows),
        "out_json": args.out_json,
        "out_csv": args.out_csv or "N/A",
        "out_xlsx": args.out_xlsx or "N/A",
        **CANON,
    }

    print(json.dumps(status, ensure_ascii=False) if args.json else f"✅ Script manifest built: {len(rows)} scripts")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
