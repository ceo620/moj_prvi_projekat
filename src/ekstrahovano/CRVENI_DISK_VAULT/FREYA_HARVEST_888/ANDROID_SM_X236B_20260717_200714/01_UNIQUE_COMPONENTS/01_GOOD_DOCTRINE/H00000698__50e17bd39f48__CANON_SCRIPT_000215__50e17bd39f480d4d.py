# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 56_master_package_index_generator.py
# PURPOSE: Generate master index of expected TITAN package sequence
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
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
    "STEP102": "LOCKED / NOT_ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

EXPECTED_PACKAGES = [
    ("PKG-001", "TITAN_Control_Tower_Validator_v2_Package.zip", "45"),
    ("PKG-002", "TITAN_Missing_Pipeline_Scripts_v1.zip", "00B-99"),
    ("PKG-003", "TITAN_03_04_05_SSOT_Integrity_Manifest_v1.zip", "03-05"),
    ("PKG-004", "TITAN_06_17_18_Integrity_Evidence_Weight_v1.zip", "06-18"),
    ("PKG-005", "TITAN_47_48_91_97_PreProduction_v1.zip", "47-97"),
    ("PKG-006", "TITAN_19_20_21_Evidence_Review_Package_v1.zip", "19-21"),
    ("PKG-007", "TITAN_22_23_24_Review_Governance_Audit_v1.zip", "22-24"),
    ("PKG-008", "TITAN_25_26_27_Custody_Privacy_Retention_v1.zip", "25-27"),
    ("PKG-009", "TITAN_28_29_30_Observability_Drift_Dependency_v1.zip", "28-30"),
    ("PKG-010", "TITAN_31_32_33_Package_Runbook_Registry_v1.zip", "31-33"),
    ("PKG-011", "TITAN_34_35_36_SelfTest_DryRun_Receipt_v1.zip", "34-36"),
    ("PKG-012", "TITAN_37_38_39_Operator_Console_Index_v1.zip", "37-39"),
    ("PKG-013", "TITAN_40_41_42_Remediation_Gate_Matrix_v1.zip", "40-42"),
    ("PKG-014", "TITAN_43_44_49_Handoff_Rollback_FinalEvidence_v1.zip", "43-49"),
    ("PKG-015", "TITAN_50_51_52_PostHandoff_Ops_Archive_Catalog_v1.zip", "50-52"),
    ("PKG-016", "TITAN_53_54_55_Completeness_Issues_NoRelease_v1.zip", "53-55"),
    ("PKG-017", "TITAN_56_57_58_Master_Deployment_Binder_v1.zip", "56-58"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def find_package(root, filename):
    root = Path(root)
    if not root.exists():
        return "MISSING"
    direct = root / filename
    if direct.exists():
        return str(direct)
    matches = list(root.rglob(filename))
    return str(matches[0]) if matches else "MISSING"

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master Package Index"
    headers = ["Package_ID", "Expected_File", "Script_Range", "Detected_Path", "Present", "Install_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["packages"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN master package index generator")
    parser.add_argument("--packages-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = []
    for pkg_id, fname, script_range in EXPECTED_PACKAGES:
        path = find_package(args.packages_root, fname)
        records.append({
            "Package_ID": pkg_id,
            "Expected_File": fname,
            "Script_Range": script_range,
            "Detected_Path": path,
            "Present": "YES" if path != "MISSING" else "NO",
            "Install_Status": "REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO"
        })

    missing = [r for r in records if r["Present"] == "NO"]

    payload = {
        "timestamp": now_iso(),
        "component": "MASTER_PACKAGE_INDEX_GENERATOR",
        "version": "1.0",
        "status": "BLOCK" if missing else "REVIEW_REQUIRED",
        "package_count": len(records),
        "missing_count": len(missing),
        "packages": records,
        "decision": "Package index is inventory only. Presence does not approve installation or final use.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Master package index generated: {len(records)} packages")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
