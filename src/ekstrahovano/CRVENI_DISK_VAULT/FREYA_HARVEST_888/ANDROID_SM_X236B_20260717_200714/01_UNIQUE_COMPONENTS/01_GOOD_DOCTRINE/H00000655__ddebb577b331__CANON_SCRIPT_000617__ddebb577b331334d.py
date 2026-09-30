# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 33_safe_runbook_generator.py
# PURPOSE: Generate safe chronological runbook without executing pipeline
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

SAFE_ORDER = [
    ("01", "98_safe_backup_runner.py", "Create backup before mutation"),
    ("02", "00C_runtime_env_checker.py", "Check Python, folders and dependencies"),
    ("03", "00B_config_schema_validator.py", "Validate config.json schema"),
    ("04", "util_bom_cleaner.py", "Clean BOM on config, monolith and scripts"),
    ("05", "02_monolith_init.py", "Create monolith registry if missing; only if explicitly available"),
    ("06", "03_ssot_readonly_exporter.py", "Export read-only SSoT snapshot"),
    ("07", "04_ssot_integrity_checker.py", "Check SSoT integrity"),
    ("08", "05_script_manifest_builder.py", "Build script manifest"),
    ("09", "06_script_integrity_checker.py", "Verify script hashes"),
    ("10", "00_guardian_v2.py", "Run Guardian gate"),
    ("11", "15_filefinding_register_builder.py", "Build FileFinding register"),
    ("12", "16_evidence_gap_loader.py", "Load evidence gaps"),
    ("13", "17_evidence_link_validator.py", "Validate gap links"),
    ("14", "18_filefinding_evidence_weight_calculator.py", "Calculate signal/evidence weights"),
    ("15", "45_control_tower_validator.py", "Validate Control Tower rules"),
    ("16", "19_evidence_bundle_builder.py", "Build evidence bundle"),
    ("17", "20_gap_closure_candidate_reporter.py", "Create manual review candidate report"),
    ("18", "21_manual_review_queue_builder.py", "Create manual review queue"),
    ("19", "22_review_decision_importer.py", "Import review decisions as non-canonical log"),
    ("20", "25_chain_of_custody_logger.py", "Log custody events"),
    ("21", "26_sensitive_data_redaction_scanner.py", "Scan for sensitive data"),
    ("22", "27_retention_policy_checker.py", "Check retention without deletion"),
    ("23", "28_log_consolidator.py", "Consolidate JSONL audit timeline"),
    ("24", "30_dependency_lock_exporter.py", "Export dependency lock"),
    ("25", "47_control_tower_dashboard_exporter.py", "Export dashboard"),
    ("26", "48_release_readiness_checker.py", "Confirm NOT_READY under active canon"),
    ("27", "91_incident_reporter.py", "Create incident report when BLOCK exists"),
    ("28", "24_audit_pack_exporter.py", "Build audit pack for reviewer"),
    ("29", "97_preproduction_freeze.py", "Freeze attempt must return FREEZE_DENIED"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def generate_markdown(root, excel_path, scan_root):
    lines = []
    lines.append("# TITAN Safe Chronological Runbook")
    lines.append("")
    lines.append("STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    lines.append("")
    lines.append("This runbook is execution guidance only. It does not approve evidence, close gates, write canonical SSoT, or allow final use.")
    lines.append("")
    lines.append("## Canonical Locks")
    lines.append("")
    for k, v in CANON.items():
        lines.append(f"- `{k}` = `{v}`")
    lines.append("")
    lines.append("## Safe Order")
    lines.append("")
    lines.append("| Order | Script | Purpose |")
    lines.append("|---:|---|---|")
    for order, script, purpose in SAFE_ORDER:
        lines.append(f"| {order} | `{script}` | {purpose} |")
    lines.append("")
    lines.append("## Operator Variables")
    lines.append("")
    lines.append(f"- ROOT: `{root}`")
    lines.append(f"- EXCEL: `{excel_path}`")
    lines.append(f"- SCAN_ROOT: `{scan_root}`")
    lines.append("")
    lines.append("## Expected Terminal Status")
    lines.append("")
    lines.append("```text")
    lines.append("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    lines.append("48_release_readiness_checker.py = NOT_READY")
    lines.append("97_preproduction_freeze.py = FREEZE_DENIED")
    lines.append("```")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate safe TITAN runbook")
    parser.add_argument("--root", default=r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL")
    parser.add_argument("--excel", default=r"%USERPROFILE%\Desktop\TITAN_FileFinding_EvidenceGap_Template.xlsx")
    parser.add_argument("--scan-root", default=r"C:\DANIJELA")
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {
        "timestamp": now_iso(),
        "component": "SAFE_RUNBOOK_GENERATOR",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "safe_order": [{"order": o, "script": s, "purpose": p} for o, s, p in SAFE_ORDER],
        "root": args.root,
        "excel": args.excel,
        "scan_root": args.scan_root,
        "decision": "Runbook generated only; no execution performed.",
        **CANON
    }

    try:
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text(generate_markdown(args.root, args.excel, args.scan_root), encoding="utf-8")
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Runbook generated: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
