# ============================================================
# TITAN_KERNEL: 100_post_orchestration_denial_receipt.py
# PURPOSE: Generate final receipt proving orchestration remained denied/locked
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

EXIT_DENIED = 1
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

def summarize(path):
    if not path or not os.path.exists(path):
        return {"path": path, "exists": False, "sha256": "MISSING", "status": "MISSING"}
    rec = {"path": path, "exists": True, "sha256": sha256_file(path), "status": "UNKNOWN"}
    if path.lower().endswith(".json"):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            rec["status"] = data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN")))
            rec["component"] = data.get("component", "UNKNOWN")
        except Exception as exc:
            rec["status"] = "UNREADABLE"
            rec["error"] = str(exc)
    return rec

def main():
    parser = argparse.ArgumentParser(description="Generate post-orchestration denial receipt")
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = [summarize(p) for p in args.artifacts]

    receipt = {
        "timestamp": now_iso(),
        "component": "POST_ORCHESTRATION_DENIAL_RECEIPT",
        "version": "1.0",
        "status": "ORCHESTRATION_DENIED",
        "artifact_count": len(records),
        "artifacts": records,
        "final_decision": "NO RELEASE / NO FINAL USE / ORCHESTRATION LOCKED",
        "decision": "This is final denial receipt. It grants no approval and confirms lock state.",
        **CANON
    }

    md = [
        "# TITAN Post-Orchestration Denial Receipt",
        "",
        f"Generated At: {receipt['timestamp']}",
        "",
        "## Final Decision",
        "",
        "```text",
        "NO RELEASE / NO FINAL USE / ORCHESTRATION LOCKED",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Artifact Summary",
        "",
        "| Artifact | Exists | Status | SHA256 |",
        "|---|---:|---|---|",
    ]

    for r in records:
        md.append(f"| `{r.get('path')}` | {r.get('exists')} | {r.get('status')} | `{r.get('sha256')}` |")

    md.extend([
        "",
        "## Canonical Controls",
        "",
    ])
    for k, v in CANON.items():
        md.append(f"- `{k}` = `{v}`")

    md.extend([
        "",
        "This receipt does not approve evidence, close gates, write canonical SSoT, unlock STEP102, or allow final use.",
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(receipt, ensure_ascii=False, indent=2) if args.json else "⛔ Post-orchestration denial receipt generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_DENIED

if __name__ == "__main__":
    sys.exit(main())
