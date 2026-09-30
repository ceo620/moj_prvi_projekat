# ============================================================
# TITAN_KERNEL: 112_review_only_proof_generator.py
# PURPOSE: Generate proof that system remains review/audit-only
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

EXIT_LOCKED = 1
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

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def summarize(path):
    if not path or not os.path.exists(path):
        return {"path": path, "exists": False, "status": "MISSING"}
    try:
        if path.lower().endswith(".json"):
            data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            return {
                "path": path,
                "exists": True,
                "status": data.get("status", data.get("release_status", data.get("freeze_status", "UNKNOWN"))),
                "component": data.get("component", "UNKNOWN")
            }
    except Exception as exc:
        return {"path": path, "exists": True, "status": "UNREADABLE", "error": str(exc)}
    return {"path": path, "exists": True, "status": "REVIEW_REQUIRED"}

def main():
    parser = argparse.ArgumentParser(description="Generate review-only proof")
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    artifact_summaries = [summarize(p) for p in args.artifacts]

    payload = {
        "timestamp": now_iso(),
        "component": "REVIEW_ONLY_PROOF_GENERATOR",
        "version": "1.0",
        "status": "REVIEW_ONLY_PROOF_LOCKED",
        "artifact_count": len(artifact_summaries),
        "artifacts": artifact_summaries,
        "proof_statement": "System artifacts are restricted to review/audit-only use under SYSTEM RED.",
        "decision": "Proof document does not approve final use or production execution.",
        **CANON
    }

    payload["proof_hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    md = [
        "# TITAN Review-Only Proof",
        "",
        f"Generated At: {payload['timestamp']}",
        "",
        "## Proof Statement",
        "",
        payload["proof_statement"],
        "",
        "```text",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "```",
        "",
        "## Artifacts",
        "",
        "| Artifact | Exists | Status | Component |",
        "|---|---:|---|---|",
    ]

    for a in artifact_summaries:
        md.append(f"| `{a.get('path')}` | {a.get('exists')} | {a.get('status')} | {a.get('component','UNKNOWN')} |")

    md.extend([
        "",
        "## Proof Hash",
        "",
        f"`{payload['proof_hash']}`",
        "",
        "No production execution. No final use. No evidence approval. No gate closure. No SSoT write. No STEP102 unlock.",
        "",
        "SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
    ])

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(md), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "🔒 Review-only proof generated")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_LOCKED

if __name__ == "__main__":
    sys.exit(main())
