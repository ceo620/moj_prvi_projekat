# ============================================================
# TITAN_KERNEL: 137_ultimate_handoff_denial_index.py
# PURPOSE: Build ultimate index of all handoff-denial evidence artifacts
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

KEYWORDS = [
    "handoff",
    "operational_transfer",
    "review_only",
    "do_not_run",
    "no_operational",
    "denial",
    "locked",
    "nonacceptance",
    "nothing_accepted",
    "final_master_seal",
    "immutable_ledger",
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
    n = path.name.lower()
    return path.suffix.lower() in EXTS and any(k in n for k in KEYWORDS)

def classify(path):
    n = path.name.lower()
    if "handoff_denial" in n:
        return "HANDOFF_DENIAL"
    if "handoff_boundary" in n:
        return "HANDOFF_BOUNDARY"
    if "no_operational" in n:
        return "NO_OPERATIONAL_HANDOFF"
    if "operational_transfer" in n:
        return "TRANSFER_VALIDATION"
    if "do_not_run" in n:
        return "DO_NOT_RUN"
    if "review_only" in n:
        return "REVIEW_ONLY"
    if "nonacceptance" in n or "nothing_accepted" in n:
        return "NONACCEPTANCE"
    return "HANDOFF_LOCK_EVIDENCE"

def collect(roots):
    records = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and include(item):
                records.append({
                    "Handoff_Evidence_ID": f"HOFF-{len(records)+1:05d}",
                    "Artifact_Name": item.name,
                    "Artifact_Type": classify(item),
                    "Path": str(item),
                    "SHA256": sha256_file(item),
                    "Size_Bytes": item.stat().st_size,
                    "Modified_UTC": datetime.utcfromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                    "Handoff_Allowed": "NO",
                    "Operational_Transfer_Allowed": "NO",
                    "Canonical_Effect": "NONE",
                    "Final_Use_Allowed": "NO",
                })
    return records

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ultimate Handoff Index"
    headers = ["Handoff_Evidence_ID", "Artifact_Name", "Artifact_Type", "Path", "SHA256", "Size_Bytes", "Modified_UTC", "Handoff_Allowed", "Operational_Transfer_Allowed", "Canonical_Effect", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="Build ultimate handoff denial index")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = collect(args.roots)

    payload = {
        "timestamp": now_iso(),
        "component": "ULTIMATE_HANDOFF_DENIAL_INDEX",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "records": records,
        "decision": "Ultimate handoff denial index is audit inventory only. It grants no handoff or final use.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Ultimate handoff denial index built: {len(records)} records")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
