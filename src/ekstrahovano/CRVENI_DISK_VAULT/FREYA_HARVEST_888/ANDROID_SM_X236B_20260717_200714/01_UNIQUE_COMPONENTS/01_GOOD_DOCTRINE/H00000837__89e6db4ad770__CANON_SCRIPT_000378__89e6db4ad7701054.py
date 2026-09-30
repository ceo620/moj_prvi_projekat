# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 97_preproduction_freeze.py
# PURPOSE: Attempt preproduction freeze; deny under active canon
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

EXIT_FREEZE_DENIED = 1
EXIT_FILE_ERROR = 2

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

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_hash(path):
    if not path or not os.path.exists(path) or not os.path.isfile(path):
        return "MISSING"
    return sha256_file(path)

def main():
    parser = argparse.ArgumentParser(description="TITAN preproduction freeze gate")
    parser.add_argument("--manifest", help="script_manifest.json")
    parser.add_argument("--ssot-snapshot", help="ssot_readonly_snapshot.json")
    parser.add_argument("--readiness", help="release_readiness.json")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    blockers = [
        "SYSTEM RED hard lock active",
        "STEP102 LOCKED / NOT ACCEPTED",
        "FINAL_USE_ALLOWED = NO",
        "SSOT_WRITE_ALLOWED = NO",
        "EVIDENCE_APPROVAL_ALLOWED = NO",
        "GATE_CLOSURE_ALLOWED = NO",
        "Evidence gaps remain > 0",
        "P0 gates remain blocked",
    ]

    payload = {
        "timestamp": now_iso(),
        "component": "PREPRODUCTION_FREEZE",
        "version": "1.0",
        "freeze_status": "FREEZE_DENIED",
        "status": "BLOCK",
        "decision": "Preproduction freeze denied under active canon.",
        "blockers": blockers,
        "artifact_hashes": {
            "manifest": safe_hash(args.manifest) if args.manifest else "N/A",
            "ssot_snapshot": safe_hash(args.ssot_snapshot) if args.ssot_snapshot else "N/A",
            "readiness": safe_hash(args.readiness) if args.readiness else "N/A",
        },
        "note": "This script records denial only. It does not create a release candidate and does not approve final use.",
        **CANON,
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "⛔ FREEZE DENIED")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_FREEZE_DENIED

if __name__ == "__main__":
    sys.exit(main())
