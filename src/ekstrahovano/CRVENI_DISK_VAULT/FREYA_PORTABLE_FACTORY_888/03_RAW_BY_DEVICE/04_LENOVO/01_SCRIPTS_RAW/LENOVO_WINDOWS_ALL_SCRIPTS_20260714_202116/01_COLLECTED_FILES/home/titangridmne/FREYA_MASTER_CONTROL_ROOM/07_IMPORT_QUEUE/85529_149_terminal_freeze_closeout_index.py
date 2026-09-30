# ============================================================
# TITAN_KERNEL: 149_terminal_freeze_closeout_index.py
# PURPOSE: Build closeout index for terminal frozen locked state
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

CLOSEOUT_FILES = [
    "terminal_archive_freeze_index.json",
    "terminal_archive_freeze_index.xlsx",
    "terminal_freeze_drift_validation.json",
    "terminal_frozen_locked_receipt.json",
    "terminal_frozen_locked_receipt.md",
    "all_archives_locked_receipt.json",
    "all_archives_locked_receipt.md",
    "handoff_lock_archive_receipt.json",
    "handoff_lock_archive_receipt.md",
    "ultimate_handoff_lock_seal.json",
    "ultimate_handoff_lock_seal.md",
    "final_immutable_ledger.json",
    "final_immutable_ledger.xlsx",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    if not path or not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists() and direct.is_file():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def infer_status(path):
    if path is None or not path.exists():
        return "MISSING"
    if path.suffix.lower() != ".json":
        return "REVIEW_ONLY_ARTIFACT"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN")))
    except Exception:
        return "UNREADABLE"

def write_xlsx(payload, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Freeze Closeout Index"
    headers = ["Closeout_ID", "Artifact", "Path", "Exists", "Status", "SHA256", "Size_Bytes", "Closeout_Treatment", "Canonical_Effect", "Final_Use_Allowed"]
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
    parser = argparse.ArgumentParser(description="Build terminal freeze closeout index")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = []
    for idx, name in enumerate(CLOSEOUT_FILES, start=1):
        p = find_file(args.reports_root, name)
        exists = p is not None and p.exists()
        records.append({
            "Closeout_ID": f"TFCO-{idx:05d}",
            "Artifact": name,
            "Path": str(p) if p else "MISSING",
            "Exists": exists,
            "Status": infer_status(p),
            "SHA256": sha256_file(p),
            "Size_Bytes": p.stat().st_size if exists else 0,
            "Closeout_Treatment": "REVIEW_ONLY_LOCKED",
            "Canonical_Effect": "NONE",
            "Final_Use_Allowed": "NO",
        })

    payload = {
        "timestamp": now_iso(),
        "component": "TERMINAL_FREEZE_CLOSEOUT_INDEX",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "record_count": len(records),
        "missing_count": sum(1 for r in records if not r["Exists"]),
        "records": records,
        "decision": "Terminal freeze closeout index is review-only inventory. It grants no authority.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Terminal freeze closeout index built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
