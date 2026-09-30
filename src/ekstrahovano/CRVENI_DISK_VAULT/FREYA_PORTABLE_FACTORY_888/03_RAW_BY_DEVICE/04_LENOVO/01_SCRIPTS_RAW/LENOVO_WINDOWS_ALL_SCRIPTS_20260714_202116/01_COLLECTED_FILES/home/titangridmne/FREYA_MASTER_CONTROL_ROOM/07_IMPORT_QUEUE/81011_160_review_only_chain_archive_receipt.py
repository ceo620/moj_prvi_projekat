# ============================================================
# TITAN_KERNEL: 160_review_only_chain_archive_receipt.py
# PURPOSE: Generate receipt for review-only chain archive and validation
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
    parser = argparse.ArgumentParser(description="Generate review-only chain archive receipt")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    validation = load_json(args.validation)

    if manifest is None or validation is None:
        print("❌ Missing manifest or validation JSON")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_CHAIN_ARCHIVE_RECEIPT",
        "version": "1.0",
        "status": "REVIEW_ONLY_CHAIN_ARCHIVE_RECEIPT_LOCKED",
        "operator": args.operator,
        "archive_id": manifest.get("archive_id", "UNKNOWN"),
        "archive_zip": manifest.get("archive_zip", "UNKNOWN"),
        "archive_zip_sha256": manifest.get("archive_zip_sha256", "UNKNOWN"),
        "validation_status": validation.get("status", "UNKNOWN"),
        "validation_violations": validation.get("violation_count", "UNKNOWN"),
        "allowed_scope": "READ_ONLY_REVIEW_OR_AUDIT_ONLY",
        "receipt_statement": "Review-only chain archive is recorded. No operational action, approval, handoff, SSoT write, STEP102 unlock, or final use is authorized.",
        "decision": "Receipt is documentary only and grants no authority.",
        **CANON,
    }

    payload["review_only_chain_archive_receipt_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Review-Only Chain Archive Receipt",
        "",
        f"Generated At: {payload['timestamp']}",
        f"Operator: {payload['operator']}",
        "",
        "## Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Archive",
        "",
        f"- Archive ID: `{payload['archive_id']}`",
        f"- Archive ZIP: `{payload['archive_zip']}`",
        f"- Archive ZIP SHA256: `{payload['archive_zip_sha256']}`",
        "",
        "## Validation",
        "",
        f"- Validation status: `{payload['validation_status']}`",
        f"- Validation violations: `{payload['validation_violations']}`",
        "",
        "## Allowed Scope",
        "",
        f"`{payload['allowed_scope']}`",
        "",
        "## Receipt Statement",
        "",
        payload["receipt_statement"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Receipt Hash",
        "",
        f"`{payload['review_only_chain_archive_receipt_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Review-only chain archive receipt generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
