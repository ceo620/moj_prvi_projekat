# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 27_retention_policy_checker.py
# PURPOSE: Check artifact age and retention policy without deleting files
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_FILE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def age_days(path):
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - mtime).days

def iter_files(root, recursive):
    root = Path(root)
    iterator = root.rglob("*") if recursive else root.glob("*")
    for p in iterator:
        if p.is_file():
            yield p

def main():
    parser = argparse.ArgumentParser(description="Check retention policy; no deletion")
    parser.add_argument("--target", required=True)
    parser.add_argument("--max-age-days", type=int, default=365)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"❌ Target ne postoji: {target}")
        return EXIT_FILE_ERROR

    paths = [target] if target.is_file() else list(iter_files(target, args.recursive))

    records = []
    review_required = 0

    for path in paths:
        days = age_days(path)
        status = "REVIEW_REQUIRED" if days > args.max_age_days else "WITHIN_RETENTION_WINDOW"
        if status == "REVIEW_REQUIRED":
            review_required += 1

        records.append({
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "modified_utc": datetime.utcfromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            "age_days": days,
            "max_age_days": args.max_age_days,
            "retention_status": status,
            "recommended_action": "MANUAL_REVIEW_ONLY",
            "auto_deleted": False,
            "final_use_allowed": "NO"
        })

    report = {
        "timestamp": now_iso(),
        "component": "RETENTION_POLICY_CHECKER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED" if review_required else "PASS",
        "checked_files": len(records),
        "review_required_count": review_required,
        "records": records,
        "decision": "No file was deleted. This is a retention review report only.",
        **CANON
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"✅ Retention report written: {args.out_json}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
