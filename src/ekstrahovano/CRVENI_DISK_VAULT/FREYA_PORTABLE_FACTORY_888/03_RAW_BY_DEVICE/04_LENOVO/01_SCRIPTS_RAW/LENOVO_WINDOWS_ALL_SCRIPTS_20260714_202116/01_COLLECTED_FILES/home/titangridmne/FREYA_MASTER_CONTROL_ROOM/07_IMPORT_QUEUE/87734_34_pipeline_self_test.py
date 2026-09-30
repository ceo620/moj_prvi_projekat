# ============================================================
# TITAN_KERNEL: 34_pipeline_self_test.py
# PURPOSE: Verify expected TITAN scripts exist and are readable
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_FILE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

EXPECTED_SCRIPTS = [
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
    "45_control_tower_validator.py",
    "46_validation_report_reader.py",
    "47_control_tower_dashboard_exporter.py",
    "48_release_readiness_checker.py",
    "90_pipeline_state_manager.py",
    "91_incident_reporter.py",
    "97_preproduction_freeze.py",
    "98_safe_backup_runner.py",
    "99_master_orchestrator.py",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="TITAN pipeline self-test")
    parser.add_argument("--scripts-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.scripts_root)
    records = []
    missing_count = 0
    unreadable_count = 0

    for name in EXPECTED_SCRIPTS:
        path = root / name
        rec = {
            "script": name,
            "path": str(path),
            "exists": path.exists(),
            "readable": False,
            "sha256": "MISSING",
            "size_bytes": 0,
            "status": "UNKNOWN"
        }

        if not path.exists():
            missing_count += 1
            rec["status"] = "MISSING"
        else:
            try:
                rec["sha256"] = sha256_file(path)
                rec["size_bytes"] = path.stat().st_size
                with open(path, "rb") as f:
                    f.read(1)
                rec["readable"] = True
                rec["status"] = "PASS"
            except Exception as exc:
                unreadable_count += 1
                rec["status"] = "UNREADABLE"
                rec["error"] = str(exc)

        records.append(rec)

    blocked = missing_count > 0 or unreadable_count > 0

    result = {
        "timestamp": now_iso(),
        "component": "PIPELINE_SELF_TEST",
        "version": "1.0",
        "status": "BLOCK" if blocked else "REVIEW_REQUIRED",
        "scripts_expected": len(EXPECTED_SCRIPTS),
        "missing_count": missing_count,
        "unreadable_count": unreadable_count,
        "records": records,
        "decision": "Self-test is audit-only. Passing self-test is not release approval.",
        **CANON,
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Self-test BLOCK" if blocked else "✅ Self-test completed"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if blocked else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
