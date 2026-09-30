# ============================================================
# TITAN_KERNEL: 64_local_hash_seal_generator.py
# PURPOSE: Generate local hash seal for selected final reports
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

def main():
    parser = argparse.ArgumentParser(description="Generate local hash seal for final reports")
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-txt", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = []
    concat = ""

    for f in args.files:
        digest = sha256_file(f)
        exists = digest != "MISSING"
        records.append({
            "path": f,
            "exists": exists,
            "sha256": digest,
            "size_bytes": os.path.getsize(f) if exists else 0,
            "final_use_allowed": "NO"
        })
        concat += f"{f}|{digest}\n"

    seal_hash = hashlib.sha256(concat.encode("utf-8")).hexdigest()

    payload = {
        "timestamp": now_iso(),
        "component": "LOCAL_HASH_SEAL_GENERATOR",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "seal_type": "LOCAL_SHA256_CONCAT_SEAL",
        "seal_hash": seal_hash,
        "records": records,
        "decision": "Local hash seal confirms file state only. It is not a digital signature or approval.",
        **CANON
    }

    lines = [
        "TITAN LOCAL HASH SEAL",
        f"Generated_At: {payload['timestamp']}",
        f"Seal_Hash: {seal_hash}",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "Files:"
    ]
    for r in records:
        lines.append(f"- {r['path']} | exists={r['exists']} | sha256={r['sha256']}")

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_txt).write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Local hash seal: {args.out_txt}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
