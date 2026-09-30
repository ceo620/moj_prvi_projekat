#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
26_capex_loan_bankability_analyzer.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 26 — CAPEX & Loan Bankability Analyzer
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build a CAPEX / loan / bankability analysis from existing TITAN RAG outputs.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT create a financial model or lender approval.
It consolidates evidence-linked CAPEX, loan, DSCR, WACC, IRR, NPV, equity,
grant, covenant and bankability signals for manual finance/lender review.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/financial_signals_report.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MEMO.json
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_MEMO.json
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
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_BANKABILITY_MEMO.md
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_BANKABILITY_CHECKLIST.csv
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_GAP_REGISTER.csv
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_EVIDENCE_INDEX.csv
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_COVENANT_REVIEW.csv
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_MANIFEST.json
05_reports/capex_loan_bankability_analysis/source_exports/...
06_logs/capex_loan_bankability_analyzer_audit.jsonl
06_logs/capex_loan_bankability_analyzer_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\26_capex_loan_bankability_analyzer.py" --print

Profile examples
----------------
python ".\\08_scripts\\26_capex_loan_bankability_analyzer.py" --profile EBRD --print
python ".\\08_scripts\\26_capex_loan_bankability_analyzer.py" --profile EIB --print
python ".\\08_scripts\\26_capex_loan_bankability_analyzer.py" --profile BANK --print

Custom output folder
--------------------
python ".\\08_scripts\\26_capex_loan_bankability_analyzer.py" --output-dir ".\\05_reports\\capex_loan_bankability_analysis_v1"
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


SCRIPT_NAME = "26_capex_loan_bankability_analyzer.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "capex_loan_bankability_analysis"

OUTPUT_MEMO_MD = "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.md"
OUTPUT_MEMO_JSON = "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json"
OUTPUT_CHECKLIST_CSV = "TITAN_CAPEX_LOAN_BANKABILITY_CHECKLIST.csv"
OUTPUT_GAP_REGISTER_CSV = "TITAN_CAPEX_LOAN_GAP_REGISTER.csv"
OUTPUT_EVIDENCE_INDEX_CSV = "TITAN_CAPEX_LOAN_EVIDENCE_INDEX.csv"
OUTPUT_COVENANT_CSV = "TITAN_CAPEX_LOAN_COVENANT_REVIEW.csv"
OUTPUT_MANIFEST_JSON = "TITAN_CAPEX_LOAN_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "capex_loan_bankability_analyzer_audit.jsonl"
ERROR_LOG = Path("06_logs") / "capex_loan_bankability_analyzer_errors.jsonl"

BANK_READY = "CAPEX_LOAN_BANKABILITY_READY_FOR_REVIEW"
BANK_REVIEW_REQUIRED = "CAPEX_LOAN_BANKABILITY_REVIEW_REQUIRED"
BANK_BLOCKED = "CAPEX_LOAN_BANKABILITY_BLOCKED"
BANK_INCOMPLETE = "CAPEX_LOAN_BANKABILITY_INCOMPLETE"

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
    "financial_signals": Path("05_reports") / "financial_signals_report.json",
    "lender_dd_pack": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "legal_compliance": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "esg_permitting": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.json",
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
    "financial_signals_csv": Path("05_reports") / "financial_signals.csv",
    "financial_signals_json": Path("05_reports") / "financial_signals_report.json",
    "lender_dd_pack_md": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.md",
    "lender_gap_register_csv": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_GAP_REGISTER.csv",
    "board_memo_md": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.md",
    "board_conditions_csv": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_APPROVAL_CONDITIONS.csv",
    "legal_memo_md": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.md",
    "esg_memo_md": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.md",
    "risk_signals_csv": Path("05_reports") / "risk_signals.csv",
    "ssot_candidates_csv": Path("05_reports") / "ssot_candidates.csv",
    "conflict_report_csv": Path("05_reports") / "conflict_report.csv",
    "citation_report_csv": Path("05_reports") / "citation_verification_report.csv",
    "document_priority_csv": Path("05_reports") / "document_priority_rank.csv",
    "evidence_report_csv": Path("05_reports") / "evidence_pack_report.csv",
    "control_tower_xlsx": Path("05_reports") / "TITAN_RAG_CONTROL_TOWER.xlsx",
}

BANKABILITY_REQUIREMENTS = [
    {
        "Requirement_ID": "BANK-001",
        "Area": "Audit Integrity",
        "Requirement": "Financial and bankability conclusions must have a valid audit record.",
        "Source": "latest_audit_record",
        "Field": "audit_status",
        "Pass_Values": ["AUDIT_PASS"],
        "Warning_Values": ["AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "BANK-002",
        "Area": "Citation Integrity",
        "Requirement": "CAPEX/loan/model evidence must be traceable to source_path and chunk_id.",
        "Source": "citation_verification",
        "Field": "verification_status",
        "Pass_Values": ["CITATION_VERIFICATION_PASS"],
        "Warning_Values": ["CITATION_VERIFICATION_PASS_WITH_WARNINGS", "CITATION_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "BANK-003",
        "Area": "Conflict Control",
        "Requirement": "Material financial conflicts must be absent or manually resolved.",
        "Source": "conflict_report",
        "Field": "summary.institutional_status",
        "Pass_Values": ["NO_CONFLICTS_DETECTED"],
        "Warning_Values": ["CONFLICTS_DETECTED_REVIEW_REQUIRED", "HIGH_CONFLICT_RISK_MANUAL_REVIEW"],
        "Critical": True,
    },
    {
        "Requirement_ID": "BANK-004",
        "Area": "Financial Signals",
        "Requirement": "Financial signal register must contain at least one financial signal.",
        "Source": "financial_signals",
        "Field": "summary.total_signals",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
    },
    {
        "Requirement_ID": "BANK-005",
        "Area": "Critical Risk Control",
        "Requirement": "Critical risks must be zero or formally exceptioned before lender reliance.",
        "Source": "risk_signals",
        "Field": "summary.critical_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "BANK-006",
        "Area": "Document Review",
        "Requirement": "P0 documents must be reviewed before bankability reliance.",
        "Source": "document_priority",
        "Field": "summary.p0_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "BANK-007",
        "Area": "Lender DD Linkage",
        "Requirement": "Lender DD pack must not be blocked or incomplete.",
        "Source": "lender_dd_pack",
        "Field": "dd_status",
        "Pass_Values": ["LENDER_DD_READY_FOR_REVIEW", "LENDER_DD_REVIEW_REQUIRED"],
        "Warning_Values": ["LENDER_DD_REVIEW_REQUIRED"],
        "Critical": False,
    },
    {
        "Requirement_ID": "BANK-008",
        "Area": "Board Decision Linkage",
        "Requirement": "Board memo must not be blocked or incomplete.",
        "Source": "board_memo",
        "Field": "decision_status",
        "Pass_Values": ["APPROVE_FOR_NEXT_STAGE", "APPROVE_WITH_CONDITIONS", "DEFER_PENDING_REVIEW"],
        "Warning_Values": ["APPROVE_WITH_CONDITIONS", "DEFER_PENDING_REVIEW"],
        "Critical": False,
    },
    {
        "Requirement_ID": "BANK-009",
        "Area": "Legal/ESG Dependency",
        "Requirement": "Legal and ESG packs should not be blocked for lender reliance.",
        "Source": "legal_compliance",
        "Field": "legal_status",
        "Pass_Values": ["LEGAL_COMPLIANCE_READY_FOR_REVIEW", "LEGAL_COMPLIANCE_REVIEW_REQUIRED"],
        "Warning_Values": ["LEGAL_COMPLIANCE_REVIEW_REQUIRED"],
        "Critical": False,
    },
    {
        "Requirement_ID": "BANK-010",
        "Area": "Evidence Availability",
        "Requirement": "Evidence report must contain at least one evidence source.",
        "Source": "evidence_report",
        "Field": "summary.source_file_count",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
    },
]

BANKABILITY_KEYWORDS = {
    "CAPEX": ["capex", "capital expenditure", "investment cost", "project cost", "equipment cost", "construction cost"],
    "OPEX": ["opex", "operating cost", "operating expense", "maintenance cost"],
    "LOAN": ["loan", "debt", "credit facility", "debt facility", "financing facility", "borrowing"],
    "EQUITY": ["equity", "share capital", "capital contribution"],
    "GRANT": ["grant", "subsidy", "incentive", "state aid"],
    "DSCR": ["dscr", "debt service coverage", "coverage ratio"],
    "WACC": ["wacc", "weighted average cost"],
    "IRR": ["irr", "internal rate of return"],
    "NPV": ["npv", "net present value"],
    "EBITDA": ["ebitda", "operating profit"],
    "REVENUE": ["revenue", "sales", "turnover"],
    "INTEREST_RATE": ["interest rate", "euribor", "margin", "coupon"],
    "MATURITY": ["maturity", "tenor", "repayment period", "amortization"],
    "COVENANT": ["covenant", "condition precedent", "condition subsequent", "undertaking", "waiver"],
    "COLLATERAL": ["collateral", "security", "pledge", "mortgage", "guarantee"],
    "LENDER": ["eib", "ebrd", "ifc", "lender", "bank", "credit committee"],
    "CONTINGENCY": ["contingency", "risk reserve", "price escalation", "inflation"],
}

COVENANT_KEYWORDS = {
    "DSCR_COVENANT": ["dscr", "debt service coverage", "coverage ratio"],
    "LEVERAGE_COVENANT": ["debt/equity", "debt to equity", "leverage", "gearing"],
    "INTEREST_RATE": ["interest rate", "euribor", "margin", "coupon"],
    "MATURITY_REPAYMENT": ["maturity", "tenor", "repayment", "amortization", "grace period"],
    "SECURITY_PACKAGE": ["collateral", "security", "pledge", "mortgage", "guarantee"],
    "CONDITIONS_PRECEDENT": ["condition precedent", "cp", "before disbursement", "prior to disbursement"],
    "UNDERTAKINGS": ["undertaking", "reporting", "information covenant", "negative pledge"],
    "DEFAULT_TERMINATION": ["default", "event of default", "termination", "acceleration"],
}

PROFILE_FOCUS = {
    "EBRD": ["CAPEX", "LOAN", "DSCR", "EQUITY", "GRANT", "COVENANT", "LENDER"],
    "EIB": ["CAPEX", "LOAN", "DSCR", "WACC", "IRR", "NPV", "LENDER"],
    "IFC": ["CAPEX", "LOAN", "DSCR", "EBITDA", "REVENUE", "COLLATERAL", "COVENANT"],
    "BANK": ["LOAN", "DSCR", "INTEREST_RATE", "MATURITY", "COLLATERAL", "COVENANT"],
    "BOARD": ["CAPEX", "LOAN", "EQUITY", "GRANT", "RISK", "COVENANT"],
}


@dataclass(frozen=True)
class BankPaths:
    base_dir: Path
    output_dir: Path
    memo_md: Path
    memo_json: Path
    checklist_csv: Path
    gap_register_csv: Path
    evidence_index_csv: Path
    covenant_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def short_text(value: Any, max_chars: int = 1200) -> str:
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> BankPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return BankPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        memo_md=output_dir / OUTPUT_MEMO_MD,
        memo_json=output_dir / OUTPUT_MEMO_JSON,
        checklist_csv=output_dir / OUTPUT_CHECKLIST_CSV,
        gap_register_csv=output_dir / OUTPUT_GAP_REGISTER_CSV,
        evidence_index_csv=output_dir / OUTPUT_EVIDENCE_INDEX_CSV,
        covenant_csv=output_dir / OUTPUT_COVENANT_CSV,
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
        "Profile_Area": req["Area"],
        "Requirement": req["Requirement"],
        "Source_Report": source,
        "Required_Field": field,
        "Observed_Value": value,
        "Check_Status": status,
        "Gap_Status": gap_status,
        "Critical": bool(req.get("Critical")),
        "Reason": reason,
        "Recommended_Action": requirement_action(req, status),
    }


def requirement_action(req: dict[str, Any], status: str) -> str:
    if status == CHECK_PASS:
        return "No immediate action; preserve evidence in bankability pack."

    area = req.get("Area")
    if area == "Audit Integrity":
        return "Rerun Step 08 and verify latest_audit_record."
    if area == "Citation Integrity":
        return "Rerun Step 13 and fix source_path/chunk_id traceability for financial evidence."
    if area == "Conflict Control":
        return "Resolve financial conflicts through Step 14 and SSOT review before model/lender use."
    if area == "Financial Signals":
        return "Rerun Step 16 with CAPEX/loan/DSCR/WACC/IRR/NPV-focused query."
    if area == "Critical Risk Control":
        return "Close or formally exception critical risks before lender reliance."
    if area == "Document Review":
        return "Review P0 documents before bankability reliance."
    if area == "Lender DD Linkage":
        return "Review lender DD gap register and close blocker/high gaps."
    if area == "Board Decision Linkage":
        return "Review board memo conditions before treating pack as approved."
    if area == "Legal/ESG Dependency":
        return "Review legal/ESG blockers that can affect bankability."
    if area == "Evidence Availability":
        return "Rerun Step 06/12 with lender-focused query and rebuild downstream reports."
    return "Manual finance/lender review required."


def build_checklist(reports: dict[str, dict[str, Any] | None], profile: str) -> list[dict[str, Any]]:
    rows = []
    focus = set(PROFILE_FOCUS.get(profile.upper(), []))
    for req in BANKABILITY_REQUIREMENTS:
        row = evaluate_requirement(req, reports)
        row["Profile"] = profile.upper()
        row["Profile_Focus"] = row["Profile_Area"] in focus
        rows.append(row)
    return rows


def detect_bankability_categories(text: str) -> list[str]:
    lower = text.lower()
    cats = []
    for category, terms in BANKABILITY_KEYWORDS.items():
        for term in terms:
            if term.lower() in lower:
                cats.append(category)
                break
    return sorted(set(cats))


def detect_covenant_categories(text: str) -> list[str]:
    lower = text.lower()
    cats = []
    for category, terms in COVENANT_KEYWORDS.items():
        for term in terms:
            if term.lower() in lower:
                cats.append(category)
                break
    return sorted(set(cats))


def build_bankability_evidence_index(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    financial_report = reports.get("financial_signals")
    financial_rows = financial_report.get("signals", []) if isinstance(financial_report, dict) else []
    if isinstance(financial_rows, list):
        for item in financial_rows:
            if not isinstance(item, dict):
                continue
            text = " ".join([
                str(item.get("Signal_Category") or ""),
                str(item.get("Value_Type") or ""),
                str(item.get("Canonical_Value") or ""),
                str(item.get("Context") or ""),
                str(item.get("Source_Path") or ""),
            ])
            cats = detect_bankability_categories(text) or [str(item.get("Signal_Category") or "FINANCIAL_SIGNAL")]
            rows.append({
                "Evidence_ID": "BANK-FIN-" + sha256_text(str(item.get("Signal_ID") or item.get("Source_Path") or ""))[:14],
                "Bankability_Category": "; ".join(cats),
                "Evidence_Type": "FINANCIAL_SIGNAL",
                "Rank": item.get("Evidence_Rank"),
                "Final_Score": item.get("Confidence_Score"),
                "Source_Path": item.get("Source_Path"),
                "File_Name": item.get("File_Name"),
                "Chunk_ID": item.get("Chunk_ID"),
                "Section_Label": item.get("Section_Label"),
                "Value_Type": item.get("Value_Type"),
                "Canonical_Value": item.get("Canonical_Value"),
                "Unit": item.get("Unit"),
                "Status": item.get("Financial_Status"),
                "Severity": item.get("Severity"),
                "Excerpt": short_text(item.get("Context"), 1200),
                "Recommended_Use": item.get("Recommended_Action"),
            })

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
            cats = detect_bankability_categories(text)
            if not cats:
                continue
            rows.append({
                "Evidence_ID": "BANK-EVID-" + sha256_text(str(item.get("chunk_id") or item.get("source_path") or ""))[:14],
                "Bankability_Category": "; ".join(cats),
                "Evidence_Type": "EVIDENCE_CHUNK",
                "Rank": item.get("rank"),
                "Final_Score": item.get("final_score"),
                "Source_Path": item.get("source_path"),
                "File_Name": item.get("file_name"),
                "Chunk_ID": item.get("chunk_id"),
                "Section_Label": item.get("section_label"),
                "Value_Type": None,
                "Canonical_Value": None,
                "Unit": None,
                "Status": None,
                "Severity": None,
                "Excerpt": short_text(item.get("excerpt"), 1200),
                "Recommended_Use": "Manual finance/lender review; not final model input.",
            })

    return rows


def build_covenant_review(reports: dict[str, dict[str, Any] | None], bank_evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in bank_evidence:
        text = " ".join([
            str(item.get("Bankability_Category") or ""),
            str(item.get("Excerpt") or ""),
            str(item.get("Source_Path") or ""),
            str(item.get("Canonical_Value") or ""),
        ])
        cov_cats = detect_covenant_categories(text)
        for cat in cov_cats:
            rows.append({
                "Covenant_ID": "COV-" + sha256_text(cat + "|" + str(item.get("Evidence_ID")))[:14],
                "Covenant_Category": cat,
                "Evidence_ID": item.get("Evidence_ID"),
                "Source_Path": item.get("Source_Path"),
                "Chunk_ID": item.get("Chunk_ID"),
                "Observed_Value": item.get("Canonical_Value"),
                "Value_Type": item.get("Value_Type"),
                "Confidence_Score": item.get("Final_Score"),
                "Review_Status": "REVIEW_REQUIRED",
                "Recommended_Action": covenant_action(cat),
                "Excerpt": short_text(item.get("Excerpt"), 900),
            })

    if not rows:
        rows.append({
            "Covenant_ID": "COV-NO-COVENANT-EVIDENCE",
            "Covenant_Category": "NO_COVENANT_EVIDENCE_DETECTED",
            "Evidence_ID": None,
            "Source_Path": None,
            "Chunk_ID": None,
            "Observed_Value": None,
            "Value_Type": None,
            "Confidence_Score": None,
            "Review_Status": "REVIEW_REQUIRED",
            "Recommended_Action": "Rerun retrieval with loan term sheet/covenant/security package keywords or mark covenants as not yet available.",
            "Excerpt": "",
        })

    return rows


def covenant_action(category: str) -> str:
    if category == "DSCR_COVENANT":
        return "Validate DSCR threshold, calculation basis, testing date and model consistency."
    if category == "LEVERAGE_COVENANT":
        return "Validate leverage/gearing definition and debt/equity measurement basis."
    if category == "INTEREST_RATE":
        return "Confirm base rate, margin, fixed/floating logic and sensitivity impact."
    if category == "MATURITY_REPAYMENT":
        return "Confirm tenor, grace period, amortization and repayment schedule."
    if category == "SECURITY_PACKAGE":
        return "Confirm collateral, guarantees, perfection steps and legal enforceability."
    if category == "CONDITIONS_PRECEDENT":
        return "List CPs and map each to evidence owner and closure status."
    if category == "UNDERTAKINGS":
        return "Review reporting and negative/positive undertakings."
    if category == "DEFAULT_TERMINATION":
        return "Review default triggers, cure periods and acceleration rights."
    return "Manual covenant review required."


def build_gap_register(checklist: list[dict[str, Any]], bank_evidence: list[dict[str, Any]], covenant_rows: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for row in checklist:
        if row["Check_Status"] == CHECK_PASS:
            continue
        gaps.append({
            "Gap_ID": "BANK-GAP-" + sha256_text(row["Requirement_ID"])[:12],
            "Requirement_ID": row["Requirement_ID"],
            "Area": row["Profile_Area"],
            "Gap_Status": row["Gap_Status"],
            "Severity": "CRITICAL" if row["Gap_Status"] == GAP_OPEN_CRITICAL else "HIGH" if row["Gap_Status"] == GAP_OPEN_HIGH else "MEDIUM",
            "Description": row["Requirement"],
            "Observed_Value": row["Observed_Value"],
            "Reason": row["Reason"],
            "Recommended_Action": row["Recommended_Action"],
            "Source_Report": row["Source_Report"],
            "Owner": "Finance / Danijela / TITAN Operator",
            "Due_Logic": "Before lender/board reliance" if row["Critical"] else "Before final bankability pack freeze",
            "Evidence_Closure_Rule": "Update source report or attach finance/lender review until status becomes PASS or formal exception is recorded.",
        })

    category_count: dict[str, int] = {}
    for item in bank_evidence:
        for cat in str(item.get("Bankability_Category") or "").split(";"):
            cat = cat.strip()
            if cat:
                category_count[cat] = category_count.get(cat, 0) + 1

    focus = set(PROFILE_FOCUS.get(profile.upper(), []))

    for category, count in sorted(category_count.items()):
        severity = "HIGH" if category in focus else "MEDIUM"
        gaps.append({
            "Gap_ID": "BANK-CAT-" + sha256_text(category)[:12],
            "Requirement_ID": "BANK-CATEGORY-COVERAGE",
            "Area": category,
            "Gap_Status": GAP_MONITOR,
            "Severity": severity,
            "Description": f"Evidence references bankability category {category}.",
            "Observed_Value": count,
            "Reason": f"{count} evidence/financial signal records detected for {category}.",
            "Recommended_Action": "Finance/lender reviewer should confirm whether the evidence is sufficient for model/DD use.",
            "Source_Report": "financial_signals_report.json / evidence_pack_report.json",
            "Owner": "Finance / Danijela",
            "Due_Logic": "Before final lender pack freeze",
            "Evidence_Closure_Rule": "Reviewed by finance/lender reviewer and documented as cleared / open / not applicable.",
        })

    missing_core = []
    for core in ["CAPEX", "LOAN", "DSCR"]:
        if category_count.get(core, 0) == 0:
            missing_core.append(core)

    for core in missing_core:
        gaps.append({
            "Gap_ID": "BANK-MISSING-" + core,
            "Requirement_ID": "BANK-CORE-EVIDENCE",
            "Area": core,
            "Gap_Status": GAP_OPEN_HIGH,
            "Severity": "HIGH",
            "Description": f"No direct {core} evidence detected in bankability evidence index.",
            "Observed_Value": 0,
            "Reason": f"{core} is usually material for CAPEX/loan bankability review.",
            "Recommended_Action": f"Rerun Step 06 with {core}-focused query and rerun Steps 12, 16, 17, 18, 26.",
            "Source_Report": "financial_signals_report.json / evidence_pack_report.json",
            "Owner": "Finance / Danijela",
            "Due_Logic": "Before lender reliance",
            "Evidence_Closure_Rule": f"{core} evidence must be found or formally marked not applicable.",
        })

    if covenant_rows and covenant_rows[0].get("Covenant_ID") == "COV-NO-COVENANT-EVIDENCE":
        gaps.append({
            "Gap_ID": "BANK-GAP-COVENANTS",
            "Requirement_ID": "BANK-COVENANT-EVIDENCE",
            "Area": "COVENANT",
            "Gap_Status": GAP_OPEN_MEDIUM,
            "Severity": "MEDIUM",
            "Description": "No covenant evidence detected.",
            "Observed_Value": 0,
            "Reason": "Loan covenant/term sheet documents may not yet exist or query did not retrieve them.",
            "Recommended_Action": "Retrieve lender term sheet, loan agreement draft or covenant schedule when available.",
            "Source_Report": "covenant_review",
            "Owner": "Finance / Legal / Danijela",
            "Due_Logic": "Before loan documentation review",
            "Evidence_Closure_Rule": "Covenant register must be populated or scope marked not applicable.",
        })

    return gaps


def determine_bankability_status(checklist: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> tuple[str, list[str]]:
    reasons = []
    missing = [x for x in checklist if x["Check_Status"] == CHECK_MISSING]
    critical_fail = [x for x in checklist if x["Critical"] and x["Check_Status"] == CHECK_FAIL]
    critical_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_CRITICAL]
    high_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_HIGH]

    if missing:
        reasons.append(f"Missing CAPEX/loan source reports: {len(missing)}")
        return BANK_INCOMPLETE, reasons
    if critical_fail or critical_gaps:
        reasons.append(f"Critical CAPEX/loan bankability blockers: checks={len(critical_fail)}, gaps={len(critical_gaps)}")
        return BANK_BLOCKED, reasons
    if high_gaps or any(x["Check_Status"] == CHECK_WARNING for x in checklist):
        reasons.append(f"CAPEX/loan bankability review required: high_gaps={len(high_gaps)}; warnings={sum(1 for x in checklist if x['Check_Status'] == CHECK_WARNING)}")
        return BANK_REVIEW_REQUIRED, reasons

    reasons.append("Core CAPEX/loan traceability gates are clean enough for manual finance/lender review pack.")
    return BANK_READY, reasons


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
            "capex_loan_analysis_consolidates_existing_reports_only": True,
            "not_financial_advice_or_lender_approval": True,
            "source_documents_not_modified": True,
            "manual_finance_lender_review_required": True,
            "audit_precedes_decision": True,
        },
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_memo(
    reports: dict[str, dict[str, Any] | None],
    checklist: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    bank_evidence: list[dict[str, Any]],
    covenant_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    profile: str,
    strict: bool,
) -> dict[str, Any]:
    bank_status, reasons = determine_bankability_status(checklist, gaps)

    latest_answer = reports.get("latest_answer") or {}
    answer_conf = latest_answer.get("confidence") if isinstance(latest_answer.get("confidence"), dict) else {}

    memo = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "CAPEX_LOAN_BANKABILITY_ANALYSIS_AUDIT_LOCKED",
        "profile": profile.upper(),
        "strict_mode": strict,
        "bankability_status": bank_status,
        "bankability_status_reasons": reasons,
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
            "bankability_evidence_rows": len(bank_evidence),
            "covenant_review_rows": len(covenant_rows),
            "financial_signals": safe_int(nested_get(reports.get("financial_signals"), "summary.total_signals", 0)),
            "financial_review_required": safe_int(nested_get(reports.get("financial_signals"), "summary.review_required", 0)),
            "financial_conflict_blocked": safe_int(nested_get(reports.get("financial_signals"), "summary.conflict_blocked", 0)),
            "audit_status": nested_get(reports.get("latest_audit_record"), "audit_status"),
            "citation_status": nested_get(reports.get("citation_verification"), "verification_status"),
            "conflict_status": nested_get(reports.get("conflict_report"), "summary.institutional_status"),
            "critical_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0)),
            "high_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0)),
            "p0_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0)),
            "p1_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0)),
            "lender_dd_status": nested_get(reports.get("lender_dd_pack"), "dd_status"),
            "board_decision_status": nested_get(reports.get("board_memo"), "decision_status"),
            "legal_status": nested_get(reports.get("legal_compliance"), "legal_status"),
            "esg_status": nested_get(reports.get("esg_permitting"), "esg_status"),
        },
        "checklist": checklist,
        "gap_register": gaps,
        "bankability_evidence_index": bank_evidence,
        "covenant_review": covenant_rows,
        "top_financial_signals": top_collection(reports.get("financial_signals"), "signals", 40),
        "top_risks": top_collection(reports.get("risk_signals"), "signals", 25),
        "top_conflicts": top_collection(reports.get("conflict_report"), "conflicts", 20),
        "top_documents": top_collection(reports.get("document_priority"), "documents", 25),
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "manifest_sha256": manifest.get("manifest_sha256"),
        "governance_rule": {
            "not_financial_advice_or_lender_approval": True,
            "manual_finance_lender_review_required": True,
            "consolidates_existing_reports_only": True,
            "no_new_unsupported_claims": True,
            "source_documents_not_modified": True,
            "json_reports_and_original_sources_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    memo["capex_loan_bankability_memo_sha256"] = sha256_json(memo)
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
        "Profile",
        "Profile_Area",
        "Profile_Focus",
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
        "Bankability_Category",
        "Evidence_Type",
        "Rank",
        "Final_Score",
        "Source_Path",
        "File_Name",
        "Chunk_ID",
        "Section_Label",
        "Value_Type",
        "Canonical_Value",
        "Unit",
        "Status",
        "Severity",
        "Excerpt",
        "Recommended_Use",
    ])


def write_covenant_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Covenant_ID",
        "Covenant_Category",
        "Evidence_ID",
        "Source_Path",
        "Chunk_ID",
        "Observed_Value",
        "Value_Type",
        "Confidence_Score",
        "Review_Status",
        "Recommended_Action",
        "Excerpt",
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
            f"{md_escape(row.get('Profile_Area'))} | "
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
    for row in rows[:120]:
        lines.append(
            f"| {md_escape(row.get('Gap_ID'))} | "
            f"{md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Gap_Status'))} | "
            f"{md_escape(short_text(row.get('Reason'), 260))} | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def evidence_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No CAPEX/loan evidence rows."
    lines = [
        "| Category | Type | Value | Score | Source | Chunk | Use |",
        "|---|---|---|---:|---|---|---|",
    ]
    for row in rows[:120]:
        lines.append(
            f"| {md_escape(row.get('Bankability_Category'))} | "
            f"{md_escape(row.get('Evidence_Type'))} | "
            f"{md_escape(row.get('Canonical_Value'))} | "
            f"{row.get('Final_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"`{md_escape(row.get('Chunk_ID'))}` | "
            f"{md_escape(row.get('Recommended_Use'))} |"
        )
    return "\n".join(lines)


def covenants_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No covenant review rows."
    lines = [
        "| Covenant | Value | Confidence | Source | Action |",
        "|---|---|---:|---|---|",
    ]
    for row in rows[:80]:
        lines.append(
            f"| {md_escape(row.get('Covenant_Category'))} | "
            f"{md_escape(row.get('Observed_Value'))} | "
            f"{row.get('Confidence_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def memo_to_markdown(memo: dict[str, Any]) -> str:
    snapshot = memo.get("executive_snapshot", {}) if isinstance(memo.get("executive_snapshot"), dict) else {}
    metrics = memo.get("metrics", {}) if isinstance(memo.get("metrics"), dict) else {}

    metric_lines = ["| Metric | Value |", "|---|---|"]
    for k, v in metrics.items():
        metric_lines.append(f"| {md_escape(k)} | {md_escape(v)} |")

    return f"""# TITAN CAPEX & Loan Bankability Analysis Memo

## 1. Memo Identity

| Field | Value |
|---|---|
| Created At | {memo.get("created_at")} |
| Profile | {memo.get("profile")} |
| Bankability Status | {memo.get("bankability_status")} |
| Query | {md_escape(memo.get("query"))} |
| Memo SHA-256 | `{memo.get("capex_loan_bankability_memo_sha256")}` |

**Status reasons**

```json
{json.dumps(memo.get("bankability_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Important Limitation

```text
This is not financial advice, lender approval, a valuation, or a complete financial model.
It is an evidence-linked CAPEX/loan/bankability analysis for manual finance and lender review.
Final model inputs and credit conclusions must be approved by authorized finance/lender reviewers.
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

## 5. CAPEX / Loan Bankability Checklist

{checklist_md(memo.get("checklist", []))}

---

## 6. CAPEX / Loan Gap Register

{gaps_md(memo.get("gap_register", []))}

---

## 7. Bankability Evidence Index

{evidence_md(memo.get("bankability_evidence_index", []))}

---

## 8. Covenant Review

{covenants_md(memo.get("covenant_review", []))}

---

## 9. Top Financial Signals

```json
{json.dumps(memo.get("top_financial_signals", []), indent=2, ensure_ascii=False)[:14000]}
```

---

## 10. Top Risks

```json
{json.dumps(memo.get("top_risks", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 11. Top Conflicts

```json
{json.dumps(memo.get("top_conflicts", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 12. Governance Rule

```text
Not financial advice or lender approval.
Manual finance/lender review required.
Consolidates existing reports only.
No new unsupported claims.
Source documents are not modified.
JSON reports and original sources remain authoritative.
Audit precedes decision.
```
"""


def print_summary(memo: dict[str, Any], paths: BankPaths) -> None:
    metrics = memo.get("metrics", {}) if isinstance(memo.get("metrics"), dict) else {}
    print("=" * 100)
    print("TITAN CAPEX & LOAN BANKABILITY ANALYZER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Profile:                  {memo.get('profile')}")
    print(f"Bankability status:       {memo.get('bankability_status')}")
    print(f"Checklist pass/warn/fail: {metrics.get('checklist_pass')}/{metrics.get('checklist_warning')}/{metrics.get('checklist_fail')}")
    print(f"Critical gaps:            {metrics.get('critical_gaps')}")
    print(f"High gaps:                {metrics.get('high_gaps')}")
    print(f"Evidence rows:             {metrics.get('bankability_evidence_rows')}")
    print(f"Covenant rows:             {metrics.get('covenant_review_rows')}")
    print("-" * 100)
    print(f"Memo Markdown:            {paths.memo_md}")
    print(f"Memo JSON:                {paths.memo_json}")
    print(f"Checklist CSV:            {paths.checklist_csv}")
    print(f"Gap Register CSV:         {paths.gap_register_csv}")
    print(f"Evidence Index CSV:       {paths.evidence_index_csv}")
    print(f"Covenant CSV:             {paths.covenant_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 26 — CAPEX & loan bankability analyzer.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--profile", default="EBRD", choices=["EBRD", "EIB", "IFC", "BANK", "BOARD"], help="Finance/lender review profile.")
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
        checklist = build_checklist(reports, args.profile)
        bank_evidence = build_bankability_evidence_index(reports)
        covenant_rows = build_covenant_review(reports, bank_evidence)
        gaps = build_gap_register(checklist, bank_evidence, covenant_rows, args.profile)
        copied_files = copy_source_exports(base_dir, paths.output_dir, copy_files=not bool(args.no_copy_files))
        manifest = build_manifest(base_dir, paths.output_dir, copied_files)

        memo = build_memo(
            reports=reports,
            checklist=checklist,
            gaps=gaps,
            bank_evidence=bank_evidence,
            covenant_rows=covenant_rows,
            manifest=manifest,
            profile=args.profile,
            strict=bool(args.strict),
        )

        markdown = memo_to_markdown(memo)

        write_json(paths.memo_json, memo)
        write_text(paths.memo_md, markdown)
        write_checklist_csv(paths.checklist_csv, checklist)
        write_gap_csv(paths.gap_register_csv, gaps)
        write_evidence_csv(paths.evidence_index_csv, bank_evidence)
        write_covenant_csv(paths.covenant_csv, covenant_rows)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "CAPEX_LOAN_BANKABILITY_ANALYSIS_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "profile": args.profile,
            "bankability_status": memo.get("bankability_status"),
            "memo_sha256": memo.get("capex_loan_bankability_memo_sha256"),
            "manifest_sha256": manifest.get("manifest_sha256"),
            "outputs": {
                "memo_md": str(paths.memo_md),
                "memo_json": str(paths.memo_json),
                "checklist_csv": str(paths.checklist_csv),
                "gap_register_csv": str(paths.gap_register_csv),
                "evidence_index_csv": str(paths.evidence_index_csv),
                "covenant_csv": str(paths.covenant_csv),
                "manifest_json": str(paths.manifest_json),
            },
        })

        print_summary(memo, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "CAPEX_LOAN_BANKABILITY_ANALYSIS_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "profile": args.profile,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN CAPEX & LOAN BANKABILITY ANALYZER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
