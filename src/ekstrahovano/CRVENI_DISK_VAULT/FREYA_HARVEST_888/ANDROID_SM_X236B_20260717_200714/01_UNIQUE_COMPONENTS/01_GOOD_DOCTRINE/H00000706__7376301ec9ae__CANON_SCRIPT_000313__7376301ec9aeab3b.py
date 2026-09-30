# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 61_no_release_closeout_zip_builder.py
# PURPOSE: Build NO RELEASE closeout ZIP from key operator artifacts
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

DEFAULT_ARTIFACTS = [
    "no_release_memorandum.md",
    "no_release_memorandum.json",
    "operator_binder.md",
    "operator_status_snapshot.txt",
    "operator_status_snapshot.json",
    "known_issues_register.json",
    "known_issues_register.xlsx",
    "artifact_completeness_report.json",
    "release_readiness.json",
    "preproduction_freeze_denied.json",
    "execution_receipt.txt",
    "execution_receipt.json",
    "reviewer_handoff_checklist.xlsx",
    "rollback_plan.xlsx",
    "master_package_index.xlsx",
    "all_packages_checksum_ledger.xlsx",
    "script_number_map.xlsx",
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

def find_artifact(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def main():
    parser = argparse.ArgumentParser(description="Build TITAN NO RELEASE closeout ZIP")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--extra-files", nargs="*", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    closeout_id = f"NO_RELEASE_CLOSEOUT_{stamp()}"
    work_dir = Path(args.out_dir) / closeout_id
    files_dir = work_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    wanted = DEFAULT_ARTIFACTS + args.extra_files
    included = []
    missing = []

    for name in wanted:
        p = Path(name)
        src = p if p.exists() and p.is_file() else find_artifact(args.reports_root, name)

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
            "size_bytes": dest.stat().st_size
        })

    manifest = {
        "closeout_id": closeout_id,
        "timestamp": now_iso(),
        "component": "NO_RELEASE_CLOSEOUT_ZIP_BUILDER",
        "version": "1.0",
        "status": "NO_RELEASE_CLOSEOUT_BUILT",
        "included_count": len(included),
        "missing_count": len(missing),
        "included": included,
        "missing": missing,
        "decision": "Closeout ZIP documents NO RELEASE status only. It is not production approval.",
        **CANON
    }

    manifest_path = work_dir / "no_release_closeout_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = work_dir / "README_NO_RELEASE_CLOSEOUT.txt"
    readme.write_text(
        "TITAN NO RELEASE CLOSEOUT\n"
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE\n\n"
        "This package is documentation only.\n"
        "It does not approve evidence, close gates, write canonical SSoT, unlock STEP102, or allow final use.\n",
        encoding="utf-8"
    )

    zip_path = Path(args.out_dir) / f"{closeout_id}.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for item in work_dir.rglob("*"):
                z.write(item, arcname=str(item.relative_to(work_dir)))
        manifest["closeout_zip"] = str(zip_path)
        manifest["closeout_zip_sha256"] = sha256_file(zip_path)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ ZIP write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else f"✅ NO RELEASE closeout ZIP: {zip_path}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
