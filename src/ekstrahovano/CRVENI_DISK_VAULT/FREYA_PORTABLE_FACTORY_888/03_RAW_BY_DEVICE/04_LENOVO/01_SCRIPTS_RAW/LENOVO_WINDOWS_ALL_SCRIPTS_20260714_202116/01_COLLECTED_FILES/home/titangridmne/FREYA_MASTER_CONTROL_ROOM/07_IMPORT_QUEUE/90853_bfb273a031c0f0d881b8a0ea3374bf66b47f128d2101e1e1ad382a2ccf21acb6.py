#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
24_legal_compliance_gap_analyzer.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 24 — Legal & Compliance Gap Analyzer
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build a legal/compliance gap analysis from existing TITAN RAG outputs.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT provide legal advice or make final legal determinations.
It consolidates evidence-linked legal/compliance signals for manual legal review.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/latest_audit_record.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json
05_reports/risk_signals_report.json
05_reports/ssot_candidates_report.json
05_reports/document_priority_rank.json
05_reports/evidence_pack_report.json
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json

Outputs
-------
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MEMO.md
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MEMO.json
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_CHECKLIST.csv
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_GAP_REGISTER.csv
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_EVIDENCE_INDEX.csv
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MANIFEST.json
05_reports/legal_compliance_gap_analysis/source_exports/...
06_logs/legal_compliance_gap_analyzer_audit.jsonl
06_logs/legal_compliance_gap_analyzer_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\24_legal_compliance_gap_analyzer.py" --print

Jurisdiction profile
--------------------
python ".\\08_scripts\\24_legal_compliance_gap_analyzer.py" --jurisdiction Montenegro --print
python ".\\08_scripts\\24_legal_compliance_gap_analyzer.py" --jurisdiction EU --print

Custom output folder
--------------------
python ".\\08_scripts\\24_legal_compliance_gap_analyzer.py" --output-dir ".\\05_reports\\legal_compliance_gap_analysis_v1"
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "24_legal_compliance_gap_analyzer.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "legal_compliance_gap_analysis"

OUTPUT_MEMO_MD = "TITAN_LEGAL_COMPLIANCE_MEMO.md"
OUTPUT_MEMO_JSON = "TITAN_LEGAL_COMPLIANCE_MEMO.json"
OUTPUT_CHECKLIST_CSV = "TITAN_LEGAL_COMPLIANCE_CHECKLIST.csv"
OUTPUT_GAP_REGISTER_CSV = "TITAN_LEGAL_GAP_REGISTER.csv"
OUTPUT_EVIDENCE_INDEX_CSV = "TITAN_LEGAL_EVIDENCE_INDEX.csv"
OUTPUT_MANIFEST_JSON = "TITAN_LEGAL_COMPLIANCE_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "legal_compliance_gap_analyzer_audit.jsonl"
ERROR_LOG = Path("06_logs") / "legal_compliance_gap_analyzer_errors.jsonl"

LEGAL_READY = "LEGAL_COMPLIANCE_READY_FOR_REVIEW"
LEGAL_REVIEW_REQUIRED = "LEGAL_COMPLIANCE_REVIEW_REQUIRED"
LEGAL_BLOCKED = "LEGAL_COMPLIANCE_BLOCKED"
LEGAL_INCOMPLETE = "LEGAL_COMPLIANCE_INCOMPLETE"

CHECK_PASS = "PASS"
CHECK_WARNING = "WARNING"
CHECK_FAIL = "FAIL"
CHECK_MISSING = "MISSING"

GAP_OPEN_CRITICAL = "OPEN_CRITICAL"
GAP_OPEN_HIGH = "OPEN_HIGH"
GAP_OPEN_MEDIUM = "OPEN_MEDIUM"
GAP_MONITOR = "MONITOR"
GAP_CLOSED_BY_EVIDENCE = "CLOSED_BY_EVIDENCE"

SOURCE_JSON_FILES = {
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "lender_dd_pack": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "ssot_candidates": Path("05_reports") / "ssot_candidates_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "evidence_report": Path("05_reports") / "evidence_pack_report.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_answer": Path("05_reports") / "latest_rag_answer.json",
}

SOURCE_EXPORT_FILES = {
    "board_memo_md": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.md",
    "board_memo_json": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "board_actions_csv": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_ACTIONS.csv",
    "board_conditions_csv": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_APPROVAL_CONDITIONS.csv",
    "lender_dd_pack_md": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.md",
    "lender_dd_pack_json": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "lender_gap_register_csv": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_GAP_REGISTER.csv",
    "risk_signals_csv": Path("05_reports") / "risk_signals.csv",
    "ssot_candidates_csv": Path("05_reports") / "ssot_candidates.csv",
    "conflict_report_csv": Path("05_reports") / "conflict_report.csv",
    "citation_report_csv": Path("05_reports") / "citation_verification_report.csv",
    "evidence_report_csv": Path("05_reports") / "evidence_pack_report.csv",
    "document_priority_csv": Path("05_reports") / "document_priority_rank.csv",
}

LEGAL_REQUIREMENTS = [
    {
        "Requirement_ID": "LC-001",
        "Area": "Evidence Traceability",
        "Requirement": "Legal/compliance statements must be traceable to source_path and chunk_id.",
        "Source": "citation_verification",
        "Field": "verification_status",
        "Pass_Values": ["CITATION_VERIFICATION_PASS"],
        "Warning_Values": ["CITATION_VERIFICATION_PASS_WITH_WARNINGS", "CITATION_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "LC-002",
        "Area": "Audit Integrity",
        "Requirement": "Latest answer/evidence set must have a valid audit record.",
        "Source": "latest_audit_record",
        "Field": "audit_status",
        "Pass_Values": ["AUDIT_PASS"],
        "Warning_Values": ["AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "LC-003",
        "Area": "Conflict Governance",
        "Requirement": "Material legal/status/date/value conflicts must be resolved or explicitly escalated.",
        "Source": "conflict_report",
        "Field": "summary.institutional_status",
        "Pass_Values": ["NO_CONFLICTS_DETECTED"],
        "Warning_Values": ["CONFLICTS_DETECTED_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "LC-004",
        "Area": "Critical Risk Control",
        "Requirement": "Critical legal/compliance risks must be zero or formally exceptioned.",
        "Source": "risk_signals",
        "Field": "summary.critical_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "LC-005",
        "Area": "Document Review",
        "Requirement": "P0 priority documents must be reviewed before formal reliance.",
        "Source": "document_priority",
        "Field": "summary.p0_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "LC-006",
        "Area": "SSOT Governance",
        "Requirement": "SSOT candidates must not be conflict-blocked for legal/compliance reliance.",
        "Source": "ssot_candidates",
        "Field": "summary.conflict_blocked",
        "Pass_Values": [0, "0", None],
        "Warning_Values": [],
        "Critical": False,
    },
    {
        "Requirement_ID": "LC-007",
        "Area": "Board Conditions",
        "Requirement": "Board memo must not be blocked or incomplete.",
        "Source": "board_memo",
        "Field": "decision_status",
        "Pass_Values": ["APPROVE_FOR_NEXT_STAGE", "APPROVE_WITH_CONDITIONS", "DEFER_PENDING_REVIEW"],
        "Warning_Values": ["APPROVE_WITH_CONDITIONS", "DEFER_PENDING_REVIEW"],
        "Critical": False,
    },
    {
        "Requirement_ID": "LC-008",
        "Area": "Lender DD Conditions",
        "Requirement": "Lender DD pack must not be blocked or incomplete.",
        "Source": "lender_dd_pack",
        "Field": "dd_status",
        "Pass_Values": ["LENDER_DD_READY_FOR_REVIEW", "LENDER_DD_REVIEW_REQUIRED"],
        "Warning_Values": ["LENDER_DD_REVIEW_REQUIRED"],
        "Critical": False,
    },
    {
        "Requirement_ID": "LC-009",
        "Area": "Evidence Availability",
        "Requirement": "Evidence report must contain at least one source file.",
        "Source": "evidence_report",
        "Field": "summary.source_file_count",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
    },
]

LEGAL_KEYWORDS = {
    "CONTRACT_EXECUTION": [
        "contract", "agreement", "signed", "unsigned", "executed", "terminated",
        "ugovor", "potpisan", "nepotpisan", "raskid",
    ],
    "PERMIT_APPROVAL": [
        "permit", "license", "approval", "regulatory", "dozvol", "odobrenje",
        "licenca", "regulator",
    ],
    "PROCUREMENT": [
        "procurement", "tender", "public procurement", "bid", "nabavka", "tender",
    ],
    "CORPORATE_AUTHORITY": [
        "board", "shareholder", "resolution", "authorized", "director", "osnivač",
        "odbor", "skupština", "ovlašćen", "ovlascen",
    ],
    "LAND_PROPERTY": [
        "land", "property", "title", "ownership", "lease", "zemljište", "zemljiste",
        "vlasništvo", "vlasnistvo", "zakup",
    ],
    "SECURITY_COLLATERAL": [
        "pledge", "mortgage", "collateral", "security", "zaloga", "hipoteka",
    ],
    "ESG_EHS": [
        "environment", "environmental", "social", "health and safety", "ehs", "esg",
        "životna sredina", "zivotna sredina",
    ],
    "DATA_PRIVACY": [
        "personal data", "gdpr", "privacy", "data protection", "lični podaci", "licni podaci",
    ],
    "SANCTIONS_AML": [
        "sanctions", "aml", "anti-money laundering", "kyc", "beneficial owner",
        "sankcije", "sprečavanje pranja", "sprecavanje pranja",
    ],
    "STATE_AID_SUBSIDY": [
        "state aid", "subsidy", "grant", "incentive", "državna pomoć", "drzavna pomoc",
        "subvencija",
    ],
    "DISPUTE_LITIGATION": [
        "dispute", "litigation", "claim", "court", "arbitration", "spor", "sud",
        "arbitraža", "arbitraza",
    ],
}


@dataclass(frozen=True)
class LegalPaths:
    base_dir: Path
    output_dir: Path
    memo_md: Path
    memo_json: Path
    checklist_csv: Path
    gap_register_csv: Path
    evidence_index_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def short_text(value: Any, max_chars: int = 1000) -> str:
    text = str(value or "").replace("\x00", "")
    if len(text) > max_chars:
        return text[:max_chars] + " ...[TRUNCATED]"
    return text


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> LegalPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return LegalPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        memo_md=output_dir / OUTPUT_MEMO_MD,
        memo_json=output_dir / OUTPUT_MEMO_JSON,
        checklist_csv=output_dir / OUTPUT_CHECKLIST_CSV,
        gap_register_csv=output_dir / OUTPUT_GAP_REGISTER_CSV,
        evidence_index_csv=output_dir / OUTPUT_EVIDENCE_INDEX_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in SOURCE_JSON_FILES.items()
    }


def evaluate_requirement(req: dict[str, Any], reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    source = req["Source"]
    report = reports.get(source)
    field = req.get("Field")
    value = nested_get(report, field) if field else None

    if report is None:
        status = CHECK_MISSING
        gap_status = GAP_OPEN_CRITICAL if req.get("Critical") else GAP_OPEN_HIGH
        reason = f"Missing source report: {source}"
    else:
        condition = req.get("Pass_Condition")
        if condition == "value_gt_0":
            passed = safe_float(value, 0.0) > 0
            status = CHECK_PASS if passed else CHECK_FAIL
            reason = f"{field}={value}; expected > 0"
        elif value in req.get("Pass_Values", []):
            status = CHECK_PASS
            reason = f"{field}={value}"
        elif value in req.get("Warning_Values", []):
            status = CHECK_WARNING
            reason = f"{field}={value}; warning/manual review"
        else:
            status = CHECK_FAIL
            reason = f"{field}={value}; expected {req.get('Pass_Values')}"

        if status == CHECK_PASS:
            gap_status = GAP_CLOSED_BY_EVIDENCE
        elif status == CHECK_WARNING:
            gap_status = GAP_OPEN_MEDIUM
        elif req.get("Critical"):
            gap_status = GAP_OPEN_CRITICAL
        else:
            gap_status = GAP_OPEN_HIGH

    return {
        "Requirement_ID": req["Requirement_ID"],
        "Jurisdiction_Area": req["Area"],
        "Requirement": req["Requirement"],
        "Source_Report": source,
        "Required_Field": field,
        "Observed_Value": value,
        "Check_Status": status,
        "Gap_Status": gap_status,
        "Critical": bool(req.get("Critical")),
        "Reason": reason,
        "Recommended_Action": legal_requirement_action(req, status),
    }


def legal_requirement_action(req: dict[str, Any], status: str) -> str:
    if status == CHECK_PASS:
        return "No immediate action; preserve evidence in legal file."

    area = req.get("Area")
    if area == "Evidence Traceability":
        return "Rerun citation verification and fix source_path/chunk_id traceability."
    if area == "Audit Integrity":
        return "Rerun final audit and verify latest_audit_record."
    if area == "Conflict Governance":
        return "Resolve material conflicts through SSOT hierarchy and legal review."
    if area == "Critical Risk Control":
        return "Close or formally exception critical risks before reliance."
    if area == "Document Review":
        return "Review P0 documents and clear blockers."
    if area == "SSOT Governance":
        return "Review conflict-blocked SSOT candidates."
    if area == "Board Conditions":
        return "Review board decision memo conditions and close open conditions."
    if area == "Lender DD Conditions":
        return "Review lender due diligence pack gaps."
    if area == "Evidence Availability":
        return "Rerun retrieval/reporting to generate evidence source coverage."
    return "Manual legal/compliance review required."


def build_checklist(reports: dict[str, dict[str, Any] | None], jurisdiction: str) -> list[dict[str, Any]]:
    rows = []
    for req in LEGAL_REQUIREMENTS:
        row = evaluate_requirement(req, reports)
        row["Jurisdiction"] = jurisdiction
        rows.append(row)
    return rows


def detect_legal_categories(text: str) -> list[str]:
    lower = text.lower()
    categories = []
    for category, terms in LEGAL_KEYWORDS.items():
        for term in terms:
            if term.lower() in lower:
                categories.append(category)
                break
    return sorted(set(categories))


def build_legal_evidence_index(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    evidence_report = reports.get("evidence_report")
    evidence = evidence_report.get("evidence", []) if isinstance(evidence_report, dict) else []
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, dict):
                continue
            text = " ".join([
                str(item.get("file_name") or ""),
                str(item.get("source_path") or ""),
                str(item.get("excerpt") or ""),
                str(item.get("keyword_hits") or ""),
            ])
            categories = detect_legal_categories(text)
            if not categories:
                continue
            rows.append({
                "Evidence_ID": "LEGAL-EVID-" + sha256_text(str(item.get("chunk_id") or item.get("source_path") or ""))[:14],
                "Legal_Category": "; ".join(categories),
                "Evidence_Type": "EVIDENCE_CHUNK",
                "Rank": item.get("rank"),
                "Final_Score": item.get("final_score"),
                "Source_Path": item.get("source_path"),
                "File_Name": item.get("file_name"),
                "Chunk_ID": item.get("chunk_id"),
                "Section_Label": item.get("section_label"),
                "Excerpt_SHA256": item.get("excerpt_sha256"),
                "Excerpt": short_text(item.get("excerpt"), 1200),
                "Recommended_Use": "Manual legal/compliance review; not final legal conclusion.",
            })

    risk_report = reports.get("risk_signals")
    risks = risk_report.get("signals", []) if isinstance(risk_report, dict) else []
    if isinstance(risks, list):
        for risk in risks:
            if not isinstance(risk, dict):
                continue
            text = " ".join([str(risk.get("Risk_Type") or ""), str(risk.get("Context") or ""), str(risk.get("Source_Path") or "")])
            categories = detect_legal_categories(text)
            if categories or str(risk.get("Risk_Type") or "") in {"SIGNATURE_LEGAL_RISK", "PERMIT_REGULATORY_RISK", "CITATION_RISK", "CONFLICT_RISK", "SSOT_GOVERNANCE_RISK"}:
                rows.append({
                    "Evidence_ID": "LEGAL-RISK-" + sha256_text(str(risk.get("Risk_ID") or ""))[:14],
                    "Legal_Category": "; ".join(categories) or str(risk.get("Risk_Type") or ""),
                    "Evidence_Type": "RISK_SIGNAL",
                    "Rank": None,
                    "Final_Score": risk.get("Confidence_Score"),
                    "Source_Path": risk.get("Source_Path"),
                    "File_Name": risk.get("File_Name"),
                    "Chunk_ID": risk.get("Chunk_ID"),
                    "Section_Label": risk.get("Section_Label"),
                    "Excerpt_SHA256": None,
                    "Excerpt": short_text(risk.get("Context"), 1200),
                    "Recommended_Use": risk.get("Recommended_Action"),
                })

    return rows


def build_gap_register(
    checklist: list[dict[str, Any]],
    legal_evidence: list[dict[str, Any]],
    reports: dict[str, dict[str, Any] | None],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for row in checklist:
        if row["Check_Status"] == CHECK_PASS:
            continue
        gaps.append({
            "Gap_ID": "LEGAL-GAP-" + sha256_text(row["Requirement_ID"])[:12],
            "Requirement_ID": row["Requirement_ID"],
            "Area": row["Jurisdiction_Area"],
            "Gap_Status": row["Gap_Status"],
            "Severity": "CRITICAL" if row["Gap_Status"] == GAP_OPEN_CRITICAL else "HIGH" if row["Gap_Status"] == GAP_OPEN_HIGH else "MEDIUM",
            "Description": row["Requirement"],
            "Observed_Value": row["Observed_Value"],
            "Reason": row["Reason"],
            "Recommended_Action": row["Recommended_Action"],
            "Source_Report": row["Source_Report"],
            "Owner": "Legal counsel / Danijela / TITAN Operator",
            "Due_Logic": "Before board/lender reliance" if row["Critical"] else "Before final pack freeze",
            "Evidence_Closure_Rule": "Update source report until checklist status becomes PASS or formal legal exception is recorded.",
        })

    # Add category coverage gaps for areas with detected evidence but no clean conclusion.
    category_count: dict[str, int] = {}
    for item in legal_evidence:
        for cat in str(item.get("Legal_Category") or "").split(";"):
            cat = cat.strip()
            if cat:
                category_count[cat] = category_count.get(cat, 0) + 1

    for category, count in sorted(category_count.items()):
        gaps.append({
            "Gap_ID": "LEGAL-CAT-" + sha256_text(category)[:12],
            "Requirement_ID": "LEGAL-CATEGORY-COVERAGE",
            "Area": category,
            "Gap_Status": GAP_MONITOR,
            "Severity": "MEDIUM",
            "Description": f"Evidence references legal/compliance category {category}.",
            "Observed_Value": count,
            "Reason": f"{count} evidence/risk records detected for {category}.",
            "Recommended_Action": "Legal counsel should review category-specific evidence and decide whether formal memo language is needed.",
            "Source_Report": "evidence_pack_report.json / risk_signals_report.json",
            "Owner": "Legal counsel / Danijela",
            "Due_Logic": "Before final lender/board pack freeze",
            "Evidence_Closure_Rule": "Reviewed by counsel and documented as cleared / open / not applicable.",
        })

    return gaps


def determine_legal_status(checklist: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> tuple[str, list[str]]:
    reasons = []

    missing = [x for x in checklist if x["Check_Status"] == CHECK_MISSING]
    critical_fail = [x for x in checklist if x["Critical"] and x["Check_Status"] == CHECK_FAIL]
    critical_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_CRITICAL]
    high_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_HIGH]

    if missing:
        reasons.append(f"Missing legal/compliance source reports: {len(missing)}")
        return LEGAL_INCOMPLETE, reasons

    if critical_fail or critical_gaps:
        reasons.append(f"Critical legal/compliance blockers: checks={len(critical_fail)}, gaps={len(critical_gaps)}")
        return LEGAL_BLOCKED, reasons

    if high_gaps or any(x["Check_Status"] == CHECK_WARNING for x in checklist):
        reasons.append(f"Legal/compliance review required: high_gaps={len(high_gaps)}; warnings={sum(1 for x in checklist if x['Check_Status'] == CHECK_WARNING)}")
        return LEGAL_REVIEW_REQUIRED, reasons

    reasons.append("Core legal/compliance traceability gates are clean enough for manual legal review pack.")
    return LEGAL_READY, reasons


def copy_source_exports(base_dir: Path, output_dir: Path, copy_files: bool) -> list[dict[str, Any]]:
    target_dir = output_dir / "source_exports"
    target_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for name, rel_path in SOURCE_EXPORT_FILES.items():
        source = base_dir / rel_path
        target = target_dir / source.name

        if not source.exists():
            rows.append({
                "Name": name,
                "Source_Path": str(source),
                "Exists": False,
                "Copied": False,
                "Target_Path": None,
                "SHA256": None,
            })
            continue

        if copy_files:
            shutil.copy2(source, target)
            rows.append({
                "Name": name,
                "Source_Path": str(source),
                "Exists": True,
                "Copied": True,
                "Target_Path": str(target),
                "SHA256": sha256_file(target),
            })
        else:
            rows.append({
                "Name": name,
                "Source_Path": str(source),
                "Exists": True,
                "Copied": False,
                "Target_Path": str(target),
                "SHA256": sha256_file(source),
            })

    return rows


def build_manifest(base_dir: Path, output_dir: Path, copied_files: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for name, rel_path in SOURCE_JSON_FILES.items():
        path = base_dir / rel_path
        rows.append({
            "Name": name,
            "Path": str(path),
            "Exists": path.exists(),
            "Type": "json",
            "Size_Bytes": path.stat().st_size if path.exists() else None,
            "Modified_UTC": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if path.exists() else None,
            "SHA256": sha256_file(path),
        })
    for name, rel_path in SOURCE_EXPORT_FILES.items():
        path = base_dir / rel_path
        rows.append({
            "Name": name,
            "Path": str(path),
            "Exists": path.exists(),
            "Type": path.suffix.lower().strip("."),
            "Size_Bytes": path.stat().st_size if path.exists() else None,
            "Modified_UTC": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if path.exists() else None,
            "SHA256": sha256_file(path),
        })

    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "output_dir": str(output_dir),
        "source_manifest": rows,
        "copied_files": copied_files,
        "governance_rule": {
            "legal_compliance_analysis_consolidates_existing_reports_only": True,
            "not_legal_advice": True,
            "source_documents_not_modified": True,
            "manual_legal_review_required": True,
            "audit_precedes_decision": True,
        },
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_memo(
    reports: dict[str, dict[str, Any] | None],
    checklist: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    legal_evidence: list[dict[str, Any]],
    manifest: dict[str, Any],
    jurisdiction: str,
    strict: bool,
) -> dict[str, Any]:
    legal_status, reasons = determine_legal_status(checklist, gaps)

    latest_answer = reports.get("latest_answer") or {}
    answer_conf = latest_answer.get("confidence") if isinstance(latest_answer.get("confidence"), dict) else {}

    memo = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "LEGAL_COMPLIANCE_GAP_ANALYSIS_AUDIT_LOCKED",
        "jurisdiction": jurisdiction,
        "strict_mode": strict,
        "legal_status": legal_status,
        "legal_status_reasons": reasons,
        "query": nested_get(reports.get("latest_evidence_pack"), "query") or latest_answer.get("query"),
        "executive_snapshot": {
            "direct_answer_snapshot": short_text(latest_answer.get("direct_answer"), 1600),
            "answer_institutional_status": latest_answer.get("institutional_status"),
            "answer_confidence_score": answer_conf.get("confidence_score"),
            "answer_confidence_label": answer_conf.get("confidence_label"),
            "next_action": latest_answer.get("next_action"),
            "risk_if_skipped": latest_answer.get("risk_if_skipped"),
        },
        "metrics": {
            "checklist_items": len(checklist),
            "checklist_pass": sum(1 for x in checklist if x["Check_Status"] == CHECK_PASS),
            "checklist_warning": sum(1 for x in checklist if x["Check_Status"] == CHECK_WARNING),
            "checklist_fail": sum(1 for x in checklist if x["Check_Status"] == CHECK_FAIL),
            "checklist_missing": sum(1 for x in checklist if x["Check_Status"] == CHECK_MISSING),
            "gap_count": len(gaps),
            "critical_gaps": sum(1 for x in gaps if x["Gap_Status"] == GAP_OPEN_CRITICAL),
            "high_gaps": sum(1 for x in gaps if x["Gap_Status"] == GAP_OPEN_HIGH),
            "legal_evidence_rows": len(legal_evidence),
            "audit_status": nested_get(reports.get("latest_audit_record"), "audit_status"),
            "citation_status": nested_get(reports.get("citation_verification"), "verification_status"),
            "conflict_status": nested_get(reports.get("conflict_report"), "summary.institutional_status"),
            "critical_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0)),
            "high_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0)),
            "p0_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0)),
            "p1_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0)),
        },
        "checklist": checklist,
        "gap_register": gaps,
        "legal_evidence_index": legal_evidence,
        "top_risks": top_collection(reports.get("risk_signals"), "signals", 25),
        "top_conflicts": top_collection(reports.get("conflict_report"), "conflicts", 20),
        "top_documents": top_collection(reports.get("document_priority"), "documents", 25),
        "top_ssot_candidates": top_collection(reports.get("ssot_candidates"), "candidates", 25),
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "manifest_sha256": manifest.get("manifest_sha256"),
        "governance_rule": {
            "not_legal_advice": True,
            "manual_legal_review_required": True,
            "consolidates_existing_reports_only": True,
            "no_new_unsupported_claims": True,
            "source_documents_not_modified": True,
            "json_reports_and_original_sources_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    memo["legal_compliance_memo_sha256"] = sha256_json(memo)
    return memo


def top_collection(report: dict[str, Any] | None, key: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        return []
    rows = report.get(key, [])
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)][:limit]


def write_checklist_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Requirement_ID",
        "Jurisdiction",
        "Jurisdiction_Area",
        "Requirement",
        "Source_Report",
        "Required_Field",
        "Observed_Value",
        "Check_Status",
        "Gap_Status",
        "Critical",
        "Reason",
        "Recommended_Action",
    ])


def write_gap_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Gap_ID",
        "Requirement_ID",
        "Area",
        "Gap_Status",
        "Severity",
        "Description",
        "Observed_Value",
        "Reason",
        "Recommended_Action",
        "Source_Report",
        "Owner",
        "Due_Logic",
        "Evidence_Closure_Rule",
    ])


def write_evidence_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Evidence_ID",
        "Legal_Category",
        "Evidence_Type",
        "Rank",
        "Final_Score",
        "Source_Path",
        "File_Name",
        "Chunk_ID",
        "Section_Label",
        "Excerpt_SHA256",
        "Excerpt",
        "Recommended_Use",
    ])


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def checklist_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No checklist rows."
    lines = [
        "| ID | Area | Status | Critical | Observed | Action |",
        "|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Requirement_ID'))} | "
            f"{md_escape(row.get('Jurisdiction_Area'))} | "
            f"{md_escape(row.get('Check_Status'))} | "
            f"{row.get('Critical')} | "
            f"{md_escape(row.get('Observed_Value'))} | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def gaps_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No gaps."
    lines = [
        "| Gap | Severity | Area | Status | Reason | Action |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows[:100]:
        lines.append(
            f"| {md_escape(row.get('Gap_ID'))} | "
            f"{md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Gap_Status'))} | "
            f"{md_escape(short_text(row.get('Reason'), 250))} | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def evidence_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No legal/compliance evidence rows."
    lines = [
        "| Category | Type | Score | Source | Chunk | Use |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows[:100]:
        lines.append(
            f"| {md_escape(row.get('Legal_Category'))} | "
            f"{md_escape(row.get('Evidence_Type'))} | "
            f"{row.get('Final_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"`{md_escape(row.get('Chunk_ID'))}` | "
            f"{md_escape(row.get('Recommended_Use'))} |"
        )
    return "\n".join(lines)


def memo_to_markdown(memo: dict[str, Any]) -> str:
    snapshot = memo.get("executive_snapshot", {}) if isinstance(memo.get("executive_snapshot"), dict) else {}
    metrics = memo.get("metrics", {}) if isinstance(memo.get("metrics"), dict) else {}

    metric_lines = ["| Metric | Value |", "|---|---|"]
    for k, v in metrics.items():
        metric_lines.append(f"| {md_escape(k)} | {md_escape(v)} |")

    return f"""# TITAN Legal & Compliance Gap Analysis Memo

## 1. Memo Identity

| Field | Value |
|---|---|
| Created At | {memo.get("created_at")} |
| Jurisdiction | {memo.get("jurisdiction")} |
| Legal Status | {memo.get("legal_status")} |
| Query | {md_escape(memo.get("query"))} |
| Memo SHA-256 | `{memo.get("legal_compliance_memo_sha256")}` |

**Status reasons**

```json
{json.dumps(memo.get("legal_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Important Limitation

```text
This is not legal advice.
This is an evidence-linked legal/compliance gap analysis for manual legal review.
Final legal conclusions must be made by qualified counsel or authorized decision-makers.
```

---

## 3. Executive Snapshot

| Field | Value |
|---|---|
| Answer Institutional Status | {snapshot.get("answer_institutional_status")} |
| Answer Confidence Score | {snapshot.get("answer_confidence_score")} |
| Answer Confidence Label | {snapshot.get("answer_confidence_label")} |

**Direct answer snapshot**

```text
{snapshot.get("direct_answer_snapshot") or ""}
```

**Risk if skipped**

```text
{snapshot.get("risk_if_skipped") or ""}
```

**Next action**

```text
{snapshot.get("next_action") or ""}
```

---

## 4. Metrics

{chr(10).join(metric_lines)}

---

## 5. Legal / Compliance Checklist

{checklist_md(memo.get("checklist", []))}

---

## 6. Legal Gap Register

{gaps_md(memo.get("gap_register", []))}

---

## 7. Legal Evidence Index

{evidence_md(memo.get("legal_evidence_index", []))}

---

## 8. Top Risks

```json
{json.dumps(memo.get("top_risks", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 9. Top Conflicts

```json
{json.dumps(memo.get("top_conflicts", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 10. Priority Documents

```json
{json.dumps(memo.get("top_documents", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 11. Governance Rule

```text
Not legal advice.
Manual legal review required.
Consolidates existing reports only.
No new unsupported claims.
Source documents are not modified.
JSON reports and original sources remain authoritative.
Audit precedes decision.
```
"""


def print_summary(memo: dict[str, Any], paths: LegalPaths) -> None:
    metrics = memo.get("metrics", {}) if isinstance(memo.get("metrics"), dict) else {}
    print("=" * 100)
    print("TITAN LEGAL & COMPLIANCE GAP ANALYZER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Jurisdiction:             {memo.get('jurisdiction')}")
    print(f"Legal status:             {memo.get('legal_status')}")
    print(f"Checklist pass/warn/fail: {metrics.get('checklist_pass')}/{metrics.get('checklist_warning')}/{metrics.get('checklist_fail')}")
    print(f"Critical gaps:            {metrics.get('critical_gaps')}")
    print(f"High gaps:                {metrics.get('high_gaps')}")
    print(f"Legal evidence rows:      {metrics.get('legal_evidence_rows')}")
    print("-" * 100)
    print(f"Memo Markdown:            {paths.memo_md}")
    print(f"Memo JSON:                {paths.memo_json}")
    print(f"Checklist CSV:            {paths.checklist_csv}")
    print(f"Gap Register CSV:         {paths.gap_register_csv}")
    print(f"Evidence Index CSV:       {paths.evidence_index_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 24 — legal compliance gap analyzer.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--jurisdiction", default="Montenegro", choices=["Montenegro", "EU", "Generic"], help="Jurisdiction label for the memo.")
    parser.add_argument("--no-copy-files", action="store_true", help="Do not copy exports into source_exports.")
    parser.add_argument("--strict", action="store_true", help="Strict metadata flag.")
    parser.add_argument("--print", action="store_true", help="Print Markdown memo to console.")

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
        checklist = build_checklist(reports, args.jurisdiction)
        legal_evidence = build_legal_evidence_index(reports)
        gaps = build_gap_register(checklist, legal_evidence, reports)
        copied_files = copy_source_exports(base_dir, paths.output_dir, copy_files=not bool(args.no_copy_files))
        manifest = build_manifest(base_dir, paths.output_dir, copied_files)

        memo = build_memo(
            reports=reports,
            checklist=checklist,
            gaps=gaps,
            legal_evidence=legal_evidence,
            manifest=manifest,
            jurisdiction=args.jurisdiction,
            strict=bool(args.strict),
        )

        markdown = memo_to_markdown(memo)

        write_json(paths.memo_json, memo)
        write_text(paths.memo_md, markdown)
        write_checklist_csv(paths.checklist_csv, checklist)
        write_gap_csv(paths.gap_register_csv, gaps)
        write_evidence_csv(paths.evidence_index_csv, legal_evidence)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "LEGAL_COMPLIANCE_GAP_ANALYSIS_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "jurisdiction": args.jurisdiction,
            "legal_status": memo.get("legal_status"),
            "memo_sha256": memo.get("legal_compliance_memo_sha256"),
            "manifest_sha256": manifest.get("manifest_sha256"),
            "outputs": {
                "memo_md": str(paths.memo_md),
                "memo_json": str(paths.memo_json),
                "checklist_csv": str(paths.checklist_csv),
                "gap_register_csv": str(paths.gap_register_csv),
                "evidence_index_csv": str(paths.evidence_index_csv),
                "manifest_json": str(paths.manifest_json),
            },
        })

        print_summary(memo, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "LEGAL_COMPLIANCE_GAP_ANALYSIS_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "jurisdiction": args.jurisdiction,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN LEGAL & COMPLIANCE GAP ANALYZER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
