# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 36_execution_receipt_generator.py
# PURPOSE: Generate execution receipt from key reports without approving use
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    if not os.path.exists(path) or not os.path.isfile(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def summarize_json(path):
    if not os.path.exists(path):
        return {"exists": False, "sha256": "MISSING"}
    rec = {"exists": True, "sha256": sha256_file(path), "path": path}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        for key in ["status", "release_status", "freeze_status", "component", "timestamp"]:
            if isinstance(data, dict) and key in data:
                rec[key] = data[key]
    except Exception as exc:
        rec["parse_error"] = str(exc)
    return rec

def summarize_jsonl(path):
    if not os.path.exists(path):
        return {"exists": False, "sha256": "MISSING", "events": 0, "block_events": 0}
    events = 0
    blocks = 0
    invalid = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events += 1
            try:
                obj = json.loads(line)
                if obj.get("status") == "BLOCK":
                    blocks += 1
            except json.JSONDecodeError:
                invalid += 1
    return {"exists": True, "sha256": sha256_file(path), "path": path, "events": events, "block_events": blocks, "invalid_json": invalid}

def main():
    parser = argparse.ArgumentParser(description="TITAN execution receipt generator")
    parser.add_argument("--json-reports", nargs="*", default=[])
    parser.add_argument("--jsonl-reports", nargs="*", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-txt", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    receipt = {
        "timestamp": now_iso(),
        "component": "EXECUTION_RECEIPT_GENERATOR",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "json_reports": [summarize_json(p) for p in args.json_reports],
        "jsonl_reports": [summarize_jsonl(p) for p in args.jsonl_reports],
        "decision": "Receipt is evidence of attempted/recorded execution only. It is not approval.",
        **CANON,
    }

    lines = [
        "TITAN EXECUTION RECEIPT",
        f"Generated_At: {receipt['timestamp']}",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "JSON Reports:"
    ]

    for r in receipt["json_reports"]:
        lines.append(f"- {r.get('path','UNKNOWN')} | exists={r.get('exists')} | status={r.get('status', r.get('release_status', r.get('freeze_status','UNKNOWN')))} | sha256={r.get('sha256')}")

    lines.append("")
    lines.append("JSONL Reports:")
    for r in receipt["jsonl_reports"]:
        lines.append(f"- {r.get('path','UNKNOWN')} | exists={r.get('exists')} | events={r.get('events')} | blocks={r.get('block_events')} | sha256={r.get('sha256')}")

    lines.append("")
    lines.append("Canonical Locks:")
    for k, v in CANON.items():
        lines.append(f"- {k} = {v}")

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_txt).write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(receipt, ensure_ascii=False, indent=2) if args.json else f"✅ Execution receipt: {args.out_txt}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
