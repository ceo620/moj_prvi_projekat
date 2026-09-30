# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 114_readonly_archive_manifest_validator.py
# PURPOSE: Validate read-only proof archive manifest
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Validate read-only proof archive manifest")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    if manifest is None:
        result = {
            "timestamp": now_iso(),
            "component": "READONLY_ARCHIVE_MANIFEST_VALIDATOR",
            "status": "BLOCK",
            "message": "Manifest missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []

    for key, expected in CANON.items():
        actual = manifest.get(key)
        if actual != expected:
            violations.append({
                "field": key,
                "expected": expected,
                "actual": actual,
                "violation": "Manifest canon mismatch"
            })

    for item in manifest.get("included", []):
        if item.get("final_use_allowed") != "NO":
            violations.append({
                "item": item.get("name", "UNKNOWN"),
                "violation": "Included item final_use_allowed must be NO"
            })

    if manifest.get("status") != "READONLY_PROOF_ARCHIVE_BUILT":
        violations.append({
            "field": "status",
            "expected": "READONLY_PROOF_ARCHIVE_BUILT",
            "actual": manifest.get("status"),
            "violation": "Unexpected manifest status"
        })

    result = {
        "timestamp": now_iso(),
        "component": "READONLY_ARCHIVE_MANIFEST_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "manifest": args.manifest,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Read-only archive validation is documentary only. It does not approve final use.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Read-only archive violation" if violations else "✅ Read-only archive manifest validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
