# ============================================================
# TITAN_KERNEL: 147_terminal_freeze_drift_validator.py
# PURPOSE: Validate terminal archive state has not drifted from freeze index
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
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

def sha256_file(path):
    if not os.path.exists(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Validate terminal freeze drift")
    parser.add_argument("--freeze-index", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    freeze = load_json(args.freeze_index)
    if freeze is None:
        result = {
            "timestamp": now_iso(),
            "component": "TERMINAL_FREEZE_DRIFT_VALIDATOR",
            "status": "BLOCK",
            "message": "Freeze index missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    checked = 0

    for row in freeze.get("records", []):
        checked += 1
        path = row.get("Path")
        expected_hash = row.get("SHA256")
        expected_size = row.get("Size_Bytes")

        if not path or not os.path.exists(path):
            violations.append({
                "Freeze_Item_ID": row.get("Freeze_Item_ID"),
                "Path": path,
                "violation": "Frozen artifact missing"
            })
            continue

        actual_hash = sha256_file(path)
        actual_size = Path(path).stat().st_size

        if actual_hash != expected_hash:
            violations.append({
                "Freeze_Item_ID": row.get("Freeze_Item_ID"),
                "Path": path,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "violation": "SHA256 drift"
            })

        if actual_size != expected_size:
            violations.append({
                "Freeze_Item_ID": row.get("Freeze_Item_ID"),
                "Path": path,
                "expected_size": expected_size,
                "actual_size": actual_size,
                "violation": "Size drift"
            })

        if row.get("Final_Use_Allowed") != "NO":
            violations.append({"Freeze_Item_ID": row.get("Freeze_Item_ID"), "violation": "Final_Use_Allowed must be NO"})

        if row.get("Canonical_Effect") != "NONE":
            violations.append({"Freeze_Item_ID": row.get("Freeze_Item_ID"), "violation": "Canonical_Effect must be NONE"})

    payload = {
        "timestamp": now_iso(),
        "component": "TERMINAL_FREEZE_DRIFT_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "checked_count": checked,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Freeze drift validation is audit-only and grants no authority.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Terminal freeze drift detected" if violations else "✅ No terminal freeze drift detected"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
