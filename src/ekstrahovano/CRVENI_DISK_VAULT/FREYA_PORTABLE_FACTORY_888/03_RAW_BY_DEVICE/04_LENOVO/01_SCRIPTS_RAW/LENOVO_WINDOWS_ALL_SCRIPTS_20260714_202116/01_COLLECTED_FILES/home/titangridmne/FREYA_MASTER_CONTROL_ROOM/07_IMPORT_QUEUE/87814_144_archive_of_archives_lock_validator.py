# ============================================================
# TITAN_KERNEL: 144_archive_of_archives_lock_validator.py
# PURPOSE: Validate archive-of-archives inventory preserves locked/no-use state
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import zipfile
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
    ("HANDOFF_ALLOWED_YES", r"HANDOFF_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("OPERATIONAL_TRANSFER_YES", r"OPERATIONAL_TRANSFER_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|APPROVED|UNLOCKED)"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
    ("RELEASE_APPROVED", r"\b(release approved|production approved|final use approved|operational handoff authorized)\b"),
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
                "violation": "Forbidden approval/handoff/final-use signal"
            })
    return hits

def scan_zip(path):
    violations = []
    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            if bad:
                violations.append({"archive": path, "violation": f"Bad zip member: {bad}"})
            for info in z.infolist():
                if info.is_dir():
                    continue
                if Path(info.filename).suffix.lower() not in TEXT_EXTS:
                    continue
                try:
                    text = z.read(info.filename).decode("utf-8-sig", errors="replace")
                    violations.extend(scan_text(text, f"{path}::{info.filename}"))
                except Exception as exc:
                    violations.append({"archive": path, "item": info.filename, "violation": f"Unreadable item: {exc}"})
    except Exception as exc:
        violations.append({"archive": path, "violation": f"ZIP unreadable: {exc}"})
    return violations

def main():
    parser = argparse.ArgumentParser(description="Validate archive-of-archives lock state")
    parser.add_argument("--index-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.index_json)
    if index is None:
        result = {
            "timestamp": now_iso(),
            "component": "ARCHIVE_OF_ARCHIVES_LOCK_VALIDATOR",
            "status": "BLOCK",
            "message": "Archive-of-archives index missing",
            **CANON
        }
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["message"])
        return EXIT_FILE_ERROR

    violations = []
    checked = 0

    for rec in index.get("records", []):
        checked += 1
        if rec.get("Operational_Handoff_Allowed") != "NO":
            violations.append({"record": rec.get("ArchiveOfArchives_ID"), "violation": "Operational_Handoff_Allowed must be NO"})
        if rec.get("Final_Use_Allowed") != "NO":
            violations.append({"record": rec.get("ArchiveOfArchives_ID"), "violation": "Final_Use_Allowed must be NO"})
        if rec.get("Canonical_Effect") != "NONE":
            violations.append({"record": rec.get("ArchiveOfArchives_ID"), "violation": "Canonical_Effect must be NONE"})
        path = rec.get("Path")
        if not path or not os.path.exists(path):
            violations.append({"record": rec.get("ArchiveOfArchives_ID"), "path": path, "violation": "Archive missing"})
            continue
        violations.extend(scan_zip(path))

    payload = {
        "timestamp": now_iso(),
        "component": "ARCHIVE_OF_ARCHIVES_LOCK_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "archives_checked": checked,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Archive-of-archives validation blocks approval/handoff/final-use signals and grants no authority.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Archive-of-archives violation found" if violations else "✅ Archive-of-archives lock validated"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
