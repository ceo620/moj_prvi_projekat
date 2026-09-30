# ============================================================
# TITAN_KERNEL: 98_safe_backup_runner.py
# PURPOSE: Create timestamped backup before mutation
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

def now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def copy_item(src, dst):
    src = Path(src)
    dst = Path(dst)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

def main():
    parser = argparse.ArgumentParser(description="TITAN safe backup runner")
    parser.add_argument("--source", required=True)
    parser.add_argument("--backup-root", default=r"C:\Users\Korisnik\Desktop\TITAN_BACKUPS")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"❌ Source ne postoji: {source}")
        return 1

    dest = Path(args.backup_root) / f"{source.name}_backup_{now_stamp()}"
    copy_item(source, dest)

    manifest = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "component": "SAFE_BACKUP_RUNNER",
        "source": str(source),
        "backup": str(dest),
        "system_status": "SYSTEM RED",
        "step102": "LOCKED / NOT ACCEPTED",
        "final_use_allowed": "NO"
    }

    if source.is_file():
        manifest["source_sha256"] = sha256_file(source)
        manifest["backup_sha256"] = sha256_file(dest)

    manifest_path = dest if dest.is_dir() else dest.parent
    manifest_file = manifest_path / "backup_manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
