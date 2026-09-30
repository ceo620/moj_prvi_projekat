# ============================================================
# TITAN_KERNEL: 62_artifact_traceability_graph_builder.py
# PURPOSE: Build traceability graph script -> report -> evidence -> gate
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
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

REPORT_MAP = [
    ("03_ssot_readonly_exporter.py", "ssot_readonly_snapshot.json", "SSOT", "P0-02"),
    ("04_ssot_integrity_checker.py", "ssot_integrity_report.jsonl", "SSOT", "P0-02"),
    ("05_script_manifest_builder.py", "script_manifest.json", "SCRIPT", "P0-03"),
    ("06_script_integrity_checker.py", "script_integrity_report.jsonl", "SCRIPT", "P0-03"),
    ("15_filefinding_register_builder.py", "TITAN_FileFinding_EvidenceGap_Template.xlsx", "EVIDENCE", "P0-04"),
    ("17_evidence_link_validator.py", "evidence_link_report.jsonl", "EVIDENCE", "P0-05"),
    ("18_filefinding_evidence_weight_calculator.py", "evidence_weight_report.jsonl", "EVIDENCE", "P0-04"),
    ("45_control_tower_validator.py", "control_tower_validation_report.jsonl", "CONTROL", "P0-06"),
    ("47_control_tower_dashboard_exporter.py", "control_tower_dashboard.xlsx", "REPORTING", "P0-06"),
    ("48_release_readiness_checker.py", "release_readiness.json", "RELEASE", "P0-09"),
    ("97_preproduction_freeze.py", "preproduction_freeze_denied.json", "FREEZE", "P0-10"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def exists_under(root, name):
    root = Path(root)
    if not root.exists():
        return "MISSING"
    direct = root / name
    if direct.exists():
        return str(direct)
    matches = list(root.rglob(name))
    return str(matches[0]) if matches else "MISSING"

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Traceability Graph"
    headers = ["Node_ID", "Script", "Report", "Domain", "Gate", "Script_Path", "Report_Path", "Link_Status", "Final_Use_Allowed"]
    ws.append(headers)

    for row in payload["edges"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def write_plantuml(payload, out_puml):
    lines = ["@startuml", "title TITAN Traceability Graph - NO FINAL USE"]
    lines.append('skinparam componentStyle rectangle')
    lines.append('package "Scripts" {')
    for e in payload["edges"]:
        lines.append(f'  component "{e["Script"]}" as S{e["Node_ID"]}')
    lines.append("}")
    lines.append('package "Reports" {')
    for e in payload["edges"]:
        lines.append(f'  artifact "{e["Report"]}" as R{e["Node_ID"]}')
    lines.append("}")
    lines.append('package "P0 Gates" {')
    gates = sorted(set(e["Gate"] for e in payload["edges"]))
    for idx, g in enumerate(gates, start=1):
        lines.append(f'  rectangle "{g}\\nBLOCKED" as G{idx}')
    lines.append("}")
    gate_index = {g: i for i, g in enumerate(gates, start=1)}
    for e in payload["edges"]:
        lines.append(f'S{e["Node_ID"]} --> R{e["Node_ID"]}')
        lines.append(f'R{e["Node_ID"]} --> G{gate_index[e["Gate"]]}')
    lines.append('note bottom: SYSTEM RED — STEP102 LOCKED — NO FINAL USE')
    lines.append("@enduml")
    Path(out_puml).parent.mkdir(parents=True, exist_ok=True)
    Path(out_puml).write_text("\n".join(lines), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Build TITAN artifact traceability graph")
    parser.add_argument("--root", required=True)
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--out-puml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    scripts_root = Path(args.root) / "SCRIPTS"

    edges = []
    for idx, (script, report, domain, gate) in enumerate(REPORT_MAP, start=1):
        script_path = exists_under(scripts_root, script)
        report_path = exists_under(args.reports_root, report)
        edges.append({
            "Node_ID": f"{idx:03d}",
            "Script": script,
            "Report": report,
            "Domain": domain,
            "Gate": gate,
            "Script_Path": script_path,
            "Report_Path": report_path,
            "Link_Status": "COMPLETE" if script_path != "MISSING" and report_path != "MISSING" else "INCOMPLETE",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "ARTIFACT_TRACEABILITY_GRAPH_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "edge_count": len(edges),
        "incomplete_count": sum(1 for e in edges if e["Link_Status"] != "COMPLETE"),
        "edges": edges,
        "decision": "Traceability graph is visibility only. It does not approve any gate or evidence.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)
        if args.out_puml:
            write_plantuml(payload, args.out_puml)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Traceability graph built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
