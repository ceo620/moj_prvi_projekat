# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 73_safety_control_index_builder.py
# PURPOSE: Build index of TITAN safety controls and linked scripts
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
except ImportError:
    openpyxl = None

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

CONTROLS = [
    ("CTRL-001", "SYSTEM RED Hard Lock", "00_guardian_v2.py;45_control_tower_validator.py;71_approval_boundary_simulator.py", "Blocks automated status upgrades"),
    ("CTRL-002", "STEP102 Evidence Gap Lock", "45_control_tower_validator.py;17_evidence_link_validator.py;42_gap_remediation_tracker.py", "Keeps STEP102 locked while gaps remain"),
    ("CTRL-003", "AI Signal Evidence Mapping", "15_filefinding_register_builder.py;18_filefinding_evidence_weight_calculator.py", "Weight 0 without FileFinding/Evidence mapping"),
    ("CTRL-004", "SSOT No-Write Boundary", "03_ssot_readonly_exporter.py;04_ssot_integrity_checker.py;23_manual_override_key_verifier.py", "Allows read-only export/check only"),
    ("CTRL-005", "No Gate Closure Automation", "41_gate_evidence_matrix_builder.py;48_release_readiness_checker.py;97_preproduction_freeze.py", "Prevents automatic gate closure"),
    ("CTRL-006", "No Final Use", "48_release_readiness_checker.py;55_no_release_memorandum_generator.py;61_no_release_closeout_zip_builder.py", "Keeps final use disabled"),
    ("CTRL-007", "Package/Script Integrity", "05_script_manifest_builder.py;06_script_integrity_checker.py;59_all_packages_checksum_ledger.py", "Verifies hashes and package integrity"),
    ("CTRL-008", "Review Governance", "21_manual_review_queue_builder.py;22_review_decision_importer.py;69_reviewer_attestation_template.py", "Separates human review from approval"),
    ("CTRL-009", "Provenance and Custody", "25_chain_of_custody_logger.py;65_artifact_provenance_register.py", "Records artifact origin and handling"),
    ("CTRL-010", "Negative Testing", "72_red_team_negative_tests.py", "Confirms unsafe transitions remain blocked"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Safety Control Index"
    headers = ["Control_ID", "Control_Name", "Linked_Scripts", "Purpose", "Status", "Can_Close_Gate", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["controls"]:
        ws.append([row.get(h, "") for h in headers])
    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])
    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build TITAN safety control index")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    controls = []
    for cid, name, scripts, purpose in CONTROLS:
        controls.append({
            "Control_ID": cid,
            "Control_Name": name,
            "Linked_Scripts": scripts,
            "Purpose": purpose,
            "Status": "CONTROL_DIAMOND_NOT_EXECUTED",
            "Can_Close_Gate": "NO",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "SAFETY_CONTROL_INDEX_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "control_count": len(controls),
        "controls": controls,
        "decision": "Safety control index documents controls only. It does not execute or approve them.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Safety control index built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
