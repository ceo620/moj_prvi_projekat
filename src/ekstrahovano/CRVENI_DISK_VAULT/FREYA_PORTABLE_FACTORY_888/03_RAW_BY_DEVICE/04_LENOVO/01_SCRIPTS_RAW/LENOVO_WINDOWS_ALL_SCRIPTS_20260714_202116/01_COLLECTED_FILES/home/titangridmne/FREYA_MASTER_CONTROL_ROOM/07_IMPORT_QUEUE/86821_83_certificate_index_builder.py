# ============================================================
# TITAN_KERNEL: 83_certificate_index_builder.py
# PURPOSE: Index locked/no-release certificates and related memoranda
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

CERT_NAMES = [
    "final_locked_state_certificate.json",
    "final_locked_state_certificate.md",
    "no_release_memorandum.json",
    "no_release_memorandum.md",
    "decision_ledger.json",
    "board_decision_validation.json",
    "release_readiness.json",
    "preproduction_freeze_denied.json",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    if not path.exists() or not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def find_file(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def infer_status(path):
    if not path or not path.exists() or path.suffix.lower() != ".json":
        return "REVIEW_REQUIRED"
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
    ws.title = "Certificate Index"
    headers = ["Certificate_ID", "Name", "Path", "Exists", "SHA256", "Size_Bytes", "Inferred_Status", "Review_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in payload["certificates"]:
        ws.append([row.get(h, "") for h in headers])
    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])
    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="Build TITAN certificate index")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    certs = []
    for idx, name in enumerate(CERT_NAMES, start=1):
        p = find_file(args.reports_root, name)
        exists = p is not None and p.exists()
        certs.append({
            "Certificate_ID": f"CERT-{idx:05d}",
            "Name": name,
            "Path": str(p) if p else "MISSING",
            "Exists": exists,
            "SHA256": sha256_file(p) if p else "MISSING",
            "Size_Bytes": p.stat().st_size if exists else 0,
            "Inferred_Status": infer_status(p) if p else "MISSING",
            "Review_Status": "REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO"
        })

    payload = {
        "timestamp": now_iso(),
        "component": "CERTIFICATE_INDEX_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "certificate_count": len(certs),
        "missing_count": sum(1 for c in certs if not c["Exists"]),
        "certificates": certs,
        "decision": "Certificate index is audit inventory only.",
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

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "✅ Certificate index built")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
