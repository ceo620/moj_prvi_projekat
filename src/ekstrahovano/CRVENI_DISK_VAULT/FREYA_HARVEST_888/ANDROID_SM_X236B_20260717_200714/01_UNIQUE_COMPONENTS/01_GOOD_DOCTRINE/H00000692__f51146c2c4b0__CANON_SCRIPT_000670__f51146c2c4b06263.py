# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 193_final_terminal_hash_ledger.py
# PURPOSE: Generate terminal hash ledger
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


def main():
    parser = argparse.ArgumentParser(description="Generate terminal hash ledger")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.reports_root)
    records = []
    if root.exists():
        for item in root.rglob("*"):
            if item.is_file() and item.suffix.lower() in {".json",".md",".xlsx",".txt",".zip"}:
                records.append({
                    "Record_ID": f"193-{len(records)+1:06d}",
                    "Artifact": item.name,
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Review_Only": "YES",
                    "Operational_Action_Allowed": "NO",
                    "Canonical_Effect": "NONE",
                    "Final_Use_Allowed": "NO"
                })
    ledger_hash = sha256_text("\n".join(f"{r['Record_ID']}|{r['Path']}|{r['SHA256']}" for r in records))
    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_TERMINAL_HASH_LEDGER",
        "version": "1.0",
        "status": "FINAL_TERMINAL_HASH_LEDGER_LOCKED",
        "record_count": len(records),
        "ledger_hash": ledger_hash,
        "records": records,
        "decision": "Generate terminal hash ledger. No authority granted.",
        **CANON
    }
    write_json(args.out_json, payload)
    print_status(payload, args.json)
    return 1 if "LOCKED" in payload["status"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
