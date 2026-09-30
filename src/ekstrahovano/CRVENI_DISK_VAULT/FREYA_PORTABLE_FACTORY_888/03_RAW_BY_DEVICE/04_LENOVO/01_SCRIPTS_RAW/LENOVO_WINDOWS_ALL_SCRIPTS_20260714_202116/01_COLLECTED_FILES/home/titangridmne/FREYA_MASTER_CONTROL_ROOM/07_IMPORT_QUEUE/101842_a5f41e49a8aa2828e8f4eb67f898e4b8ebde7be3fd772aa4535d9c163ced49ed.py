# ============================================================
# TITAN_KERNEL: 54_known_issues_register_builder.py
# PURPOSE: Build known issues register from BLOCK events and missing artifacts
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def read_jsonl_blocks(path):
    out = []
    if not path or not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if item.get("status") == "BLOCK":
                    out.append({
                        "Source": path,
                        "Line": idx,
                        "Component": item.get("component", item.get("tool", "UNKNOWN")),
                        "Issue_Type": "BLOCK_EVENT",
                        "Severity": item.get("severity", "CRITICAL"),
                        "Description": item.get("message", ""),
                        "Status": "OPEN"
                    })
            except json.JSONDecodeError:
                out.append({
                    "Source": path,
                    "Line": idx,
                    "Component": "INVALID_JSON",
                    "Issue_Type": "INVALID_JSON",
                    "Severity": "HIGH",
                    "Description": line[:300],
                    "Status": "OPEN"
                })
    return out

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Known Issues"
    headers = ["Issue_ID", "Source", "Line", "Component", "Issue_Type", "Severity", "Description", "Owner", "Status", "Can_Close_Gate", "Final_Use_Allowed"]
    ws.append(headers)
    for issue in payload["issues"]:
        ws.append([issue.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN known issues register builder")
    parser.add_argument("--jsonl-reports", nargs="*", default=[])
    parser.add_argument("--completeness-report")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raw_issues = []
    for report in args.jsonl_reports:
        raw_issues.extend(read_jsonl_blocks(report))

    comp = load_json(args.completeness_report)
    if comp:
        for rec in comp.get("records", []):
            if not rec.get("Exists", False):
                raw_issues.append({
                    "Source": args.completeness_report,
                    "Line": "",
                    "Component": "ARTIFACT_COMPLETENESS_CHECKER",
                    "Issue_Type": "MISSING_ARTIFACT",
                    "Severity": "HIGH",
                    "Description": f"Missing artifact: {rec.get('Artifact_Name')}",
                    "Status": "OPEN"
                })

    issues = []
    for idx, issue in enumerate(raw_issues, start=1):
        issue["Issue_ID"] = f"ISSUE-{idx:05d}"
        issue["Owner"] = "REVIEW_REQUIRED"
        issue["Can_Close_Gate"] = "NO"
        issue["Final_Use_Allowed"] = "NO"
        issues.append(issue)

    payload = {
        "timestamp": now_iso(),
        "component": "KNOWN_ISSUES_REGISTER_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "issue_count": len(issues),
        "issues": issues,
        "decision": "Known issues register is tracking only. It does not resolve issues automatically.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Known issues register built: {len(issues)} issues")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
