# ============================================================
# TITAN_KERNEL: 84_locked_certificate_consistency_validator.py
# PURPOSE: Validate locked certificate and denial artifacts match active canon
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

EXPECTED = {
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
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def validate_file(path):
    result = {
        "path": path,
        "exists": os.path.exists(path),
        "violations": [],
        "checked_fields": []
    }

    if not result["exists"]:
        result["violations"].append("File missing")
        return result

    try:
        data = load_json(path)
    except Exception as exc:
        result["violations"].append(f"JSON unreadable: {exc}")
        return result

    for key, expected in EXPECTED.items():
        actual = data.get(key)
        result["checked_fields"].append({"field": key, "expected": expected, "actual": actual})
        if actual != expected:
            result["violations"].append(f"{key} expected {expected}, got {actual}")

    status = data.get("status", "")
    release_status = data.get("release_status", "")
    freeze_status = data.get("freeze_status", "")

    if release_status == "READY":
        result["violations"].append("release_status cannot be READY")
    if freeze_status == "FREEZE_ALLOWED":
        result["violations"].append("freeze_status cannot be FREEZE_ALLOWED")
    if status in {"APPROVED", "RELEASED", "FINAL_USE_ALLOWED", "UNLOCKED"}:
        result["violations"].append(f"Forbidden status: {status}")

    return result

def main():
    parser = argparse.ArgumentParser(description="Validate locked certificate consistency")
    parser.add_argument("--json-files", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = [validate_file(p) for p in args.json_files]
    violations = [v for r in results for v in r["violations"]]

    payload = {
        "timestamp": now_iso(),
        "component": "LOCKED_CERTIFICATE_CONSISTENCY_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "file_count": len(results),
        "violation_count": len(violations),
        "results": results,
        "decision": "Consistency validation cannot approve release. Any inconsistency is blocked.",
        **EXPECTED
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Certificate inconsistency" if violations else "✅ Certificates consistent with lock"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
