# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 04_ssot_integrity_checker.py
# PURPOSE: Check Monolith/SSoT candidate integrity without writing SSoT
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
EXIT_BLOCK = 1
EXIT_FILE_ERROR = 2
EXIT_SCHEMA_ERROR = 3

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

REQUIRED_FIELDS = ["Lucky_Number"]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def emit_jsonl(path, event):
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def make_event(status, check_id, message, severity="INFO", extra=None):
    event = {
        "timestamp": now_iso(),
        "component": "SSOT_INTEGRITY_CHECKER",
        "version": "1.0",
        "status": status,
        "check_id": check_id,
        "severity": severity,
        "message": message,
        **CANON,
    }
    if extra:
        event.update(extra)
    return event

def main():
    parser = argparse.ArgumentParser(description="TITAN SSoT integrity checker")
    parser.add_argument("--monolith", required=True, help="Path to monolith_registry.json")
    parser.add_argument("--expected-sha256", help="Optional expected SHA-256")
    parser.add_argument("--target-signals", type=int, default=888888)
    parser.add_argument("--report", help="Optional JSONL report path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    events = []
    blocked = False

    if not os.path.exists(args.monolith):
        e = make_event("BLOCK", "SSOT-001", "Monolith/SSoT file missing", "CRITICAL", {"monolith": args.monolith})
        emit_jsonl(args.report, e)
        print(json.dumps(e, ensure_ascii=False) if args.json else e["message"])
        return EXIT_FILE_ERROR

    try:
        digest = sha256_file(args.monolith)
        size = os.path.getsize(args.monolith)
        events.append(make_event("PASS", "SSOT-002", "Monolith file readable and hashed", "HIGH", {
            "monolith": args.monolith,
            "sha256": digest,
            "size_bytes": size
        }))
    except Exception as exc:
        e = make_event("BLOCK", "SSOT-002", f"Monolith hash/read failed: {exc}", "CRITICAL", {"monolith": args.monolith})
        emit_jsonl(args.report, e)
        print(json.dumps(e, ensure_ascii=False) if args.json else e["message"])
        return EXIT_FILE_ERROR

    if args.expected_sha256:
        if digest.lower() == args.expected_sha256.lower():
            events.append(make_event("PASS", "SSOT-003", "SHA-256 matches expected value", "CRITICAL", {"sha256": digest}))
        else:
            blocked = True
            events.append(make_event("BLOCK", "SSOT-003", "SHA-256 mismatch", "CRITICAL", {
                "actual_sha256": digest,
                "expected_sha256": args.expected_sha256
            }))
    else:
        events.append(make_event("REVIEW_REQUIRED", "SSOT-003", "No expected SHA-256 provided; baseline hash captured only", "HIGH", {
            "captured_sha256": digest
        }))

    try:
        data = load_json(args.monolith)
        events.append(make_event("PASS", "SSOT-004", "Monolith JSON parsed with utf-8-sig", "CRITICAL"))
    except Exception as exc:
        blocked = True
        events.append(make_event("BLOCK", "SSOT-004", f"Monolith JSON parse failed: {exc}", "CRITICAL"))

    if not blocked and isinstance(data, dict):
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            blocked = True
            events.append(make_event("BLOCK", "SSOT-005", "Required SSoT fields missing", "CRITICAL", {"missing_fields": missing}))
        else:
            events.append(make_event("PASS", "SSOT-005", "Required SSoT fields present", "CRITICAL", {"required_fields": REQUIRED_FIELDS}))

        lucky = data.get("Lucky_Number")
        if isinstance(lucky, int):
            if lucky == args.target_signals:
                events.append(make_event("PASS", "SSOT-006", "Lucky_Number equals target_signals", "CRITICAL", {
                    "Lucky_Number": lucky,
                    "target_signals": args.target_signals
                }))
            else:
                blocked = True
                events.append(make_event("BLOCK", "SSOT-006", "Lucky_Number does not equal target_signals", "CRITICAL", {
                    "Lucky_Number": lucky,
                    "target_signals": args.target_signals
                }))
        else:
            blocked = True
            events.append(make_event("BLOCK", "SSOT-006", "Lucky_Number is missing or not integer", "CRITICAL", {"Lucky_Number": lucky}))
    elif not blocked:
        blocked = True
        events.append(make_event("BLOCK", "SSOT-007", "Monolith root must be JSON object", "CRITICAL"))

    summary = make_event(
        "BLOCK" if blocked else "REVIEW_REQUIRED",
        "SUMMARY",
        "SSoT integrity check complete. This is not production approval.",
        "CRITICAL",
        {"blocked": blocked}
    )
    events.append(summary)

    for e in events:
        emit_jsonl(args.report, e)

    if args.json:
        print(json.dumps({"events": events}, ensure_ascii=False, indent=2))
    else:
        for e in events:
            print(f"{e['status']} | {e['check_id']} | {e['message']}")
        print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")

    return EXIT_BLOCK if blocked else EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
