# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ============================================================
# TITAN_KERNEL: 39_next_action_recommender.py
# PURPOSE: Recommend safe next actions from status snapshot without approving anything
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

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="TITAN safe next action recommender")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.snapshot):
        print(f"❌ Snapshot ne postoji: {args.snapshot}")
        return EXIT_FILE_ERROR

    snapshot = load_json(args.snapshot)

    recommendations = []

    release = snapshot.get("release_readiness") or {}
    freeze = snapshot.get("freeze_report") or {}
    control_counts = (snapshot.get("control_report_counts") or {}).get("counts", {})
    audit_counts = (snapshot.get("audit_timeline_counts") or {}).get("counts", {})

    if release.get("release_status") != "READY":
        recommendations.append({
            "Priority": "P0",
            "Action": "Keep release blocked",
            "Reason": "Release readiness is not READY under active canon",
            "Script": "48_release_readiness_checker.py"
        })

    if freeze.get("freeze_status") != "FREEZE_ALLOWED":
        recommendations.append({
            "Priority": "P0",
            "Action": "Keep preproduction freeze denied",
            "Reason": "Freeze report is not FREEZE_ALLOWED and STEP102 is locked",
            "Script": "97_preproduction_freeze.py"
        })

    if control_counts.get("BLOCK", 0) > 0 or audit_counts.get("BLOCK", 0) > 0:
        recommendations.append({
            "Priority": "P0",
            "Action": "Review BLOCK events",
            "Reason": "Validation/audit logs contain BLOCK events",
            "Script": "91_incident_reporter.py"
        })

    recommendations.extend([
        {
            "Priority": "P1",
            "Action": "Update FileFinding Register with real Evidence_ID and Reviewer",
            "Reason": "AI/evidence signals require FileFinding_ID + Evidence_ID + Reviewer before weight can be non-zero",
            "Script": "15_filefinding_register_builder.py / 18_filefinding_evidence_weight_calculator.py"
        },
        {
            "Priority": "P1",
            "Action": "Rebuild manual review queue",
            "Reason": "Reviewer-facing queue must reflect latest evidence bundle and gap candidate status",
            "Script": "21_manual_review_queue_builder.py"
        },
        {
            "Priority": "P2",
            "Action": "Regenerate dashboard and operator snapshot",
            "Reason": "Operator view must reflect newest reports",
            "Script": "47_control_tower_dashboard_exporter.py / 38_operator_status_snapshot.py"
        }
    ])

    payload = {
        "timestamp": now_iso(),
        "component": "NEXT_ACTION_RECOMMENDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "recommendations": recommendations,
        "decision": "Recommendations are safe next actions only. They are not approvals.",
        **CANON
    }

    lines = [
        "# TITAN Safe Next Actions",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "| Priority | Action | Reason | Script |",
        "|---|---|---|---|"
    ]

    for r in recommendations:
        lines.append(f"| {r['Priority']} | {r['Action']} | {r['Reason']} | `{r['Script']}` |")

    lines.append("")
    lines.append("No recommendation approves evidence, closes gates, writes canonical SSoT, unlocks STEP102, or allows final use.")

    try:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Next actions: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
