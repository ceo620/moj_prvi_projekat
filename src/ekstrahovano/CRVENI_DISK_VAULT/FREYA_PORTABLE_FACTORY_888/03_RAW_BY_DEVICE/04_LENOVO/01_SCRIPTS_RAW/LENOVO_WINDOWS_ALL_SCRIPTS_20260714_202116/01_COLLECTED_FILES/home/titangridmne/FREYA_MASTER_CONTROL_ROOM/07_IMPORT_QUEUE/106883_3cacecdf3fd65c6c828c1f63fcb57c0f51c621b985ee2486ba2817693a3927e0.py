# ============================================================
# TITAN_KERNEL: 162_review_only_chain_freeze_validator.py
# PURPOSE: Validate review-only chain archive index has no drift and no authority flags
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
    parser = argparse.ArgumentParser(description="Validate review-only chain archive freeze state")
    parser.add_argument("--chain-index", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.chain_index)
    if index is None:
        result = {
            "timestamp": now_iso(),
            "component": "REVIEW_ONLY_CHAIN_FREEZE_VALIDATOR",
            "status": "BLOCK",
            "message": "Chain index missing",
            **CANON,
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    checked = 0

    for rec in index.get("records", []):
        checked += 1
        path = rec.get("Path")
        if not path or not os.path.exists(path):
            violations.append({"record": rec.get("Chain_Archive_Index_ID"), "path": path, "violation": "Indexed artifact missing"})
            continue

        actual_hash = sha256_file(path)
        if actual_hash != rec.get("SHA256"):
            violations.append({
                "record": rec.get("Chain_Archive_Index_ID"),
                "path": path,
                "expected_sha256": rec.get("SHA256"),
                "actual_sha256": actual_hash,
                "violation": "SHA256 drift"
            })

        actual_size = Path(path).stat().st_size
        if actual_size != rec.get("Size_Bytes"):
            violations.append({
                "record": rec.get("Chain_Archive_Index_ID"),
                "path": path,
                "expected_size": rec.get("Size_Bytes"),
                "actual_size": actual_size,
                "violation": "Size drift"
            })

        if rec.get("Review_Only") != "YES":
            violations.append({"record": rec.get("Chain_Archive_Index_ID"), "violation": "Review_Only must be YES"})
        if rec.get("Operational_Action_Allowed") != "NO":
            violations.append({"record": rec.get("Chain_Archive_Index_ID"), "violation": "Operational_Action_Allowed must be NO"})
        if rec.get("Canonical_Effect") != "NONE":
            violations.append({"record": rec.get("Chain_Archive_Index_ID"), "violation": "Canonical_Effect must be NONE"})
        if rec.get("Final_Use_Allowed") != "NO":
            violations.append({"record": rec.get("Chain_Archive_Index_ID"), "violation": "Final_Use_Allowed must be NO"})

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_CHAIN_FREEZE_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "records_checked": checked,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Freeze validation confirms review-only chain inventory only. It grants no authority.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Review-only chain freeze violation found" if violations else "✅ Review-only chain freeze validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
