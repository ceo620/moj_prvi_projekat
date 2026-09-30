# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 125_final_master_index_builder.py
# PURPOSE: Build final master index of terminal locked artifacts, archives and memoranda
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import hashlib
import json
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

EXTS = {".json", ".jsonl", ".xlsx", ".txt", ".md", ".zip", ".puml"}

TERMINAL_KEYWORDS = [
    "final",
    "locked",
    "no_release",
    "denial",
    "nonacceptance",
    "nothing_accepted",
    "readonly",
    "read_only",
    "do_not_run",
    "warning",
    "closure",
    "closeout",
    "chain_complete",
    "reconciliation",
    "blocked",
    "certificate",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def include(path):
    name = path.name.lower()
    return path.suffix.lower() in EXTS and any(k in name for k in TERMINAL_KEYWORDS)

def classify(path):
    n = path.name.lower()
    if n.endswith(".zip"):
        return "ARCHIVE"
    if "memorandum" in n or "memo" in n:
        return "MEMORANDUM"
    if "certificate" in n:
        return "CERTIFICATE"
    if "index" in n or "register" in n:
        return "INDEX_REGISTER"
    if "validation" in n or "validator" in n:
        return "VALIDATION"
    if "notice" in n or "warning" in n:
        return "NOTICE_WARNING"
    if "summary" in n:
        return "SUMMARY"
    return "LOCKED_ARTIFACT"

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
                    "Master_Index_ID": f"MIDX-{len(rows)+1:05d}",
                    "Artifact_Name": item.name,
                    "Artifact_Class": classify(item),
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Canonical_Effect": "NONE",
                    "Review_Status": "REVIEW_REQUIRED",
                    "Final_Use_Allowed": "NO",
                })
    return rows

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Final Master Index"
    headers = ["Master_Index_ID", "Artifact_Name", "Artifact_Class", "Path", "SHA256", "Size_Bytes", "Modified_UTC", "Canonical_Effect", "Review_Status", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="Build final master index of terminal locked artifacts")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = collect(args.roots)

    payload = {
        "timestamp": now_iso(),
        "component": "FINAL_MASTER_INDEX_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "records": records,
        "decision": "Final master index is read-only inventory. It does not approve or unlock anything.",
        **CANON,
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.out_xlsx:
            write_xlsx(payload, args.out_xlsx)
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Final master index built: {len(records)} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
