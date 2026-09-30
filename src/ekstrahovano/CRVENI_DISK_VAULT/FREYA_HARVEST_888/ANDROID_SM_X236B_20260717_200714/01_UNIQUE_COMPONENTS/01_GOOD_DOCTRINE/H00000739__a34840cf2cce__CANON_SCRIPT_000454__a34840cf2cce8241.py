# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 139_ultimate_handoff_lock_seal.py
# PURPOSE: Generate ultimate handoff lock seal memorandum
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
    parser = argparse.ArgumentParser(description="Generate ultimate handoff lock seal")
    parser.add_argument("--handoff-index", required=True)
    parser.add_argument("--handoff-validation", required=True)
    parser.add_argument("--operator", default="UNKNOWN")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.handoff_index)
    validation = load_json(args.handoff_validation)

    if index is None or validation is None:
        print("❌ Missing handoff index or validation JSON")
        return EXIT_FILE_ERROR

    payload = {
        "timestamp": now_iso(),
        "component": "ULTIMATE_HANDOFF_LOCK_SEAL",
        "version": "1.0",
        "status": "ULTIMATE_HANDOFF_LOCK_SEALED",
        "operator": args.operator,
        "handoff_index_records": index.get("record_count", "UNKNOWN"),
        "validation_status": validation.get("status", "UNKNOWN"),
        "validation_violations": validation.get("violation_count", "UNKNOWN"),
        "handoff_allowed": "NO",
        "operational_transfer_allowed": "NO",
        "review_only_allowed": "YES",
        "seal_statement": "All indexed handoff evidence remains locked. No operational handoff, production transfer, STEP102 acceptance, or final use is authorized.",
        "decision": "Ultimate handoff lock seal is documentary only. It grants no operational authority.",
        **CANON,
    }

    payload["ultimate_handoff_lock_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Ultimate Handoff Lock Seal",
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
        "## Handoff Lock State",
        "",
        "- Handoff allowed: `NO`",
        "- Operational transfer allowed: `NO`",
        "- Review-only allowed: `YES`",
        "",
        "## Indexed Evidence",
        "",
        f"- Handoff index records: `{payload['handoff_index_records']}`",
        f"- Validation status: `{payload['validation_status']}`",
        f"- Validation violations: `{payload['validation_violations']}`",
        "",
        "## Seal Statement",
        "",
        payload["seal_statement"],
        "",
        "## Canonical Controls",
        "",
    ]

    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "## Ultimate Handoff Lock Hash",
        "",
        f"`{payload['ultimate_handoff_lock_hash']}`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Ultimate handoff lock seal generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    raise SystemExit(main())
