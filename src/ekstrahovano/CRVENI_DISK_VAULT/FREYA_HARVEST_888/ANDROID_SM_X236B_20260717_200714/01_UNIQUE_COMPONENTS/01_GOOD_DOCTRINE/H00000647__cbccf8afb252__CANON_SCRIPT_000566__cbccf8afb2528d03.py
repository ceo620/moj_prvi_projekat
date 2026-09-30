# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 40_remediation_plan_builder.py
# PURPOSE: Build remediation plan from blockers and next actions
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
EXIT_FILE_ERROR = 2
EXIT_WRITE_ERROR = 3

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
    rows = []
    if not path or not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("status") == "BLOCK":
                    rows.append({
                        "source_file": path,
                        "line": idx,
                        "component": obj.get("component", obj.get("tool", "UNKNOWN")),
                        "id": obj.get("rule_id", obj.get("check_id", "UNKNOWN")),
                        "message": obj.get("message", ""),
                        "severity": obj.get("severity", "UNKNOWN"),
                    })
            except json.JSONDecodeError:
                rows.append({
                    "source_file": path,
                    "line": idx,
                    "component": "INVALID_JSON",
                    "id": "INVALID_JSON",
                    "message": line[:300],
                    "severity": "HIGH",
                })
    return rows

def classify_action(block):
    msg = (block.get("message") or "").lower()
    cid = (block.get("id") or "").upper()

    if "evidence" in msg or "filefinding" in msg or "RULE-02" in cid:
        return "Update FileFinding/Evidence mapping and rerun 17/18/45"
    if "gap" in msg or "RULE-03" in cid:
        return "Attach valid FileFinding_ID to gap or keep gap open for manual review"
    if "script" in msg or "sha" in msg or "SCRIPT" in cid:
        return "Rebuild script manifest, verify hash, backup before accepting drift"
    if "config" in msg or "schema" in msg:
        return "Fix config schema/path issue and rerun config validator"
    if "monolith" in msg or "ssot" in msg:
        return "Regenerate read-only SSoT snapshot and rerun integrity checker"
    return "Manual review required; create reviewer note and custody event"

def write_xlsx(plan, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Remediation Plan"
    headers = ["Task_ID", "Priority", "Source_Component", "Source_ID", "Severity", "Problem", "Recommended_Action", "Owner", "Status", "Can_Close_Gate", "Final_Use_Allowed"]
    ws.append(headers)

    for item in plan["tasks"]:
        ws.append([item.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build TITAN remediation plan")
    parser.add_argument("--reports", nargs="*", default=[], help="JSONL reports to inspect for BLOCK events")
    parser.add_argument("--next-actions", help="next_actions.json")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    blocks = []
    for r in args.reports:
        blocks.extend(read_jsonl_blocks(r))

    tasks = []
    for idx, b in enumerate(blocks, start=1):
        tasks.append({
            "Task_ID": f"REM-{idx:05d}",
            "Priority": "P0" if b.get("severity") == "CRITICAL" else "P1",
            "Source_Component": b.get("component", "UNKNOWN"),
            "Source_ID": b.get("id", "UNKNOWN"),
            "Severity": b.get("severity", "UNKNOWN"),
            "Problem": b.get("message", ""),
            "Recommended_Action": classify_action(b),
            "Owner": "REVIEW_REQUIRED",
            "Status": "OPEN",
            "Can_Close_Gate": "NO",
            "Final_Use_Allowed": "NO",
        })

    next_actions = load_json(args.next_actions)
    if next_actions:
        for rec in next_actions.get("recommendations", []):
            tasks.append({
                "Task_ID": f"REM-{len(tasks)+1:05d}",
                "Priority": rec.get("Priority", "P1"),
                "Source_Component": "NEXT_ACTION_RECOMMENDER",
                "Source_ID": rec.get("Script", "UNKNOWN"),
                "Severity": "REVIEW_REQUIRED",
                "Problem": rec.get("Reason", ""),
                "Recommended_Action": rec.get("Action", ""),
                "Owner": "REVIEW_REQUIRED",
                "Status": "OPEN",
                "Can_Close_Gate": "NO",
                "Final_Use_Allowed": "NO",
            })

    plan = {
        "timestamp": now_iso(),
        "component": "REMEDIATION_PLAN_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "task_count": len(tasks),
        "tasks": tasks,
        "decision": "Remediation plan is advisory. It does not close gates or approve evidence.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(plan, args.out_xlsx)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(plan, ensure_ascii=False, indent=2) if args.json else f"✅ Remediation plan built: {len(tasks)} tasks")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
