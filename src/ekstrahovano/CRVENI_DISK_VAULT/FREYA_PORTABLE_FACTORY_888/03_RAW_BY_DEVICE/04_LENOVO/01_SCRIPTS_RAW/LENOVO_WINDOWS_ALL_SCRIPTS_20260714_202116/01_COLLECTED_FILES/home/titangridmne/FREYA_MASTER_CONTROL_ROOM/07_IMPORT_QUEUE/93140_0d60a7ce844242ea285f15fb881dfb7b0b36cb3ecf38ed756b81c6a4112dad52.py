# ============================================================
# TITAN_KERNEL: 96_prefreeze_denial_precheck.py
# PURPOSE: Precheck before 97_preproduction_freeze; expected denial
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_DENIED = 1
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

REQUIRED = [
    "pipeline_state.json",
    "state_transition_denial.json",
    "emergency_stop_ledger.json",
    "rollback_readiness_verification.json",
    "final_locked_state_certificate.json",
    "no_release_memorandum.json",
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

def load_status(path):
    if path is None:
        return "MISSING"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN")))
    except Exception:
        return "UNREADABLE"

def main():
    parser = argparse.ArgumentParser(description="Pre-freeze denial precheck")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    artifacts = []
    for name in REQUIRED:
        p = find_file(args.reports_root, name)
        artifacts.append({
            "Artifact": name,
            "Path": str(p) if p else "MISSING",
            "Exists": p is not None,
            "Status": load_status(p),
            "Final_Use_Allowed": "NO"
        })

    missing = [a for a in artifacts if not a["Exists"]]
    denial_reasons = [
        "SYSTEM RED hard lock active",
        "STEP102 LOCKED / NOT ACCEPTED",
        "FINAL_USE_ALLOWED = NO",
        "P0 gates remain blocked",
        "Evidence approval and gate closure remain disallowed",
        "Freeze must be denied under active canon"
    ]

    payload = {
        "timestamp": now_iso(),
        "component": "PREFREEZE_DENIAL_PRECHECK",
        "version": "1.0",
        "status": "FREEZE_PRECHECK_DENIED",
        "missing_count": len(missing),
        "artifacts": artifacts,
        "denial_reasons": denial_reasons,
        "expected_next_result": "97_preproduction_freeze.py must return FREEZE_DENIED",
        "decision": "Do not treat pre-freeze checks as approval. Freeze remains denied.",
        **CANON
    }

    md = [
        "# TITAN Pre-Freeze Denial Precheck",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "## Artifacts",
        "",
        "| Artifact | Exists | Status |",
        "|---|---:|---|",
    ]

    for a in artifacts:
        md.append(f"| `{a['Artifact']}` | {a['Exists']} | {a['Status']} |")

    md.extend([
        "",
        "## Expected Next Result",
        "",
        "`97_preproduction_freeze.py = FREEZE_DENIED`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "⛔ Pre-freeze denial confirmed")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_DENIED

if __name__ == "__main__":
    sys.exit(main())
