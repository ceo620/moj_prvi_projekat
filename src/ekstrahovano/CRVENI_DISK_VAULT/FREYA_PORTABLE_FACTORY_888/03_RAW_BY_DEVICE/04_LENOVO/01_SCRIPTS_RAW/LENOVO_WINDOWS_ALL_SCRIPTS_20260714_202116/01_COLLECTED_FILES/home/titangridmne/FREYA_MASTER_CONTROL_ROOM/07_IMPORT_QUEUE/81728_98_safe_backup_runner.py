# ============================================================
# TITAN_KERNEL: 98_safe_backup_runner.py
# PURPOSE: Create safe backup manifest/copy before any orchestration attempt
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

DEFAULT_EXTS = {".py", ".ps1", ".json", ".jsonl", ".xlsx", ".txt", ".md", ".puml"}

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def should_include(path):
    return path.is_file() and path.suffix.lower() in DEFAULT_EXTS

def main():
    parser = argparse.ArgumentParser(description="TITAN safe backup runner")
    parser.add_argument("--root", required=True)
    parser.add_argument("--backup-root", required=True)
    parser.add_argument("--copy-files", action="store_true")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    backup_id = f"TITAN_SAFE_BACKUP_{stamp()}"
    backup_dir = Path(args.backup_root) / backup_id
    files_dir = backup_dir / "files"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if args.copy_files:
        files_dir.mkdir(parents=True, exist_ok=True)

    records = []
    missing_root = not root.exists()

    if root.exists():
        for item in root.rglob("*"):
            if not should_include(item):
                continue
            rel = item.relative_to(root)
            rec = {
                "relative_path": str(rel),
                "source_path": str(item),
                "sha256": sha256_file(item),
                "size_bytes": item.stat().st_size,
                "copied_to": "N/A",
                "final_use_allowed": "NO"
            }
            if args.copy_files:
                dest = files_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                rec["copied_to"] = str(dest)
            records.append(rec)

    manifest = {
        "timestamp": now_iso(),
        "component": "SAFE_BACKUP_RUNNER",
        "version": "1.0",
        "status": "BLOCK" if missing_root else "REVIEW_REQUIRED",
        "backup_id": backup_id,
        "root": str(root),
        "backup_dir": str(backup_dir),
        "copy_files": args.copy_files,
        "record_count": len(records),
        "records": records,
        "decision": "Backup is safety artifact only. It does not approve orchestration or final use.",
        **CANON
    }

    try:
        manifest_path = backup_dir / "safe_backup_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else f"✅ Safe backup manifest: {backup_dir}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
