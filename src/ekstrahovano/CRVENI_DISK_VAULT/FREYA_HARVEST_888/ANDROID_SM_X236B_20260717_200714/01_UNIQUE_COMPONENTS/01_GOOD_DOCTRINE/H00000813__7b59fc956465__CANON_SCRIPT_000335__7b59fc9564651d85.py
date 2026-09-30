# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 70_immutable_export_manifest_builder.py
# PURPOSE: Build immutable-style export manifest for selected artifacts
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    if not os.path.exists(path) or not os.path.isfile(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def manifest_hash(records):
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Build immutable export manifest")
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-txt", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = []
    for idx, f in enumerate(args.files, start=1):
        exists = os.path.exists(f) and os.path.isfile(f)
        records.append({
            "Export_Item_ID": f"EXP-{idx:05d}",
            "Path": f,
            "Exists": exists,
            "SHA256": sha256_file(f),
            "Size_Bytes": os.path.getsize(f) if exists else 0,
            "Captured_At": now_iso(),
            "Mutable_After_Export": "UNKNOWN",
            "Final_Use_Allowed": "NO"
        })

    ledger_hash = manifest_hash(records)

    payload = {
        "timestamp": now_iso(),
        "component": "IMMUTABLE_EXPORT_MANIFEST_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "manifest_hash": ledger_hash,
        "record_count": len(records),
        "records": records,
        "decision": "Manifest records export state only. It is not legal immutability, approval, or release.",
        **CANON
    }

    lines = [
        "TITAN IMMUTABLE-STYLE EXPORT MANIFEST",
        f"Generated_At: {payload['timestamp']}",
        f"Manifest_Hash: {ledger_hash}",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "Items:"
    ]
    for r in records:
        lines.append(f"- {r['Export_Item_ID']} | exists={r['Exists']} | sha256={r['SHA256']} | {r['Path']}")

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_txt).write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Immutable export manifest: {args.out_txt}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
