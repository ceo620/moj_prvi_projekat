# ============================================================
# TITAN_KERNEL: 126_master_index_integrity_validator.py
# PURPOSE: Validate final master index contains no approval/final-use effect
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
    ("FINAL_USE_ALLOWED_YES", r"FINAL_USE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("APPROVED_FOR_FINAL_USE", r"\b(approved for final use|final use approved|production approved|release approved)\b"),
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|APPROVED|UNLOCKED)"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
    ("SSOT_WRITE_YES", r"SSOT_WRITE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("GATE_CLOSURE_YES", r"GATE_CLOSURE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("EVIDENCE_APPROVAL_YES", r"EVIDENCE_APPROVAL_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
]

TEXT_EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".puml", ".ps1", ".py"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def scan_file(path):
    violations = []
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        return [{"path": path, "pattern": "UNREADABLE", "line": 0, "match": str(exc)}]

    for pid, pat in FORBIDDEN:
        for m in re.finditer(pat, text, re.IGNORECASE):
            violations.append({
                "path": path,
                "pattern": pid,
                "line": text.count("\n", 0, m.start()) + 1,
                "match": m.group(0)[:200],
                "violation": "Forbidden approval/final-use signal"
            })
    return violations

def main():
    parser = argparse.ArgumentParser(description="Validate final master index integrity")
    parser.add_argument("--index-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.index_json)
    if index is None:
        result = {
            "timestamp": now_iso(),
            "component": "MASTER_INDEX_INTEGRITY_VALIDATOR",
            "status": "BLOCK",
            "message": "Index missing",
            **CANON,
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    scanned = 0

    for rec in index.get("records", []):
        if rec.get("Canonical_Effect") != "NONE":
            violations.append({"record": rec.get("Master_Index_ID"), "violation": "Canonical_Effect must be NONE"})
        if rec.get("Final_Use_Allowed") != "NO":
            violations.append({"record": rec.get("Master_Index_ID"), "violation": "Final_Use_Allowed must be NO"})

        path = rec.get("Path")
        if not path or not os.path.exists(path):
            violations.append({"record": rec.get("Master_Index_ID"), "path": path, "violation": "Indexed artifact missing"})
            continue

        if Path(path).suffix.lower() in TEXT_EXTS:
            scanned += 1
            violations.extend(scan_file(path))

    payload = {
        "timestamp": now_iso(),
        "component": "MASTER_INDEX_INTEGRITY_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "record_count": len(index.get("records", [])),
        "text_files_scanned": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Master index validation blocks approval/final-use signals. It grants no approval.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Master index violation found" if violations else "✅ Master index integrity validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
