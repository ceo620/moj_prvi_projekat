# ============================================================
# TITAN_KERNEL: 117_locked_chain_integrity_validator.py
# PURPOSE: Validate locked-chain artifacts do not contain acceptance/final-use approval
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import re
import sys
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

FORBIDDEN_PATTERNS = [
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|APPROVED|UNLOCKED)"),
    ("FINAL_USE_ALLOWED_YES", r"FINAL_USE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("EVIDENCE_APPROVAL_ALLOWED_YES", r"EVIDENCE_APPROVAL_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("GATE_CLOSURE_ALLOWED_YES", r"GATE_CLOSURE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("SSOT_WRITE_ALLOWED_YES", r"SSOT_WRITE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
    ("RELEASE_APPROVED", r"\b(release approved|production approved|approved for final use)\b"),
]

TEXT_EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".puml", ".ps1", ".py"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_index(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def scan_text_file(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        return [{"path": path, "pattern": "UNREADABLE", "line": 0, "match": str(exc)}]

    violations = []
    for pid, pat in FORBIDDEN_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            violations.append({
                "path": path,
                "pattern": pid,
                "line": text.count("\n", 0, m.start()) + 1,
                "match": m.group(0)[:200],
                "violation": "Forbidden approval/unlock/final-use wording"
            })
    return violations

def main():
    parser = argparse.ArgumentParser(description="Validate locked-chain integrity")
    parser.add_argument("--index-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_index(args.index_json)
    if index is None:
        result = {
            "timestamp": now_iso(),
            "component": "LOCKED_CHAIN_INTEGRITY_VALIDATOR",
            "status": "BLOCK",
            "message": "Index missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    scanned = 0

    for rec in index.get("records", []):
        path = rec.get("Path")
        if not path or not os.path.exists(path):
            violations.append({"path": path or "UNKNOWN", "violation": "Indexed artifact missing"})
            continue

        if rec.get("Final_Use_Allowed") != "NO":
            violations.append({"path": path, "violation": "Index row Final_Use_Allowed is not NO"})

        if Path(path).suffix.lower() in TEXT_EXTS:
            scanned += 1
            violations.extend(scan_text_file(path))

    result = {
        "timestamp": now_iso(),
        "component": "LOCKED_CHAIN_INTEGRITY_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "indexed_records": len(index.get("records", [])),
        "text_files_scanned": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Locked-chain integrity validation blocks any acceptance/final-use signal. It grants no approval.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Locked-chain violation found" if violations else "✅ Locked-chain integrity validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
