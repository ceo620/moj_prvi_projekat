#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
27_investor_data_room_freeze_builder.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 27 — Investor Data Room Freeze Builder
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Create an investor/lender data-room freeze snapshot from existing TITAN RAG
outputs.

This script does NOT scan all source documents.
This script does NOT modify original source documents.
This script does NOT certify legal/financial/ESG conclusions.
It consolidates already-produced reports and selected exports into a frozen,
hash-registered, review-ready data-room package.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.
Freeze precedes distribution.

Inputs
------
05_reports/TITAN_RAG_CONTROL_TOWER.xlsx
05_reports/executive_pack/...
05_reports/lender_due_diligence_pack/...
05_reports/board_decision_memo/...
05_reports/legal_compliance_gap_analysis/...
05_reports/esg_permitting_risk_analysis/...
05_reports/capex_loan_bankability_analysis/...
05_reports/*.json
05_reports/*.csv

Outputs
-------
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_INDEX.csv
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_REPORT.md
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_REPORT.json
05_reports/investor_data_room_freeze/FROZEN_EXPORTS/...
06_logs/investor_data_room_freeze_builder_audit.jsonl
06_logs/investor_data_room_freeze_builder_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\27_investor_data_room_freeze_builder.py" --print

Strict freeze
-------------
python ".\\08_scripts\\27_investor_data_room_freeze_builder.py" --strict --print

No file copy, manifest only
---------------------------
python ".\\08_scripts\\27_investor_data_room_freeze_builder.py" --manifest-only --print
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


SCRIPT_NAME = "27_investor_data_room_freeze_builder.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "investor_data_room_freeze"

OUTPUT_INDEX_CSV = "TITAN_INVESTOR_DATA_ROOM_FREEZE_INDEX.csv"
OUTPUT_MANIFEST_JSON = "TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json"
OUTPUT_REPORT_MD = "TITAN_INVESTOR_DATA_ROOM_FREEZE_REPORT.md"
OUTPUT_REPORT_JSON = "TITAN_INVESTOR_DATA_ROOM_FREEZE_REPORT.json"

AUDIT_LOG = Path("06_logs") / "investor_data_room_freeze_builder_audit.jsonl"
ERROR_LOG = Path("06_logs") / "investor_data_room_freeze_builder_errors.jsonl"

FREEZE_READY = "DATA_ROOM_FREEZE_READY"
FREEZE_REVIEW_REQUIRED = "DATA_ROOM_FREEZE_REVIEW_REQUIRED"
FREEZE_BLOCKED = "DATA_ROOM_FREEZE_BLOCKED"
FREEZE_INCOMPLETE = "DATA_ROOM_FREEZE_INCOMPLETE"

REQUIRED_CORE_FILES = {
    "control_tower_xlsx": Path("05_reports") / "TITAN_RAG_CONTROL_TOWER.xlsx",
    "control_tower_summary": Path("05_reports") / "rag_control_tower_export_summary.json",
    "executive_pack_md": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.md",
    "executive_pack_json": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "lender_dd_pack_md": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.md",
    "lender_dd_pack_json": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "board_memo_md": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.md",
    "board_memo_json": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "legal_memo_md": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.md",
    "legal_memo_json": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "esg_memo_md": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.md",
    "esg_memo_json": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.json",
    "capex_bankability_md": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.md",
    "capex_bankability_json": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json",
    "night_run_summary": Path("05_reports") / "night_run_summary.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_rag_answer": Path("05_reports") / "latest_rag_answer.json",
}

SUPPORTING_FILES = {
    "lender_dd_checklist": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_CHECKLIST.csv",
    "lender_dd_gap_register": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_GAP_REGISTER.csv",
    "lender_dd_evidence_index": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_EVIDENCE_INDEX.csv",
    "board_actions": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_ACTIONS.csv",
    "board_conditions": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_APPROVAL_CONDITIONS.csv",
    "legal_checklist": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_CHECKLIST.csv",
    "legal_gap_register": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_GAP_REGISTER.csv",
    "legal_evidence_index": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_EVIDENCE_INDEX.csv",
    "esg_checklist": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_CHECKLIST.csv",
    "esg_gap_register": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_GAP_REGISTER.csv",
    "esg_evidence_index": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_EVIDENCE_INDEX.csv",
    "capex_checklist": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_CHECKLIST.csv",
    "capex_gap_register": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_GAP_REGISTER.csv",
    "capex_evidence_index": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_EVIDENCE_INDEX.csv",
    "capex_covenant_review": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_COVENANT_REVIEW.csv",
    "risk_signals": Path("05_reports") / "risk_signals.csv",
    "financial_signals": Path("05_reports") / "financial_signals.csv",
    "ssot_candidates": Path("05_reports") / "ssot_candidates.csv",
    "conflict_report": Path("05_reports") / "conflict_report.csv",
    "citation_report": Path("05_reports") / "citation_verification_report.csv",
    "document_priority": Path("05_reports") / "document_priority_rank.csv",
    "evidence_report": Path("05_reports") / "evidence_pack_report.csv",
    "evidence_sources": Path("05_reports") / "evidence_sources.csv",
    "morning_briefing": Path("05_reports") / "morning_briefing.md",
    "morning_tasks": Path("05_reports") / "morning_briefing_tasks.csv",
}

STATUS_JSON_FILES = {
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "lender_dd_pack": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "legal_compliance": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "esg_permitting": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.json",
    "capex_bankability": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
}


@dataclass(frozen=True)
class FreezePaths:
    base_dir: Path
    output_dir: Path
    frozen_exports_dir: Path
    index_csv: Path
    manifest_json: Path
    report_md: Path
    report_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> FreezePaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return FreezePaths(
        base_dir=base_dir,
        output_dir=output_dir,
        frozen_exports_dir=output_dir / "FROZEN_EXPORTS",
        index_csv=output_dir / OUTPUT_INDEX_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        report_md=output_dir / OUTPUT_REPORT_MD,
        report_json=output_dir / OUTPUT_REPORT_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def file_record(base_dir: Path, name: str, rel_path: Path, category: str, mandatory: bool) -> dict[str, Any]:
    source = base_dir / rel_path
    exists = source.exists() and source.is_file()
    return {
        "Freeze_Item_ID": "FREEZE-" + hashlib.sha256(str(rel_path).encode("utf-8")).hexdigest()[:14],
        "Name": name,
        "Category": category,
        "Mandatory": mandatory,
        "Exists": exists,
        "Source_Path": str(source),
        "Relative_Path": str(rel_path),
        "File_Name": source.name,
        "Extension": source.suffix.lower(),
        "Size_Bytes": source.stat().st_size if exists else None,
        "Modified_UTC": datetime.fromtimestamp(source.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if exists else None,
        "Source_SHA256": sha256_file(source) if exists else None,
        "Frozen_Path": None,
        "Frozen_SHA256": None,
        "Copied": False,
        "Copy_Status": "PENDING" if exists else "MISSING",
    }


def build_freeze_index(base_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, rel_path in REQUIRED_CORE_FILES.items():
        rows.append(file_record(base_dir, name, rel_path, "CORE", True))
    for name, rel_path in SUPPORTING_FILES.items():
        rows.append(file_record(base_dir, name, rel_path, "SUPPORTING", False))
    return rows


def copy_freeze_files(rows: list[dict[str, Any]], paths: FreezePaths, manifest_only: bool) -> list[dict[str, Any]]:
    paths.frozen_exports_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        if not row["Exists"]:
            continue

        source = Path(row["Source_Path"])
        category_dir = paths.frozen_exports_dir / row["Category"]
        category_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{row['Name']}__{source.name}"
        target = category_dir / safe_name

        if manifest_only:
            row["Frozen_Path"] = str(target)
            row["Frozen_SHA256"] = row["Source_SHA256"]
            row["Copied"] = False
            row["Copy_Status"] = "MANIFEST_ONLY"
            continue

        shutil.copy2(source, target)
        row["Frozen_Path"] = str(target)
        row["Frozen_SHA256"] = sha256_file(target)
        row["Copied"] = True
        row["Copy_Status"] = "COPIED" if row["Frozen_SHA256"] == row["Source_SHA256"] else "HASH_MISMATCH"

    return rows


def load_status_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in STATUS_JSON_FILES.items()
    }


def determine_freeze_status(rows: list[dict[str, Any]], status_reports: dict[str, dict[str, Any] | None], strict: bool) -> tuple[str, list[str]]:
    reasons: list[str] = []

    missing_mandatory = [r for r in rows if r["Mandatory"] and not r["Exists"]]
    hash_mismatch = [r for r in rows if r.get("Copy_Status") == "HASH_MISMATCH"]

    if missing_mandatory:
        reasons.append(f"Missing mandatory freeze files: {len(missing_mandatory)}")
        return FREEZE_INCOMPLETE, reasons

    if hash_mismatch:
        reasons.append(f"Frozen copy hash mismatch count: {len(hash_mismatch)}")
        return FREEZE_BLOCKED, reasons

    audit_status = nested_get(status_reports.get("latest_audit_record"), "audit_status")
    citation_status = nested_get(status_reports.get("citation_verification"), "verification_status")
    executive_status = nested_get(status_reports.get("executive_pack"), "pack_status")
    dd_status = nested_get(status_reports.get("lender_dd_pack"), "dd_status")
    board_status = nested_get(status_reports.get("board_memo"), "decision_status")
    legal_status = nested_get(status_reports.get("legal_compliance"), "legal_status")
    esg_status = nested_get(status_reports.get("esg_permitting"), "esg_status")
    bank_status = nested_get(status_reports.get("capex_bankability"), "bankability_status")
    critical_risks = safe_int(nested_get(status_reports.get("risk_signals"), "summary.critical_count", 0))
    p0_documents = safe_int(nested_get(status_reports.get("document_priority"), "summary.p0_count", 0))

    blockers = []
    if audit_status in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE", None}:
        blockers.append(f"audit_status={audit_status}")
    if citation_status in {"CITATION_VERIFICATION_FAIL", "NO_EVIDENCE_NO_CITATION", None}:
        blockers.append(f"citation_status={citation_status}")
    if executive_status in {"EXECUTIVE_PACK_BLOCKED", "EXECUTIVE_PACK_INCOMPLETE", None}:
        blockers.append(f"executive_pack={executive_status}")
    if dd_status in {"LENDER_DD_BLOCKED", "LENDER_DD_INCOMPLETE", None}:
        blockers.append(f"lender_dd={dd_status}")
    if board_status in {"DO_NOT_APPROVE_BLOCKED", "INCOMPLETE_NO_BOARD_DECISION", None}:
        blockers.append(f"board_status={board_status}")
    if legal_status in {"LEGAL_COMPLIANCE_BLOCKED", "LEGAL_COMPLIANCE_INCOMPLETE", None}:
        blockers.append(f"legal_status={legal_status}")
    if esg_status in {"ESG_PERMITTING_BLOCKED", "ESG_PERMITTING_INCOMPLETE", None}:
        blockers.append(f"esg_status={esg_status}")
    if bank_status in {"CAPEX_LOAN_BANKABILITY_BLOCKED", "CAPEX_LOAN_BANKABILITY_INCOMPLETE", None}:
        blockers.append(f"bankability_status={bank_status}")
    if critical_risks > 0:
        blockers.append(f"critical_risks={critical_risks}")
    if p0_documents > 0:
        blockers.append(f"p0_documents={p0_documents}")

    if blockers:
        reasons.append("Blocking status flags: " + "; ".join(blockers))
        if strict:
            return FREEZE_BLOCKED, reasons
        return FREEZE_REVIEW_REQUIRED, reasons

    warnings = []
    warning_status_values = [
        executive_status,
        dd_status,
        board_status,
        legal_status,
        esg_status,
        bank_status,
        audit_status,
        citation_status,
    ]
    for status in warning_status_values:
        if status and any(token in str(status) for token in ["REVIEW_REQUIRED", "WITH_CONDITIONS", "DEFER", "WARNING"]):
            warnings.append(str(status))

    if warnings:
        reasons.append("Review/warning statuses present: " + "; ".join(warnings))
        return FREEZE_REVIEW_REQUIRED, reasons

    reasons.append("Mandatory files exist and core status gates are clean.")
    return FREEZE_READY, reasons


def build_status_snapshot(status_reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    return {
        "executive_pack_status": nested_get(status_reports.get("executive_pack"), "pack_status"),
        "lender_dd_status": nested_get(status_reports.get("lender_dd_pack"), "dd_status"),
        "board_decision_status": nested_get(status_reports.get("board_memo"), "decision_status"),
        "legal_status": nested_get(status_reports.get("legal_compliance"), "legal_status"),
        "esg_status": nested_get(status_reports.get("esg_permitting"), "esg_status"),
        "bankability_status": nested_get(status_reports.get("capex_bankability"), "bankability_status"),
        "audit_status": nested_get(status_reports.get("latest_audit_record"), "audit_status"),
        "citation_status": nested_get(status_reports.get("citation_verification"), "verification_status"),
        "conflict_status": nested_get(status_reports.get("conflict_report"), "summary.institutional_status"),
        "risk_status": nested_get(status_reports.get("risk_signals"), "summary.institutional_status"),
        "critical_risks": safe_int(nested_get(status_reports.get("risk_signals"), "summary.critical_count", 0)),
        "high_risks": safe_int(nested_get(status_reports.get("risk_signals"), "summary.high_count", 0)),
        "ranked_documents": safe_int(nested_get(status_reports.get("document_priority"), "summary.ranked_documents", 0)),
        "p0_documents": safe_int(nested_get(status_reports.get("document_priority"), "summary.p0_count", 0)),
        "p1_documents": safe_int(nested_get(status_reports.get("document_priority"), "summary.p1_count", 0)),
    }


def build_manifest(paths: FreezePaths, rows: list[dict[str, Any]], status_reports: dict[str, dict[str, Any] | None], strict: bool, manifest_only: bool) -> dict[str, Any]:
    freeze_status, reasons = determine_freeze_status(rows, status_reports, strict=strict)

    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "INVESTOR_DATA_ROOM_FREEZE_AUDIT_LOCKED",
        "base_dir": str(paths.base_dir),
        "output_dir": str(paths.output_dir),
        "frozen_exports_dir": str(paths.frozen_exports_dir),
        "strict_mode": strict,
        "manifest_only": manifest_only,
        "freeze_status": freeze_status,
        "freeze_status_reasons": reasons,
        "status_snapshot": build_status_snapshot(status_reports),
        "summary": {
            "total_items": len(rows),
            "mandatory_items": sum(1 for r in rows if r["Mandatory"]),
            "supporting_items": sum(1 for r in rows if not r["Mandatory"]),
            "existing_items": sum(1 for r in rows if r["Exists"]),
            "missing_items": sum(1 for r in rows if not r["Exists"]),
            "copied_items": sum(1 for r in rows if r["Copied"]),
            "hash_mismatch_items": sum(1 for r in rows if r.get("Copy_Status") == "HASH_MISMATCH"),
            "missing_mandatory_items": sum(1 for r in rows if r["Mandatory"] and not r["Exists"]),
        },
        "freeze_index": rows,
        "governance_rule": {
            "freeze_consolidates_existing_outputs_only": True,
            "source_documents_not_modified": True,
            "frozen_copy_hash_must_match_source_hash": True,
            "freeze_is_distribution_snapshot_not_final_truth": True,
            "json_reports_and_original_sources_remain_authoritative": True,
            "audit_precedes_decision": True,
            "freeze_precedes_distribution": True,
        },
    }
    manifest["freeze_manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "freeze_status": manifest.get("freeze_status"),
        "freeze_status_reasons": manifest.get("freeze_status_reasons"),
        "status_snapshot": manifest.get("status_snapshot"),
        "summary": manifest.get("summary"),
        "freeze_manifest_sha256": manifest.get("freeze_manifest_sha256"),
        "distribution_note": (
            "This data-room freeze is a controlled review snapshot. "
            "It does not replace original documents, legal review, lender review, financial model approval or board approval."
        ),
        "recommended_next_action": recommended_next_action(manifest),
    }
    report["freeze_report_sha256"] = sha256_json(report)
    return report


def recommended_next_action(manifest: dict[str, Any]) -> str:
    status = manifest.get("freeze_status")
    if status == FREEZE_READY:
        return "Proceed to investor/lender review distribution after authorized sign-off."
    if status == FREEZE_REVIEW_REQUIRED:
        return "Review warning statuses and missing supporting files before distribution."
    if status == FREEZE_BLOCKED:
        return "Do not distribute. Resolve blockers or obtain formal exception."
    if status == FREEZE_INCOMPLETE:
        return "Generate missing mandatory reports/files, then rebuild freeze."
    return "Manual review required."


def write_index_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Freeze_Item_ID",
        "Name",
        "Category",
        "Mandatory",
        "Exists",
        "Source_Path",
        "Relative_Path",
        "File_Name",
        "Extension",
        "Size_Bytes",
        "Modified_UTC",
        "Source_SHA256",
        "Frozen_Path",
        "Frozen_SHA256",
        "Copied",
        "Copy_Status",
    ])


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def index_table_md(rows: list[dict[str, Any]], limit: int = 120) -> str:
    if not rows:
        return "No freeze items."
    lines = [
        "| Category | Mandatory | Exists | Copied | Name | SHA256 | Frozen Path |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in rows[:limit]:
        lines.append(
            f"| {md_escape(row.get('Category'))} | "
            f"{row.get('Mandatory')} | "
            f"{row.get('Exists')} | "
            f"{row.get('Copied')} | "
            f"{md_escape(row.get('Name'))} | "
            f"`{md_escape(row.get('Source_SHA256'))}` | "
            f"`{md_escape(row.get('Frozen_Path'))}` |"
        )
    return "\n".join(lines)


def report_to_markdown(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    snapshot = report.get("status_snapshot", {}) if isinstance(report.get("status_snapshot"), dict) else {}
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    status_lines = ["| Status Field | Value |", "|---|---|"]
    for key, value in snapshot.items():
        status_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    summary_lines = ["| Metric | Value |", "|---|---|"]
    for key, value in summary.items():
        summary_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    return f"""# TITAN Investor Data Room Freeze Report

## 1. Freeze Identity

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Freeze Status | {report.get("freeze_status")} |
| Manifest SHA-256 | `{report.get("freeze_manifest_sha256")}` |
| Report SHA-256 | `{report.get("freeze_report_sha256")}` |

**Freeze status reasons**

```json
{json.dumps(report.get("freeze_status_reasons", []), indent=2, ensure_ascii=False)}
```

**Recommended next action**

```text
{report.get("recommended_next_action")}
```

---

## 2. Distribution Note

```text
{report.get("distribution_note")}
```

---

## 3. Status Snapshot

{chr(10).join(status_lines)}

---

## 4. Freeze Summary

{chr(10).join(summary_lines)}

---

## 5. Freeze Index

{index_table_md(manifest.get("freeze_index", []))}

---

## 6. Governance Rule

```text
Freeze consolidates existing outputs only.
Source documents are not modified.
Frozen copy hash must match source hash.
Freeze is a distribution snapshot, not final truth.
JSON reports and original sources remain authoritative.
Audit precedes decision.
Freeze precedes distribution.
```
"""


def print_summary(report: dict[str, Any], paths: FreezePaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN INVESTOR DATA ROOM FREEZE BUILDER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Freeze status:            {report.get('freeze_status')}")
    print(f"Total items:              {summary.get('total_items')}")
    print(f"Mandatory items:          {summary.get('mandatory_items')}")
    print(f"Missing mandatory:        {summary.get('missing_mandatory_items')}")
    print(f"Copied items:             {summary.get('copied_items')}")
    print(f"Hash mismatches:          {summary.get('hash_mismatch_items')}")
    print("-" * 100)
    print(f"Freeze Index CSV:         {paths.index_csv}")
    print(f"Freeze Manifest JSON:     {paths.manifest_json}")
    print(f"Freeze Report MD:         {paths.report_md}")
    print(f"Freeze Report JSON:       {paths.report_json}")
    print(f"Frozen Exports:           {paths.frozen_exports_dir}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 27 — investor data room freeze builder.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--manifest-only", action="store_true", help="Do not copy files; build hash manifest only.")
    parser.add_argument("--strict", action="store_true", help="Strict mode blocks freeze on status warnings/blockers.")
    parser.add_argument("--print", action="store_true", help="Print Markdown freeze report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, args.output_dir)

    try:
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        paths.output_dir.mkdir(parents=True, exist_ok=True)
        paths.frozen_exports_dir.mkdir(parents=True, exist_ok=True)

        index_rows = build_freeze_index(base_dir)
        index_rows = copy_freeze_files(index_rows, paths, manifest_only=bool(args.manifest_only))
        status_reports = load_status_reports(base_dir)
        manifest = build_manifest(
            paths=paths,
            rows=index_rows,
            status_reports=status_reports,
            strict=bool(args.strict),
            manifest_only=bool(args.manifest_only),
        )
        report = build_report(manifest)
        markdown = report_to_markdown(report, manifest)

        write_index_csv(paths.index_csv, index_rows)
        write_json(paths.manifest_json, manifest)
        write_json(paths.report_json, report)
        write_text(paths.report_md, markdown)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "INVESTOR_DATA_ROOM_FREEZE_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "freeze_status": report.get("freeze_status"),
            "freeze_manifest_sha256": manifest.get("freeze_manifest_sha256"),
            "freeze_report_sha256": report.get("freeze_report_sha256"),
            "summary": report.get("summary"),
            "outputs": {
                "index_csv": str(paths.index_csv),
                "manifest_json": str(paths.manifest_json),
                "report_md": str(paths.report_md),
                "report_json": str(paths.report_json),
                "frozen_exports_dir": str(paths.frozen_exports_dir),
            },
        })

        print_summary(report, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "INVESTOR_DATA_ROOM_FREEZE_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN INVESTOR DATA ROOM FREEZE BUILDER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
