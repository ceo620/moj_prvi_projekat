# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 89_final_readiness_snapshot_aggregator.py
# PURPOSE: Aggregate final pre-orchestration readiness/denial state
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
EXIT_WRITE_ERROR = 2

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

DEFAULT_INPUTS = [
    "final_locked_state_certificate.json",
    "no_release_memorandum.json",
    "decision_ledger.json",
    "release_readiness.json",
    "preproduction_freeze_denied.json",
    "artifact_completeness_report.json",
    "known_issues_register.json",
    "approval_boundary_simulation.json",
    "red_team_negative_tests.json",
    "locked_certificate_consistency_validation.json",
    "archive_reconciliation_report.json",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def load_json_safe(path):
    if not path or not path.exists():
        return {"exists": False, "status": "MISSING", "path": str(path) if path else "MISSING"}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        status = data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN")))
        return {"exists": True, "path": str(path), "status": status, "component": data.get("component", "UNKNOWN"), "raw": data}
    except Exception as exc:
        return {"exists": True, "path": str(path), "status": "UNREADABLE", "error": str(exc)}

def main():
    parser = argparse.ArgumentParser(description="Aggregate final pre-orchestration readiness/denial snapshot")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    inputs = []
    for name in DEFAULT_INPUTS:
        p = find_file(args.reports_root, name)
        rec = load_json_safe(p)
        rec["name"] = name
        inputs.append(rec)

    missing = [x for x in inputs if not x.get("exists")]
    block_like = [x for x in inputs if str(x.get("status", "")).upper() in {"BLOCK", "NO_RELEASE", "LOCKED_CERTIFIED", "ACTIVE_DENIAL", "FREEZE_SIMULATION_DENIED"}]

    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_READINESS_SNAPSHOT_AGGREGATOR",
        "version": "1.0",
        "status": "SYSTEM_RED_LOCKED",
        "input_count": len(inputs),
        "missing_count": len(missing),
        "block_or_denial_signal_count": len(block_like),
        "inputs": [{k: v for k, v in x.items() if k != "raw"} for x in inputs],
        "decision": "Pre-orchestration state remains locked. This aggregator does not run 90/99 or approve final use.",
        **CANON
    }

    md = [
        "# TITAN Final Readiness Snapshot Aggregator",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "## Summary",
        "",
        f"- Inputs checked: {payload['input_count']}",
        f"- Missing inputs: {payload['missing_count']}",
        f"- Block/denial signals: {payload['block_or_denial_signal_count']}",
        "",
        "## Inputs",
        "",
        "| Name | Exists | Status | Component |",
        "|---|---:|---|---|",
    ]
    for item in payload["inputs"]:
        md.append(f"| {item.get('name')} | {item.get('exists')} | {item.get('status')} | {item.get('component','UNKNOWN')} |")

    md.extend([
        "",
        "## Decision",
        "",
        "No final use. Do not execute production orchestration.",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```"
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Final readiness snapshot: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
