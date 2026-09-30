# ============================================================
# TITAN_KERNEL: 107_final_use_nonactivation_checker.py
# PURPOSE: Check that final-use activation did not occur in key artifacts
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
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

FORBIDDEN_PATTERNS = [
    ("FINAL_USE_ALLOWED_YES", r"FINAL_USE_ALLOWED\s*[=:]\s*(YES|TRUE|1)"),
    ("FINAL_USE_TEXT", r"\b(final use allowed|production approved|release approved)\b"),
    ("STEP102_ACCEPTED", r"STEP102\s*[=:]\s*(ACCEPTED|UNLOCKED|APPROVED)"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
    ("GATE_CLOSED", r"\bGATE[_\s-]*CLOSED\s*[=:]?\s*(YES|TRUE|1)?\b"),
    ("SSOT_WRITE_ALLOWED", r"SSOT_WRITE_ALLOWED\s*[=:]\s*(YES|TRUE|1)"),
]

EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".ps1", ".py"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def iter_files(root):
    root = Path(root)
    if root.is_file():
        yield root
    elif root.exists():
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in EXTS:
                yield p

def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        return [{"file": str(path), "pattern": "UNREADABLE", "line": 0, "match": str(exc)}]

    hits = []
    for pattern_id, pattern in FORBIDDEN_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            hits.append({
                "file": str(path),
                "pattern": pattern_id,
                "line": text.count("\n", 0, m.start()) + 1,
                "match": m.group(0)[:200],
                "final_use_allowed": "NO"
            })
    return hits

def main():
    parser = argparse.ArgumentParser(description="Check no final-use activation occurred")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files_scanned = 0
    violations = []

    for root in args.roots:
        for path in iter_files(root):
            files_scanned += 1
            violations.extend(scan_file(path))

    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_USE_NONACTIVATION_CHECKER",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "files_scanned": files_scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Any final-use activation wording is blocked. This checker does not approve use.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Final-use activation signal found" if violations else "✅ No final-use activation detected"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
