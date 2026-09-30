#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
25_esg_permitting_risk_analyzer.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 25 — ESG & Permitting Risk Analyzer
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build an ESG / EHS / permitting risk analysis from existing TITAN RAG outputs.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT provide legal, environmental or engineering certification.
It consolidates evidence-linked ESG/EHS/permitting signals for manual expert review.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MEMO.json
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/risk_signals_report.json
05_reports/document_priority_rank.json
05_reports/evidence_pack_report.json
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json

Outputs
-------
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_MEMO.md
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_MEMO.json
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_CHECKLIST.csv
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_GAP_REGISTER.csv
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_EVIDENCE_INDEX.csv
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_MANIFEST.json
05_reports/esg_permitting_risk_analysis/source_exports/...
06_logs/esg_permitting_risk_analyzer_audit.jsonl
06_logs/esg_permitting_risk_analyzer_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\25_esg_permitting_risk_analyzer.py" --print

Profile examples
----------------
python ".\\08_scripts\\25_esg_permitting_risk_analyzer.py" --profile EBRD --print
python ".\\08_scripts\\25_esg_permitting_risk_analyzer.py" --profile IFC --print
python ".\\08_scripts\\25_esg_permitting_risk_analyzer.py" --profile LOCAL_PERMITTING --print
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


SCRIPT_NAME = "25_esg_permitting_risk_analyzer.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "esg_permitting_risk_analysis"

OUTPUT_MEMO_MD = "TITAN_ESG_PERMITTING_MEMO.md"
OUTPUT_MEMO_JSON = "TITAN_ESG_PERMITTING_MEMO.json"
OUTPUT_CHECKLIST_CSV = "TITAN_ESG_PERMITTING_CHECKLIST.csv"
OUTPUT_GAP_REGISTER_CSV = "TITAN_ESG_PERMITTING_GAP_REGISTER.csv"
OUTPUT_EVIDENCE_INDEX_CSV = "TITAN_ESG_PERMITTING_EVIDENCE_INDEX.csv"
OUTPUT_MANIFEST_JSON = "TITAN_ESG_PERMITTING_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "esg_permitting_risk_analyzer_audit.jsonl"
ERROR_LOG = Path("06_logs") / "esg_permitting_risk_analyzer_errors.jsonl"

ESG_READY = "ESG_PERMITTING_READY_FOR_REVIEW"
ESG_REVIEW_REQUIRED = "ESG_PERMITTING_REVIEW_REQUIRED"
ESG_BLOCKED = "ESG_PERMITTING_BLOCKED"
ESG_INCOMPLETE = "ESG_PERMITTING_INCOMPLETE"

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
    "legal_compliance": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "lender_dd_pack": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "evidence_report": Path("05_reports") / "evidence_pack_report.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_answer": Path("05_reports") / "latest_rag_answer.json",
}

SOURCE_EXPORT_FILES = {
    "legal_memo_md": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.md",
    "legal_memo_json": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "legal_checklist_csv": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_CHECKLIST.csv",
    "legal_gap_register_csv": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_GAP_REGISTER.csv",
    "board_memo_md": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.md",
    "lender_dd_pack_md": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.md",
    "risk_signals_csv": Path("05_reports") / "risk_signals.csv",
    "document_priority_csv": Path("05_reports") / "document_priority_rank.csv",
    "evidence_report_csv": Path("05_reports") / "evidence_pack_report.csv",
    "evidence_sources_csv": Path("05_reports") / "evidence_sources.csv",
    "citation_report_csv": Path("05_reports") / "citation_verification_report.csv",
    "conflict_report_csv": Path("05_reports") / "conflict_report.csv",
}

ESG_REQUIREMENTS = [
    {
        "Requirement_ID": "ESG-001",
        "Area": "Evidence Traceability",
        "Requirement": "ESG/EHS/permitting claims must be traceable to source_path and chunk_id.",
        "Source": "citation_verification",
        "Field": "verification_status",
        "Pass_Values": ["CITATION_VERIFICATION_PASS"],
        "Warning_Values": ["CITATION_VERIFICATION_PASS_WITH_WARNINGS", "CITATION_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "ESG-002",
        "Area": "Audit Integrity",
        "Requirement": "Latest evidence set must have a valid audit record.",
        "Source": "latest_audit_record",
        "Field": "audit_status",
        "Pass_Values": ["AUDIT_PASS"],
        "Warning_Values": ["AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "ESG-003",
        "Area": "Critical Risk Control",
        "Requirement": "Critical risks must be zero or formally exceptioned before lender/board reliance.",
        "Source": "risk_signals",
        "Field": "summary.critical_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "ESG-004",
        "Area": "Permit / Regulatory Evidence",
        "Requirement": "Evidence pack should contain permit/regulatory evidence if permitting is in project scope.",
        "Source": "evidence_report",
        "Field": "summary.source_file_count",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
    },
    {
        "Requirement_ID": "ESG-005",
        "Area": "Document Review",
        "Requirement": "P0 documents must be reviewed before ESG/permitting reliance.",
        "Source": "document_priority",
        "Field": "summary.p0_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "ESG-006",
        "Area": "Conflict Governance",
        "Requirement": "Material ESG/permit/status conflicts must be resolved or escalated.",
        "Source": "conflict_report",
        "Field": "summary.institutional_status",
        "Pass_Values": ["NO_CONFLICTS_DETECTED"],
        "Warning_Values": ["CONFLICTS_DETECTED_REVIEW_REQUIRED", "HIGH_CONFLICT_RISK_MANUAL_REVIEW"],
        "Critical": False,
    },
    {
        "Requirement_ID": "ESG-007",
        "Area": "Legal Compliance Linkage",
        "Requirement": "Legal/compliance memo should not be blocked or incomplete.",
        "Source": "legal_compliance",
        "Field": "legal_status",
        "Pass_Values": ["LEGAL_COMPLIANCE_READY_FOR_REVIEW", "LEGAL_COMPLIANCE_REVIEW_REQUIRED"],
        "Warning_Values": ["LEGAL_COMPLIANCE_REVIEW_REQUIRED"],
        "Critical": False,
    },
    {
        "Requirement_ID": "ESG-008",
        "Area": "Board / Lender Linkage",
        "Requirement": "Board memo and lender DD pack should exist for ESG governance linkage.",
        "Source": "lender_dd_pack",
        "Field": "dd_status",
        "Pass_Values": ["LENDER_DD_READY_FOR_REVIEW", "LENDER_DD_REVIEW_REQUIRED"],
        "Warning_Values": ["LENDER_DD_REVIEW_REQUIRED"],
        "Critical": False,
    },
]

ESG_KEYWORDS = {
    "ENVIRONMENTAL_PERMIT": [
        "environmental permit", "permit", "license", "approval", "eia", "esia",
        "environmental impact", "dozvol", "odobrenje", "procjena uticaja", "procena uticaja",
    ],
    "EHS_HEALTH_SAFETY": [
        "health and safety", "occupational safety", "ehs", "hse", "work safety",
        "zaštita na radu", "zastita na radu", "bezbjednost", "bezbednost",
    ],
    "ESG_GENERAL": [
        "esg", "environmental", "social", "governance", "sustainability", "održivost", "odrzivost",
    ],
    "LAND_USE_SITE": [
        "land", "site", "location", "zoning", "urban planning", "construction permit",
        "zemljište", "zemljiste", "lokacija", "urbanistič", "urbanistick", "građevinska dozvola", "gradjevinska dozvola",
    ],
    "POLLUTION_EMISSIONS": [
        "emission", "pollution", "waste", "water", "air", "noise", "hazardous", "otpad",
        "emisija", "zagađenje", "zagadjenje", "voda", "vazduh", "buka", "opasan",
    ],
    "SOCIAL_STAKEHOLDER": [
        "stakeholder", "community", "public consultation", "resettlement", "grievance",
        "zajednica", "javna rasprava", "pritužba", "prituzba",
    ],
    "BIODIVERSITY": [
        "biodiversity", "habitat", "protected area", "species", "natura", "biodiverzitet",
        "zaštićeno područje", "zasticeno podrucje",
    ],
    "CLIMATE_ENERGY": [
        "climate", "carbon", "co2", "energy efficiency", "greenhouse", "ghg",
        "klima", "ugljen", "energetska efikasnost",
    ],
    "LABOR_WORKING_CONDITIONS": [
        "labor", "labour", "worker", "working conditions", "employment", "radnik", "radni uslovi",
    ],
    "SUPPLY_CHAIN": [
        "supplier", "supply chain", "procurement", "vendor", "dobavljač", "dobavljac", "nabavka",
    ],
}

PROFILE_FOCUS = {
    "EBRD": ["ENVIRONMENTAL_PERMIT", "EHS_HEALTH_SAFETY", "SOCIAL_STAKEHOLDER", "LABOR_WORKING_CONDITIONS", "SUPPLY_CHAIN"],
    "IFC": ["ENVIRONMENTAL_PERMIT", "EHS_HEALTH_SAFETY", "BIODIVERSITY", "SOCIAL_STAKEHOLDER", "LABOR_WORKING_CONDITIONS"],
    "EIB": ["ENVIRONMENTAL_PERMIT", "CLIMATE_ENERGY", "ESG_GENERAL", "LAND_USE_SITE", "POLLUTION_EMISSIONS"],
    "LOCAL_PERMITTING": ["ENVIRONMENTAL_PERMIT", "LAND_USE_SITE", "POLLUTION_EMISSIONS", "EHS_HEALTH_SAFETY"],
    "BOARD": ["ESG_GENERAL", "ENVIRONMENTAL_PERMIT", "EHS_HEALTH_SAFETY", "CRITICAL_RISK_CONTROL"],
}


@dataclass(frozen=True)
class ESGPaths:
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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> ESGPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return ESGPaths(
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
        return "No immediate action; preserve evidence in ESG/permitting pack."

    area = req.get("Area")
    if area == "Evidence Traceability":
        return "Rerun Step 13 and fix source_path/chunk_id traceability."
    if area == "Audit Integrity":
        return "Rerun Step 08 and verify audit status."
    if area == "Critical Risk Control":
        return "Close or formally exception critical risks."
    if area == "Permit / Regulatory Evidence":
        return "Retrieve or identify permit/regulatory evidence; rerun Step 06/12 with permit-focused query."
    if area == "Document Review":
        return "Review P0 documents before ESG/permitting reliance."
    if area == "Conflict Governance":
        return "Resolve or escalate ESG/permit conflicts through SSOT review."
    if area == "Legal Compliance Linkage":
        return "Review legal compliance memo and close blocking legal gaps."
    if area == "Board / Lender Linkage":
        return "Review lender DD pack and board memo linkage."
    return "Manual ESG/permitting review required."


def build_checklist(reports: dict[str, dict[str, Any] | None], profile: str) -> list[dict[str, Any]]:
    rows = []
    focus = set(PROFILE_FOCUS.get(profile.upper(), []))
    for req in ESG_REQUIREMENTS:
        row = evaluate_requirement(req, reports)
        row["Profile"] = profile.upper()
        row["Profile_Focus"] = row["Profile_Area"] in focus
        rows.append(row)
    return rows


def detect_esg_categories(text: str) -> list[str]:
    lower = text.lower()
    categories = []
    for category, terms in ESG_KEYWORDS.items():
        for term in terms:
            if term.lower() in lower:
                categories.append(category)
                break
    return sorted(set(categories))


def build_esg_evidence_index(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
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
            categories = detect_esg_categories(text)
            if not categories:
                continue

            rows.append({
                "Evidence_ID": "ESG-EVID-" + sha256_text(str(item.get("chunk_id") or item.get("source_path") or ""))[:14],
                "ESG_Category": "; ".join(categories),
                "Evidence_Type": "EVIDENCE_CHUNK",
                "Rank": item.get("rank"),
                "Final_Score": item.get("final_score"),
                "Source_Path": item.get("source_path"),
                "File_Name": item.get("file_name"),
                "Chunk_ID": item.get("chunk_id"),
                "Section_Label": item.get("section_label"),
                "Excerpt_SHA256": item.get("excerpt_sha256"),
                "Excerpt": short_text(item.get("excerpt"), 1200),
                "Recommended_Use": "Manual ESG/EHS/permitting review; not final expert determination.",
            })

    risk_report = reports.get("risk_signals")
    risks = risk_report.get("signals", []) if isinstance(risk_report, dict) else []

    if isinstance(risks, list):
        for risk in risks:
            if not isinstance(risk, dict):
                continue
            text = " ".join([str(risk.get("Risk_Type") or ""), str(risk.get("Context") or ""), str(risk.get("Source_Path") or "")])
            categories = detect_esg_categories(text)
            risk_type = str(risk.get("Risk_Type") or "")
            if categories or risk_type in {"PERMIT_REGULATORY_RISK", "LENDER_BANKABILITY_RISK", "COST_OVERRUN_RISK", "SCHEDULE_RISK"}:
                rows.append({
                    "Evidence_ID": "ESG-RISK-" + sha256_text(str(risk.get("Risk_ID") or ""))[:14],
                    "ESG_Category": "; ".join(categories) or risk_type,
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


def build_gap_register(checklist: list[dict[str, Any]], esg_evidence: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for row in checklist:
        if row["Check_Status"] == CHECK_PASS:
            continue
        gaps.append({
            "Gap_ID": "ESG-GAP-" + sha256_text(row["Requirement_ID"])[:12],
            "Requirement_ID": row["Requirement_ID"],
            "Area": row["Profile_Area"],
            "Gap_Status": row["Gap_Status"],
            "Severity": "CRITICAL" if row["Gap_Status"] == GAP_OPEN_CRITICAL else "HIGH" if row["Gap_Status"] == GAP_OPEN_HIGH else "MEDIUM",
            "Description": row["Requirement"],
            "Observed_Value": row["Observed_Value"],
            "Reason": row["Reason"],
            "Recommended_Action": row["Recommended_Action"],
            "Source_Report": row["Source_Report"],
            "Owner": "ESG/EHS/Permitting expert / Danijela / TITAN Operator",
            "Due_Logic": "Before lender/board reliance" if row["Critical"] else "Before final ESG pack freeze",
            "Evidence_Closure_Rule": "Update source report or attach expert review until status becomes PASS or formal exception is recorded.",
        })

    category_count: dict[str, int] = {}
    for item in esg_evidence:
        for cat in str(item.get("ESG_Category") or "").split(";"):
            cat = cat.strip()
            if cat:
                category_count[cat] = category_count.get(cat, 0) + 1

    profile_focus = set(PROFILE_FOCUS.get(profile.upper(), []))

    for category, count in sorted(category_count.items()):
        severity = "HIGH" if category in profile_focus else "MEDIUM"
        gaps.append({
            "Gap_ID": "ESG-CAT-" + sha256_text(category)[:12],
            "Requirement_ID": "ESG-CATEGORY-COVERAGE",
            "Area": category,
            "Gap_Status": GAP_MONITOR,
            "Severity": severity,
            "Description": f"Evidence references ESG/permitting category {category}.",
            "Observed_Value": count,
            "Reason": f"{count} evidence/risk records detected for {category}.",
            "Recommended_Action": "Expert should review category-specific evidence and classify as cleared / open / not applicable.",
            "Source_Report": "evidence_pack_report.json / risk_signals_report.json",
            "Owner": "ESG/EHS/Permitting expert / Danijela",
            "Due_Logic": "Before final lender/board ESG pack freeze",
            "Evidence_Closure_Rule": "Reviewed by expert and documented as cleared / open / not applicable.",
        })

    # If no ESG evidence was detected, create a focused gap.
    if not esg_evidence:
        gaps.append({
            "Gap_ID": "ESG-GAP-NO-EVIDENCE",
            "Requirement_ID": "ESG-EVIDENCE-COVERAGE",
            "Area": "ESG_EVIDENCE_COVERAGE",
            "Gap_Status": GAP_OPEN_HIGH,
            "Severity": "HIGH",
            "Description": "No ESG/EHS/permitting-specific evidence detected in current evidence pack.",
            "Observed_Value": 0,
            "Reason": "Current retrieval may not have used ESG/permitting query terms.",
            "Recommended_Action": "Rerun Step 06 with ESG/EHS/permitting-focused query and rerun Steps 12, 17, 18, 25.",
            "Source_Report": "evidence_pack_report.json",
            "Owner": "Danijela / TITAN Operator",
            "Due_Logic": "Before ESG/permitting reliance",
            "Evidence_Closure_Rule": "ESG evidence index must contain relevant records or scope must be formally marked not applicable.",
        })

    return gaps


def determine_esg_status(checklist: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> tuple[str, list[str]]:
    reasons = []

    missing = [x for x in checklist if x["Check_Status"] == CHECK_MISSING]
    critical_fail = [x for x in checklist if x["Critical"] and x["Check_Status"] == CHECK_FAIL]
    critical_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_CRITICAL]
    high_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_HIGH]

    if missing:
        reasons.append(f"Missing ESG/permitting source reports: {len(missing)}")
        return ESG_INCOMPLETE, reasons

    if critical_fail or critical_gaps:
        reasons.append(f"Critical ESG/permitting blockers: checks={len(critical_fail)}, gaps={len(critical_gaps)}")
        return ESG_BLOCKED, reasons

    if high_gaps or any(x["Check_Status"] == CHECK_WARNING for x in checklist):
        reasons.append(f"ESG/permitting review required: high_gaps={len(high_gaps)}; warnings={sum(1 for x in checklist if x['Check_Status'] == CHECK_WARNING)}")
        return ESG_REVIEW_REQUIRED, reasons

    reasons.append("Core ESG/permitting traceability gates are clean enough for manual expert review pack.")
    return ESG_READY, reasons


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
            "esg_permitting_analysis_consolidates_existing_reports_only": True,
            "not_environmental_or_permitting_certification": True,
            "source_documents_not_modified": True,
            "manual_expert_review_required": True,
            "audit_precedes_decision": True,
        },
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_memo(
    reports: dict[str, dict[str, Any] | None],
    checklist: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    esg_evidence: list[dict[str, Any]],
    manifest: dict[str, Any],
    profile: str,
    strict: bool,
) -> dict[str, Any]:
    esg_status, reasons = determine_esg_status(checklist, gaps)

    latest_answer = reports.get("latest_answer") or {}
    answer_conf = latest_answer.get("confidence") if isinstance(latest_answer.get("confidence"), dict) else {}

    memo = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "ESG_PERMITTING_RISK_ANALYSIS_AUDIT_LOCKED",
        "profile": profile.upper(),
        "strict_mode": strict,
        "esg_status": esg_status,
        "esg_status_reasons": reasons,
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
            "esg_evidence_rows": len(esg_evidence),
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
        "esg_evidence_index": esg_evidence,
        "top_risks": top_collection(reports.get("risk_signals"), "signals", 25),
        "top_conflicts": top_collection(reports.get("conflict_report"), "conflicts", 20),
        "top_documents": top_collection(reports.get("document_priority"), "documents", 25),
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "manifest_sha256": manifest.get("manifest_sha256"),
        "governance_rule": {
            "not_environmental_or_permitting_certification": True,
            "manual_esg_ehs_permitting_expert_review_required": True,
            "consolidates_existing_reports_only": True,
            "no_new_unsupported_claims": True,
            "source_documents_not_modified": True,
            "json_reports_and_original_sources_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    memo["esg_permitting_memo_sha256"] = sha256_json(memo)
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
        "ESG_Category",
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
        return "No ESG/permitting evidence rows."
    lines = [
        "| Category | Type | Score | Source | Chunk | Use |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows[:100]:
        lines.append(
            f"| {md_escape(row.get('ESG_Category'))} | "
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

    return f"""# TITAN ESG & Permitting Risk Analysis Memo

## 1. Memo Identity

| Field | Value |
|---|---|
| Created At | {memo.get("created_at")} |
| Profile | {memo.get("profile")} |
| ESG/Permitting Status | {memo.get("esg_status")} |
| Query | {md_escape(memo.get("query"))} |
| Memo SHA-256 | `{memo.get("esg_permitting_memo_sha256")}` |

**Status reasons**

```json
{json.dumps(memo.get("esg_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Important Limitation

```text
This is not an environmental, EHS or permitting certification.
This is an evidence-linked ESG/EHS/permitting risk analysis for manual expert review.
Final conclusions must be made by qualified ESG/EHS/permitting experts and authorized decision-makers.
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

## 5. ESG / Permitting Checklist

{checklist_md(memo.get("checklist", []))}

---

## 6. ESG / Permitting Gap Register

{gaps_md(memo.get("gap_register", []))}

---

## 7. ESG / Permitting Evidence Index

{evidence_md(memo.get("esg_evidence_index", []))}

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
Not environmental/EHS/permitting certification.
Manual expert review required.
Consolidates existing reports only.
No new unsupported claims.
Source documents are not modified.
JSON reports and original sources remain authoritative.
Audit precedes decision.
```
"""


def print_summary(memo: dict[str, Any], paths: ESGPaths) -> None:
    metrics = memo.get("metrics", {}) if isinstance(memo.get("metrics"), dict) else {}
    print("=" * 100)
    print("TITAN ESG & PERMITTING RISK ANALYZER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Profile:                  {memo.get('profile')}")
    print(f"ESG/Permitting status:    {memo.get('esg_status')}")
    print(f"Checklist pass/warn/fail: {metrics.get('checklist_pass')}/{metrics.get('checklist_warning')}/{metrics.get('checklist_fail')}")
    print(f"Critical gaps:            {metrics.get('critical_gaps')}")
    print(f"High gaps:                {metrics.get('high_gaps')}")
    print(f"ESG evidence rows:         {metrics.get('esg_evidence_rows')}")
    print("-" * 100)
    print(f"Memo Markdown:            {paths.memo_md}")
    print(f"Memo JSON:                {paths.memo_json}")
    print(f"Checklist CSV:            {paths.checklist_csv}")
    print(f"Gap Register CSV:         {paths.gap_register_csv}")
    print(f"Evidence Index CSV:       {paths.evidence_index_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 25 — ESG & permitting risk analyzer.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--profile", default="EBRD", choices=["EBRD", "IFC", "EIB", "LOCAL_PERMITTING", "BOARD"], help="ESG/permitting review profile.")
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
        esg_evidence = build_esg_evidence_index(reports)
        gaps = build_gap_register(checklist, esg_evidence, args.profile)
        copied_files = copy_source_exports(base_dir, paths.output_dir, copy_files=not bool(args.no_copy_files))
        manifest = build_manifest(base_dir, paths.output_dir, copied_files)

        memo = build_memo(
            reports=reports,
            checklist=checklist,
            gaps=gaps,
            esg_evidence=esg_evidence,
            manifest=manifest,
            profile=args.profile,
            strict=bool(args.strict),
        )

        markdown = memo_to_markdown(memo)

        write_json(paths.memo_json, memo)
        write_text(paths.memo_md, markdown)
        write_checklist_csv(paths.checklist_csv, checklist)
        write_gap_csv(paths.gap_register_csv, gaps)
        write_evidence_csv(paths.evidence_index_csv, esg_evidence)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "ESG_PERMITTING_RISK_ANALYSIS_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "profile": args.profile,
            "esg_status": memo.get("esg_status"),
            "memo_sha256": memo.get("esg_permitting_memo_sha256"),
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
            "event": "ESG_PERMITTING_RISK_ANALYSIS_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "profile": args.profile,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN ESG & PERMITTING RISK ANALYZER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
