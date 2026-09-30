#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
32_sovereign_charter_v60_1_builder.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 32 — Sovereign Charter v60.1 Builder
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build a premium institutional draft package for:

TITAN-GRID Sovereign Infrastructure Platform
Sovereign Charter & Operational Matrix v60.1

Part A:
    Establishment Charter

Part B:
    Operational Matrix

This script does NOT create unsupported facts.
This script does NOT replace legal counsel, board approval, lender review or SSOT authority.
This script uses existing TITAN RAG evidence/governance outputs to create a
document-ready charter skeleton with placeholders where evidence is missing.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.
SSOT governs institutional drafting.
Unsupported financial/legal/ESG assertions remain placeholders.

Inputs
------
05_reports/ssot_alignment/TITAN_SSOT_ALIGNMENT_REPORT.json
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MEMO.json
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_MEMO.json
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/risk_signals_report.json
05_reports/financial_signals_report.json
05_reports/ssot_candidates_report.json
05_reports/document_priority_rank.json
05_reports/latest_evidence_pack.json
05_reports/latest_audit_record.json

Outputs
-------
05_reports/sovereign_charter_v60_1/TITAN-GRID_Sovereign_Charter_and_Operational_Matrix_v60.1.md
05_reports/sovereign_charter_v60_1/TITAN-GRID_Sovereign_Charter_and_Operational_Matrix_v60.1.json
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_Document_Control.csv
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_KPI_Matrix.csv
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_RACI_Matrix.csv
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_Risk_Mitigation_Matrix.csv
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_Treasury_Matrix.csv
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_Evidence_Link_Register.csv
05_reports/sovereign_charter_v60_1/TITAN-GRID_v60.1_Charter_Manifest.json
06_logs/sovereign_charter_v60_1_builder_audit.jsonl
06_logs/sovereign_charter_v60_1_builder_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\32_sovereign_charter_v60_1_builder.py" --print

Institutional mode
------------------
python ".\\08_scripts\\32_sovereign_charter_v60_1_builder.py" --mode institutional --print

Strict evidence mode
--------------------
python ".\\08_scripts\\32_sovereign_charter_v60_1_builder.py" --strict-evidence --print
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


SCRIPT_NAME = "32_sovereign_charter_v60_1_builder.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "sovereign_charter_v60_1"

OUTPUT_CHARTER_MD = "TITAN-GRID_Sovereign_Charter_and_Operational_Matrix_v60.1.md"
OUTPUT_CHARTER_JSON = "TITAN-GRID_Sovereign_Charter_and_Operational_Matrix_v60.1.json"
OUTPUT_DOCUMENT_CONTROL_CSV = "TITAN-GRID_v60.1_Document_Control.csv"
OUTPUT_KPI_CSV = "TITAN-GRID_v60.1_KPI_Matrix.csv"
OUTPUT_RACI_CSV = "TITAN-GRID_v60.1_RACI_Matrix.csv"
OUTPUT_RISK_CSV = "TITAN-GRID_v60.1_Risk_Mitigation_Matrix.csv"
OUTPUT_TREASURY_CSV = "TITAN-GRID_v60.1_Treasury_Matrix.csv"
OUTPUT_EVIDENCE_LINK_CSV = "TITAN-GRID_v60.1_Evidence_Link_Register.csv"
OUTPUT_MANIFEST_JSON = "TITAN-GRID_v60.1_Charter_Manifest.json"

AUDIT_LOG = Path("06_logs") / "sovereign_charter_v60_1_builder_audit.jsonl"
ERROR_LOG = Path("06_logs") / "sovereign_charter_v60_1_builder_errors.jsonl"

CHARTER_READY = "CHARTER_DRAFT_READY"
CHARTER_REVIEW_REQUIRED = "CHARTER_REVIEW_REQUIRED"
CHARTER_BLOCKED = "CHARTER_BLOCKED"
CHARTER_INCOMPLETE = "CHARTER_INCOMPLETE"

SOURCE_JSON_FILES = {
    "ssot_alignment": Path("05_reports") / "ssot_alignment" / "TITAN_SSOT_ALIGNMENT_REPORT.json",
    "capex_bankability": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json",
    "legal_compliance": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "esg_permitting": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.json",
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "lender_dd": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "financial_signals": Path("05_reports") / "financial_signals_report.json",
    "ssot_candidates": Path("05_reports") / "ssot_candidates_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
}


@dataclass(frozen=True)
class CharterPaths:
    base_dir: Path
    output_dir: Path
    charter_md: Path
    charter_json: Path
    document_control_csv: Path
    kpi_csv: Path
    raci_csv: Path
    risk_csv: Path
    treasury_csv: Path
    evidence_link_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_label() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def short_text(value: Any, max_chars: int = 1400) -> str:
    text = str(value or "").replace("\x00", "")
    return text if len(text) <= max_chars else text[:max_chars] + " ...[TRUNCATED]"


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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> CharterPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return CharterPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        charter_md=output_dir / OUTPUT_CHARTER_MD,
        charter_json=output_dir / OUTPUT_CHARTER_JSON,
        document_control_csv=output_dir / OUTPUT_DOCUMENT_CONTROL_CSV,
        kpi_csv=output_dir / OUTPUT_KPI_CSV,
        raci_csv=output_dir / OUTPUT_RACI_CSV,
        risk_csv=output_dir / OUTPUT_RISK_CSV,
        treasury_csv=output_dir / OUTPUT_TREASURY_CSV,
        evidence_link_csv=output_dir / OUTPUT_EVIDENCE_LINK_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in SOURCE_JSON_FILES.items()
    }


def first_value(rows: list[dict[str, Any]], categories: list[str], value_keys: list[str]) -> Any:
    for row in rows:
        row_text = json.dumps(row, ensure_ascii=False).lower()
        if any(cat.lower() in row_text for cat in categories):
            for key in value_keys:
                if row.get(key) not in [None, ""]:
                    return row.get(key)
    return None


def financial_signal_rows(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    payload = reports.get("financial_signals") or {}
    rows = payload.get("signals", [])
    return [x for x in rows if isinstance(x, dict)] if isinstance(rows, list) else []


def risk_signal_rows(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    payload = reports.get("risk_signals") or {}
    rows = payload.get("signals", [])
    return [x for x in rows if isinstance(x, dict)] if isinstance(rows, list) else []


def ssot_candidate_rows(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    payload = reports.get("ssot_candidates") or {}
    rows = payload.get("candidates", [])
    return [x for x in rows if isinstance(x, dict)] if isinstance(rows, list) else []


def build_evidence_summary(reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    financial_rows = financial_signal_rows(reports)
    risk_rows = risk_signal_rows(reports)
    ssot_rows = ssot_candidate_rows(reports)

    return {
        "query": nested_get(reports.get("latest_evidence_pack"), "query"),
        "evidence_count": nested_get(reports.get("latest_evidence_pack"), "evidence_count", 0),
        "source_file_count": nested_get(reports.get("latest_evidence_pack"), "source_file_count", 0),
        "audit_status": nested_get(reports.get("latest_audit_record"), "audit_status"),
        "citation_status": nested_get(reports.get("citation_verification"), "verification_status"),
        "conflict_status": nested_get(reports.get("conflict_report"), "summary.institutional_status"),
        "ssot_alignment_status": nested_get(reports.get("ssot_alignment"), "alignment_status"),
        "ssot_alignment_score": nested_get(reports.get("ssot_alignment"), "alignment_score"),
        "financial_signal_count": len(financial_rows),
        "risk_signal_count": len(risk_rows),
        "ssot_candidate_count": len(ssot_rows),
        "capex_value": first_value(financial_rows, ["CAPEX", "capital expenditure", "project cost"], ["Canonical_Value", "Value", "Amount"]),
        "debt_value": first_value(financial_rows, ["LOAN", "DEBT", "credit facility"], ["Canonical_Value", "Value", "Amount"]),
        "equity_value": first_value(financial_rows, ["EQUITY", "capital contribution"], ["Canonical_Value", "Value", "Amount"]),
        "grant_value": first_value(financial_rows, ["GRANT", "subsidy"], ["Canonical_Value", "Value", "Amount"]),
        "dscr_value": first_value(financial_rows, ["DSCR", "coverage ratio"], ["Canonical_Value", "Value", "Ratio"]),
        "irr_value": first_value(financial_rows, ["IRR"], ["Canonical_Value", "Value", "Percent"]),
        "npv_value": first_value(financial_rows, ["NPV"], ["Canonical_Value", "Value", "Amount"]),
        "ebitda_value": first_value(financial_rows, ["EBITDA"], ["Canonical_Value", "Value", "Amount"]),
    }


def placeholder_or_value(value: Any, placeholder: str, strict_evidence: bool) -> str:
    if value not in [None, ""]:
        return str(value)
    return f"[PLACEHOLDER — {placeholder}]" if strict_evidence else f"[TO BE CONFIRMED — {placeholder}]"


def determine_charter_status(reports: dict[str, dict[str, Any] | None], strict_evidence: bool) -> tuple[str, list[str]]:
    reasons = []

    required = ["ssot_alignment", "latest_audit_record", "latest_evidence_pack"]
    missing = [name for name in required if reports.get(name) is None]
    if missing:
        return CHARTER_INCOMPLETE, ["Missing required reports: " + ", ".join(missing)]

    alignment = nested_get(reports.get("ssot_alignment"), "alignment_status")
    audit_status = nested_get(reports.get("latest_audit_record"), "audit_status")
    evidence_count = safe_int(nested_get(reports.get("latest_evidence_pack"), "evidence_count", 0))
    critical_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0))
    conflicts = nested_get(reports.get("conflict_report"), "summary.institutional_status")

    if evidence_count <= 0:
        return CHARTER_BLOCKED, ["No evidence pack available; charter must not assert project facts."]

    if audit_status not in {"AUDIT_PASS", "AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"}:
        return CHARTER_BLOCKED, [f"Audit status blocks charter drafting: {audit_status}"]

    if alignment in {"SSOT_BLOCKED", "SSOT_INCOMPLETE"}:
        return CHARTER_BLOCKED, [f"SSOT alignment blocks charter drafting: {alignment}"]

    if strict_evidence and alignment != "SSOT_ALIGNED":
        return CHARTER_REVIEW_REQUIRED, [f"Strict evidence mode requires clean SSOT alignment; current={alignment}"]

    if critical_risks > 0:
        return CHARTER_REVIEW_REQUIRED, [f"Critical risks exist; charter must remain draft/review: {critical_risks}"]

    if conflicts in {"HIGH_CONFLICT_RISK_MANUAL_REVIEW", "CONFLICTS_DETECTED_REVIEW_REQUIRED"}:
        return CHARTER_REVIEW_REQUIRED, [f"Conflicts require review before final charter: {conflicts}"]

    if alignment in {"SSOT_CONDITIONAL_ALIGNMENT", "SSOT_NOT_READY"}:
        return CHARTER_REVIEW_REQUIRED, [f"SSOT alignment is conditional/not-ready: {alignment}"]

    return CHARTER_READY, ["Core evidence/audit/SSOT gates allow draft charter generation."]


def document_control_rows(args: argparse.Namespace, charter_status: str) -> list[dict[str, Any]]:
    return [
        {"Field": "Document Title", "Value": "TITAN-GRID Sovereign Charter and Operational Matrix"},
        {"Field": "Version", "Value": "v60.1"},
        {"Field": "Release Type", "Value": "Internal Release"},
        {"Field": "Classification", "Value": "Confidential | Internal Release – Sovereign Use Only"},
        {"Field": "Document Mode", "Value": args.mode},
        {"Field": "Draft Status", "Value": charter_status},
        {"Field": "Prepared By", "Value": args.prepared_by},
        {"Field": "Owner", "Value": args.owner},
        {"Field": "Date", "Value": args.date or today_label()},
        {"Field": "Header Standard", "Value": "TITAN-GRID | Sovereign Infrastructure Platform | v60.1 | Confidential"},
        {"Field": "Footer Standard", "Value": "Page X of Y | Internal Release – Sovereign Use Only"},
        {"Field": "Format", "Value": "A4 Portrait"},
        {"Field": "Margins", "Value": "2.5 cm all sides"},
        {"Field": "Primary Color", "Value": "#0052CC"},
        {"Field": "Accent Color", "Value": "#003399"},
        {"Field": "Secondary Color", "Value": "#1F2A44"},
    ]


def kpi_rows(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"KPI_Category": "Financial", "KPI": "Total Project CAPEX", "Current_Value": placeholder_or_value(evidence.get("capex_value"), "CAPEX evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "Debt Facility / Loan Amount", "Current_Value": placeholder_or_value(evidence.get("debt_value"), "Debt/loan evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "Equity Contribution", "Current_Value": placeholder_or_value(evidence.get("equity_value"), "Equity evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "Grant / Subsidy", "Current_Value": placeholder_or_value(evidence.get("grant_value"), "Grant/subsidy evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "DSCR", "Current_Value": placeholder_or_value(evidence.get("dscr_value"), "DSCR model evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "IRR", "Current_Value": placeholder_or_value(evidence.get("irr_value"), "IRR model evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "NPV", "Current_Value": placeholder_or_value(evidence.get("npv_value"), "NPV model evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Financial", "KPI": "EBITDA Projection", "Current_Value": placeholder_or_value(evidence.get("ebitda_value"), "EBITDA projection evidence required", True), "Evidence_Source": "financial_signals_report.json", "Review_Status": "EVIDENCE_REQUIRED"},
        {"KPI_Category": "Operational", "KPI": "Milestone Completion Rate", "Current_Value": "[PLACEHOLDER — milestone schedule required]", "Evidence_Source": "implementation roadmap", "Review_Status": "PLACEHOLDER"},
        {"KPI_Category": "ESG", "KPI": "Permit Readiness Status", "Current_Value": "[PLACEHOLDER — permit evidence required]", "Evidence_Source": "esg_permitting memo", "Review_Status": "PLACEHOLDER"},
        {"KPI_Category": "Risk", "KPI": "Critical Risk Count", "Current_Value": nested_get_value_as_str(evidence, "critical_risk_count", "[TO BE CALCULATED]"), "Evidence_Source": "risk_signals_report.json", "Review_Status": "SYSTEM_DERIVED"},
    ]


def nested_get_value_as_str(payload: dict[str, Any], key: str, default: str) -> str:
    value = payload.get(key)
    return str(value) if value not in [None, ""] else default


def raci_rows() -> list[dict[str, Any]]:
    return [
        {"Process": "SSOT Governance", "Responsible": "TITAN Operator", "Accountable": "CFO / Admin", "Consulted": "Legal / Finance / Technical", "Informed": "Board / Lenders"},
        {"Process": "Evidence Retrieval", "Responsible": "RAG Engine", "Accountable": "TITAN Operator", "Consulted": "Document Owners", "Informed": "CFO"},
        {"Process": "Financial Architecture", "Responsible": "Finance Lead", "Accountable": "CFO", "Consulted": "Lenders / Advisors", "Informed": "Board"},
        {"Process": "Legal & Compliance Review", "Responsible": "Legal Counsel", "Accountable": "Authorized Signatory", "Consulted": "CFO / Project Sponsor", "Informed": "Board"},
        {"Process": "ESG / Permitting Review", "Responsible": "ESG/EHS/Permitting Expert", "Accountable": "Project Sponsor", "Consulted": "Legal / Technical", "Informed": "Lenders"},
        {"Process": "Board Decision", "Responsible": "Board Secretariat", "Accountable": "Board / Authorized Person", "Consulted": "CFO / Legal / Technical", "Informed": "Investors / Lenders"},
        {"Process": "External Release", "Responsible": "TITAN Operator", "Accountable": "CFO / Admin", "Consulted": "Legal / Board", "Informed": "Authorized Recipients"},
        {"Process": "Post-Release Receipt", "Responsible": "TITAN Operator", "Accountable": "CFO", "Consulted": "Recipients", "Informed": "Board / Audit File"},
    ]


def risk_matrix_rows(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    risks = risk_signal_rows(reports)[:30]
    rows = []
    for idx, risk in enumerate(risks, start=1):
        rows.append({
            "Risk_ID": risk.get("Risk_ID") or f"RISK-{idx:03d}",
            "Risk_Category": risk.get("Risk_Type") or "UNCLASSIFIED",
            "Severity": risk.get("Severity") or "REVIEW",
            "Description": short_text(risk.get("Context"), 500),
            "Mitigation": risk.get("Recommended_Action") or "Manual review required.",
            "Evidence_Source": risk.get("Source_Path"),
            "Owner": "TITAN Operator / Responsible Workstream",
            "Status": risk.get("Risk_Status") or "REVIEW_REQUIRED",
        })
    if not rows:
        rows.append({
            "Risk_ID": "RISK-PLACEHOLDER",
            "Risk_Category": "Risk register pending",
            "Severity": "REVIEW",
            "Description": "No risk signals available in current input.",
            "Mitigation": "Run Step 17 and rebuild charter.",
            "Evidence_Source": "risk_signals_report.json",
            "Owner": "TITAN Operator",
            "Status": "PLACEHOLDER",
        })
    return rows


def treasury_rows(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"Treasury_Area": "Funding Structure", "Control_Item": "Grant / Equity / Debt split", "Current_Value": f"Grant={placeholder_or_value(evidence.get('grant_value'), 'grant evidence', True)} | Equity={placeholder_or_value(evidence.get('equity_value'), 'equity evidence', True)} | Debt={placeholder_or_value(evidence.get('debt_value'), 'debt evidence', True)}", "Control_Status": "EVIDENCE_REQUIRED"},
        {"Treasury_Area": "Debt Service", "Control_Item": "DSCR covenant reference", "Current_Value": placeholder_or_value(evidence.get("dscr_value"), "DSCR evidence", True), "Control_Status": "EVIDENCE_REQUIRED"},
        {"Treasury_Area": "Capital Allocation", "Control_Item": "CAPEX budget control", "Current_Value": placeholder_or_value(evidence.get("capex_value"), "CAPEX evidence", True), "Control_Status": "EVIDENCE_REQUIRED"},
        {"Treasury_Area": "De-risking", "Control_Item": "Contingency / reserve logic", "Current_Value": "[PLACEHOLDER — contingency policy required]", "Control_Status": "PLACEHOLDER"},
        {"Treasury_Area": "Reporting", "Control_Item": "Monthly treasury reporting", "Current_Value": "Monthly CFO report / quarterly board report", "Control_Status": "DRAFT"},
    ]


def evidence_link_rows(reports: dict[str, dict[str, Any] | None], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, payload in reports.items():
        if payload is None:
            rows.append({"Source_Report": name, "Exists": False, "SHA256": None, "Status_Field": None, "Status_Value": None, "Use_In_Charter": "MISSING"})
        else:
            rows.append({
                "Source_Report": name,
                "Exists": True,
                "SHA256": sha256_json(payload),
                "Status_Field": primary_status_field(name),
                "Status_Value": primary_status_value(name, payload),
                "Use_In_Charter": use_in_charter(name),
            })
    return rows


def primary_status_field(name: str) -> str:
    mapping = {
        "ssot_alignment": "alignment_status",
        "capex_bankability": "bankability_status",
        "legal_compliance": "legal_status",
        "esg_permitting": "esg_status",
        "board_memo": "decision_status",
        "lender_dd": "dd_status",
        "executive_pack": "pack_status",
        "latest_audit_record": "audit_status",
        "citation_verification": "verification_status",
        "conflict_report": "summary.institutional_status",
    }
    return mapping.get(name, "summary/status")


def primary_status_value(name: str, payload: dict[str, Any]) -> Any:
    field = primary_status_field(name)
    if "." in field:
        return nested_get(payload, field)
    return payload.get(field) or nested_get(payload, "summary.institutional_status") or payload.get("status")


def use_in_charter(name: str) -> str:
    mapping = {
        "ssot_alignment": "Governance anchor",
        "capex_bankability": "Financial architecture",
        "legal_compliance": "Legal framework",
        "esg_permitting": "ESG/permitting",
        "board_memo": "Board conditions",
        "lender_dd": "Lender due diligence",
        "executive_pack": "Executive summary",
        "risk_signals": "Risk matrix",
        "financial_signals": "Financial KPI placeholders/evidence",
        "ssot_candidates": "SSOT architecture",
        "document_priority": "Document control",
        "latest_evidence_pack": "Evidence trace",
        "latest_audit_record": "Audit status",
    }
    return mapping.get(name, "Reference")


def charter_sections(args: argparse.Namespace, evidence: dict[str, Any], reports: dict[str, dict[str, Any] | None], strict_evidence: bool) -> dict[str, Any]:
    capex = placeholder_or_value(evidence.get("capex_value"), "Total Project CAPEX must be supported by financial evidence", strict_evidence)
    grant = placeholder_or_value(evidence.get("grant_value"), "Grant/subsidy evidence required", strict_evidence)
    equity = placeholder_or_value(evidence.get("equity_value"), "Equity evidence required", strict_evidence)
    debt = placeholder_or_value(evidence.get("debt_value"), "Debt/loan evidence required", strict_evidence)
    dscr = placeholder_or_value(evidence.get("dscr_value"), "DSCR evidence required", strict_evidence)
    irr = placeholder_or_value(evidence.get("irr_value"), "IRR evidence required", strict_evidence)
    npv = placeholder_or_value(evidence.get("npv_value"), "NPV evidence required", strict_evidence)
    ebitda = placeholder_or_value(evidence.get("ebitda_value"), "EBITDA evidence required", strict_evidence)

    return {
        "cover": {
            "title": "TITAN-GRID Sovereign Infrastructure Platform",
            "subtitle": "Establishment Charter & Operational Matrix",
            "version": "v60.1 – Internal Release",
            "strategic_subtitle": "A Strategic Multi-Asset Industrial Hub for the Adriatic-Balkan Corridor",
            "classification": "Confidential | Internal Release – Sovereign Use Only",
            "date": args.date or today_label(),
        },
        "part_a": [
            {
                "code": "A1",
                "title": "Executive Summary",
                "body": (
                    "TITAN-GRID is structured as a sovereign-grade infrastructure and industrial platform "
                    "intended to consolidate strategic project governance, evidence-controlled decisioning, "
                    "financial architecture, operational accountability and institutional reporting into one "
                    "controlled governance framework. This draft is generated from the TITAN evidence pipeline "
                    "and remains subject to SSOT, legal, financial, ESG and board review."
                ),
            },
            {
                "code": "A2",
                "title": "Vision & Strategic Mandate",
                "body": (
                    "The platform mandate is to support a strategic multi-asset industrial hub for the "
                    "Adriatic-Balkan Corridor, with emphasis on sovereign industrial resilience, lender-grade "
                    "transparency, auditability and controlled execution. The mandate must be validated against "
                    "government, permitting, lender and board requirements before external reliance."
                ),
            },
            {
                "code": "A3",
                "title": "Strategic Objectives",
                "body": (
                    "The strategic objectives shall be SMART, measurable and linked to source evidence. "
                    "Draft objectives include: establish a bankable industrial platform; preserve SSOT integrity; "
                    "maintain audit-grade data room governance; enable lender due diligence; control CAPEX and "
                    "treasury execution; strengthen ESG/permitting readiness; and maintain transparent reporting."
                ),
            },
            {
                "code": "A4",
                "title": "Legal & Institutional Framework",
                "body": (
                    "The legal form, concession/PPP status, licensing, regulatory framework and sovereign "
                    "interface remain subject to legal counsel review. No legal status is locked by this draft. "
                    f"Current legal compliance status: {nested_get(reports.get('legal_compliance'), 'legal_status', '[PLACEHOLDER]')}."
                ),
            },
            {
                "code": "A5",
                "title": "Ownership, Governance & UBO",
                "body": (
                    "Ownership, UBO, authorized signatory, board/advisory structure and approval authority "
                    "must be completed from verified corporate documents. This draft preserves placeholders "
                    "where formal evidence is missing: Sponsor [PLACEHOLDER], UBO [PLACEHOLDER], Authorized "
                    "Signatory [PLACEHOLDER], Board/Advisory Structure [PLACEHOLDER]."
                ),
            },
            {
                "code": "A6",
                "title": "Financial Architecture & TITAN-GRID SSOT Reference Layer",
                "body": (
                    "The financial architecture is governed by TITAN MASTER SSOT v1.0 as the locked architectural "
                    "truth layer, while this v60.1 Charter defines the institutional, financial and operational "
                    "mandate of the TITAN-GRID platform. Current evidence-linked draft values: "
                    f"Total Project CAPEX: {capex}; Grant: {grant}; Equity: {equity}; Debt: {debt}; "
                    f"DSCR: {dscr}; IRR: {irr}; NPV: {npv}; EBITDA Projection: {ebitda}. "
                    "Values marked as placeholders must not be used as final financial inputs."
                ),
            },
            {
                "code": "A7",
                "title": "Operational Sovereignty & Risk Management",
                "body": (
                    "Operational sovereignty is based on evidence control, SSOT governance, audit logs, "
                    "controlled release gates, risk registers and approval workflows. Critical risks, conflicts, "
                    "citation failures and P0 document issues block institutional reliance until resolved."
                ),
            },
            {
                "code": "A8",
                "title": "Implementation Roadmap & Milestones",
                "body": (
                    "Implementation milestones shall be mapped to verified documents, board approvals, lender "
                    "requirements, permitting events, CAPEX procurement gates and treasury availability. "
                    "Detailed dates remain placeholders unless supported by evidence."
                ),
            },
            {
                "code": "A9",
                "title": "Signatures & Approvals",
                "body": (
                    "Signature blocks are reserved for UBO, Authorized Person, Board Representative, Witness/Notary "
                    "where applicable. Signature does not waive unresolved SSOT deviations, legal gaps, lender "
                    "conditions or audit blockers."
                ),
            },
        ],
        "part_b": [
            {
                "code": "B1",
                "title": "Operational Governance Model",
                "body": "Operational governance is implemented through RACI ownership, escalation rules, SSOT controls and evidence-linked approvals.",
            },
            {
                "code": "B2",
                "title": "Organizational Structure & Key Roles",
                "body": "Key roles include Sponsor, UBO, Authorized Signatory, CFO, Admin, TITAN Operator, Legal Counsel, ESG/EHS Expert, Finance Lead, Board and Lender/Investor reviewers.",
            },
            {
                "code": "B3",
                "title": "Core Processes & Workflows",
                "body": "Core workflows include evidence retrieval, audit, conflict detection, SSOT candidate extraction, financial/risk extraction, board/lender pack generation, freeze, gatekeeping, release package preparation and receipt audit.",
            },
            {
                "code": "B4",
                "title": "KPI Dashboard & Performance Matrix",
                "body": "The KPI matrix covers financial, operational, ESG and risk KPIs. Values must remain evidence-linked and reviewed before final use.",
            },
            {
                "code": "B5",
                "title": "Data & SSOT Architecture",
                "body": "The data architecture follows TITAN MASTER SSOT v1.0 and the local RAG principle: evidence precedes intelligence; retrieval precedes generation; audit precedes decision.",
            },
            {
                "code": "B6",
                "title": "Technology & Digital Sovereignty Stack",
                "body": "The stack includes local evidence retrieval, controlled JSON/CSV/Markdown outputs, audit logs, frozen manifests, release gates and hash-based traceability.",
            },
            {
                "code": "B7",
                "title": "Risk Register & Mitigation Matrix",
                "body": "The risk matrix is derived from current risk signal outputs and must be updated after each material evidence refresh.",
            },
            {
                "code": "B8",
                "title": "Financial Control & Treasury Matrix",
                "body": "Treasury controls include funding structure, CAPEX budget control, DSCR/covenant review, reserve logic and periodic CFO reporting.",
            },
            {
                "code": "B9",
                "title": "Reporting & Transparency Framework",
                "body": "Reporting cadence includes monthly operational/finance reporting, quarterly board reporting, lender reporting where applicable and annual governance review.",
            },
            {
                "code": "B10",
                "title": "Amendment & Version Control Procedure",
                "body": "All amendments must be versioned, logged, supported by evidence and reviewed against SSOT alignment before institutional release.",
            },
        ],
    }


def build_charter_package(args: argparse.Namespace, reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    evidence = build_evidence_summary(reports)
    evidence["critical_risk_count"] = safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0))
    charter_status, status_reasons = determine_charter_status(reports, strict_evidence=bool(args.strict_evidence))
    sections = charter_sections(args, evidence, reports, strict_evidence=bool(args.strict_evidence))

    package = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "SOVEREIGN_CHARTER_V60_1_AUDIT_LOCKED",
        "document_identity": {
            "title": "TITAN-GRID Sovereign Charter and Operational Matrix",
            "version": "v60.1",
            "classification": "Confidential | Internal Release – Sovereign Use Only",
            "document_type": "Establishment Charter + Operational Matrix",
            "mode": args.mode,
            "prepared_by": args.prepared_by,
            "owner": args.owner,
            "date": args.date or today_label(),
        },
        "layout_standard": {
            "format": "A4 Portrait",
            "margins": "2.5 cm all sides",
            "header": "TITAN-GRID | Sovereign Infrastructure Platform | v60.1 | Confidential",
            "footer": "Page X of Y | Internal Release – Sovereign Use Only",
            "primary_color": "#0052CC",
            "accent_color": "#003399",
            "secondary_color": "#1F2A44",
            "body_font": "Calibri / Arial 11 pt",
            "heading_1": "Calibri Bold 18–20 pt, #003399",
            "heading_2": "Calibri Bold 14–16 pt, #0052CC",
            "tables": "Navy header, white text, alternating light-blue rows",
        },
        "charter_status": charter_status,
        "charter_status_reasons": status_reasons,
        "strict_evidence": bool(args.strict_evidence),
        "evidence_summary": evidence,
        "sections": sections,
        "document_control": document_control_rows(args, charter_status),
        "kpi_matrix": kpi_rows(evidence),
        "raci_matrix": raci_rows(),
        "risk_mitigation_matrix": risk_matrix_rows(reports),
        "treasury_matrix": treasury_rows(evidence),
        "evidence_link_register": evidence_link_rows(reports, evidence),
        "governance_rule": {
            "does_not_create_unsupported_facts": True,
            "placeholders_required_when_evidence_missing": True,
            "master_ssot_remains_authoritative": True,
            "not_legal_financial_or_lender_approval": True,
            "audit_precedes_decision": True,
        },
    }
    package["sovereign_charter_v60_1_sha256"] = sha256_json(package)
    return package


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def table_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No rows."
    headers = []
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(row.get(h)) for h in headers) + " |")
    return "\n".join(lines)


def package_to_markdown(package: dict[str, Any]) -> str:
    doc = package["document_identity"]
    layout = package["layout_standard"]
    sections = package["sections"]
    evidence = package["evidence_summary"]

    lines = []
    lines.append(f"# {doc['title']}")
    lines.append("")
    lines.append("## SOVEREIGN INFRASTRUCTURE PLATFORM")
    lines.append("")
    lines.append("**ESTABLISHMENT CHARTER & OPERATIONAL MATRIX**")
    lines.append("")
    lines.append(f"**Version:** {doc['version']} – Internal Release")
    lines.append("")
    lines.append("**Subtitle:** A Strategic Multi-Asset Industrial Hub for the Adriatic-Balkan Corridor")
    lines.append("")
    lines.append(f"**Date:** {doc['date']}")
    lines.append("")
    lines.append(f"**Classification:** {doc['classification']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Document Control")
    lines.append("")
    lines.append(table_md(package["document_control"]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Confidentiality Notice")
    lines.append("")
    lines.append("This document is confidential and intended for internal sovereign use only. It is a draft institutional package generated from the TITAN evidence and governance pipeline. It must not be treated as final legal, financial, lender or board approval.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Layout Standard")
    lines.append("")
    for key, value in layout.items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Evidence & SSOT Status")
    lines.append("")
    lines.append(f"- **Charter Status:** {package['charter_status']}")
    lines.append(f"- **Charter Status Reasons:** {', '.join(package['charter_status_reasons'])}")
    lines.append(f"- **SSOT Alignment Status:** {evidence.get('ssot_alignment_status')}")
    lines.append(f"- **SSOT Alignment Score:** {evidence.get('ssot_alignment_score')}")
    lines.append(f"- **Audit Status:** {evidence.get('audit_status')}")
    lines.append(f"- **Citation Status:** {evidence.get('citation_status')}")
    lines.append(f"- **Conflict Status:** {evidence.get('conflict_status')}")
    lines.append(f"- **Evidence Count:** {evidence.get('evidence_count')}")
    lines.append(f"- **Source File Count:** {evidence.get('source_file_count')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# PART A — ESTABLISHMENT CHARTER")
    lines.append("")
    for section in sections["part_a"]:
        lines.append(f"## {section['code']}. {section['title']}")
        lines.append("")
        lines.append(section["body"])
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# PART B — OPERATIONAL MATRIX")
    lines.append("")
    for section in sections["part_b"]:
        lines.append(f"## {section['code']}. {section['title']}")
        lines.append("")
        lines.append(section["body"])
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# APPENDICES")
    lines.append("")
    lines.append("## C1. KPI Dashboard & Performance Matrix")
    lines.append("")
    lines.append(table_md(package["kpi_matrix"]))
    lines.append("")
    lines.append("## C2. RACI Matrix")
    lines.append("")
    lines.append(table_md(package["raci_matrix"]))
    lines.append("")
    lines.append("## C3. Risk Register & Mitigation Matrix")
    lines.append("")
    lines.append(table_md(package["risk_mitigation_matrix"]))
    lines.append("")
    lines.append("## C4. Financial Control & Treasury Matrix")
    lines.append("")
    lines.append(table_md(package["treasury_matrix"]))
    lines.append("")
    lines.append("## C5. Evidence Link Register")
    lines.append("")
    lines.append(table_md(package["evidence_link_register"]))
    lines.append("")
    lines.append("## C6. Signatures & Approvals")
    lines.append("")
    lines.append("| Role | Name | Signature | Date |")
    lines.append("|---|---|---|---|")
    lines.append("| UBO | [PLACEHOLDER] |  |  |")
    lines.append("| Authorized Person | [PLACEHOLDER] |  |  |")
    lines.append("| CFO / Finance Lead | [PLACEHOLDER] |  |  |")
    lines.append("| Witness / Notary, if required | [PLACEHOLDER] |  |  |")
    lines.append("")
    lines.append("## C7. Version History")
    lines.append("")
    lines.append("| Version | Date | Change | Owner |")
    lines.append("|---|---|---|---|")
    lines.append(f"| v60.1 | {doc['date']} | Initial sovereign charter and operational matrix draft generated from TITAN evidence pipeline. | {doc['owner']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Governance Rule")
    lines.append("")
    lines.append("```text")
    lines.append("Evidence precedes intelligence.")
    lines.append("Retrieval precedes generation.")
    lines.append("Audit precedes decision.")
    lines.append("SSOT governs institutional drafting.")
    lines.append("Unsupported financial/legal/ESG assertions remain placeholders.")
    lines.append("TITAN MASTER SSOT v1.0 remains the locked architectural authority.")
    lines.append("```")
    lines.append("")
    lines.append(f"**Document SHA-256:** `{package['sovereign_charter_v60_1_sha256']}`")
    lines.append("")
    return "\n".join(lines)


def build_manifest(paths: CharterPaths, reports: dict[str, dict[str, Any] | None], package: dict[str, Any]) -> dict[str, Any]:
    source_manifest = []
    for name, rel_path in SOURCE_JSON_FILES.items():
        path = paths.base_dir / rel_path
        source_manifest.append({
            "Name": name,
            "Path": str(path),
            "Exists": path.exists() and path.is_file(),
            "Size_Bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            "Modified_UTC": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if path.exists() and path.is_file() else None,
            "SHA256": sha256_file(path),
            "Use": use_in_charter(name),
        })

    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "base_dir": str(paths.base_dir),
        "output_dir": str(paths.output_dir),
        "charter_status": package.get("charter_status"),
        "charter_sha256": package.get("sovereign_charter_v60_1_sha256"),
        "source_manifest": source_manifest,
        "outputs": {
            "charter_md": str(paths.charter_md),
            "charter_json": str(paths.charter_json),
            "document_control_csv": str(paths.document_control_csv),
            "kpi_csv": str(paths.kpi_csv),
            "raci_csv": str(paths.raci_csv),
            "risk_csv": str(paths.risk_csv),
            "treasury_csv": str(paths.treasury_csv),
            "evidence_link_csv": str(paths.evidence_link_csv),
            "manifest_json": str(paths.manifest_json),
        },
        "governance_rule": package.get("governance_rule"),
    }
    manifest["charter_manifest_sha256"] = sha256_json(manifest)
    return manifest


def print_summary(package: dict[str, Any], paths: CharterPaths) -> None:
    evidence = package.get("evidence_summary", {})
    print("=" * 100)
    print("TITAN-GRID SOVEREIGN CHARTER v60.1 BUILDER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Charter status:           {package.get('charter_status')}")
    print(f"SSOT alignment:           {evidence.get('ssot_alignment_status')}")
    print(f"Audit status:             {evidence.get('audit_status')}")
    print(f"Evidence count:           {evidence.get('evidence_count')}")
    print(f"Financial signals:        {evidence.get('financial_signal_count')}")
    print(f"Risk signals:             {evidence.get('risk_signal_count')}")
    print("-" * 100)
    print(f"Charter Markdown:         {paths.charter_md}")
    print(f"Charter JSON:             {paths.charter_json}")
    print(f"Document Control CSV:     {paths.document_control_csv}")
    print(f"KPI Matrix CSV:           {paths.kpi_csv}")
    print(f"RACI Matrix CSV:          {paths.raci_csv}")
    print(f"Risk Matrix CSV:          {paths.risk_csv}")
    print(f"Treasury Matrix CSV:      {paths.treasury_csv}")
    print(f"Evidence Link CSV:        {paths.evidence_link_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 32 — Sovereign Charter v60.1 builder.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--mode", default="institutional", choices=["institutional", "board", "lender", "internal"], help="Drafting mode.")
    parser.add_argument("--prepared-by", default="TITAN Local Evidence RAG Engine", help="Prepared by label.")
    parser.add_argument("--owner", default="Danijela / CFO", help="Document owner label.")
    parser.add_argument("--date", default="", help="Document date. Defaults to today.")
    parser.add_argument("--strict-evidence", action="store_true", help="Use stricter placeholder policy and status checks.")
    parser.add_argument("--print", action="store_true", help="Print Markdown charter to console.")

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
        package = build_charter_package(args, reports)
        markdown = package_to_markdown(package)
        manifest = build_manifest(paths, reports, package)

        write_json(paths.charter_json, package)
        write_text(paths.charter_md, markdown)
        write_csv(paths.document_control_csv, package["document_control"], ["Field", "Value"])
        write_csv(paths.kpi_csv, package["kpi_matrix"], ["KPI_Category", "KPI", "Current_Value", "Evidence_Source", "Review_Status"])
        write_csv(paths.raci_csv, package["raci_matrix"], ["Process", "Responsible", "Accountable", "Consulted", "Informed"])
        write_csv(paths.risk_csv, package["risk_mitigation_matrix"], ["Risk_ID", "Risk_Category", "Severity", "Description", "Mitigation", "Evidence_Source", "Owner", "Status"])
        write_csv(paths.treasury_csv, package["treasury_matrix"], ["Treasury_Area", "Control_Item", "Current_Value", "Control_Status"])
        write_csv(paths.evidence_link_csv, package["evidence_link_register"], ["Source_Report", "Exists", "SHA256", "Status_Field", "Status_Value", "Use_In_Charter"])
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "SOVEREIGN_CHARTER_V60_1_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "charter_status": package.get("charter_status"),
            "charter_sha256": package.get("sovereign_charter_v60_1_sha256"),
            "manifest_sha256": manifest.get("charter_manifest_sha256"),
            "outputs": manifest.get("outputs"),
        })

        print_summary(package, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "SOVEREIGN_CHARTER_V60_1_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN-GRID SOVEREIGN CHARTER v60.1 BUILDER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
