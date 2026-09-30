# ============================================================
# TITAN_KERNEL: 06_script_integrity_checker.py
# PURPOSE: Compare current script hashes against script manifest
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_FILE_ERROR = 2
EXIT_SCHEMA_ERROR = 3

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

REQUIRED_FIELDS = ["Script_ID", "Script_Name", "Path", "SHA256"]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def emit_jsonl(path, event):
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def make_event(status, check_id, message, severity="INFO", extra=None):
    event = {
        "timestamp": now_iso(),
        "component": "SCRIPT_INTEGRITY_CHECKER",
        "version": "1.0",
        "status": status,
        "check_id": check_id,
        "severity": severity,
        "message": message,
        **CANON,
    }
    if extra:
        event.update(extra)
    return event

def load_manifest(path):
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and "scripts" in payload:
            return payload["scripts"]
        if isinstance(payload, list):
            return payload
        raise ValueError("JSON manifest must contain 'scripts' list or be a list")

    if path.lower().endswith(".csv"):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    raise ValueError("Supported manifest formats: .json, .csv")

def validate_rows(rows):
    errors = []
    for idx, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"Row {idx}: missing field {field}")
    return errors

def main():
    parser = argparse.ArgumentParser(description="TITAN script integrity checker")
    parser.add_argument("--manifest", required=True, help="script_manifest.json or script_manifest.csv")
    parser.add_argument("--report", required=True, help="Output JSONL report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    events = []
    blocked = False

    if not os.path.exists(args.manifest):
        e = make_event("BLOCK", "SCRIPT-001", "Manifest file missing", "CRITICAL", {"manifest": args.manifest})
        emit_jsonl(args.report, e)
        print(json.dumps(e, ensure_ascii=False) if args.json else e["message"])
        return EXIT_FILE_ERROR

    try:
        rows = load_manifest(args.manifest)
    except Exception as exc:
        e = make_event("BLOCK", "SCRIPT-002", f"Manifest unreadable: {exc}", "CRITICAL", {"manifest": args.manifest})
        emit_jsonl(args.report, e)
        print(json.dumps(e, ensure_ascii=False) if args.json else e["message"])
        return EXIT_FILE_ERROR

    schema_errors = validate_rows(rows)
    if schema_errors:
        e = make_event("BLOCK", "SCRIPT-003", "Manifest schema invalid", "CRITICAL", {"errors": schema_errors})
        emit_jsonl(args.report, e)
        print(json.dumps(e, ensure_ascii=False) if args.json else "\n".join(schema_errors))
        return EXIT_SCHEMA_ERROR

    checked = 0
    missing = []
    mismatches = []
    passes = []

    for row in rows:
        checked += 1
        script_id = str(row.get("Script_ID", "")).strip()
        path = str(row.get("Path", "")).strip()
        expected = str(row.get("SHA256", "")).strip().lower()

        if not os.path.exists(path):
            blocked = True
            missing.append({"Script_ID": script_id, "Path": path})
            continue

        try:
            actual = sha256_file(path).lower()
        except Exception as exc:
            blocked = True
            mismatches.append({"Script_ID": script_id, "Path": path, "error": str(exc)})
            continue

        if actual != expected:
            blocked = True
            mismatches.append({
                "Script_ID": script_id,
                "Path": path,
                "expected_sha256": expected,
                "actual_sha256": actual
            })
        else:
            passes.append({"Script_ID": script_id, "Path": path})

    events.append(make_event(
        "PASS" if not missing else "BLOCK",
        "SCRIPT-004",
        "Script path existence check",
        "Script paths checked",
        "CRITICAL",
        {"checked": checked, "missing_count": len(missing), "missing": missing}
    ))

    events.append(make_event(
        "PASS" if not mismatches else "BLOCK",
        "SCRIPT-005",
        "Script SHA-256 integrity check",
        "Current script hashes compared to manifest",
        "CRITICAL",
        {"checked": checked, "mismatch_count": len(mismatches), "mismatches": mismatches}
    ))

    summary = make_event(
        "BLOCK" if blocked else "REVIEW_REQUIRED",
        "SUMMARY",
        "Script integrity check complete. This is not production approval.",
        "CRITICAL",
        {"checked": checked, "pass_count": len(passes), "missing_count": len(missing), "mismatch_count": len(mismatches), "blocked": blocked}
    )
    events.append(summary)

    for e in events:
        emit_jsonl(args.report, e)

    if args.json:
        print(json.dumps({"events": events}, ensure_ascii=False, indent=2))
    else:
        for e in events:
            print(f"{e['status']} | {e['check_id']} | {e['message']}")
        print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")

    return EXIT_BLOCK if blocked else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
