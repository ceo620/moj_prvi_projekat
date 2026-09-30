# ============================================================
# TITAN_KERNEL: 93_state_snapshot_diff.py
# PURPOSE: Diff two pipeline state snapshots and flag unsafe changes
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
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

DANGEROUS_FIELDS = [
    "SYSTEM_STATUS",
    "STEP102",
    "FINAL_USE_ALLOWED",
    "SSOT_WRITE_ALLOWED",
    "EVIDENCE_APPROVAL_ALLOWED",
    "GATE_CLOSURE_ALLOWED",
    "release_status",
    "freeze_status",
    "state",
    "status",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}[{i}]"
            out.update(flatten(v, key))
    else:
        out[prefix] = obj
    return out

def is_dangerous(path, old, new):
    leaf = path.split(".")[-1]
    if leaf not in DANGEROUS_FIELDS:
        return False
    if str(new).upper() in {"YES", "READY", "APPROVED", "RELEASED", "UNLOCKED", "ACCEPTED", "FREEZE_ALLOWED", "SYSTEM GREEN"}:
        return True
    if leaf in CANON and new != CANON[leaf]:
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Diff TITAN state snapshots")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline = load_json(args.baseline)
    current = load_json(args.current)
    if baseline is None or current is None:
        print("❌ Missing baseline or current JSON")
        return EXIT_FILE_ERROR

    b = flatten(baseline)
    c = flatten(current)
    keys = sorted(set(b.keys()) | set(c.keys()))
    diffs = []
    unsafe = []

    for key in keys:
        if b.get(key) != c.get(key):
            rec = {
                "path": key,
                "baseline": b.get(key),
                "current": c.get(key),
                "unsafe": is_dangerous(key, b.get(key), c.get(key))
            }
            diffs.append(rec)
            if rec["unsafe"]:
                unsafe.append(rec)

    payload = {
        "timestamp": now_iso(),
        "component": "STATE_SNAPSHOT_DIFF",
        "version": "1.0",
        "status": "BLOCK" if unsafe else "REVIEW_REQUIRED",
        "diff_count": len(diffs),
        "unsafe_diff_count": len(unsafe),
        "diffs": diffs,
        "unsafe_diffs": unsafe,
        "decision": "Snapshot diff is audit-only. Unsafe changes remain blocked.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Unsafe state diff" if unsafe else "✅ State diff reviewed"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if unsafe else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
