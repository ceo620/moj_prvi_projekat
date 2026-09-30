# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 77_audit_board_pack_builder.py
# PURPOSE: Build audit board pack index from denial/review artifacts
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

BOARD_FILES = [
    "no_release_memorandum.md",
    "operator_binder.md",
    "known_issues_register.xlsx",
    "safety_control_index.xlsx",
    "approval_boundary_simulation.json",
    "red_team_negative_tests.json",
    "release_denial_archive_manifest.json",
    "artifact_traceability_graph.xlsx",
    "control_evidence_scorecard.xlsx",
    "reviewer_attestation_template.xlsx",
    "policy_exception_verification.json",
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
    parser = argparse.ArgumentParser(description="Build TITAN audit board pack")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--extra-files", nargs="*", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pack_id = f"AUDIT_BOARD_PACK_{stamp()}"
    work = Path(args.out_dir) / pack_id
    files_dir = work / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    included = []
    missing = []

    for name in BOARD_FILES + args.extra_files:
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
        "audit_board_pack_id": pack_id,
        "timestamp": now_iso(),
        "component": "AUDIT_BOARD_PACK_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "included_count": len(included),
        "missing_count": len(missing),
        "included": included,
        "missing": missing,
        "decision": "Audit board pack is review material only. It is not approval.",
        **CANON
    }

    manifest_path = work / "audit_board_pack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = work / "README_AUDIT_BOARD_PACK.txt"
    readme.write_text(
        "TITAN AUDIT BOARD PACK\n"
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE\n\n"
        "This package is for review only.\n"
        "It does not approve evidence, close gates, write SSoT, unlock STEP102, or allow final use.\n",
        encoding="utf-8"
    )

    zip_path = Path(args.out_dir) / f"{pack_id}.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in work.rglob("*"):
                z.write(p, arcname=str(p.relative_to(work)))
        manifest["audit_board_pack_zip"] = str(zip_path)
        manifest["audit_board_pack_zip_sha256"] = sha256_file(zip_path)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ ZIP write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.json else f"✅ Audit board pack: {zip_path}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
