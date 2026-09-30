# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 32_installed_package_registry_builder.py
# PURPOSE: Build registry of installed TITAN script packages
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

try:
    import openpyxl
except ImportError:
    openpyxl = None

EXIT_OK = 0
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

SCRIPT_EXTS = {".py", ".ps1"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def detect_version(text):
    for pat in [r"VERSION:\s*([A-Za-z0-9._\-]+)", r"VERSION\s*=\s*[\"']([^\"']+)[\"']", r"version\s*=\s*[\"']([^\"']+)[\"']"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return "UNKNOWN"

def detect_purpose(text):
    m = re.search(r"PURPOSE:\s*(.+)", text)
    return m.group(1).strip() if m else "UNKNOWN"

def classify(path):
    name = path.name.lower()
    if name.endswith(".ps1") or name.startswith("install_"):
        return "INSTALLER"
    if "validator" in name or "checker" in name or "guardian" in name:
        return "CONTROL"
    if "evidence" in name or "filefinding" in name or "review" in name:
        return "EVIDENCE_REVIEW"
    if "dashboard" in name or "report" in name:
        return "REPORTING"
    if "orchestrator" in name:
        return "ORCHESTRATION"
    if "ssot" in name or "manifest" in name or "integrity" in name:
        return "INTEGRITY"
    return "SCRIPT"

def build_registry(scripts_root):
    root = Path(scripts_root)
    rows = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCRIPT_EXTS:
            continue

        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")[:10000]
        except Exception:
            text = ""

        rows.append({
            "Registry_ID": f"PKGREG-{len(rows)+1:04d}",
            "Script_Name": path.name,
            "Path": str(path),
            "SHA256": sha256_file(path),
            "Version": detect_version(text),
            "Purpose": detect_purpose(text),
            "Category": classify(path),
            "Size_Bytes": path.stat().st_size,
            "Modified_UTC": datetime.utcfromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            "Installed_Status": "DISCOVERED",
            "Review_Status": "REVIEW_REQUIRED",
            "Final_Use_Allowed": "NO"
        })

    return rows

def write_xlsx(rows, out_xlsx):
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Installed Registry"
    headers = list(rows[0].keys()) if rows else ["Registry_ID", "Script_Name", "Path", "SHA256", "Version", "Purpose", "Category", "Size_Bytes", "Modified_UTC", "Installed_Status", "Review_Status", "Final_Use_Allowed"]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])

    ws2 = wb.create_sheet("Canonical Locks")
    ws2.append(["Control", "Value"])
    for k, v in CANON.items():
        ws2.append([k, v])

    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)

def main():
    parser = argparse.ArgumentParser(description="TITAN installed package/script registry builder")
    parser.add_argument("--scripts-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-xlsx")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.scripts_root):
        print(f"❌ scripts-root ne postoji: {args.scripts_root}")
        return EXIT_FILE_ERROR

    try:
        rows = build_registry(args.scripts_root)
        payload = {
            "timestamp": now_iso(),
            "component": "INSTALLED_PACKAGE_REGISTRY_BUILDER",
            "version": "1.0",
            "status": "REVIEW_REQUIRED",
            "record_count": len(rows),
            "records": rows,
            "decision": "Registry is discovery/audit only; not canonical SSoT write.",
            **CANON
        }

        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        if args.out_xlsx:
            write_xlsx(rows, args.out_xlsx)

    except Exception as exc:
        print(f"❌ Write/build error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Installed registry built: {len(rows)} scripts")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
