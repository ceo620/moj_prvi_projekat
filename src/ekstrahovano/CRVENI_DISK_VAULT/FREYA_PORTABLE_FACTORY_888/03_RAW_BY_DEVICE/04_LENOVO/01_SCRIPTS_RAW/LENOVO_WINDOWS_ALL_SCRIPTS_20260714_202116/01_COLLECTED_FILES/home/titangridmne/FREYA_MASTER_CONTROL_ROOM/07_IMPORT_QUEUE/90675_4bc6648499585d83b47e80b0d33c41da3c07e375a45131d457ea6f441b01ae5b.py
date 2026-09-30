# ============================================================
# TITAN_KERNEL: 75_command_transcript_validator.py
# PURPOSE: Validate command transcript for forbidden production/approval commands
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
    ("FINAL_USE_YES", r"FINAL_USE_ALLOWED\s*=\s*YES"),
    ("SSOT_WRITE_YES", r"SSOT_WRITE_ALLOWED\s*=\s*YES"),
    ("EVIDENCE_APPROVAL_YES", r"EVIDENCE_APPROVAL_ALLOWED\s*=\s*YES"),
    ("GATE_CLOSURE_YES", r"GATE_CLOSURE_ALLOWED\s*=\s*YES"),
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|UNLOCKED|APPROVED)"),
    ("SYSTEM_GREEN", r"SYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)"),
    ("PRODUCTION_DEPLOY", r"\b(deploy|release|publish)\b.*\b(prod|production|final)\b"),
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def main():
    parser = argparse.ArgumentParser(description="Validate command transcript for forbidden transitions")
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.transcript):
        result = {
            "timestamp": now_iso(),
            "component": "COMMAND_TRANSCRIPT_VALIDATOR",
            "status": "BLOCK",
            "message": "Transcript missing",
            "transcript": args.transcript,
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    text = Path(args.transcript).read_text(encoding="utf-8-sig", errors="replace")
    violations = []

    for name, pat in FORBIDDEN_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            line = text.count("\n", 0, m.start()) + 1
            violations.append({
                "Pattern_ID": name,
                "Line": line,
                "Match": m.group(0)[:200],
                "Violation": "Forbidden approval/production transition detected"
            })

    result = {
        "timestamp": now_iso(),
        "component": "COMMAND_TRANSCRIPT_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Transcript validation is audit-only. Any forbidden transition remains blocked.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else ("⛔ Forbidden transcript content" if violations else "✅ Transcript reviewed"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
