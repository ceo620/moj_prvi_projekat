# ============================================================
# TITAN_KERNEL: 26_sensitive_data_redaction_scanner.py
# PURPOSE: Scan text-like files for sensitive data patterns and create review report
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_FILE_ERROR = 2
EXIT_WRITE_ERROR = 3

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT_ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

TEXT_EXTS = {".txt", ".md", ".csv", ".json", ".py", ".ps1", ".xml", ".html", ".log"}

PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "PHONE_LIKE": r"(?<!\d)(?:\+?\d[\d\s().\-]{6,}\d)(?!\d)",
    "LONG_NUMBER": r"\b\d{9,}\b",
    "POTENTIAL_IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",
    "POTENTIAL_SECRET": r"(?i)\b(api[_\- ]?key|secret|token|password|passwd)\b\s*[:=]\s*[^\s,;]+"
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def iter_files(root, recursive):
    root = Path(root)
    iterator = root.rglob("*") if recursive else root.glob("*")
    for p in iterator:
        if p.is_file() and p.suffix.lower() in TEXT_EXTS:
            yield p

def safe_read_text(path):
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""

def mask(value):
    value = str(value)
    if len(value) <= 6:
        return "*" * len(value)
    return value[:3] + "***" + value[-3:]

def main():
    parser = argparse.ArgumentParser(description="Scan for sensitive data patterns; report only")
    parser.add_argument("--target", required=True, help="File or folder to scan")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"❌ Target ne postoji: {target}")
        return EXIT_FILE_ERROR

    paths = [target] if target.is_file() else list(iter_files(target, args.recursive))

    findings = []
    scanned = 0

    for path in paths:
        if path.is_file() and path.suffix.lower() not in TEXT_EXTS:
            continue

        scanned += 1
        text = safe_read_text(path)
        for name, pattern in PATTERNS.items():
            for m in re.finditer(pattern, text):
                start = max(0, m.start() - 40)
                end = min(len(text), m.end() + 40)
                findings.append({
                    "file": str(path),
                    "file_sha256": sha256_file(path),
                    "pattern": name,
                    "masked_match": mask(m.group(0)),
                    "line_estimate": text.count("\n", 0, m.start()) + 1,
                    "context_masked": mask(text[start:end].replace("\n", " ")),
                    "action": "REVIEW_REQUIRED",
                    "auto_redacted": False,
                    "final_use_allowed": "NO"
                })

    report = {
        "timestamp": now_iso(),
        "component": "SENSITIVE_DATA_REDACTION_SCANNER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED" if findings else "PASS",
        "scanned_files": scanned,
        "finding_count": len(findings),
        "findings": findings,
        "decision": "Report only. No file was modified or redacted automatically.",
        **CANON
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"✅ Redaction scan complete: {len(findings)} findings")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
