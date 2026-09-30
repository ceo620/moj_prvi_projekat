# ============================================================
# TITAN_KERNEL: 89A_master_status_lock_verifier.py
# PURPOSE: Verify all final JSON artifacts preserve SYSTEM RED lock controls
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
EXIT_WRITE_ERROR = 2

EXPECTED = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

FORBIDDEN_VALUES = {
    "SYSTEM_STATUS": {"SYSTEM GREEN", "SYSTEM GOLDEN", "APPROVED", "PRODUCTION"},
    "STEP102": {"ACCEPTED", "UNLOCKED", "APPROVED"},
    "FINAL_USE_ALLOWED": {"YES", "TRUE", True},
    "SSOT_WRITE_ALLOWED": {"YES", "TRUE", True},
    "EVIDENCE_APPROVAL_ALLOWED": {"YES", "TRUE", True},
    "GATE_CLOSURE_ALLOWED": {"YES", "TRUE", True},
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def iter_json_files(root):
    root = Path(root)
    if root.is_file() and root.suffix.lower() == ".json":
        yield root
    elif root.exists():
        yield from root.rglob("*.json")

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"__unreadable__": str(exc)}

def main():
    parser = argparse.ArgumentParser(description="Verify master status lock across final JSON artifacts")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    violations = []
    checked_files = 0
    checked_fields = 0

    for path in iter_json_files(args.reports_root):
        checked_files += 1
        data = load_json(path)

        if "__unreadable__" in data:
            violations.append({"path": str(path), "violation": f"JSON unreadable: {data['__unreadable__']}"})
            continue

        if not isinstance(data, dict):
            continue

        for key, expected in EXPECTED.items():
            if key in data:
                checked_fields += 1
                actual = data.get(key)
                if actual in FORBIDDEN_VALUES.get(key, set()):
                    violations.append({"path": str(path), "field": key, "actual": actual, "violation": "Forbidden unlocked/approval value"})
                if actual != expected:
                    violations.append({"path": str(path), "field": key, "expected": expected, "actual": actual, "violation": "Canonical lock mismatch"})

        release_status = data.get("release_status")
        freeze_status = data.get("freeze_status")
        status = data.get("status")

        if release_status == "READY":
            violations.append({"path": str(path), "field": "release_status", "actual": release_status, "violation": "Release status cannot be READY"})
        if freeze_status == "FREEZE_ALLOWED":
            violations.append({"path": str(path), "field": "freeze_status", "actual": freeze_status, "violation": "Freeze status cannot be FREEZE_ALLOWED"})
        if status in {"APPROVED", "RELEASED", "FINAL_USE_ALLOWED", "UNLOCKED"}:
            violations.append({"path": str(path), "field": "status", "actual": status, "violation": "Forbidden final/unlocked status"})

    payload = {
        "timestamp": now_iso(),
        "component": "MASTER_STATUS_LOCK_VERIFIER",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "checked_files": checked_files,
        "checked_fields": checked_fields,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "All final JSON artifacts must preserve locked/no-use canon. This verifier does not approve release.",
        **EXPECTED
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Lock violation found" if violations else "✅ Master status lock verified"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
