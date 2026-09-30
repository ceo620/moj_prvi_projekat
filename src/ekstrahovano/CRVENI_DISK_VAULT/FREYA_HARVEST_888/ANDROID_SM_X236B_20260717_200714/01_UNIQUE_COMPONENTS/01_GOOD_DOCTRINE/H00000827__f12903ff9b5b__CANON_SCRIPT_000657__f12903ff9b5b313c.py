# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 53_artifact_completeness_checker.py
# PURPOSE: Check expected artifact/report completeness
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

EXPECTED_REPORTS = [
    "ssot_readonly_snapshot.json",
    "ssot_integrity_report.jsonl",
    "script_manifest.json",
    "script_integrity_report.jsonl",
    "control_tower_validation_report.jsonl",
    "evidence_link_report.jsonl",
    "evidence_weight_report.jsonl",
    "gap_closure_candidates.json",
    "manual_review_queue.xlsx",
    "release_readiness.json",
    "preproduction_freeze_denied.json",
    "operator_status_snapshot.json",
    "next_actions.json",
    "remediation_plan.json",
    "gate_evidence_matrix.json",
    "gap_remediation_tracker.json",
    "reviewer_handoff_checklist.json",
    "rollback_plan.json",
    "daily_ops_healthcheck.json",
    "archive_index.json",
    "master_package_catalog.json",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def inspect(root, name):
    path = Path(root) / name
    return {
        "Artifact_Name": name,
        "Path": str(path),
        "Exists": path.exists(),
        "Size_Bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        "Status": "PRESENT" if path.exists() else "MISSING",
        "Final_Use_Allowed": "NO"
    }

def main():
    parser = argparse.ArgumentParser(description="TITAN artifact completeness checker")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = [inspect(args.reports_root, name) for name in EXPECTED_REPORTS]
    missing = [r for r in records if not r["Exists"]]
    blocked = bool(missing)

    result = {
        "timestamp": now_iso(),
        "component": "ARTIFACT_COMPLETENESS_CHECKER",
        "version": "1.0",
        "status": "BLOCK" if blocked else "REVIEW_REQUIRED",
        "expected_count": len(EXPECTED_REPORTS),
        "present_count": len(records) - len(missing),
        "missing_count": len(missing),
        "records": records,
        "decision": "Completeness check is audit-only. Complete artifact set is not approval.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Missing artifacts" if blocked else "✅ Artifact completeness reviewed"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if blocked else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
