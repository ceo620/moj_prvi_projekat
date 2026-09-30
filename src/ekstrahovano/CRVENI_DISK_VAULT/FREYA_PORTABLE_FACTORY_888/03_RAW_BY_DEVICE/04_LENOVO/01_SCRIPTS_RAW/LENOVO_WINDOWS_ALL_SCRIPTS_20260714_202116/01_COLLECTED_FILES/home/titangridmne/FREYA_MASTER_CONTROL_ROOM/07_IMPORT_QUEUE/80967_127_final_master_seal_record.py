# ============================================================
# TITAN_KERNEL: 127_final_master_seal_record.py
# PURPOSE: Generate final master seal record for locked/non-final chain
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

EXIT_LOCKED = 1
EXIT_FILE_ERROR = 2
EXIT_WRITE_ERROR = 3

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

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Generate final master seal record")
    parser.add_argument("--master-index", required=True)
    parser.add_argument("--index-validation", required=True)
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    master_index = load_json(args.master_index)
    validation = load_json(args.index_validation)

    if master_index is None or validation is None:
        print("❌ Missing master index or validation JSON")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_MASTER_SEAL_RECORD",
        "version": "1.0",
        "status": "FINAL_MASTER_SEAL_LOCKED",
        "operator": args.operator,
        "master_index_records": master_index.get("record_count", "UNKNOWN"),
        "validation_status": validation.get("status", "UNKNOWN"),
        "validation_violations": validation.get("violation_count", "UNKNOWN"),
        "seal_statement": "Final master seal records a locked, non-final, non-accepted, review-only chain.",
        "decision": "Master seal is not approval, not release, not STEP102 acceptance, and not final use.",
        **CANON,
    }

    payload["master_seal_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Final Master Seal Record",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        "",
        "## Final Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Seal Statement",
        "",
        payload["seal_statement"],
        "",
        "## Indexed Evidence",
        "",
        f"- Master index records: `{payload['master_index_records']}`",
        f"- Validation status: `{payload['validation_status']}`",
        f"- Validation violations: `{payload['validation_violations']}`",
        "",
        "## Decision",
        "",
        payload["decision"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Master Seal Hash",
        "",
        f"`{payload['master_seal_hash']}`",
        "",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Final master seal record generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
