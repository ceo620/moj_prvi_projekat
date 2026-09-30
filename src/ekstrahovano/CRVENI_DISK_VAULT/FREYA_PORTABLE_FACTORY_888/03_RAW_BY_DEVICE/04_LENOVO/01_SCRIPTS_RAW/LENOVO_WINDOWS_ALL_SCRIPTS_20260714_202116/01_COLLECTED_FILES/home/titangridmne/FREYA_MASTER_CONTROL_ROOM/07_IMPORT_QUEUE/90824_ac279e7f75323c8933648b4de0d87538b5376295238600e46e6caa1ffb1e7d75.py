# ============================================================
# TITAN_KERNEL: 87_duplicate_artifact_register.py
# PURPOSE: Build duplicate artifact register by SHA-256 across reports/archives
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
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

EXTS = {".json", ".jsonl", ".xlsx", ".csv", ".txt", ".md", ".html", ".zip", ".puml"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def collect_files(roots):
    files = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and item.suffix.lower() in EXTS:
                try:
                    files.append({
                        "Name": item.name,
                        "Path": str(item),
                        "SHA256": sha256_file(item),
                        "Size_Bytes": item.stat().st_size,
                        "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                        "Final_Use_Allowed": "NO"
                    })
                except Exception:
                    pass
    return files

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Duplicate Register"
    headers = ["Duplicate_Group_ID", "SHA256", "Duplicate_Count", "Name", "Path", "Size_Bytes", "Modified_UTC", "Treatment", "Final_Use_Allowed"]
    ws.append(headers)
    for group in payload["duplicate_groups"]:
        for item in group["Items"]:
            ws.append([
                group["Duplicate_Group_ID"],
                group["SHA256"],
                group["Duplicate_Count"],
                item["Name"],
                item["Path"],
                item["Size_Bytes"],
                item["Modified_UTC"],
                "REVIEW_REQUIRED",
                "NO",
            ])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN duplicate artifact register")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = collect_files(args.roots)
    by_hash = defaultdict(list)
    for f in files:
        by_hash[f["SHA256"]].append(f)

    duplicate_groups = []
    for digest, items in by_hash.items():
        if len(items) > 1:
            duplicate_groups.append({
                "Duplicate_Group_ID": f"DUP-{len(duplicate_groups)+1:05d}",
                "SHA256": digest,
                "Duplicate_Count": len(items),
                "Items": items,
                "Treatment": "REVIEW_REQUIRED",
                "Final_Use_Allowed": "NO"
            })

    payload = {
        "timestamp": now_iso(),
        "component": "DUPLICATE_ARTIFACT_REGISTER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "files_scanned": len(files),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
        "decision": "Duplicates are visible for review only. No artifact is deleted or approved.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Duplicate register built: {len(duplicate_groups)} groups")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
