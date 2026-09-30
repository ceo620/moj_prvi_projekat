#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
31_ssot_alignment_validator.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 31 — SSOT Alignment Validator
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Validate whether the operational TITAN RAG / release chain complies with the
TITAN MASTER SSOT v1.0 governance architecture.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT approve lender export.
It validates alignment against locked SSOT principles:
- Evidence precedes intelligence
- Retrieval precedes generation
- Audit precedes decision
- Freeze precedes distribution
- Gatekeeping precedes external release
- Receipt register follows transmission
- Export requires snapshot / submission / approval / authorized role
- Decision statuses must align with READY / CONDITIONAL / NOT READY / BLOCK logic

Inputs
------
05_reports/post_release_audit/TITAN_POST_RELEASE_AUDIT_REGISTER.json
05_reports/external_release_package/TITAN_EXTERNAL_RELEASE_MANIFEST.json
05_reports/distribution_readiness/TITAN_DISTRIBUTION_READINESS_DECISION.json
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/latest_audit_record.json
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json
05_reports/risk_signals_report.json
05_reports/document_priority_rank.json

Outputs
-------
05_reports/ssot_alignment/TITAN_SSOT_ALIGNMENT_REPORT.md
05_reports/ssot_alignment/TITAN_SSOT_ALIGNMENT_REPORT.json
05_reports/ssot_alignment/TITAN_SSOT_ALIGNMENT_CHECKLIST.csv
05_reports/ssot_alignment/TITAN_SSOT_DEVIATION_REGISTER.csv
05_reports/ssot_alignment/TITAN_SSOT_CORRECTIVE_ACTION_REGISTER.csv
05_reports/ssot_alignment/TITAN_SSOT_ALIGNMENT_MANIFEST.json
06_logs/ssot_alignment_validator_audit.jsonl
06_logs/ssot_alignment_validator_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\31_ssot_alignment_validator.py" --print

Strict SSOT mode
----------------
python ".\\08_scripts\\31_ssot_alignment_validator.py" --strict --print

Export-intent validation
------------------------
python ".\\08_scripts\\31_ssot_alignment_validator.py" --export-intent --role CFO --print
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "31_ssot_alignment_validator.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "ssot_alignment"

OUTPUT_REPORT_MD = "TITAN_SSOT_ALIGNMENT_REPORT.md"
OUTPUT_REPORT_JSON = "TITAN_SSOT_ALIGNMENT_REPORT.json"
OUTPUT_CHECKLIST_CSV = "TITAN_SSOT_ALIGNMENT_CHECKLIST.csv"
OUTPUT_DEVIATION_CSV = "TITAN_SSOT_DEVIATION_REGISTER.csv"
OUTPUT_CORRECTIVE_CSV = "TITAN_SSOT_CORRECTIVE_ACTION_REGISTER.csv"
OUTPUT_MANIFEST_JSON = "TITAN_SSOT_ALIGNMENT_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "ssot_alignment_validator_audit.jsonl"
ERROR_LOG = Path("06_logs") / "ssot_alignment_validator_errors.jsonl"

ALIGNMENT_ALIGNED = "SSOT_ALIGNED"
ALIGNMENT_CONDITIONAL = "SSOT_CONDITIONAL_ALIGNMENT"
ALIGNMENT_NOT_READY = "SSOT_NOT_READY"
ALIGNMENT_BLOCKED = "SSOT_BLOCKED"
ALIGNMENT_INCOMPLETE = "SSOT_INCOMPLETE"

CHECK_PASS = "PASS"
CHECK_WARNING = "WARNING"
CHECK_FAIL = "FAIL"
CHECK_MISSING = "MISSING"

DEV_CRITICAL = "CRITICAL_DEVIATION"
DEV_HIGH = "HIGH_DEVIATION"
DEV_MEDIUM = "MEDIUM_DEVIATION"
DEV_LOW = "LOW_DEVIATION"

SOURCE_JSON_FILES = {
    "post_release_audit": Path("05_reports") / "post_release_audit" / "TITAN_POST_RELEASE_AUDIT_REGISTER.json",
    "external_release": Path("05_reports") / "external_release_package" / "TITAN_EXTERNAL_RELEASE_MANIFEST.json",
    "distribution_readiness": Path("05_reports") / "distribution_readiness" / "TITAN_DISTRIBUTION_READINESS_DECISION.json",
    "freeze_manifest": Path("05_reports") / "investor_data_room_freeze" / "TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json",
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "lender_dd": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "legal_compliance": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "esg_permitting": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.json",
    "capex_bankability": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_rag_answer": Path("05_reports") / "latest_rag_answer.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "ssot_candidates": Path("05_reports") / "ssot_candidates_report.json",
}

SSOT_RULES = [
    {
        "Rule_ID": "SSOT-001",
        "Area": "Evidence before intelligence",
        "Rule": "A latest evidence pack must exist before answer/report/release reliance.",
        "Source": "latest_evidence_pack",
        "Field": "evidence_count",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
        "Corrective_Action": "Run Step 06 and Step 12 before answer/report/release use.",
    },
    {
        "Rule_ID": "SSOT-002",
        "Area": "Retrieval before generation",
        "Rule": "Generated answer must be tied to an evidence pack.",
        "Source": "latest_rag_answer",
        "Field": "evidence_count",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
        "Corrective_Action": "Regenerate answer only after retrieval evidence exists.",
    },
    {
        "Rule_ID": "SSOT-003",
        "Area": "Audit before decision",
        "Rule": "Latest audit record must exist and pass before board/distribution reliance.",
        "Source": "latest_audit_record",
        "Field": "audit_status",
        "Pass_Values": ["AUDIT_PASS"],
        "Warning_Values": ["AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"],
        "Critical": True,
        "Corrective_Action": "Run Step 08 and resolve audit exceptions.",
    },
    {
        "Rule_ID": "SSOT-004",
        "Area": "Citation traceability",
        "Rule": "Material conclusions must have citation/source traceability.",
        "Source": "citation_verification",
        "Field": "verification_status",
        "Pass_Values": ["CITATION_VERIFICATION_PASS"],
        "Warning_Values": ["CITATION_VERIFICATION_PASS_WITH_WARNINGS", "CITATION_REVIEW_REQUIRED"],
        "Critical": True,
        "Corrective_Action": "Run Step 13 and fix source_path/chunk_id/excerpt issues.",
    },
    {
        "Rule_ID": "SSOT-005",
        "Area": "Conflict resolution",
        "Rule": "Material conflicts must be absent or explicitly escalated before export/distribution.",
        "Source": "conflict_report",
        "Field": "summary.institutional_status",
        "Pass_Values": ["NO_CONFLICTS_DETECTED"],
        "Warning_Values": ["CONFLICTS_DETECTED_REVIEW_REQUIRED", "HIGH_CONFLICT_RISK_MANUAL_REVIEW"],
        "Critical": True,
        "Corrective_Action": "Run Step 14 and resolve conflicts using authority hierarchy.",
    },
    {
        "Rule_ID": "SSOT-006",
        "Area": "Decision readiness",
        "Rule": "Board decision must not be blocked or incomplete.",
        "Source": "board_memo",
        "Field": "decision_status",
        "Pass_Values": ["APPROVE_FOR_NEXT_STAGE"],
        "Warning_Values": ["APPROVE_WITH_CONDITIONS", "DEFER_PENDING_REVIEW"],
        "Critical": False,
        "Corrective_Action": "Run Step 23 and close board conditions/blockers.",
    },
    {
        "Rule_ID": "SSOT-007",
        "Area": "Freeze before distribution",
        "Rule": "Frozen data-room package must exist before distribution readiness gate.",
        "Source": "freeze_manifest",
        "Field": "freeze_status",
        "Pass_Values": ["DATA_ROOM_FREEZE_READY"],
        "Warning_Values": ["DATA_ROOM_FREEZE_REVIEW_REQUIRED"],
        "Critical": True,
        "Corrective_Action": "Run Step 27 and resolve missing mandatory files/hash mismatches.",
    },
    {
        "Rule_ID": "SSOT-008",
        "Area": "Gatekeeping before external release",
        "Rule": "Distribution readiness decision must allow release before external package creation.",
        "Source": "distribution_readiness",
        "Field": "distribution_decision",
        "Pass_Values": ["GO_FOR_DISTRIBUTION"],
        "Warning_Values": ["GO_WITH_CONDITIONS", "HOLD_PENDING_REVIEW"],
        "Critical": True,
        "Corrective_Action": "Run Step 28 and resolve blockers/conditions before release.",
    },
    {
        "Rule_ID": "SSOT-009",
        "Area": "Release package control",
        "Rule": "External release package must not be blocked or incomplete.",
        "Source": "external_release",
        "Field": "release_status",
        "Pass_Values": ["EXTERNAL_RELEASE_PACKAGE_READY"],
        "Warning_Values": ["EXTERNAL_RELEASE_PACKAGE_CONDITIONAL", "EXTERNAL_RELEASE_INTERNAL_PREP_ONLY"],
        "Critical": False,
        "Corrective_Action": "Run Step 29 only after Step 28 allows distribution, or keep as internal prep only.",
    },
    {
        "Rule_ID": "SSOT-010",
        "Area": "Receipt follows transmission",
        "Rule": "Post-release audit register must exist after release package preparation/manual distribution.",
        "Source": "post_release_audit",
        "Field": "post_release_status",
        "Pass_Values": ["POST_RELEASE_AUDIT_READY"],
        "Warning_Values": ["POST_RELEASE_AUDIT_CONDITIONAL", "POST_RELEASE_AUDIT_DRY_RUN"],
        "Critical": False,
        "Corrective_Action": "Run Step 30 with recipients/distribution metadata after manual transmission.",
    },
    {
        "Rule_ID": "SSOT-011",
        "Area": "Risk gate",
        "Rule": "Critical risks must be zero before export/distribution reliance.",
        "Source": "risk_signals",
        "Field": "summary.critical_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
        "Corrective_Action": "Close or formally exception critical risks; rerun Steps 17, 18, 27, 28.",
    },
    {
        "Rule_ID": "SSOT-012",
        "Area": "Document priority gate",
        "Rule": "P0 documents must be zero before distribution reliance.",
        "Source": "document_priority",
        "Field": "summary.p0_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
        "Corrective_Action": "Review P0 documents; rerun Step 18 and downstream gate steps.",
    },
]

EXPORT_RULES = [
    {
        "Rule_ID": "EXPORT-001",
        "Area": "SSOT snapshot condition",
        "Rule": "SSOT snapshot/freeze manifest must exist for export intent.",
        "Source": "freeze_manifest",
        "Field": "freeze_manifest_sha256",
        "Pass_Condition": "not_empty",
        "Critical": True,
        "Corrective_Action": "Run Step 27 and preserve immutable manifest.",
    },
    {
        "Rule_ID": "EXPORT-002",
        "Area": "Submission record condition",
        "Rule": "Distribution readiness decision acts as submission/release decision record.",
        "Source": "distribution_readiness",
        "Field": "distribution_readiness_decision_sha256",
        "Pass_Condition": "not_empty",
        "Critical": True,
        "Corrective_Action": "Run Step 28 and preserve decision record.",
    },
    {
        "Rule_ID": "EXPORT-003",
        "Area": "Approval event condition",
        "Rule": "Distribution decision must be GO or formally conditionally accepted before release.",
        "Source": "distribution_readiness",
        "Field": "distribution_decision",
        "Pass_Values": ["GO_FOR_DISTRIBUTION"],
        "Warning_Values": ["GO_WITH_CONDITIONS"],
        "Critical": True,
        "Corrective_Action": "Resolve blockers/conditions or record formal approval exception.",
    },
    {
        "Rule_ID": "EXPORT-004",
        "Area": "Role condition",
        "Rule": "Lender export requires role CFO or ADMIN.",
        "Source": "__runtime__",
        "Field": "role",
        "Pass_Values": ["CFO", "ADMIN"],
        "Warning_Values": [],
        "Critical": True,
        "Corrective_Action": "Run export-intent validation with --role CFO or --role ADMIN.",
    },
]


@dataclass(frozen=True)
class AlignmentPaths:
    base_dir: Path
    output_dir: Path
    report_md: Path
    report_json: Path
    checklist_csv: Path
    deviation_csv: Path
    corrective_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in [None, ""]:
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in [None, ""]:
            return default
        return float(value)
    except Exception:
        return default


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def nested_get(payload: dict[str, Any] | None, path: str, default: Any = None) -> Any:
    if not isinstance(payload, dict):
        return default
    cur: Any = payload
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
    return default if cur is None else cur


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> AlignmentPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return AlignmentPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        report_md=output_dir / OUTPUT_REPORT_MD,
        report_json=output_dir / OUTPUT_REPORT_JSON,
        checklist_csv=output_dir / OUTPUT_CHECKLIST_CSV,
        deviation_csv=output_dir / OUTPUT_DEVIATION_CSV,
        corrective_csv=output_dir / OUTPUT_CORRECTIVE_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in SOURCE_JSON_FILES.items()
    }


def runtime_report(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "role": args.role.upper(),
        "export_intent": bool(args.export_intent),
        "strict": bool(args.strict),
        "validator_version": SCRIPT_VERSION,
    }


def evaluate_rule(rule: dict[str, Any], reports: dict[str, dict[str, Any] | None], runtime: dict[str, Any]) -> dict[str, Any]:
    source = rule["Source"]
    field = rule.get("Field")
    report = runtime if source == "__runtime__" else reports.get(source)
    value = nested_get(report, field) if field else None

    if report is None:
        status = CHECK_MISSING
        reason = f"Missing source report: {source}"
    else:
        condition = rule.get("Pass_Condition")
        if condition == "value_gt_0":
            status = CHECK_PASS if safe_float(value, 0.0) > 0 else CHECK_FAIL
            reason = f"{field}={value}; expected > 0"
        elif condition == "not_empty":
            status = CHECK_PASS if value not in [None, ""] else CHECK_FAIL
            reason = f"{field} is {'present' if status == CHECK_PASS else 'empty'}"
        elif value in rule.get("Pass_Values", []):
            status = CHECK_PASS
            reason = f"{field}={value}"
        elif value in rule.get("Warning_Values", []):
            status = CHECK_WARNING
            reason = f"{field}={value}; warning/conditional alignment"
        else:
            status = CHECK_FAIL
            reason = f"{field}={value}; expected {rule.get('Pass_Values')}"

    return {
        "Rule_ID": rule["Rule_ID"],
        "Area": rule["Area"],
        "Rule": rule["Rule"],
        "Source_Report": source,
        "Required_Field": field,
        "Observed_Value": value,
        "Check_Status": status,
        "Critical": bool(rule.get("Critical")),
        "Reason": reason,
        "Corrective_Action": rule.get("Corrective_Action"),
    }


def build_checklist(reports: dict[str, dict[str, Any] | None], runtime: dict[str, Any], export_intent: bool) -> list[dict[str, Any]]:
    rows = [evaluate_rule(rule, reports, runtime) for rule in SSOT_RULES]
    if export_intent:
        rows.extend(evaluate_rule(rule, reports, runtime) for rule in EXPORT_RULES)
    return rows


def deviation_severity(row: dict[str, Any], strict: bool) -> str:
    if row["Check_Status"] == CHECK_MISSING:
        return DEV_CRITICAL if row["Critical"] else DEV_HIGH
    if row["Check_Status"] == CHECK_FAIL:
        return DEV_CRITICAL if row["Critical"] else DEV_HIGH
    if row["Check_Status"] == CHECK_WARNING:
        return DEV_HIGH if strict and row["Critical"] else DEV_MEDIUM
    return DEV_LOW


def build_deviations(checklist: list[dict[str, Any]], strict: bool) -> list[dict[str, Any]]:
    deviations = []
    for row in checklist:
        if row["Check_Status"] == CHECK_PASS:
            continue
        severity = deviation_severity(row, strict)
        raw = f"{row['Rule_ID']}|{row['Check_Status']}|{row.get('Observed_Value')}|{severity}"
        deviations.append({
            "Deviation_ID": "SSOT-DEV-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12],
            "Rule_ID": row["Rule_ID"],
            "Severity": severity,
            "Area": row["Area"],
            "Check_Status": row["Check_Status"],
            "Observed_Value": row.get("Observed_Value"),
            "Reason": row["Reason"],
            "Source_Report": row["Source_Report"],
            "Corrective_Action": row["Corrective_Action"],
            "Owner": "Danijela / TITAN Operator",
            "Due_Logic": "Before lender/export/release reliance" if severity in {DEV_CRITICAL, DEV_HIGH} else "Before final archive",
            "Status": "OPEN",
        })
    return deviations


def build_corrective_actions(deviations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, dev in enumerate(deviations, start=1):
        raw = f"{dev['Deviation_ID']}|{dev['Corrective_Action']}"
        rows.append({
            "Action_ID": "SSOT-ACT-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12],
            "Priority": idx,
            "Deviation_ID": dev["Deviation_ID"],
            "Severity": dev["Severity"],
            "Area": dev["Area"],
            "Action": dev["Corrective_Action"],
            "Owner": dev["Owner"],
            "Due_Logic": dev["Due_Logic"],
            "Closure_Evidence": "Regenerate source report and rerun Step 31 until check is PASS or formally accepted.",
            "Status": "OPEN",
        })
    return rows


def determine_alignment_status(checklist: list[dict[str, Any]], deviations: list[dict[str, Any]], strict: bool) -> tuple[str, list[str], float]:
    total = len(checklist)
    pass_count = sum(1 for x in checklist if x["Check_Status"] == CHECK_PASS)
    warning_count = sum(1 for x in checklist if x["Check_Status"] == CHECK_WARNING)
    fail_count = sum(1 for x in checklist if x["Check_Status"] == CHECK_FAIL)
    missing_count = sum(1 for x in checklist if x["Check_Status"] == CHECK_MISSING)
    critical_devs = [d for d in deviations if d["Severity"] == DEV_CRITICAL]
    high_devs = [d for d in deviations if d["Severity"] == DEV_HIGH]

    score = round(pass_count / total, 4) if total else 0.0
    reasons = []

    if missing_count > 0:
        reasons.append(f"Missing SSOT-alignment inputs: {missing_count}")
        return ALIGNMENT_INCOMPLETE, reasons, score

    if critical_devs:
        reasons.append(f"Critical SSOT deviations: {len(critical_devs)}")
        return ALIGNMENT_BLOCKED, reasons, score

    if strict and high_devs:
        reasons.append(f"Strict mode blocks high SSOT deviations: {len(high_devs)}")
        return ALIGNMENT_BLOCKED, reasons, score

    if fail_count > 0 or high_devs:
        reasons.append(f"Non-critical/high deviations require correction: fails={fail_count}, high={len(high_devs)}")
        return ALIGNMENT_NOT_READY, reasons, score

    if warning_count > 0:
        reasons.append(f"Conditional SSOT alignment warnings: {warning_count}")
        return ALIGNMENT_CONDITIONAL, reasons, score

    reasons.append("All SSOT alignment checks passed.")
    return ALIGNMENT_ALIGNED, reasons, score


def build_source_manifest(base_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for name, rel_path in SOURCE_JSON_FILES.items():
        path = base_dir / rel_path
        exists = path.exists() and path.is_file()
        rows.append({
            "Name": name,
            "Path": str(path),
            "Exists": exists,
            "Size_Bytes": path.stat().st_size if exists else None,
            "Modified_UTC": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if exists else None,
            "SHA256": sha256_file(path) if exists else None,
        })
    return rows


def build_manifest(paths: AlignmentPaths, reports: dict[str, dict[str, Any] | None], source_manifest: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "base_dir": str(paths.base_dir),
        "output_dir": str(paths.output_dir),
        "source_manifest": source_manifest,
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "alignment_report_sha256": report.get("ssot_alignment_report_sha256"),
        "governance_rule": {
            "validator_does_not_modify_sources": True,
            "validator_does_not_approve_export": True,
            "master_ssot_remains_architectural_authority": True,
            "audit_precedes_decision": True,
            "export_requires_snapshot_submission_approval_role": True,
        },
    }
    manifest["ssot_alignment_manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_report(
    paths: AlignmentPaths,
    args: argparse.Namespace,
    reports: dict[str, dict[str, Any] | None],
    runtime: dict[str, Any],
    checklist: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
    corrective_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    alignment_status, reasons, score = determine_alignment_status(checklist, deviations, strict=bool(args.strict))

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "SSOT_ALIGNMENT_VALIDATION_AUDIT_LOCKED",
        "master_ssot_reference": {
            "document": "TITAN_MASTER_SSOT_v1.0.pdf",
            "ssot_version": "1.0",
            "status": "LOCKED_ARCHITECTURAL",
            "governance_anchor": True,
        },
        "strict_mode": bool(args.strict),
        "export_intent": bool(args.export_intent),
        "role": args.role.upper(),
        "alignment_status": alignment_status,
        "alignment_reasons": reasons,
        "alignment_score": score,
        "summary": {
            "check_count": len(checklist),
            "pass_count": sum(1 for x in checklist if x["Check_Status"] == CHECK_PASS),
            "warning_count": sum(1 for x in checklist if x["Check_Status"] == CHECK_WARNING),
            "fail_count": sum(1 for x in checklist if x["Check_Status"] == CHECK_FAIL),
            "missing_count": sum(1 for x in checklist if x["Check_Status"] == CHECK_MISSING),
            "deviation_count": len(deviations),
            "critical_deviations": sum(1 for x in deviations if x["Severity"] == DEV_CRITICAL),
            "high_deviations": sum(1 for x in deviations if x["Severity"] == DEV_HIGH),
            "medium_deviations": sum(1 for x in deviations if x["Severity"] == DEV_MEDIUM),
            "corrective_actions": len(corrective_actions),
        },
        "runtime_context": runtime,
        "checklist": checklist,
        "deviation_register": deviations,
        "corrective_action_register": corrective_actions,
        "status_snapshot": {
            "audit_status": nested_get(reports.get("latest_audit_record"), "audit_status"),
            "citation_status": nested_get(reports.get("citation_verification"), "verification_status"),
            "conflict_status": nested_get(reports.get("conflict_report"), "summary.institutional_status"),
            "critical_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0)),
            "p0_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0)),
            "freeze_status": nested_get(reports.get("freeze_manifest"), "freeze_status"),
            "distribution_decision": nested_get(reports.get("distribution_readiness"), "distribution_decision"),
            "release_status": nested_get(reports.get("external_release"), "release_status"),
            "post_release_status": nested_get(reports.get("post_release_audit"), "post_release_status"),
        },
        "outputs": {
            "report_md": str(paths.report_md),
            "report_json": str(paths.report_json),
            "checklist_csv": str(paths.checklist_csv),
            "deviation_csv": str(paths.deviation_csv),
            "corrective_csv": str(paths.corrective_csv),
            "manifest_json": str(paths.manifest_json),
        },
        "governance_rule": {
            "does_not_modify_sources": True,
            "does_not_approve_export": True,
            "validates_alignment_only": True,
            "master_ssot_is_authoritative_truth_layer": True,
            "audit_precedes_decision": True,
            "freeze_precedes_distribution": True,
            "gatekeeping_precedes_external_release": True,
            "export_requires_snapshot_submission_approval_role": True,
        },
    }
    report["ssot_alignment_report_sha256"] = sha256_json(report)
    return report


def write_checklist_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Rule_ID", "Area", "Rule", "Source_Report", "Required_Field", "Observed_Value",
        "Check_Status", "Critical", "Reason", "Corrective_Action"
    ])


def write_deviation_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Deviation_ID", "Rule_ID", "Severity", "Area", "Check_Status", "Observed_Value",
        "Reason", "Source_Report", "Corrective_Action", "Owner", "Due_Logic", "Status"
    ])


def write_corrective_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Action_ID", "Priority", "Deviation_ID", "Severity", "Area", "Action",
        "Owner", "Due_Logic", "Closure_Evidence", "Status"
    ])


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def checklist_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No checklist rows."
    lines = ["| Rule | Area | Status | Critical | Observed | Reason |", "|---|---|---|---:|---|---|"]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Rule_ID'))} | {md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Check_Status'))} | {row.get('Critical')} | "
            f"{md_escape(row.get('Observed_Value'))} | {md_escape(row.get('Reason'))} |"
        )
    return "\n".join(lines)


def deviations_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No deviations."
    lines = ["| Severity | Rule | Area | Reason | Action |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Severity'))} | {md_escape(row.get('Rule_ID'))} | "
            f"{md_escape(row.get('Area'))} | {md_escape(row.get('Reason'))} | "
            f"{md_escape(row.get('Corrective_Action'))} |"
        )
    return "\n".join(lines)


def actions_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No corrective actions."
    lines = ["| Priority | Severity | Area | Action | Due |", "|---:|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {row.get('Priority')} | {md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Area'))} | {md_escape(row.get('Action'))} | "
            f"{md_escape(row.get('Due_Logic'))} |"
        )
    return "\n".join(lines)


def report_to_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    snapshot = report.get("status_snapshot", {}) if isinstance(report.get("status_snapshot"), dict) else {}

    summary_lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in summary.items():
        summary_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    snapshot_lines = ["| Field | Value |", "|---|---|"]
    for key, value in snapshot.items():
        snapshot_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    return f"""# TITAN SSOT Alignment Validation Report

## 1. Validation Identity

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Alignment Status | {report.get("alignment_status")} |
| Alignment Score | {report.get("alignment_score")} |
| Strict Mode | {report.get("strict_mode")} |
| Export Intent | {report.get("export_intent")} |
| Runtime Role | {report.get("role")} |
| Report SHA-256 | `{report.get("ssot_alignment_report_sha256")}` |

**Alignment reasons**

```json
{json.dumps(report.get("alignment_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Master SSOT Anchor

```text
TITAN MASTER SSOT v1.0 is the locked architectural authority for the operational RAG/release chain.
This validator checks whether Steps 1–30 comply with the locked governance doctrine:
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.
Freeze precedes distribution.
Gatekeeping precedes external release.
Receipt register follows transmission.
```

---

## 3. Summary

{chr(10).join(summary_lines)}

---

## 4. Status Snapshot

{chr(10).join(snapshot_lines)}

---

## 5. Alignment Checklist

{checklist_md(report.get("checklist", []))}

---

## 6. Deviation Register

{deviations_md(report.get("deviation_register", []))}

---

## 7. Corrective Action Register

{actions_md(report.get("corrective_action_register", []))}

---

## 8. Governance Rule

```text
Validator does not modify sources.
Validator does not approve export.
Validator validates alignment only.
MASTER SSOT remains authoritative truth layer.
Audit precedes decision.
Freeze precedes distribution.
Gatekeeping precedes external release.
Export requires snapshot, submission record, approval event and CFO/ADMIN role.
```
"""


def build_source_manifest(base_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "Name": name,
            "Path": str(base_dir / rel_path),
            "Exists": (base_dir / rel_path).exists(),
            "SHA256": sha256_file(base_dir / rel_path),
        }
        for name, rel_path in SOURCE_JSON_FILES.items()
    ]


def print_summary(report: dict[str, Any], paths: AlignmentPaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN SSOT ALIGNMENT VALIDATOR v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Alignment status:         {report.get('alignment_status')}")
    print(f"Alignment score:          {report.get('alignment_score')}")
    print(f"Pass/warn/fail/missing:   {summary.get('pass_count')}/{summary.get('warning_count')}/{summary.get('fail_count')}/{summary.get('missing_count')}")
    print(f"Critical deviations:      {summary.get('critical_deviations')}")
    print(f"High deviations:          {summary.get('high_deviations')}")
    print("-" * 100)
    print(f"Report Markdown:          {paths.report_md}")
    print(f"Report JSON:              {paths.report_json}")
    print(f"Checklist CSV:            {paths.checklist_csv}")
    print(f"Deviation CSV:            {paths.deviation_csv}")
    print(f"Corrective CSV:           {paths.corrective_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 31 — SSOT alignment validator.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--strict", action="store_true", help="Strict mode treats high/warning deviations more conservatively.")
    parser.add_argument("--export-intent", action="store_true", help="Validate mandatory export conditions from SSOT governance model.")
    parser.add_argument("--role", default="CFO", choices=["ADMIN", "CFO", "ANALYST", "VIEWER", "LENDER"], help="Runtime role for export-intent validation.")
    parser.add_argument("--print", action="store_true", help="Print Markdown report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, args.output_dir)

    try:
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        paths.output_dir.mkdir(parents=True, exist_ok=True)

        reports = load_reports(base_dir)
        runtime = runtime_report(args)
        checklist = build_checklist(reports, runtime, export_intent=bool(args.export_intent))
        deviations = build_deviations(checklist, strict=bool(args.strict))
        corrective_actions = build_corrective_actions(deviations)
        report = build_report(paths, args, reports, runtime, checklist, deviations, corrective_actions)
        source_manifest = build_source_manifest(base_dir)
        manifest = build_manifest(paths, reports, source_manifest, report)
        markdown = report_to_markdown(report)

        write_json(paths.report_json, report)
        write_text(paths.report_md, markdown)
        write_checklist_csv(paths.checklist_csv, checklist)
        write_deviation_csv(paths.deviation_csv, deviations)
        write_corrective_csv(paths.corrective_csv, corrective_actions)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "SSOT_ALIGNMENT_VALIDATION_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "alignment_status": report.get("alignment_status"),
            "alignment_score": report.get("alignment_score"),
            "report_sha256": report.get("ssot_alignment_report_sha256"),
            "manifest_sha256": manifest.get("ssot_alignment_manifest_sha256"),
            "summary": report.get("summary"),
            "outputs": report.get("outputs"),
        })

        print_summary(report, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "SSOT_ALIGNMENT_VALIDATION_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN SSOT ALIGNMENT VALIDATOR FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
