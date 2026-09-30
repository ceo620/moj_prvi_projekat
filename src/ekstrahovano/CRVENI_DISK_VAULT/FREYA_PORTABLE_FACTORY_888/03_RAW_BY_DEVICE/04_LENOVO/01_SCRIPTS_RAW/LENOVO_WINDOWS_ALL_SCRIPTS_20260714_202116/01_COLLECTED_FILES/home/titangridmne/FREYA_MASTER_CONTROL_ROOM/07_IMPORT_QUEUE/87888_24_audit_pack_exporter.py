# ============================================================
# TITAN_KERNEL: 24_audit_pack_exporter.py
# PURPOSE: Build reviewer audit pack from reports, manifests and dashboards
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

def safe_copy(src, dst_dir):
    src = Path(src)
    if not src.exists() or not src.is_file():
        return None
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    return dst

def main():
    parser = argparse.ArgumentParser(description="Create TITAN reviewer audit pack")
    parser.add_argument("--inputs", nargs="+", required=True, help="Files to include")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pack_id = f"AUDIT_PACK_{stamp()}"
    out_dir = Path(args.out_dir) / pack_id
    included_dir = out_dir / "included_files"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "audit_pack_id": pack_id,
        "created_at": now_iso(),
        "component": "AUDIT_PACK_EXPORTER",
        "version": "1.0",
        "included": [],
        "missing": [],
        "note": "Audit pack is for reviewer transfer only. It is not final-use approval.",
        **CANON
    }

    for item in args.inputs:
        src = Path(item)
        if not src.exists() or not src.is_file():
            manifest["missing"].append(str(src))
            continue

        copied = safe_copy(src, included_dir)
        if copied:
            manifest["included"].append({
                "source": str(src),
                "copied_to": str(copied),
                "sha256": sha256_file(copied),
                "size_bytes": copied.stat().st_size
            })

    manifest_path = out_dir / "audit_pack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = Path(args.out_dir) / f"{pack_id}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.rglob("*"):
            z.write(p, arcname=str(p.relative_to(out_dir)))

    result = {
        "timestamp": now_iso(),
        "component": "AUDIT_PACK_EXPORTER",
        "status": "REVIEW_REQUIRED",
        "audit_pack_dir": str(out_dir),
        "audit_pack_zip": str(zip_path),
        "included_count": len(manifest["included"]),
        "missing_count": len(manifest["missing"]),
        **CANON
    }

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"✅ Audit pack: {zip_path}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
