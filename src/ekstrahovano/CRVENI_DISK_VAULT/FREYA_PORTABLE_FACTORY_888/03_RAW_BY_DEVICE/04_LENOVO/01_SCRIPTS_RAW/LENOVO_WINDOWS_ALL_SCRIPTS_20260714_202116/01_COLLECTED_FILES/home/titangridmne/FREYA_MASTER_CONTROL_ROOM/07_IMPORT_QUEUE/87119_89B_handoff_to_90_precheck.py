# ============================================================
# TITAN_KERNEL: 89B_handoff_to_90_precheck.py
# PURPOSE: Precheck before 90_pipeline_state_manager without executing it
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
EXIT_BLOCK = 1
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

REQUIRED_PRECHECK_ARTIFACTS = [
    "final_readiness_snapshot.json",
    "master_status_lock_verification.json",
    "final_locked_state_certificate.json",
    "no_release_memorandum.json",
    "decision_ledger.json",
    "known_issues_register.json",
]

REQUIRED_NEXT_SCRIPTS = [
    "90_pipeline_state_manager.py",
    "91_incident_reporter.py",
    "97_preproduction_freeze.py",
    "98_safe_backup_runner.py",
    "99_master_orchestrator.py",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def exists_under(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists():
        return str(direct)
    matches = list(root.rglob(name)) if root.exists() else []
    return str(matches[0]) if matches else "MISSING"

def main():
    parser = argparse.ArgumentParser(description="Precheck handoff to 90 pipeline state manager")
    parser.add_argument("--root", required=True)
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    script_checks = []
    for script in REQUIRED_NEXT_SCRIPTS:
        path = exists_under(Path(args.root) / "SCRIPTS", script)
        script_checks.append({"Script": script, "Path": path, "Exists": path != "MISSING", "Execute_Now": "NO"})

    artifact_checks = []
    for artifact in REQUIRED_PRECHECK_ARTIFACTS:
        path = exists_under(args.reports_root, artifact)
        artifact_checks.append({"Artifact": artifact, "Path": path, "Exists": path != "MISSING", "Canonical_Effect": "NONE"})

    missing_scripts = [x for x in script_checks if not x["Exists"]]
    missing_artifacts = [x for x in artifact_checks if not x["Exists"]]

    payload = {
        "timestamp": now_iso(),
        "component": "HANDOFF_TO_90_PRECHECK",
        "version": "1.0",
        "status": "BLOCK" if missing_scripts or missing_artifacts else "REVIEW_REQUIRED",
        "script_checks": script_checks,
        "artifact_checks": artifact_checks,
        "missing_script_count": len(missing_scripts),
        "missing_artifact_count": len(missing_artifacts),
        "execute_90_now": "NO",
        "decision": "Precheck prepares handoff only. Do not execute 90/99 as production or approval.",
        **CANON
    }

    md = [
        "# TITAN Handoff to 90 Precheck",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "## Scripts",
        "",
        "| Script | Exists | Execute Now |",
        "|---|---:|---|",
    ]
    for s in script_checks:
        md.append(f"| `{s['Script']}` | {s['Exists']} | NO |")

    md.extend(["", "## Artifacts", "", "| Artifact | Exists | Canonical Effect |", "|---|---:|---|"])
    for a in artifact_checks:
        md.append(f"| `{a['Artifact']}` | {a['Exists']} | NONE |")

    md.extend([
        "",
        "## Decision",
        "",
        "`execute_90_now = NO`",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Handoff precheck: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if missing_scripts or missing_artifacts else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
