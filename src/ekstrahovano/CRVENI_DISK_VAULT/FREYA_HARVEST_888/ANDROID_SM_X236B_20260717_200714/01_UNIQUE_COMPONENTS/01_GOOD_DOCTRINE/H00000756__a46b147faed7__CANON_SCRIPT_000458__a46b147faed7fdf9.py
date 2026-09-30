# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 148_terminal_frozen_locked_receipt.py
# PURPOSE: Generate terminal receipt that archives are frozen and locked
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
    parser = argparse.ArgumentParser(description="Generate terminal frozen locked receipt")
    parser.add_argument("--freeze-index", required=True)
    parser.add_argument("--drift-validation", required=True)
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    freeze = load_json(args.freeze_index)
    drift = load_json(args.drift_validation)
    if freeze is None or drift is None:
        print("❌ Missing freeze index or drift validation JSON")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "TERMINAL_FROZEN_LOCKED_RECEIPT",
        "version": "1.0",
        "status": "TERMINAL_FROZEN_LOCKED",
        "operator": args.operator,
        "freeze_hash": freeze.get("freeze_hash", "UNKNOWN"),
        "freeze_record_count": freeze.get("record_count", "UNKNOWN"),
        "drift_validation_status": drift.get("status", "UNKNOWN"),
        "drift_violation_count": drift.get("violation_count", "UNKNOWN"),
        "receipt_statement": "Terminal archive state is frozen for review/audit-only use. No production, operational handoff, STEP102 acceptance, or final use is authorized.",
        "decision": "Frozen locked receipt is documentary only and grants no authority.",
        **CANON,
    }

    payload["terminal_frozen_receipt_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Terminal Frozen Locked Receipt",
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
        "## Freeze Summary",
        "",
        f"- Freeze hash: `{payload['freeze_hash']}`",
        f"- Freeze record count: `{payload['freeze_record_count']}`",
        f"- Drift validation status: `{payload['drift_validation_status']}`",
        f"- Drift violation count: `{payload['drift_violation_count']}`",
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
        "## Terminal Frozen Receipt Hash",
        "",
        f"`{payload['terminal_frozen_receipt_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Terminal frozen locked receipt generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
