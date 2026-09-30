#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
22_lender_due_diligence_pack_builder.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 22 — Lender Due Diligence Pack Builder
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build a lender-oriented due diligence pack from already-produced TITAN RAG
outputs.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT create unsupported lender conclusions.
It consolidates audit-grade evidence, risks, conflicts, financial signals,
SSOT candidates and document priority into a lender due diligence control pack.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/TITAN_RAG_CONTROL_TOWER.xlsx
05_reports/latest_audit_record.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json
05_reports/financial_signals_report.json
05_reports/risk_signals_report.json
05_reports/ssot_candidates_report.json
05_reports/document_priority_rank.json
05_reports/evidence_pack_report.json
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json
05_reports/morning_briefing.json

Outputs
-------
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.md
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_CHECKLIST.csv
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_GAP_REGISTER.csv
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_EVIDENCE_INDEX.csv
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_MANIFEST.json
05_reports/lender_due_diligence_pack/source_exports/...
06_logs/lender_due_diligence_pack_builder_audit.jsonl
06_logs/lender_due_diligence_pack_builder_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\22_lender_due_diligence_pack_builder.py" --print

Custom institution profile
--------------------------
python ".\\08_scripts\\22_lender_due_diligence_pack_builder.py" --institution EBRD --print

Custom output folder
--------------------
python ".\\08_scripts\\22_lender_due_diligence_pack_builder.py" --output-dir ".\\05_reports\\lender_due_diligence_pack_EBRD"
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "22_lender_due_diligence_pack_builder.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "lender_due_diligence_pack"

OUTPUT_PACK_MD = "TITAN_LENDER_DD_PACK.md"
OUTPUT_PACK_JSON = "TITAN_LENDER_DD_PACK.json"
OUTPUT_CHECKLIST_CSV = "TITAN_LENDER_DD_CHECKLIST.csv"
OUTPUT_GAP_REGISTER_CSV = "TITAN_LENDER_DD_GAP_REGISTER.csv"
OUTPUT_EVIDENCE_INDEX_CSV = "TITAN_LENDER_DD_EVIDENCE_INDEX.csv"
OUTPUT_MANIFEST_JSON = "TITAN_LENDER_DD_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "lender_due_diligence_pack_builder_audit.jsonl"
ERROR_LOG = Path("06_logs") / "lender_due_diligence_pack_builder_errors.jsonl"

DD_READY = "LENDER_DD_READY_FOR_REVIEW"
DD_REVIEW_REQUIRED = "LENDER_DD_REVIEW_REQUIRED"
DD_BLOCKED = "LENDER_DD_BLOCKED"
DD_INCOMPLETE = "LENDER_DD_INCOMPLETE"

GAP_OPEN_CRITICAL = "OPEN_CRITICAL"
GAP_OPEN_HIGH = "OPEN_HIGH"
GAP_OPEN_MEDIUM = "OPEN_MEDIUM"
GAP_MONITOR = "MONITOR"
GAP_CLOSED_BY_EVIDENCE = "CLOSED_BY_EVIDENCE"

CHECK_PASS = "PASS"
CHECK_WARNING = "WARNING"
CHECK_FAIL = "FAIL"
CHECK_MISSING = "MISSING"

SOURCE_JSON_FILES = {
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "control_tower_summary": Path("05_reports") / "rag_control_tower_export_summary.json",
    "night_run_summary": Path("05_reports") / "night_run_summary.json",
    "morning_briefing": Path("05_reports") / "morning_briefing.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "ssot_candidates": Path("05_reports") / "ssot_candidates_report.json",
    "financial_signals": Path("05_reports") / "financial_signals_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "evidence_report": Path("05_reports") / "evidence_pack_report.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_answer": Path("05_reports") / "latest_rag_answer.json",
}

SOURCE_EXPORT_FILES = {
    "control_tower_xlsx": Path("05_reports") / "TITAN_RAG_CONTROL_TOWER.xlsx",
    "executive_pack_md": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.md",
    "executive_pack_json": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "document_priority_csv": Path("05_reports") / "document_priority_rank.csv",
    "risk_signals_csv": Path("05_reports") / "risk_signals.csv",
    "financial_signals_csv": Path("05_reports") / "financial_signals.csv",
    "ssot_candidates_csv": Path("05_reports") / "ssot_candidates.csv",
    "conflict_report_csv": Path("05_reports") / "conflict_report.csv",
    "citation_report_csv": Path("05_reports") / "citation_verification_report.csv",
    "evidence_report_csv": Path("05_reports") / "evidence_pack_report.csv",
    "evidence_sources_csv": Path("05_reports") / "evidence_sources.csv",
    "morning_tasks_csv": Path("05_reports") / "morning_briefing_tasks.csv",
}

DD_REQUIREMENTS = [
    {
        "Requirement_ID": "DD-001",
        "Area": "Audit Integrity",
        "Requirement": "Latest RAG answer must have a final audit record.",
        "Source": "latest_audit_record",
        "Required_Status_Field": "audit_status",
        "Pass_Values": ["AUDIT_PASS"],
        "Warning_Values": ["AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-002",
        "Area": "Citation Integrity",
        "Requirement": "Every material answer must be traceable to source_path and chunk_id.",
        "Source": "citation_verification",
        "Required_Status_Field": "verification_status",
        "Pass_Values": ["CITATION_VERIFICATION_PASS"],
        "Warning_Values": ["CITATION_VERIFICATION_PASS_WITH_WARNINGS", "CITATION_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-003",
        "Area": "Conflict Control",
        "Requirement": "Material evidence conflicts must be absent or explicitly reviewed.",
        "Source": "conflict_report",
        "Required_Status_Field": "summary.institutional_status",
        "Pass_Values": ["NO_CONFLICTS_DETECTED"],
        "Warning_Values": ["CONFLICTS_DETECTED_REVIEW_REQUIRED"],
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-004",
        "Area": "Risk Control",
        "Requirement": "Critical risks must be zero before lender reliance.",
        "Source": "risk_signals",
        "Required_Status_Field": "summary.critical_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-005",
        "Area": "Financial Evidence",
        "Requirement": "Financial signals register must be available for CAPEX/loan/model review.",
        "Source": "financial_signals",
        "Required_Status_Field": "summary.total_signals",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-006",
        "Area": "SSOT Governance",
        "Requirement": "SSOT candidate report must exist; conflict-blocked items must be reviewed.",
        "Source": "ssot_candidates",
        "Required_Status_Field": "summary.institutional_status",
        "Pass_Values": ["SSOT_CANDIDATES_READY"],
        "Warning_Values": ["SSOT_REVIEW_REQUIRED", "SSOT_CONFLICT_BLOCKED", "NO_SSOT_CANDIDATES"],
        "Critical": False,
    },
    {
        "Requirement_ID": "DD-007",
        "Area": "Document Priority",
        "Requirement": "P0 documents must be reviewed before lender package reliance.",
        "Source": "document_priority",
        "Required_Status_Field": "summary.p0_count",
        "Pass_Values": [0, "0"],
        "Warning_Values": [],
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-008",
        "Area": "Evidence Pack",
        "Requirement": "Evidence pack report must exist with at least one source.",
        "Source": "evidence_report",
        "Required_Status_Field": "summary.source_file_count",
        "Pass_Condition": "value_gt_0",
        "Critical": True,
    },
    {
        "Requirement_ID": "DD-009",
        "Area": "Night Run",
        "Requirement": "Night run must complete without critical failure.",
        "Source": "night_run_summary",
        "Required_Status_Field": "final_status",
        "Pass_Values": ["SUCCESS", "SUCCESS_WITH_WARNINGS"],
        "Warning_Values": ["SUCCESS_WITH_WARNINGS"],
        "Critical": False,
    },
    {
        "Requirement_ID": "DD-010",
        "Area": "Control Tower",
        "Requirement": "Control Tower workbook/export must exist.",
        "Source": "control_tower_summary",
        "Required_Status_Field": "output_xlsx_sha256",
        "Pass_Condition": "not_empty",
        "Critical": False,
    },
]

INSTITUTION_REQUIREMENT_FOCUS = {
    "EIB": ["Audit Integrity", "Citation Integrity", "Risk Control", "Environmental/Social Proxy", "Financial Evidence", "Document Priority"],
    "EBRD": ["Audit Integrity", "Citation Integrity", "Risk Control", "SSOT Governance", "Financial Evidence", "Document Priority"],
    "IFC": ["Audit Integrity", "Citation Integrity", "Risk Control", "Financial Evidence", "Conflict Control", "Document Priority"],
    "BANK": ["Audit Integrity", "Citation Integrity", "Financial Evidence", "Risk Control", "Conflict Control"],
    "BOARD": ["Audit Integrity", "Risk Control", "Document Priority", "Financial Evidence", "SSOT Governance"],
}


@dataclass(frozen=True)
class DDPaths:
    base_dir: Path
    output_dir: Path
    pack_md: Path
    pack_json: Path
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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> DDPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return DDPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        pack_md=output_dir / OUTPUT_PACK_MD,
        pack_json=output_dir / OUTPUT_PACK_JSON,
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


def nested_get(payload: dict[str, Any] | None, path: str) -> Any:
    if not isinstance(payload, dict):
        return None
    cur: Any = payload
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def evaluate_requirement(req: dict[str, Any], reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    source = req["Source"]
    report = reports.get(source)
    field = req.get("Required_Status_Field")
    value = nested_get(report, field) if field else None

    if report is None:
        status = CHECK_MISSING
        gap_status = GAP_OPEN_CRITICAL if req.get("Critical") else GAP_OPEN_MEDIUM
        reason = f"Missing source report: {source}"
    else:
        pass_values = req.get("Pass_Values", [])
        warning_values = req.get("Warning_Values", [])
        condition = req.get("Pass_Condition")

        if condition == "value_gt_0":
            passed = safe_float(value, 0.0) > 0
            status = CHECK_PASS if passed else CHECK_FAIL
            reason = f"{field}={value}; expected > 0"
        elif condition == "not_empty":
            passed = value not in [None, ""]
            status = CHECK_PASS if passed else CHECK_FAIL
            reason = f"{field} is {'present' if passed else 'empty'}"
        elif value in pass_values:
            status = CHECK_PASS
            reason = f"{field}={value}"
        elif value in warning_values:
            status = CHECK_WARNING
            reason = f"{field}={value}; warning/manual review"
        else:
            status = CHECK_FAIL
            reason = f"{field}={value}; expected one of {pass_values}"

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
        "Institution_Area": req["Area"],
        "Requirement": req["Requirement"],
        "Source_Report": source,
        "Required_Field": field,
        "Observed_Value": value,
        "Check_Status": status,
        "Gap_Status": gap_status,
        "Critical": bool(req.get("Critical")),
        "Reason": reason,
        "Recommended_Action": requirement_action(req, status, value),
    }


def requirement_action(req: dict[str, Any], status: str, value: Any) -> str:
    if status == CHECK_PASS:
        return "No immediate action. Keep source evidence in lender pack."

    area = req.get("Area")
    if area == "Audit Integrity":
        return "Rerun Step 08 and review latest_audit_record.json."
    if area == "Citation Integrity":
        return "Rerun Step 13 and fix missing source_path/chunk_id/score/excerpt issues."
    if area == "Conflict Control":
        return "Review Step 14 conflicts and resolve through SSOT source hierarchy."
    if area == "Risk Control":
        return "Review Step 17 risk signals and close critical/high risk items."
    if area == "Financial Evidence":
        return "Rerun/review Step 16 financial signals; retrieve stronger CAPEX/loan/model evidence."
    if area == "SSOT Governance":
        return "Review Step 15 SSOT candidates and mark conflict-blocked/review-required items."
    if area == "Document Priority":
        return "Review Step 18 P0/P1 documents and close blockers."
    if area == "Evidence Pack":
        return "Rerun Step 06 and Step 12 with a broader lender-focused query."
    if area == "Night Run":
        return "Open night_run_summary and fix failed steps."
    if area == "Control Tower":
        return "Rerun Step 20 Control Tower export."
    return "Manual review required."


def build_checklist(reports: dict[str, dict[str, Any] | None], institution: str) -> list[dict[str, Any]]:
    focus = set(INSTITUTION_REQUIREMENT_FOCUS.get(institution.upper(), []))
    rows = []

    for req in DD_REQUIREMENTS:
        row = evaluate_requirement(req, reports)
        row["Institution"] = institution.upper()
        row["Institution_Focus"] = row["Institution_Area"] in focus
        rows.append(row)

    return rows


def build_gap_register(checklist: list[dict[str, Any]], reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for row in checklist:
        if row["Check_Status"] == CHECK_PASS:
            continue
        gaps.append({
            "Gap_ID": "GAP-" + hashlib.sha256(row["Requirement_ID"].encode("utf-8")).hexdigest()[:12],
            "Requirement_ID": row["Requirement_ID"],
            "Area": row["Institution_Area"],
            "Gap_Status": row["Gap_Status"],
            "Severity": "CRITICAL" if row["Gap_Status"] == GAP_OPEN_CRITICAL else "HIGH" if row["Gap_Status"] == GAP_OPEN_HIGH else "MEDIUM",
            "Description": row["Requirement"],
            "Observed_Value": row["Observed_Value"],
            "Reason": row["Reason"],
            "Recommended_Action": row["Recommended_Action"],
            "Source_Report": row["Source_Report"],
            "Owner": "Danijela / TITAN Operator",
            "Due_Logic": "Before lender/board submission" if row["Critical"] else "Before final DD pack freeze",
            "Evidence_Closure_Rule": "Update source report until checklist status becomes PASS.",
        })

    # Add explicit critical/high risks as gaps.
    risk_report = reports.get("risk_signals")
    risk_rows = risk_report.get("signals", []) if isinstance(risk_report, dict) else []
    if isinstance(risk_rows, list):
        for risk in risk_rows:
            if not isinstance(risk, dict):
                continue
            if risk.get("Severity") not in {"CRITICAL", "HIGH"}:
                continue
            rid = str(risk.get("Risk_ID") or "")
            gaps.append({
                "Gap_ID": "GAP-RISK-" + hashlib.sha256(rid.encode("utf-8")).hexdigest()[:12],
                "Requirement_ID": "RISK-SIGNAL",
                "Area": risk.get("Risk_Type"),
                "Gap_Status": GAP_OPEN_CRITICAL if risk.get("Severity") == "CRITICAL" else GAP_OPEN_HIGH,
                "Severity": risk.get("Severity"),
                "Description": short_text(risk.get("Context"), 600),
                "Observed_Value": risk.get("Matched_Term"),
                "Reason": f"Risk signal {rid} has severity {risk.get('Severity')}",
                "Recommended_Action": risk.get("Recommended_Action"),
                "Source_Report": "risk_signals_report.json",
                "Owner": "Danijela / TITAN Operator",
                "Due_Logic": "Before lender/board submission",
                "Evidence_Closure_Rule": "Mitigate risk or document lender-ready explanation.",
            })

    return gaps


def build_evidence_index(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    evidence_report = reports.get("evidence_report")
    evidence_rows = evidence_report.get("evidence", []) if isinstance(evidence_report, dict) else []
    source_rows = evidence_report.get("source_files", []) if isinstance(evidence_report, dict) else []

    rows: list[dict[str, Any]] = []

    if isinstance(evidence_rows, list):
        for item in evidence_rows:
            if not isinstance(item, dict):
                continue
            rows.append({
                "Evidence_ID": "EVID-" + hashlib.sha256(str(item.get("chunk_id") or item.get("source_path") or "").encode("utf-8")).hexdigest()[:14],
                "Evidence_Type": "CHUNK",
                "Rank": item.get("rank"),
                "Final_Score": item.get("final_score"),
                "Source_Path": item.get("source_path"),
                "File_Name": item.get("file_name"),
                "Chunk_ID": item.get("chunk_id"),
                "Section_Label": item.get("section_label"),
                "Excerpt_SHA256": item.get("excerpt_sha256"),
                "Evidence_Use": classify_evidence_use(item),
                "Excerpt": short_text(item.get("excerpt"), 1000),
            })

    if isinstance(source_rows, list):
        for item in source_rows:
            if not isinstance(item, dict):
                continue
            rows.append({
                "Evidence_ID": "SRC-" + hashlib.sha256(str(item.get("source_path") or "").encode("utf-8")).hexdigest()[:14],
                "Evidence_Type": "SOURCE",
                "Rank": None,
                "Final_Score": item.get("max_final_score"),
                "Source_Path": item.get("source_path"),
                "File_Name": item.get("file_name"),
                "Chunk_ID": item.get("chunk_ids"),
                "Section_Label": item.get("sections"),
                "Excerpt_SHA256": None,
                "Evidence_Use": "Source document reference",
                "Excerpt": "",
            })

    return rows


def classify_evidence_use(item: dict[str, Any]) -> str:
    text = " ".join([
        str(item.get("file_name") or ""),
        str(item.get("source_path") or ""),
        str(item.get("excerpt") or ""),
        str(item.get("keyword_hits") or ""),
    ]).lower()

    if any(x in text for x in ["capex", "dscr", "wacc", "irr", "npv", "loan", "equity", "grant", "financial"]):
        return "Financial due diligence"
    if any(x in text for x in ["risk", "conflict", "missing", "unsigned", "permit", "legal"]):
        return "Risk/legal due diligence"
    if any(x in text for x in ["eib", "ebrd", "ifc", "lender", "bank"]):
        return "Lender evidence"
    if any(x in text for x in ["ssot", "audit", "citation", "source"]):
        return "Audit/SSOT traceability"
    return "General evidence"


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
    source_manifest = []

    for name, rel_path in SOURCE_JSON_FILES.items():
        path = base_dir / rel_path
        source_manifest.append({
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
        source_manifest.append({
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
        "source_manifest": source_manifest,
        "copied_files": copied_files,
        "governance_rule": {
            "lender_pack_consolidates_existing_reports_only": True,
            "source_documents_not_modified": True,
            "json_reports_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    return manifest


def determine_dd_status(checklist: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> tuple[str, list[str]]:
    reasons: list[str] = []

    missing = [x for x in checklist if x["Check_Status"] == CHECK_MISSING]
    critical_fail = [x for x in checklist if x["Critical"] and x["Check_Status"] == CHECK_FAIL]
    critical_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_CRITICAL]
    high_gaps = [x for x in gaps if x["Gap_Status"] == GAP_OPEN_HIGH]

    if missing:
        reasons.append(f"Missing required DD reports: {len(missing)}")
        return DD_INCOMPLETE, reasons

    if critical_fail or critical_gaps:
        reasons.append(f"Critical DD blockers: checks={len(critical_fail)}, gaps={len(critical_gaps)}")
        return DD_BLOCKED, reasons

    if high_gaps or any(x["Check_Status"] == CHECK_WARNING for x in checklist):
        reasons.append(f"Review required: high_gaps={len(high_gaps)}, warnings={sum(1 for x in checklist if x['Check_Status'] == CHECK_WARNING)}")
        return DD_REVIEW_REQUIRED, reasons

    reasons.append("Core due diligence checks are clean enough for lender review pack.")
    return DD_READY, reasons


def build_pack(
    institution: str,
    reports: dict[str, dict[str, Any] | None],
    checklist: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    evidence_index: list[dict[str, Any]],
    manifest: dict[str, Any],
    strict: bool,
) -> dict[str, Any]:
    dd_status, reasons = determine_dd_status(checklist, gaps)

    latest_answer = reports.get("latest_answer") or {}
    answer_conf = latest_answer.get("confidence") if isinstance(latest_answer.get("confidence"), dict) else {}

    pack = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "LENDER_DUE_DILIGENCE_PACK_AUDIT_LOCKED",
        "institution": institution.upper(),
        "strict_mode": strict,
        "dd_status": dd_status,
        "dd_status_reasons": reasons,
        "query": nested_get(reports.get("latest_evidence_pack"), "query") or latest_answer.get("query"),
        "executive_snapshot": {
            "direct_answer_snapshot": short_text(latest_answer.get("direct_answer"), 1600),
            "answer_institutional_status": latest_answer.get("institutional_status"),
            "answer_confidence_score": answer_conf.get("confidence_score"),
            "answer_confidence_label": answer_conf.get("confidence_label"),
            "next_action": latest_answer.get("next_action"),
            "risk_if_skipped": latest_answer.get("risk_if_skipped"),
        },
        "key_metrics": {
            "checklist_items": len(checklist),
            "checklist_pass": sum(1 for x in checklist if x["Check_Status"] == CHECK_PASS),
            "checklist_warning": sum(1 for x in checklist if x["Check_Status"] == CHECK_WARNING),
            "checklist_fail": sum(1 for x in checklist if x["Check_Status"] == CHECK_FAIL),
            "checklist_missing": sum(1 for x in checklist if x["Check_Status"] == CHECK_MISSING),
            "open_gaps": len([x for x in gaps if x["Gap_Status"] != GAP_CLOSED_BY_EVIDENCE]),
            "critical_gaps": len([x for x in gaps if x["Gap_Status"] == GAP_OPEN_CRITICAL]),
            "high_gaps": len([x for x in gaps if x["Gap_Status"] == GAP_OPEN_HIGH]),
            "evidence_index_rows": len(evidence_index),
            "critical_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count"), 0),
            "high_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.high_count"), 0),
            "total_conflicts": safe_int(nested_get(reports.get("conflict_report"), "summary.total_conflicts"), 0),
            "financial_signals": safe_int(nested_get(reports.get("financial_signals"), "summary.total_signals"), 0),
            "ssot_candidates": safe_int(nested_get(reports.get("ssot_candidates"), "summary.total_candidates"), 0),
            "p0_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p0_count"), 0),
            "p1_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p1_count"), 0),
        },
        "checklist": checklist,
        "gap_register": gaps,
        "evidence_index": evidence_index,
        "top_priority_documents": top_collection(reports.get("document_priority"), "documents", 25),
        "top_risks": top_collection(reports.get("risk_signals"), "signals", 25),
        "top_financial_signals": top_collection(reports.get("financial_signals"), "signals", 25),
        "top_conflicts": top_collection(reports.get("conflict_report"), "conflicts", 25),
        "top_ssot_candidates": top_collection(reports.get("ssot_candidates"), "candidates", 25),
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "manifest_sha256": manifest.get("manifest_sha256"),
        "governance_rule": {
            "lender_pack_consolidates_existing_reports_only": True,
            "no_new_unsupported_claims": True,
            "source_documents_not_modified": True,
            "dd_status_blocked_requires_manual_review": True,
            "original_source_files_and_json_reports_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }

    pack["lender_dd_pack_sha256"] = sha256_json(pack)
    return pack


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
        "Institution",
        "Institution_Area",
        "Institution_Focus",
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


def write_evidence_index_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Evidence_ID",
        "Evidence_Type",
        "Rank",
        "Final_Score",
        "Source_Path",
        "File_Name",
        "Chunk_ID",
        "Section_Label",
        "Excerpt_SHA256",
        "Evidence_Use",
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
            f"{md_escape(row.get('Institution_Area'))} | "
            f"{md_escape(row.get('Check_Status'))} | "
            f"{row.get('Critical')} | "
            f"{md_escape(row.get('Observed_Value'))} | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def gaps_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No open gaps."
    lines = [
        "| Gap | Severity | Area | Status | Reason | Action |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows[:80]:
        lines.append(
            f"| {md_escape(row.get('Gap_ID'))} | "
            f"{md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Gap_Status'))} | "
            f"{md_escape(short_text(row.get('Reason'), 220))} | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def documents_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No document priority rows."
    lines = [
        "| Rank | Class | Score | Status | Source | Action |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('Priority_Rank')} | "
            f"{md_escape(row.get('Priority_Class'))} | "
            f"{row.get('Priority_Score')} | "
            f"{md_escape(row.get('Review_Status'))} | "
            f"`{md_escape(row.get('Document_Path'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def risks_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No risk rows."
    lines = [
        "| Severity | Status | Type | Confidence | Source | Action |",
        "|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Risk_Status'))} | "
            f"{md_escape(row.get('Risk_Type'))} | "
            f"{row.get('Confidence_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def financial_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No financial signal rows."
    lines = [
        "| Severity | Status | Category | Type | Value | Confidence | Source |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Financial_Status'))} | "
            f"{md_escape(row.get('Signal_Category'))} | "
            f"{md_escape(row.get('Value_Type'))} | "
            f"{md_escape(row.get('Canonical_Value'))} | "
            f"{row.get('Confidence_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` |"
        )
    return "\n".join(lines)


def pack_to_markdown(pack: dict[str, Any]) -> str:
    metrics = pack.get("key_metrics", {}) if isinstance(pack.get("key_metrics"), dict) else {}
    snapshot = pack.get("executive_snapshot", {}) if isinstance(pack.get("executive_snapshot"), dict) else {}

    return f"""# TITAN Lender Due Diligence Pack

## 1. Pack Identity

| Field | Value |
|---|---|
| Created At | {pack.get("created_at")} |
| Institution | {pack.get("institution")} |
| DD Status | {pack.get("dd_status")} |
| Query | {md_escape(pack.get("query"))} |
| Strict Mode | {pack.get("strict_mode")} |
| Pack SHA-256 | `{pack.get("lender_dd_pack_sha256")}` |

**DD status reasons**

```json
{json.dumps(pack.get("dd_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Executive Snapshot

| Metric | Value |
|---|---|
| Answer Institutional Status | {snapshot.get("answer_institutional_status")} |
| Answer Confidence Score | {snapshot.get("answer_confidence_score")} |
| Answer Confidence Label | {snapshot.get("answer_confidence_label")} |
| Checklist Pass | {metrics.get("checklist_pass")} |
| Checklist Warning | {metrics.get("checklist_warning")} |
| Checklist Fail | {metrics.get("checklist_fail")} |
| Checklist Missing | {metrics.get("checklist_missing")} |
| Open Gaps | {metrics.get("open_gaps")} |
| Critical Gaps | {metrics.get("critical_gaps")} |
| High Gaps | {metrics.get("high_gaps")} |
| Critical Risks | {metrics.get("critical_risks")} |
| High Risks | {metrics.get("high_risks")} |
| Conflicts | {metrics.get("total_conflicts")} |
| Financial Signals | {metrics.get("financial_signals")} |
| SSOT Candidates | {metrics.get("ssot_candidates")} |
| P0 Documents | {metrics.get("p0_documents")} |
| P1 Documents | {metrics.get("p1_documents")} |

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

## 3. Lender Due Diligence Checklist

{checklist_md(pack.get("checklist", []))}

---

## 4. Gap Register

{gaps_md(pack.get("gap_register", []))}

---

## 5. Top Priority Documents

{documents_md(pack.get("top_priority_documents", []))}

---

## 6. Top Risks

{risks_md(pack.get("top_risks", []))}

---

## 7. Top Financial Signals

{financial_md(pack.get("top_financial_signals", []))}

---

## 8. Top Conflicts

```json
{json.dumps(pack.get("top_conflicts", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 9. Top SSOT Candidates

```json
{json.dumps(pack.get("top_ssot_candidates", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 10. Governance Rule

```text
Lender DD pack consolidates existing reports only.
It does not create new unsupported claims.
It does not modify source documents.
If DD status is BLOCKED, INCOMPLETE or REVIEW_REQUIRED, manual review is mandatory.
Original source files and JSON reports remain authoritative.
Audit precedes decision.
```
"""


def print_summary(pack: dict[str, Any], paths: DDPaths) -> None:
    metrics = pack.get("key_metrics", {}) if isinstance(pack.get("key_metrics"), dict) else {}
    print("=" * 100)
    print("TITAN LENDER DUE DILIGENCE PACK BUILDER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Institution:              {pack.get('institution')}")
    print(f"DD status:                {pack.get('dd_status')}")
    print(f"Checklist pass/warn/fail: {metrics.get('checklist_pass')}/{metrics.get('checklist_warning')}/{metrics.get('checklist_fail')}")
    print(f"Open gaps:                {metrics.get('open_gaps')}")
    print(f"Critical gaps:            {metrics.get('critical_gaps')}")
    print(f"High gaps:                {metrics.get('high_gaps')}")
    print("-" * 100)
    print(f"Pack Markdown:            {paths.pack_md}")
    print(f"Pack JSON:                {paths.pack_json}")
    print(f"Checklist CSV:            {paths.checklist_csv}")
    print(f"Gap Register CSV:         {paths.gap_register_csv}")
    print(f"Evidence Index CSV:       {paths.evidence_index_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 22 — lender due diligence pack builder.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional lender DD pack output directory.")
    parser.add_argument("--institution", default="EBRD", choices=["EIB", "EBRD", "IFC", "BANK", "BOARD"], help="Institution review profile.")
    parser.add_argument("--no-copy-files", action="store_true", help="Do not copy XLSX/CSV exports into source_exports.")
    parser.add_argument("--strict", action="store_true", help="Strict metadata flag for DD governance.")
    parser.add_argument("--print", action="store_true", help="Print Markdown DD pack to console.")

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
        checklist = build_checklist(reports, args.institution)
        gaps = build_gap_register(checklist, reports)
        evidence_index = build_evidence_index(reports)
        copied_files = copy_source_exports(base_dir, paths.output_dir, copy_files=not bool(args.no_copy_files))
        manifest = build_manifest(base_dir, paths.output_dir, copied_files)

        pack = build_pack(
            institution=args.institution,
            reports=reports,
            checklist=checklist,
            gaps=gaps,
            evidence_index=evidence_index,
            manifest=manifest,
            strict=bool(args.strict),
        )

        markdown = pack_to_markdown(pack)

        write_json(paths.pack_json, pack)
        write_text(paths.pack_md, markdown)
        write_checklist_csv(paths.checklist_csv, checklist)
        write_gap_csv(paths.gap_register_csv, gaps)
        write_evidence_index_csv(paths.evidence_index_csv, evidence_index)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "LENDER_DUE_DILIGENCE_PACK_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "institution": args.institution,
            "dd_status": pack.get("dd_status"),
            "pack_sha256": pack.get("lender_dd_pack_sha256"),
            "manifest_sha256": manifest.get("manifest_sha256"),
            "outputs": {
                "pack_md": str(paths.pack_md),
                "pack_json": str(paths.pack_json),
                "checklist_csv": str(paths.checklist_csv),
                "gap_register_csv": str(paths.gap_register_csv),
                "evidence_index_csv": str(paths.evidence_index_csv),
                "manifest_json": str(paths.manifest_json),
            },
        })

        print_summary(pack, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "LENDER_DUE_DILIGENCE_PACK_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "institution": args.institution,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN LENDER DUE DILIGENCE PACK BUILDER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
