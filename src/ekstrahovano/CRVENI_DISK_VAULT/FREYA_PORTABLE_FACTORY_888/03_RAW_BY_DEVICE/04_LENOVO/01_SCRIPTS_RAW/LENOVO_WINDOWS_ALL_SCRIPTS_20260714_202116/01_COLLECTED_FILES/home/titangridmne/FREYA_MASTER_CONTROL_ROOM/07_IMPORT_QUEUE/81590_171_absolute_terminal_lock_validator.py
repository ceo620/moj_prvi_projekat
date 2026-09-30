# ============================================================
# TITAN_KERNEL: 171_absolute_terminal_lock_validator.py
# PURPOSE: Validate absolute terminal super-index preserves locked/no-authority state
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import re
import zipfile
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
    ("OPERATIONAL_ACTION_YES", r"OPERATIONAL_ACTION_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("CANONICAL_EFFECT_WRITE", r"CANONICAL_EFFECT\s*[:=]\s*(WRITE|APPROVE|CLOSE|UNLOCK)"),
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|APPROVED|UNLOCKED)"),
    ("APPROVAL_SIGNAL", r"\b(evidence approved|gate closed|release approved|production approved|final use approved)\b"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
    ("SSOT_WRITE_ALLOWED", r"SSOT_WRITE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
]

TEXT_EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".puml", ".ps1", ".py"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def scan_text(text, context):
    hits = []
    for pid, pat in FORBIDDEN:
        for m in re.finditer(pat, text, re.IGNORECASE):
            hits.append({
                "context": context,
                "pattern": pid,
                "match": m.group(0)[:200],
                "violation": "Forbidden authority/final-use signal"
            })
    return hits

def scan_file(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
        return scan_text(text, path)
    except Exception as exc:
        return [{"context": path, "pattern": "UNREADABLE", "match": str(exc), "violation": "Unreadable text artifact"}]

def scan_zip(path):
    hits = []
    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            if bad:
                hits.append({"context": path, "pattern": "BAD_ZIP_MEMBER", "match": bad, "violation": "Bad zip member"})
            for info in z.infolist():
                if info.is_dir():
                    continue
                if Path(info.filename).suffix.lower() not in TEXT_EXTS:
                    continue
                try:
                    text = z.read(info.filename).decode("utf-8-sig", errors="replace")
                    hits.extend(scan_text(text, f"{path}::{info.filename}"))
                except Exception as exc:
                    hits.append({"context": f"{path}::{info.filename}", "pattern": "UNREADABLE_ZIP_ITEM", "match": str(exc), "violation": "Unreadable zip item"})
    except Exception as exc:
        hits.append({"context": path, "pattern": "UNREADABLE_ZIP", "match": str(exc), "violation": "Unreadable zip"})
    return hits

def main():
    parser = argparse.ArgumentParser(description="Validate absolute terminal lock state")
    parser.add_argument("--super-index", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.super_index)
    if index is None:
        result = {
            "timestamp": now_iso(),
            "component": "ABSOLUTE_TERMINAL_LOCK_VALIDATOR",
            "status": "BLOCK",
            "message": "Super-index missing",
            **CANON,
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    scanned = 0

    for rec in index.get("records", []):
        if rec.get("Review_Only") != "YES":
            violations.append({"record": rec.get("Absolute_Terminal_Index_ID"), "violation": "Review_Only must be YES"})
        if rec.get("Operational_Action_Allowed") != "NO":
            violations.append({"record": rec.get("Absolute_Terminal_Index_ID"), "violation": "Operational_Action_Allowed must be NO"})
        if rec.get("Canonical_Effect") != "NONE":
            violations.append({"record": rec.get("Absolute_Terminal_Index_ID"), "violation": "Canonical_Effect must be NONE"})
        if rec.get("Final_Use_Allowed") != "NO":
            violations.append({"record": rec.get("Absolute_Terminal_Index_ID"), "violation": "Final_Use_Allowed must be NO"})

        path = rec.get("Path")
        if not path or not os.path.exists(path):
            violations.append({"record": rec.get("Absolute_Terminal_Index_ID"), "path": path, "violation": "Indexed artifact missing"})
            continue

        suffix = Path(path).suffix.lower()
        if suffix == ".zip":
            scanned += 1
            violations.extend(scan_zip(path))
        elif suffix in TEXT_EXTS:
            scanned += 1
            violations.extend(scan_file(path))

    payload = {
        "timestamp": now_iso(),
        "component": "ABSOLUTE_TERMINAL_LOCK_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "records_checked": len(index.get("records", [])),
        "artifacts_scanned": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Validator confirms absolute terminal lock metadata only. It grants no authority.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Absolute terminal lock violation found" if violations else "✅ Absolute terminal lock validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
