# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 135_operational_transfer_signal_validator.py
# PURPOSE: Validate artifacts contain no operational handoff/transfer authorization
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 1
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

FORBIDDEN = [
    ("OPERATIONAL_HANDOFF_ALLOWED", r"\b(operational handoff authorized|operational handoff allowed|handoff approved)\b"),
    ("TRANSFER_TO_PRODUCTION", r"\b(transfer to production|production handoff|ops handoff approved)\b"),
    ("FINAL_USE_HANDOFF", r"\b(final use handoff|handoff for final use)\b"),
    ("DEPLOYMENT_AUTHORIZED", r"\b(deployment authorized|release handoff approved)\b"),
    ("HANDOFF_ALLOWED_YES", r"HANDOFF_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
    ("FINAL_USE_ALLOWED_YES", r"FINAL_USE_ALLOWED\s*[:=]\s*(YES|TRUE|1)"),
]

TEXT_EXTS = {".json", ".jsonl", ".txt", ".md", ".csv", ".ps1", ".py"}

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def iter_files(roots):
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        iterator = [p] if p.is_file() else p.rglob("*")
        for item in iterator:
            if item.is_file() and item.suffix.lower() in TEXT_EXTS:
                yield item

def scan(path):
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        return [{"path": str(path), "pattern": "UNREADABLE", "line": 0, "match": str(exc)}]

    hits = []
    for pid, pat in FORBIDDEN:
        for m in re.finditer(pat, text, re.IGNORECASE):
            hits.append({
                "path": str(path),
                "pattern": pid,
                "line": text.count("\n", 0, m.start()) + 1,
                "match": m.group(0)[:200],
                "violation": "Forbidden operational transfer/handoff signal"
            })
    return hits

def main():
    parser = argparse.ArgumentParser(description="Validate no operational transfer signal exists")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    violations = []
    scanned = 0

    for path in iter_files(args.roots):
        scanned += 1
        violations.extend(scan(path))

    payload = {
        "timestamp": now_iso(),
        "component": "OPERATIONAL_TRANSFER_SIGNAL_VALIDATOR",
        "version": "1.0",
        "status": "BLOCK" if violations else "REVIEW_REQUIRED",
        "files_scanned": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "decision": "Operational transfer signals are blocked. Validator grants no handoff.",
        **CANON
    }

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else ("⛔ Operational handoff signal found" if violations else "✅ No operational transfer signal detected"))
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_BLOCK if violations else EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
