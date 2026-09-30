# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 25_chain_of_custody_logger.py
# PURPOSE: Append-only chain-of-custody log for evidence artifacts
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import getpass
import hashlib
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_FILE_ERROR = 2
EXIT_WRITE_ERROR = 3

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

ALLOWED_ACTIONS = {
    "CREATED",
    "COPIED",
    "MOVED",
    "HASHED",
    "REVIEWED",
    "EXPORTED",
    "PACKAGED",
    "VALIDATED_REFERENCE",
    "REJECTED_REFERENCE",
    "NOTE_ADDED"
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    if not path or not os.path.exists(path) or not os.path.isfile(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def emit_jsonl(path, event):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="TITAN append-only chain-of-custody logger")
    parser.add_argument("--artifact", required=True, help="Artifact/evidence file path")
    parser.add_argument("--action", required=True, help="Custody action")
    parser.add_argument("--actor", default="", help="Human reviewer/operator name")
    parser.add_argument("--note", default="")
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    action = args.action.strip().upper()
    if action not in ALLOWED_ACTIONS:
        action = "NOTE_ADDED"

    artifact_exists = os.path.exists(args.artifact)
    event = {
        "timestamp": now_iso(),
        "component": "CHAIN_OF_CUSTODY_LOGGER",
        "version": "1.0",
        "status": "LOGGED" if artifact_exists else "REVIEW_REQUIRED",
        "artifact": args.artifact,
        "artifact_exists": artifact_exists,
        "artifact_sha256": sha256_file(args.artifact),
        "action": action,
        "actor": args.actor or getpass.getuser(),
        "machine": socket.gethostname(),
        "os_user": getpass.getuser(),
        "note": args.note,
        "canonical_effect": "NONE",
        **CANON
    }

    emit_jsonl(args.out_jsonl, event)

    print(json.dumps(event, ensure_ascii=False, indent=2) if args.json else "✅ Chain-of-custody event logged")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
