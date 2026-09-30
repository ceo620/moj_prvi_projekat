# ============================================================
# TITAN_KERNEL: 175_final_mega_terminal_archive_builder.py
# PURPOSE: Build final mega terminal archive from mega-index records
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def sha256_file(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def write_md(path, title, payload, statement):
    lines = [
        f"# {title}",
        "",
        f"Generated At: {payload.get('timestamp', now_iso())}",
        "",
        "## Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Statement",
        "",
        statement,
        "",
        "## Canonical Controls",
        "",
    ]
    for k in ["SYSTEM_STATUS","RISK_BASELINE","P0_GATES","EVIDENCE_GAPS_REMAINING","EVIDENCE_APPROVED","GATES_CLOSED","STEP102","FINAL_USE_ALLOWED","SSOT_WRITE_ALLOWED","EVIDENCE_APPROVAL_ALLOWED","GATE_CLOSURE_ALLOWED"]:
        if k in payload:
            lines.append(f"- `{k}` = `{payload[k]}`")
    lines += ["", "SYSTEM RED — STEP102 LOCKED — NO FINAL USE"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    if root.exists():
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    return None

def iter_files(roots, exts=None):
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and (exts is None or item.suffix.lower() in exts):
                yield item

def print_status(payload, as_json=False):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("status", "REVIEW_REQUIRED"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")


def main():
    parser = argparse.ArgumentParser(description="Build final mega terminal archive")
    parser.add_argument("--mega-index", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.mega_index)
    if index is None:
        payload = {"timestamp": now_iso(), "component": "FINAL_MEGA_TERMINAL_ARCHIVE_BUILDER", "status": "BLOCK", "message": "Mega index missing", **CANON}
        print_status(payload, args.json)
        return 2

    archive_id = f"FINAL_MEGA_TERMINAL_ARCHIVE_{stamp()}"
    work = Path(args.out_dir) / archive_id
    files_dir = work / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    included, missing = [], []
    for rec in index.get("records", []):
        src = Path(rec.get("Path", ""))
        if not src.exists() or not src.is_file():
            missing.append(rec)
            continue
        dest = files_dir / f"{rec.get('Mega_Index_ID')}__{src.name}"
        shutil.copy2(src, dest)
        included.append({
            "Mega_Index_ID": rec.get("Mega_Index_ID"),
            "name": src.name,
            "copied_to": str(dest),
            "sha256": sha256_file(dest),
            "review_only": "YES",
            "operational_action_allowed": "NO",
            "final_use_allowed": "NO",
            "canonical_effect": "NONE"
        })

    manifest = {
        "timestamp": now_iso(),
        "component": "FINAL_MEGA_TERMINAL_ARCHIVE_BUILDER",
        "version": "1.0",
        "status": "FINAL_MEGA_TERMINAL_ARCHIVE_BUILT",
        "archive_id": archive_id,
        "included_count": len(included),
        "missing_count": len(missing),
        "included": included,
        "missing": missing,
        "decision": "Archive is terminal review-only evidence. It grants no authority.",
        **CANON
    }
    manifest_path = work / "final_mega_terminal_archive_manifest.json"
    write_json(manifest_path, manifest)
    (work / "README_FINAL_MEGA_TERMINAL_ARCHIVE.txt").write_text(
        "TITAN FINAL MEGA TERMINAL ARCHIVE\nSYSTEM RED — STEP102 LOCKED — NO FINAL USE\nReview/audit only. No authority granted.\n",
        encoding="utf-8"
    )

    zip_path = Path(args.out_dir) / f"{archive_id}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in work.rglob("*"):
            z.write(p, arcname=str(p.relative_to(work)))
    manifest["archive_zip"] = str(zip_path)
    manifest["archive_zip_sha256"] = sha256_file(zip_path)
    write_json(manifest_path, manifest)
    print_status(manifest, args.json)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
