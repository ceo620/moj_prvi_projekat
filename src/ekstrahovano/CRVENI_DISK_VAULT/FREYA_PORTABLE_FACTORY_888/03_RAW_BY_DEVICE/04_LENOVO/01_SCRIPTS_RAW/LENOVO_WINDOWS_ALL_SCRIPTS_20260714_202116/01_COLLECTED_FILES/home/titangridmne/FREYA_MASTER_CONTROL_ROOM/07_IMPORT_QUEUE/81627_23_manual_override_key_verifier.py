# ============================================================
# TITAN_KERNEL: 23_manual_override_key_verifier.py
# PURPOSE: Verify manual override key format/hash without changing system status
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
EXIT_BLOCK = 1
EXIT_FILE_ERROR = 2

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

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_key(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read().strip()

def main():
    parser = argparse.ArgumentParser(description="Verify manual override key without applying override")
    parser.add_argument("--key-file", required=True, help="Text file containing manual override key")
    parser.add_argument("--expected-sha256", required=True, help="Expected SHA-256 of key text")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.key_file):
        result = {
            "timestamp": now_iso(),
            "component": "MANUAL_OVERRIDE_KEY_VERIFIER",
            "status": "BLOCK",
            "message": "Override key file missing",
            "override_verified": False,
            "override_applied": False,
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    key = load_key(args.key_file)
    actual = sha256_text(key)
    verified = actual.lower() == args.expected_sha256.lower()

    result = {
        "timestamp": now_iso(),
        "component": "MANUAL_OVERRIDE_KEY_VERIFIER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED" if verified else "BLOCK",
        "message": "Override key hash verified but override is NOT applied by this script." if verified else "Override key hash mismatch.",
        "override_verified": verified,
        "override_applied": False,
        "key_sha256": actual,
        "expected_sha256": args.expected_sha256,
        "decision": "This verifier never changes SYSTEM RED, STEP102, gates, evidence approval, SSoT write, or final use.",
        **CANON
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK if verified else EXIT_BLOCK

if __name__ == "__main__":
    sys.exit(main())
