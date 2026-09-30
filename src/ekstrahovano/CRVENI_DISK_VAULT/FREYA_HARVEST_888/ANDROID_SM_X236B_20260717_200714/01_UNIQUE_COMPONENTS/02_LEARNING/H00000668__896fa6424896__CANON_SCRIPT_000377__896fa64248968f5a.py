# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 138_handoff_lock_state_validator.py
# PURPOSE: Validate all indexed handoff evidence preserves no-handoff lock state
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
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

FORBIDDEN = [
    ("HANDOFF_ALLOWED_YES", r"HANDOFF_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("OPERATIONAL_TRANSFER_YES", r"OPERATIONAL_TRANSFER_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("FINAL_USE_ALLOWED_YES", r"FINAL_USE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("APPROVED_HANDOFF", r"\b(handoff approved|operational handoff authorized|handoff authorized)\b"),
    ("PRODUCTION_TRANSFER", r"\b(transfer to production|production transfer approved|production handoff)\b"),
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|APPROVED|UNLOCKED)"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
]

TEXT_EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".ps1", ".py", ".puml"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def scan_text(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        return [{"path": path, "pattern": "UNREADABLE", "line": 0, "match": str(exc)}]

    hits = []
    for pid, pat in FORBIDDEN:
        for m in re.finditer(pat, text, re.IGNORECASE):
            hits.append({
                "path": path,
                "pattern": pid,
                "line": text.count("\n", 0, m.start()) + 1,
                "match": m.group(0)[:200],
                "violation": "Forbidden handoff/final-use/unlock signal"
            })
    return hits

def main():
    parser = argparse.ArgumentParser(description="Validate handoff lock state")
    parser.add_argument("--index-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.index_json)
    if index is None:
        result = {
            "timestamp": now_iso(),
            "component": "HANDOFF_LOCK_STATE_VALIDATOR",
            "status": "BLOCK",
            "message": "Index JSON missing",
            **CANON,
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    scanned = 0

    for rec in index.get("records", []):
        if rec.get("Handoff_Allowed") != "NO":
            violations.append({"record": rec.get("Handoff_Evidence_ID"), "violation": "Handoff_Allowed must be NO"})
        if rec.get("Operational_Transfer_Allowed") != "NO":
            violations.append({"record": rec.get("Handoff_Evidence_ID"), "violation": "Operational_Transfer_Allowed must be NO"})
        if rec.get("Final_Use_Allowed") != "NO":
            violations.append({"record": rec.get("Handoff_Evidence_ID"), "violation": "Final_Use_Allowed must be NO"})
        if rec.get("Canonical_Effect") != "NONE":
            violations.append({"record": rec.get("Handoff_Evidence_ID"), "violation": "Canonical_Effect must be NONE"})

        path = rec.get("Path")
        if not path or not os.path.exists(path):
            violations.append({"record": rec.get("Handoff_Evidence_ID"), "path": path, "violation": "Indexed evidence missing"})
            continue

        if Path(path).suffix.lower() in TEXT_EXTS:
            scanned += 1
            violations.extend(scan_text(path))

    result = {
        "timestamp": now_iso(),
        "component": "HANDOFF_LOCK_STATE_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "records_checked": len(index.get("records", [])),
        "text_files_scanned": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Handoff lock state validation grants no handoff and blocks all authorization signals.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Handoff lock violation found" if violations else "✅ Handoff lock state validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
