# ============================================================
# TITAN_KERNEL: 141_handoff_lock_archive_manifest_validator.py
# PURPOSE: Validate handoff lock archive manifest
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
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
    parser = argparse.ArgumentParser(description="Validate handoff lock archive manifest")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    if manifest is None:
        result = {
            "timestamp": now_iso(),
            "component": "HANDOFF_LOCK_ARCHIVE_MANIFEST_VALIDATOR",
            "status": "BLOCK",
            "message": "Manifest missing",
            **CANON,
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []

    for key, expected in CANON.items():
        actual = manifest.get(key)
        if actual != expected:
            violations.append({"field": key, "expected": expected, "actual": actual, "violation": "Canon mismatch"})

    if manifest.get("status") != "HANDOFF_LOCK_ARCHIVE_BUILT":
        violations.append({"field": "status", "expected": "HANDOFF_LOCK_ARCHIVE_BUILT", "actual": manifest.get("status"), "violation": "Unexpected manifest status"})

    for item in manifest.get("included", []):
        if item.get("handoff_allowed") != "NO":
            violations.append({"item": item.get("name", "UNKNOWN"), "violation": "handoff_allowed must be NO"})
        if item.get("operational_transfer_allowed") != "NO":
            violations.append({"item": item.get("name", "UNKNOWN"), "violation": "operational_transfer_allowed must be NO"})
        if item.get("final_use_allowed") != "NO":
            violations.append({"item": item.get("name", "UNKNOWN"), "violation": "final_use_allowed must be NO"})
        if item.get("canonical_effect") != "NONE":
            violations.append({"item": item.get("name", "UNKNOWN"), "violation": "canonical_effect must be NONE"})

    result = {
        "timestamp": now_iso(),
        "component": "HANDOFF_LOCK_ARCHIVE_MANIFEST_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "manifest": args.manifest,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Manifest validation confirms handoff lock archive metadata only. It grants no authority.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Handoff lock archive violation" if violations else "✅ Handoff lock archive manifest validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
