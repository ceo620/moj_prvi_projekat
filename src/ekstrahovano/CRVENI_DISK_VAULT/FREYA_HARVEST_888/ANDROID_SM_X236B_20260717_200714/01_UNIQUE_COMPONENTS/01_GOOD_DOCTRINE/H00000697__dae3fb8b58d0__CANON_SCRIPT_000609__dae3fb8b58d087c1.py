# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 116_locked_chain_artifact_index.py
# PURPOSE: Index final locked-chain artifacts across reports and archives
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
except ImportError:
    openpyxl = None

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

EXTS = {".json", ".jsonl", ".xlsx", ".txt", ".md", ".zip", ".puml"}

LOCKED_KEYWORDS = [
    "locked",
    "no_release",
    "denial",
    "do_not_run",
    "readonly",
    "read_only",
    "final_warning",
    "closure",
    "chain_complete",
    "blocked",
    "red_team",
    "emergency_stop",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(name):
    n = name.lower()
    if "certificate" in n:
        return "LOCKED_CERTIFICATE"
    if "denial" in n or "no_release" in n:
        return "DENIAL"
    if "readonly" in n or "read_only" in n:
        return "READONLY_PROOF"
    if "do_not_run" in n:
        return "DO_NOT_RUN"
    if "closure" in n or "closeout" in n:
        return "CLOSURE"
    if "blocked" in n:
        return "BLOCKED_OPERATION"
    if "warning" in n:
        return "WARNING"
    if "chain_complete" in n:
        return "CHAIN_COMPLETE_LOCKED"
    return "LOCKED_CHAIN_ARTIFACT"

def include(path):
    n = path.name.lower()
    return path.suffix.lower() in EXTS and any(k in n for k in LOCKED_KEYWORDS)

def collect(roots):
    rows = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and include(item):
                rows.append({
                    "Locked_Artifact_ID": f"LCK-{len(rows)+1:05d}",
                    "Artifact_Name": item.name,
                    "Artifact_Type": classify(item.name),
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Canonical_Effect": "NONE",
                    "Review_Status": "REVIEW_REQUIRED",
                    "Final_Use_Allowed": "NO"
                })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Locked Chain Index"
    headers = ["Locked_Artifact_ID", "Artifact_Name", "Artifact_Type", "Path", "SHA256", "Size_Bytes", "Modified_UTC", "Canonical_Effect", "Review_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["records"]:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build locked chain artifact index")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = collect(args.roots)

    payload = {
        "timestamp": now_iso(),
        "component": "LOCKED_CHAIN_ARTIFACT_INDEX",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "records": records,
        "decision": "Locked-chain index is inventory only. It does not approve or unlock anything.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Locked-chain index built: {len(records)} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
