# ============================================================
# TITAN_KERNEL: 57_install_order_verifier.py
# PURPOSE: Verify installed scripts against expected chronological order
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

EXPECTED_ORDER = [
    "00_guardian_v2.py",
    "00B_config_schema_validator.py",
    "00C_runtime_env_checker.py",
    "03_ssot_readonly_exporter.py",
    "04_ssot_integrity_checker.py",
    "05_script_manifest_builder.py",
    "06_script_integrity_checker.py",
    "15_filefinding_register_builder.py",
    "16_evidence_gap_loader.py",
    "17_evidence_link_validator.py",
    "18_filefinding_evidence_weight_calculator.py",
    "19_evidence_bundle_builder.py",
    "20_gap_closure_candidate_reporter.py",
    "21_manual_review_queue_builder.py",
    "22_review_decision_importer.py",
    "23_manual_override_key_verifier.py",
    "24_audit_pack_exporter.py",
    "25_chain_of_custody_logger.py",
    "26_sensitive_data_redaction_scanner.py",
    "27_retention_policy_checker.py",
    "28_log_consolidator.py",
    "29_config_drift_detector.py",
    "30_dependency_lock_exporter.py",
    "31_package_integrity_checker.py",
    "32_installed_package_registry_builder.py",
    "33_safe_runbook_generator.py",
    "34_pipeline_self_test.py",
    "35_dry_run_orchestrator.py",
    "36_execution_receipt_generator.py",
    "37_system_index_builder.py",
    "38_operator_status_snapshot.py",
    "39_next_action_recommender.py",
    "40_remediation_plan_builder.py",
    "41_gate_evidence_matrix_builder.py",
    "42_gap_remediation_tracker.py",
    "43_final_evidence_freeze_simulator.py",
    "44_reviewer_handoff_checklist.py",
    "45_control_tower_validator.py",
    "46_validation_report_reader.py",
    "47_control_tower_dashboard_exporter.py",
    "48_release_readiness_checker.py",
    "49_rollback_plan_builder.py",
    "50_daily_ops_healthcheck.py",
    "51_archive_index_builder.py",
    "52_master_package_catalog_builder.py",
    "53_artifact_completeness_checker.py",
    "54_known_issues_register_builder.py",
    "55_no_release_memorandum_generator.py",
    "56_master_package_index_generator.py",
    "57_install_order_verifier.py",
    "58_operator_binder_builder.py",
    "90_pipeline_state_manager.py",
    "91_incident_reporter.py",
    "97_preproduction_freeze.py",
    "98_safe_backup_runner.py",
    "99_master_orchestrator.py",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def main():
    parser = argparse.ArgumentParser(description="TITAN install order verifier")
    parser.add_argument("--scripts-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.scripts_root)
    records = []
    missing = []

    for idx, script in enumerate(EXPECTED_ORDER, start=1):
        path = root / script
        rec = {
            "Expected_Order": idx,
            "Script": script,
            "Path": str(path),
            "Exists": path.exists(),
            "Status": "PRESENT" if path.exists() else "MISSING",
            "Can_Run_Production": "NO",
            "Final_Use_Allowed": "NO"
        }
        if not path.exists():
            missing.append(rec)
        records.append(rec)

    payload = {
        "timestamp": now_iso(),
        "component": "INSTALL_ORDER_VERIFIER",
        "version": "1.0",
        "status": "BLOCK" if missing else "REVIEW_REQUIRED",
        "expected_count": len(EXPECTED_ORDER),
        "missing_count": len(missing),
        "records": records,
        "decision": "Install order verification is audit-only. It does not execute scripts.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Missing installed scripts" if missing else "✅ Install order verified"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if missing else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
