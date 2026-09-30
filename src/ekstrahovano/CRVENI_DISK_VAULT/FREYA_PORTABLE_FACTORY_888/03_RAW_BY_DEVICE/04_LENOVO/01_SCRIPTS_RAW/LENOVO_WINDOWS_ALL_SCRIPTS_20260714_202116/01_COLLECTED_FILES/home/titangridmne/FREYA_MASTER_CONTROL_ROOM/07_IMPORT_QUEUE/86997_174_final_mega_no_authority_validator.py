# ============================================================
# TITAN_KERNEL: 174_final_mega_no_authority_validator.py
# PURPOSE: Validate mega-index contains no authority/final-use signals
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "RISK_BASELINE": 890,
    "P0_GATES": "10/10 BLOCKED",
    "EVIDENCE_GAPS_REMAINING": 6,
    "EVIDENCE_APPROVED": 0,
    "GATES_CLOSED": 0,
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def sha256_file(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_json(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def write_md(path, title, payload, statement):
    lines = [
        f"# {title}",
        "",
        f"Generated At: {payload.get('timestamp', now_iso())}",
        "",
        "## Status",
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Statement",
        "",
        statement,
        "",
        "## Canonical Controls",
        "",
    ]
    for k in ["SYSTEM_STATUS","RISK_BASELINE","P0_GATES","EVIDENCE_GAPS_REMAINING","EVIDENCE_APPROVED","GATES_CLOSED","STEP102","FINAL_USE_ALLOWED","SSOT_WRITE_ALLOWED","EVIDENCE_APPROVAL_ALLOWED","GATE_CLOSURE_ALLOWED"]:
        if k in payload:
            lines.append(f"- `{k}` = `{payload[k]}`")
    lines += ["", "SYSTEM RED — STEP102 LOCKED — NO FINAL USE"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    if root.exists():
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    return None

def iter_files(roots, exts=None):
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and (exts is None or item.suffix.lower() in exts):
                yield item

def print_status(payload, as_json=False):
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("status", "REVIEW_REQUIRED"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")


FORBIDDEN = [
    ("FINAL_USE_ALLOWED_YES", r"FINAL_USE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("OPERATIONAL_ACTION_YES", r"OPERATIONAL_ACTION_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("STEP102_ACCEPTED", r"STEP102\s*[:=]\s*(ACCEPTED|APPROVED|UNLOCKED)"),
    ("SSOT_WRITE_YES", r"SSOT_WRITE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("GATE_CLOSURE_YES", r"GATE_CLOSURE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("EVIDENCE_APPROVAL_YES", r"EVIDENCE_APPROVAL_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("APPROVAL_TEXT", r"\b(release approved|production approved|final use approved|evidence approved|gate closed|handoff authorized)\b"),
    ("SYSTEM_GREEN", r"\bSYSTEM\s+(GREEN|GOLDEN|APPROVED|PRODUCTION)\b"),
]
TEXT_EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".puml", ".ps1", ".py"}

def scan_text(text, context):
    hits = []
    for pid, pat in FORBIDDEN:
        for m in re.finditer(pat, text, re.IGNORECASE):
            hits.append({"context": context, "pattern": pid, "match": m.group(0)[:200], "violation": "Forbidden authority signal"})
    return hits

def scan_path(path):
    path = Path(path)
    hits = []
    if not path.exists():
        return [{"context": str(path), "violation": "Indexed artifact missing"}]
    if path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path, "r") as z:
                bad = z.testzip()
                if bad:
                    hits.append({"context": str(path), "violation": f"Bad zip member: {bad}"})
                for info in z.infolist():
                    if info.is_dir() or Path(info.filename).suffix.lower() not in TEXT_EXTS:
                        continue
                    text = z.read(info.filename).decode("utf-8-sig", errors="replace")
                    hits.extend(scan_text(text, f"{path}::{info.filename}"))
        except Exception as exc:
            hits.append({"context": str(path), "violation": f"Unreadable zip: {exc}"})
    elif path.suffix.lower() in TEXT_EXTS:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        hits.extend(scan_text(text, str(path)))
    return hits

def main():
    parser = argparse.ArgumentParser(description="Validate final mega terminal no-authority state")
    parser.add_argument("--mega-index", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = load_json(args.mega_index)
    if index is None:
        payload = {"timestamp": now_iso(), "component": "FINAL_MEGA_NO_AUTHORITY_VALIDATOR", "status": "BLOCK", "message": "Mega index missing", **CANON}
        write_json(args.out_json, payload)
        print_status(payload, args.json)
        return 2

    violations = []
    scanned = 0
    for rec in index.get("records", []):
        for field, expected in [("Review_Only","YES"),("Operational_Action_Allowed","NO"),("Canonical_Effect","NONE"),("Final_Use_Allowed","NO")]:
            if rec.get(field) != expected:
                violations.append({"record": rec.get("Mega_Index_ID"), "field": field, "expected": expected, "actual": rec.get(field)})
        path = rec.get("Path")
        scanned += 1
        violations.extend(scan_path(path))

    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_MEGA_NO_AUTHORITY_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "records_checked": len(index.get("records", [])),
        "artifacts_scanned": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Validator blocks authority/final-use signals. It grants no authority.",
        **CANON
    }
    write_json(args.out_json, payload)
    print_status(payload, args.json)
    return 1 if violations else 0

if __name__ == "__main__":
    raise SystemExit(main())
