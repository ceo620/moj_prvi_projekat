# ============================================================
# TITAN_KERNEL: 104_final_closure_archive_builder.py
# PURPOSE: Build final SYSTEM RED closure archive from post-100 artifacts
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
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

FINAL_FILES = [
    "post_orchestration_denial_receipt.json",
    "post_orchestration_denial_receipt.md",
    "denial_receipt_consistency_check.json",
    "final_run_ledger.json",
    "final_run_ledger.xlsx",
    "system_remains_locked_summary.json",
    "system_remains_locked_summary.md",
    "final_locked_state_certificate.json",
    "final_locked_state_certificate.md",
    "no_release_memorandum.md",
    "decision_ledger.xlsx",
]

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

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def main():
    parser = argparse.ArgumentParser(description="Build final SYSTEM RED closure archive")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--extra-files", nargs="*", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    archive_id = f"SYSTEM_RED_FINAL_CLOSURE_{stamp()}"
    work = Path(args.out_dir) / archive_id
    files_dir = work / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    included = []
    missing = []

    for name in FINAL_FILES + args.extra_files:
        src = Path(name) if Path(name).exists() and Path(name).is_file() else find_file(args.reports_root, name)
        if src is None:
            missing.append(name)
            continue

        dest = files_dir / src.name
        shutil.copy2(src, dest)
        included.append({
            "name": src.name,
            "source": str(src),
            "copied_to": str(dest),
            "sha256": sha256_file(dest),
            "size_bytes": dest.stat().st_size,
            "final_use_allowed": "NO"
        })

    manifest = {
        "archive_id": archive_id,
        "timestamp": now_iso(),
        "component": "FINAL_CLOSURE_ARCHIVE_BUILDER",
        "version": "1.0",
        "status": "SYSTEM_RED_FINAL_CLOSURE_BUILT",
        "included_count": len(included),
        "missing_count": len(missing),
        "included": included,
        "missing": missing,
        "decision": "Final closure archive documents locked/no-release state only. It is not approval.",
        **CANON
    }

    manifest_path = work / "final_closure_archive_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = work / "README_SYSTEM_RED_FINAL_CLOSURE.txt"
    readme.write_text(
        "TITAN SYSTEM RED FINAL CLOSURE ARCHIVE\n"
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE\n\n"
        "This archive documents final locked closure only.\n"
        "It does not approve evidence, close gates, write SSoT, unlock STEP102, or allow final use.\n",
        encoding="utf-8"
    )

    zip_path = Path(args.out_dir) / f"{archive_id}.zip"

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in work.rglob("*"):
                z.write(p, arcname=str(p.relative_to(work)))

        manifest["archive_zip"] = str(zip_path)
        manifest["archive_zip_sha256"] = sha256_file(zip_path)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ ZIP write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else f"✅ Final closure archive: {zip_path}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
