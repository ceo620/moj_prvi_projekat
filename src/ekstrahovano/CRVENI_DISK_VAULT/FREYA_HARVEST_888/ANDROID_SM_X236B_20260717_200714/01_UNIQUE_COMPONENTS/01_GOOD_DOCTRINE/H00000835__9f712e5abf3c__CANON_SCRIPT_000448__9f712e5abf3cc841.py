# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 43_final_evidence_freeze_simulator.py
# PURPOSE: Simulate final evidence freeze without freezing or approving
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
    if not path or not os.path.exists(path) or not os.path.isfile(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inspect_file(path):
    return {
        "path": path,
        "exists": bool(path and os.path.exists(path) and os.path.isfile(path)),
        "sha256": sha256_file(path),
        "size_bytes": os.path.getsize(path) if path and os.path.exists(path) and os.path.isfile(path) else 0
    }

def main():
    parser = argparse.ArgumentParser(description="Simulate final evidence freeze; always denied under active canon")
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    artifact_records = [inspect_file(p) for p in args.artifacts]

    blockers = [
        "SYSTEM RED hard lock active",
        "STEP102 LOCKED / NOT ACCEPTED",
        "P0 gates remain 10/10 BLOCKED",
        "Evidence gaps remaining > 0",
        "Evidence approved = 0",
        "Gates closed = 0",
        "FINAL_USE_ALLOWED = NO",
        "SSOT_WRITE_ALLOWED = NO",
        "EVIDENCE_APPROVAL_ALLOWED = NO",
        "GATE_CLOSURE_ALLOWED = NO",
    ]

    result = {
        "timestamp": now_iso(),
        "component": "FINAL_EVIDENCE_FREEZE_SIMULATOR",
        "version": "1.0",
        "status": "FREEZE_SIMULATION_DENIED",
        "freeze_simulated": True,
        "freeze_applied": False,
        "artifact_count": len(artifact_records),
        "artifacts": artifact_records,
        "blockers": blockers,
        "decision": "Final evidence freeze is denied under active canon. This script does not freeze, approve, or release.",
        **CANON
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else "⛔ Final evidence freeze simulation denied")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_FREEZE_DENIED

if __name__ == "__main__":
    sys.exit(main())
