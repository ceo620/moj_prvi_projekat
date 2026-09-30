# ============================================================
# TITAN_KERNEL: 31_package_integrity_checker.py
# PURPOSE: Verify ZIP/package hashes and list package contents
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_FILE_ERROR = 2
EXIT_ZIP_ERROR = 3

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

def inspect_zip(path):
    items = []
    with zipfile.ZipFile(path, "r") as z:
        bad = z.testzip()
        for info in z.infolist():
            items.append({
                "name": info.filename,
                "compressed_size": info.compress_size,
                "file_size": info.file_size,
                "is_dir": info.is_dir()
            })
    return bad, items

def iter_packages(target, recursive):
    p = Path(target)
    if p.is_file() and p.suffix.lower() == ".zip":
        yield p
    elif p.is_dir():
        iterator = p.rglob("*.zip") if recursive else p.glob("*.zip")
        for item in iterator:
            if item.is_file():
                yield item

def main():
    parser = argparse.ArgumentParser(description="TITAN package integrity checker")
    parser.add_argument("--target", required=True, help="ZIP file or folder containing ZIP packages")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        result = {
            "timestamp": now_iso(),
            "component": "PACKAGE_INTEGRITY_CHECKER",
            "status": "BLOCK",
            "message": "Target missing",
            "target": str(target),
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    packages = []
    blocked = False

    for zpath in iter_packages(target, args.recursive):
        record = {
            "package_path": str(zpath),
            "package_name": zpath.name,
            "sha256": "UNKNOWN",
            "valid_zip": False,
            "bad_member": None,
            "item_count": 0,
            "items": [],
            "status": "UNKNOWN"
        }

        try:
            record["sha256"] = sha256_file(zpath)
            bad, items = inspect_zip(zpath)
            record["valid_zip"] = bad is None
            record["bad_member"] = bad
            record["item_count"] = len(items)
            record["items"] = items
            record["status"] = "PASS" if bad is None else "BLOCK"
            if bad is not None:
                blocked = True
        except Exception as exc:
            blocked = True
            record["status"] = "BLOCK"
            record["error"] = str(exc)

        packages.append(record)

    if not packages:
        blocked = True

    result = {
        "timestamp": now_iso(),
        "component": "PACKAGE_INTEGRITY_CHECKER",
        "version": "1.0",
        "status": "BLOCK" if blocked else "REVIEW_REQUIRED",
        "packages_checked": len(packages),
        "packages": packages,
        "decision": "Package integrity checked for audit only. No package is approved for final use.",
        **CANON
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"✅ Packages checked: {len(packages)}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if blocked else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
