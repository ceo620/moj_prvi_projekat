# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 119_nonacceptance_archive_builder.py
# PURPOSE: Build archive proving non-acceptance / no final use state
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "RISK_BASELINE": 890,
    "P0_GATES": "10/10 BLOCKED",
    "EVIDENCE_GAPS_REMAINING": 6,
    "EVIDENCE_APPROVED": 0,
    "GATES_CLOSED": 0,
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

NONACCEPTANCE_FILES = [
    "nothing_accepted_memorandum.json",
    "nothing_accepted_memorandum.md",
    "locked_chain_integrity_validation.json",
    "locked_chain_artifact_index.json",
    "locked_chain_artifact_index.xlsx",
    "chain_complete_locked_record.json",
    "chain_complete_locked_record.md",
    "review_only_proof.json",
    "review_only_proof.md",
    "do_not_run_notice.md",
    "final_warning_seal.md",
    "system_remains_locked_summary.md",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

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
    parser = argparse.ArgumentParser(description="Build non-acceptance archive")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--extra-files", nargs="*", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    archive_id = f"NONACCEPTANCE_ARCHIVE_{stamp()}"
    work = Path(args.out_dir) / archive_id
    files_dir = work / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    included = []
    missing = []

    for name in NONACCEPTANCE_FILES + args.extra_files:
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
            "final_use_allowed": "NO",
            "canonical_effect": "NONE",
        })

    manifest = {
        "archive_id": archive_id,
        "timestamp": now_iso(),
        "component": "NONACCEPTANCE_ARCHIVE_BUILDER",
        "version": "1.0",
        "status": "NONACCEPTANCE_ARCHIVE_BUILT",
        "included_count": len(included),
        "missing_count": len(missing),
        "included": included,
        "missing": missing,
        "decision": "Archive proves non-acceptance only. It is not approval, release, or final use.",
        **CANON,
    }

    manifest_path = work / "nonacceptance_archive_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = work / "README_NONACCEPTANCE_ARCHIVE.txt"
    readme.write_text(
        "TITAN NON-ACCEPTANCE ARCHIVE\n"
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE\n\n"
        "This archive documents that nothing is accepted, approved, released, closed, or final.\n"
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

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else f"✅ Non-acceptance archive: {zip_path}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
