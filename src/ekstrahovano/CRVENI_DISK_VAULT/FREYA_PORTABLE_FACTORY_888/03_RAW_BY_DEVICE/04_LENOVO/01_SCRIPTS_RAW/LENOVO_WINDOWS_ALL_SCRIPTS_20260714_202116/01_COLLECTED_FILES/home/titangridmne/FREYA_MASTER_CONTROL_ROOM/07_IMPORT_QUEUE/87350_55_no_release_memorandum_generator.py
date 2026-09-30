# ============================================================
# TITAN_KERNEL: 55_no_release_memorandum_generator.py
# PURPOSE: Generate formal no-release memorandum under active canon
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_NO_RELEASE = 1
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Generate TITAN no-release memorandum")
    parser.add_argument("--known-issues")
    parser.add_argument("--operator-snapshot")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    issues = load_json(args.known_issues)
    snapshot = load_json(args.operator_snapshot)

    issue_count = issues.get("issue_count", 0) if issues else "UNKNOWN"

    payload = {
        "timestamp": now_iso(),
        "component": "NO_RELEASE_MEMORANDUM_GENERATOR",
        "version": "1.0",
        "status": "NO_RELEASE",
        "issue_count": issue_count,
        "decision": "Release, production use, evidence approval, gate closure and SSoT canonical write are not allowed under active canon.",
        "known_issues_present": bool(issues),
        "operator_snapshot_present": bool(snapshot),
        **CANON
    }

    lines = [
        "# TITAN No-Release Memorandum",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "## Decision",
        "",
        "**NO RELEASE. NO FINAL USE.**",
        "",
        "The system remains under active restriction:",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Canonical Grounds",
        "",
        f"- SYSTEM_STATUS: {CANON['SYSTEM_STATUS']}",
        f"- RISK_BASELINE: {CANON['RISK_BASELINE']}",
        f"- P0_GATES: {CANON['P0_GATES']}",
        f"- EVIDENCE_GAPS_REMAINING: {CANON['EVIDENCE_GAPS_REMAINING']}",
        f"- EVIDENCE_APPROVED: {CANON['EVIDENCE_APPROVED']}",
        f"- GATES_CLOSED: {CANON['GATES_CLOSED']}",
        f"- STEP102: {CANON['STEP102']}",
        f"- FINAL_USE_ALLOWED: {CANON['FINAL_USE_ALLOWED']}",
        f"- SSOT_WRITE_ALLOWED: {CANON['SSOT_WRITE_ALLOWED']}",
        f"- EVIDENCE_APPROVAL_ALLOWED: {CANON['EVIDENCE_APPROVAL_ALLOWED']}",
        f"- GATE_CLOSURE_ALLOWED: {CANON['GATE_CLOSURE_ALLOWED']}",
        "",
        "## Known Issues",
        "",
        f"- Known issue count: {issue_count}",
        "",
        "## Operational Instruction",
        "",
        "Continue remediation, evidence review, and audit packaging only. Do not use outputs as production, final, approved, closed, or canonical artifacts.",
        "",
        "## Final Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
    ]

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"⛔ No-release memorandum: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_NO_RELEASE

if __name__ == "__main__":
    sys.exit(main())
