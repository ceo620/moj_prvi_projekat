#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
23_board_decision_memo_builder.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 23 — Board Decision Memo Builder
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build a board-level decision memorandum from existing TITAN RAG outputs.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT create unsupported conclusions.
It consolidates audit-grade outputs into a structured board decision memo:
- decision status
- recommended board action
- critical blockers
- approval conditions
- evidence summary
- financial signal summary
- risk summary
- SSOT/conflict/citation governance
- source manifest

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/latest_audit_record.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json
05_reports/risk_signals_report.json
05_reports/financial_signals_report.json
05_reports/ssot_candidates_report.json
05_reports/document_priority_rank.json
05_reports/latest_rag_answer.json
05_reports/latest_evidence_pack.json
05_reports/morning_briefing.json
05_reports/night_run_summary.json

Outputs
-------
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.md
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/board_decision_memo/TITAN_BOARD_DECISION_ACTIONS.csv
05_reports/board_decision_memo/TITAN_BOARD_APPROVAL_CONDITIONS.csv
05_reports/board_decision_memo/TITAN_BOARD_MEMO_MANIFEST.json
05_reports/board_decision_memo/source_exports/...
06_logs/board_decision_memo_builder_audit.jsonl
06_logs/board_decision_memo_builder_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\23_board_decision_memo_builder.py" --print

Custom board stance
-------------------
python ".\\08_scripts\\23_board_decision_memo_builder.py" --board-stance conservative --print
python ".\\08_scripts\\23_board_decision_memo_builder.py" --board-stance standard --print

Custom output folder
--------------------
python ".\\08_scripts\\23_board_decision_memo_builder.py" --output-dir ".\\05_reports\\board_decision_memo_v1"
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


SCRIPT_NAME = "23_board_decision_memo_builder.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "board_decision_memo"

OUTPUT_MEMO_MD = "TITAN_BOARD_DECISION_MEMO.md"
OUTPUT_MEMO_JSON = "TITAN_BOARD_DECISION_MEMO.json"
OUTPUT_ACTIONS_CSV = "TITAN_BOARD_DECISION_ACTIONS.csv"
OUTPUT_CONDITIONS_CSV = "TITAN_BOARD_APPROVAL_CONDITIONS.csv"
OUTPUT_MANIFEST_JSON = "TITAN_BOARD_MEMO_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "board_decision_memo_builder_audit.jsonl"
ERROR_LOG = Path("06_logs") / "board_decision_memo_builder_errors.jsonl"

DECISION_APPROVE = "APPROVE_FOR_NEXT_STAGE"
DECISION_APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
DECISION_DEFER = "DEFER_PENDING_REVIEW"
DECISION_BLOCK = "DO_NOT_APPROVE_BLOCKED"
DECISION_INCOMPLETE = "INCOMPLETE_NO_BOARD_DECISION"

ACTION_IMMEDIATE = "IMMEDIATE_ACTION"
ACTION_CONDITION_PRECEDENT = "CONDITION_PRECEDENT"
ACTION_CONDITION_SUBSEQUENT = "CONDITION_SUBSEQUENT"
ACTION_MONITOR = "MONITOR"

SOURCE_JSON_FILES = {
    "lender_dd_pack": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "control_tower_summary": Path("05_reports") / "rag_control_tower_export_summary.json",
    "night_run_summary": Path("05_reports") / "night_run_summary.json",
    "morning_briefing": Path("05_reports") / "morning_briefing.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "financial_signals": Path("05_reports") / "financial_signals_report.json",
    "ssot_candidates": Path("05_reports") / "ssot_candidates_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "latest_answer": Path("05_reports") / "latest_rag_answer.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
}

SOURCE_EXPORT_FILES = {
    "lender_dd_pack_md": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.md",
    "lender_dd_pack_json": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "lender_dd_checklist": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_CHECKLIST.csv",
    "lender_dd_gap_register": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_GAP_REGISTER.csv",
    "lender_dd_evidence_index": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_EVIDENCE_INDEX.csv",
    "executive_pack_md": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.md",
    "executive_pack_json": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "control_tower_xlsx": Path("05_reports") / "TITAN_RAG_CONTROL_TOWER.xlsx",
    "document_priority_csv": Path("05_reports") / "document_priority_rank.csv",
    "risk_signals_csv": Path("05_reports") / "risk_signals.csv",
    "financial_signals_csv": Path("05_reports") / "financial_signals.csv",
    "ssot_candidates_csv": Path("05_reports") / "ssot_candidates.csv",
    "conflict_report_csv": Path("05_reports") / "conflict_report.csv",
    "citation_report_csv": Path("05_reports") / "citation_verification_report.csv",
}


@dataclass(frozen=True)
class BoardPaths:
    base_dir: Path
    output_dir: Path
    memo_md: Path
    memo_json: Path
    actions_csv: Path
    conditions_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def short_text(value: Any, max_chars: int = 1600) -> str:
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


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> BoardPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return BoardPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        memo_md=output_dir / OUTPUT_MEMO_MD,
        memo_json=output_dir / OUTPUT_MEMO_JSON,
        actions_csv=output_dir / OUTPUT_ACTIONS_CSV,
        conditions_csv=output_dir / OUTPUT_CONDITIONS_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in SOURCE_JSON_FILES.items()
    }


def top_collection(report: dict[str, Any] | None, key: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        return []
    rows = report.get(key, [])
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)][:limit]


def determine_decision_status(reports: dict[str, dict[str, Any] | None], board_stance: str) -> tuple[str, list[str]]:
    reasons: list[str] = []

    required = [
        "lender_dd_pack",
        "executive_pack",
        "latest_audit_record",
        "citation_verification",
        "risk_signals",
        "document_priority",
    ]
    missing = [name for name in required if not reports.get(name)]
    if missing:
        return DECISION_INCOMPLETE, ["Missing board-critical reports: " + ", ".join(missing)]

    dd_status = nested_get(reports.get("lender_dd_pack"), "dd_status")
    executive_status = nested_get(reports.get("executive_pack"), "pack_status")
    audit_status = nested_get(reports.get("latest_audit_record"), "audit_status")
    citation_status = nested_get(reports.get("citation_verification"), "verification_status")
    conflict_status = nested_get(reports.get("conflict_report"), "summary.institutional_status")
    critical_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0))
    high_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0))
    p0_documents = safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0))
    p1_documents = safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0))

    if dd_status in {"LENDER_DD_BLOCKED", "LENDER_DD_INCOMPLETE"}:
        reasons.append(f"Lender DD status blocks board approval: {dd_status}")
    if executive_status in {"EXECUTIVE_PACK_BLOCKED", "EXECUTIVE_PACK_INCOMPLETE"}:
        reasons.append(f"Executive pack status blocks board approval: {executive_status}")
    if audit_status in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE"}:
        reasons.append(f"Audit status blocks approval: {audit_status}")
    if citation_status in {"CITATION_VERIFICATION_FAIL", "NO_EVIDENCE_NO_CITATION"}:
        reasons.append(f"Citation status blocks approval: {citation_status}")
    if critical_risks > 0:
        reasons.append(f"Critical risk count > 0: {critical_risks}")
    if p0_documents > 0:
        reasons.append(f"P0 document count > 0: {p0_documents}")

    if reasons:
        return DECISION_BLOCK, reasons

    conditional_reasons = []
    if dd_status == "LENDER_DD_REVIEW_REQUIRED":
        conditional_reasons.append("Lender DD pack requires manual review.")
    if executive_status == "EXECUTIVE_PACK_REVIEW_REQUIRED":
        conditional_reasons.append("Executive pack requires manual review.")
    if audit_status != "AUDIT_PASS":
        conditional_reasons.append(f"Audit status is not clean pass: {audit_status}")
    if citation_status != "CITATION_VERIFICATION_PASS":
        conditional_reasons.append(f"Citation verification is not clean pass: {citation_status}")
    if conflict_status in {"CONFLICTS_DETECTED_REVIEW_REQUIRED", "HIGH_CONFLICT_RISK_MANUAL_REVIEW"}:
        conditional_reasons.append(f"Conflict status requires SSOT review: {conflict_status}")
    if high_risks > 0:
        conditional_reasons.append(f"High risk count > 0: {high_risks}")
    if p1_documents > 0:
        conditional_reasons.append(f"P1 document count > 0: {p1_documents}")

    if board_stance == "conservative":
        financial_review = nested_get(reports.get("financial_signals"), "summary.review_required", 0)
        ssot_review = nested_get(reports.get("ssot_candidates"), "summary.review_required", 0)
        if safe_int(financial_review, 0) > 0:
            conditional_reasons.append(f"Financial signal review required: {financial_review}")
        if safe_int(ssot_review, 0) > 0:
            conditional_reasons.append(f"SSOT review required: {ssot_review}")

    if conditional_reasons:
        return DECISION_APPROVE_WITH_CONDITIONS if board_stance != "conservative_block" else DECISION_DEFER, conditional_reasons

    return DECISION_APPROVE, ["Core audit/citation/risk/document gates are clean."]


def build_approval_conditions(reports: dict[str, dict[str, Any] | None], decision_status: str) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []

    def add(condition_type: str, area: str, condition: str, evidence_source: str, severity: str, closure_rule: str) -> None:
        cid_raw = f"{condition_type}|{area}|{condition}|{evidence_source}"
        conditions.append({
            "Condition_ID": "COND-" + hashlib.sha256(cid_raw.encode("utf-8")).hexdigest()[:12],
            "Condition_Type": condition_type,
            "Area": area,
            "Severity": severity,
            "Condition": condition,
            "Evidence_Source": evidence_source,
            "Closure_Rule": closure_rule,
            "Owner": "Danijela / TITAN Operator",
            "Due_Logic": "Before board final approval" if condition_type == ACTION_CONDITION_PRECEDENT else "Before final lender submission",
            "Status": "OPEN",
        })

    audit_status = nested_get(reports.get("latest_audit_record"), "audit_status")
    citation_status = nested_get(reports.get("citation_verification"), "verification_status")
    conflict_status = nested_get(reports.get("conflict_report"), "summary.institutional_status")
    critical_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0))
    high_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0))
    p0_documents = safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0))
    p1_documents = safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0))
    dd_status = nested_get(reports.get("lender_dd_pack"), "dd_status")
    executive_status = nested_get(reports.get("executive_pack"), "pack_status")

    if audit_status != "AUDIT_PASS":
        add(ACTION_CONDITION_PRECEDENT, "Audit", f"Resolve audit status: {audit_status}", "latest_audit_record.json", "CRITICAL", "latest_audit_record.audit_status must be AUDIT_PASS.")

    if citation_status != "CITATION_VERIFICATION_PASS":
        add(ACTION_CONDITION_PRECEDENT, "Citation", f"Resolve citation status: {citation_status}", "citation_verification_report.json", "CRITICAL", "citation verification must pass or be explicitly accepted by board.")

    if conflict_status in {"CONFLICTS_DETECTED_REVIEW_REQUIRED", "HIGH_CONFLICT_RISK_MANUAL_REVIEW"}:
        add(ACTION_CONDITION_PRECEDENT, "Conflict", f"Resolve or approve conflict status: {conflict_status}", "conflict_report.json", "HIGH", "All material conflicts must have SSOT decision notes.")

    if critical_risks > 0:
        add(ACTION_CONDITION_PRECEDENT, "Risk", f"Close {critical_risks} critical risks.", "risk_signals_report.json", "CRITICAL", "Critical risk count must become 0 or receive formal board exception.")

    if high_risks > 0:
        add(ACTION_CONDITION_SUBSEQUENT, "Risk", f"Review {high_risks} high risks.", "risk_signals_report.json", "HIGH", "High risks must have mitigation owner and action plan.")

    if p0_documents > 0:
        add(ACTION_CONDITION_PRECEDENT, "Document Review", f"Review {p0_documents} P0 documents.", "document_priority_rank.json", "CRITICAL", "P0 count must become 0 or be formally acknowledged.")

    if p1_documents > 0:
        add(ACTION_CONDITION_SUBSEQUENT, "Document Review", f"Review {p1_documents} P1 documents.", "document_priority_rank.json", "HIGH", "P1 review must be completed before final lender submission.")

    if dd_status in {"LENDER_DD_REVIEW_REQUIRED", "LENDER_DD_BLOCKED", "LENDER_DD_INCOMPLETE"}:
        severity = "CRITICAL" if "BLOCKED" in str(dd_status) or "INCOMPLETE" in str(dd_status) else "HIGH"
        add(ACTION_CONDITION_PRECEDENT, "Lender DD", f"Resolve lender DD status: {dd_status}", "TITAN_LENDER_DD_PACK.json", severity, "DD status must be READY_FOR_REVIEW or formally exceptioned.")

    if executive_status in {"EXECUTIVE_PACK_REVIEW_REQUIRED", "EXECUTIVE_PACK_BLOCKED", "EXECUTIVE_PACK_INCOMPLETE"}:
        severity = "CRITICAL" if "BLOCKED" in str(executive_status) or "INCOMPLETE" in str(executive_status) else "HIGH"
        add(ACTION_CONDITION_PRECEDENT, "Executive Pack", f"Resolve executive pack status: {executive_status}", "TITAN_RAG_EXECUTIVE_PACK.json", severity, "Executive pack must be READY or formally exceptioned.")

    if not conditions and decision_status == DECISION_APPROVE:
        add(ACTION_MONITOR, "Governance", "Maintain audit trail and source manifest for board file.", "board_decision_memo", "LOW", "Archive memo, JSON, manifest and source_exports.")

    return conditions


def build_board_actions(decision_status: str, conditions: list[dict[str, Any]], reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    def add(action_type: str, priority: int, action: str, reason: str, source: str, owner: str = "Danijela / TITAN Operator") -> None:
        raw = f"{action_type}|{priority}|{action}|{source}"
        actions.append({
            "Action_ID": "ACT-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12],
            "Priority": priority,
            "Action_Type": action_type,
            "Action": action,
            "Reason": reason,
            "Source": source,
            "Owner": owner,
            "Status": "OPEN",
        })

    if decision_status == DECISION_BLOCK:
        add(ACTION_IMMEDIATE, 1, "Do not approve package for institutional/lender use yet.", "Blocking audit/risk/conflict/document conditions exist.", "board_decision_status")
    elif decision_status == DECISION_INCOMPLETE:
        add(ACTION_IMMEDIATE, 1, "Do not make board decision until missing reports are generated.", "Board-critical reports are incomplete.", "board_decision_status")
    elif decision_status == DECISION_DEFER:
        add(ACTION_IMMEDIATE, 1, "Defer decision pending manual review.", "Conservative board stance requires clean downstream review.", "board_decision_status")
    elif decision_status == DECISION_APPROVE_WITH_CONDITIONS:
        add(ACTION_CONDITION_PRECEDENT, 1, "Approve only subject to listed conditions precedent and subsequent.", "Non-blocking review items remain open.", "approval_conditions")
    else:
        add(ACTION_MONITOR, 3, "Approve for next stage and preserve audit pack.", "Core gates are clean.", "board_decision_status")

    for idx, cond in enumerate(conditions, start=2):
        if cond["Condition_Type"] == ACTION_MONITOR:
            continue
        add(cond["Condition_Type"], idx, cond["Condition"], cond["Closure_Rule"], cond["Evidence_Source"])

    morning_tasks = top_collection(reports.get("morning_briefing"), "top_tasks", 15)
    for task in morning_tasks:
        add(
            task.get("Severity") or ACTION_MONITOR,
            safe_int(task.get("Priority"), 99),
            str(task.get("Action") or ""),
            str(task.get("Reason") or ""),
            str(task.get("Source") or "morning_briefing"),
        )

    actions.sort(key=lambda x: safe_int(x.get("Priority"), 999))
    return actions


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
            "board_memo_consolidates_existing_reports_only": True,
            "source_documents_not_modified": True,
            "json_reports_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_memo(
    reports: dict[str, dict[str, Any] | None],
    decision_status: str,
    decision_reasons: list[str],
    conditions: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    manifest: dict[str, Any],
    board_stance: str,
    strict: bool,
) -> dict[str, Any]:
    latest_answer = reports.get("latest_answer") or {}
    answer_confidence = latest_answer.get("confidence") if isinstance(latest_answer.get("confidence"), dict) else {}

    memo = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "BOARD_DECISION_MEMO_AUDIT_LOCKED",
        "board_stance": board_stance,
        "strict_mode": strict,
        "decision_status": decision_status,
        "decision_reasons": decision_reasons,
        "recommended_board_resolution": recommended_resolution(decision_status),
        "query": nested_get(reports.get("latest_evidence_pack"), "query") or latest_answer.get("query"),
        "executive_snapshot": {
            "direct_answer_snapshot": short_text(latest_answer.get("direct_answer"), 1800),
            "answer_institutional_status": latest_answer.get("institutional_status"),
            "answer_confidence_score": answer_confidence.get("confidence_score"),
            "answer_confidence_label": answer_confidence.get("confidence_label"),
            "next_action": latest_answer.get("next_action"),
            "risk_if_skipped": latest_answer.get("risk_if_skipped"),
        },
        "decision_metrics": {
            "dd_status": nested_get(reports.get("lender_dd_pack"), "dd_status"),
            "executive_pack_status": nested_get(reports.get("executive_pack"), "pack_status"),
            "audit_status": nested_get(reports.get("latest_audit_record"), "audit_status"),
            "citation_status": nested_get(reports.get("citation_verification"), "verification_status"),
            "conflict_status": nested_get(reports.get("conflict_report"), "summary.institutional_status"),
            "risk_status": nested_get(reports.get("risk_signals"), "summary.institutional_status"),
            "critical_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0)),
            "high_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0)),
            "total_conflicts": safe_int(nested_get(reports.get("conflict_report"), "summary.total_conflicts", 0)),
            "financial_signals": safe_int(nested_get(reports.get("financial_signals"), "summary.total_signals", 0)),
            "ssot_candidates": safe_int(nested_get(reports.get("ssot_candidates"), "summary.total_candidates", 0)),
            "p0_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0)),
            "p1_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0)),
            "evidence_count": safe_int(nested_get(reports.get("latest_evidence_pack"), "evidence_count", 0)),
            "source_file_count": safe_int(nested_get(reports.get("latest_evidence_pack"), "source_file_count", 0)),
        },
        "approval_conditions": conditions,
        "board_actions": actions,
        "top_priority_documents": top_collection(reports.get("document_priority"), "documents", 25),
        "top_risks": top_collection(reports.get("risk_signals"), "signals", 25),
        "top_financial_signals": top_collection(reports.get("financial_signals"), "signals", 25),
        "top_conflicts": top_collection(reports.get("conflict_report"), "conflicts", 20),
        "top_ssot_candidates": top_collection(reports.get("ssot_candidates"), "candidates", 20),
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "manifest_sha256": manifest.get("manifest_sha256"),
        "governance_rule": {
            "board_memo_consolidates_existing_reports_only": True,
            "no_new_unsupported_claims": True,
            "source_documents_not_modified": True,
            "decision_status_is_recommendation_not_legal_approval": True,
            "board_or_authorized_officers_make_final_decision": True,
            "json_reports_and_original_source_files_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    memo["board_decision_memo_sha256"] = sha256_json(memo)
    return memo


def recommended_resolution(decision_status: str) -> str:
    if decision_status == DECISION_APPROVE:
        return "Approve progression to the next project/lender preparation stage, preserving the audit trail and evidence pack."
    if decision_status == DECISION_APPROVE_WITH_CONDITIONS:
        return "Approve progression only subject to the listed conditions precedent/subsequent and formal closure evidence."
    if decision_status == DECISION_DEFER:
        return "Defer decision until manual review items are closed and the memo is regenerated."
    if decision_status == DECISION_BLOCK:
        return "Do not approve institutional/lender use until blockers are resolved or formally exceptioned by competent authority."
    return "No board decision should be taken because the evidence pack is incomplete."


def write_actions_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Action_ID",
        "Priority",
        "Action_Type",
        "Action",
        "Reason",
        "Source",
        "Owner",
        "Status",
    ])


def write_conditions_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Condition_ID",
        "Condition_Type",
        "Area",
        "Severity",
        "Condition",
        "Evidence_Source",
        "Closure_Rule",
        "Owner",
        "Due_Logic",
        "Status",
    ])


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def metrics_md(metrics: dict[str, Any]) -> str:
    lines = [
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in metrics.items():
        lines.append(f"| {md_escape(key)} | {md_escape(value)} |")
    return "\n".join(lines)


def conditions_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No approval conditions."
    lines = [
        "| ID | Type | Severity | Area | Condition | Closure Rule |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Condition_ID'))} | "
            f"{md_escape(row.get('Condition_Type'))} | "
            f"{md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Condition'))} | "
            f"{md_escape(row.get('Closure_Rule'))} |"
        )
    return "\n".join(lines)


def actions_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No board actions."
    lines = [
        "| Priority | Type | Action | Reason | Owner |",
        "|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('Priority')} | "
            f"{md_escape(row.get('Action_Type'))} | "
            f"{md_escape(row.get('Action'))} | "
            f"{md_escape(short_text(row.get('Reason'), 300))} | "
            f"{md_escape(row.get('Owner'))} |"
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


def docs_md(rows: list[dict[str, Any]]) -> str:
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


def memo_to_markdown(memo: dict[str, Any]) -> str:
    snapshot = memo.get("executive_snapshot", {}) if isinstance(memo.get("executive_snapshot"), dict) else {}
    metrics = memo.get("decision_metrics", {}) if isinstance(memo.get("decision_metrics"), dict) else {}

    return f"""# TITAN Board Decision Memo

## 1. Decision Header

| Field | Value |
|---|---|
| Created At | {memo.get("created_at")} |
| Decision Status | {memo.get("decision_status")} |
| Board Stance | {memo.get("board_stance")} |
| Query | {md_escape(memo.get("query"))} |
| Memo SHA-256 | `{memo.get("board_decision_memo_sha256")}` |

**Recommended board resolution**

```text
{memo.get("recommended_board_resolution")}
```

**Decision reasons**

```json
{json.dumps(memo.get("decision_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Executive Snapshot

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

## 3. Decision Metrics

{metrics_md(metrics)}

---

## 4. Approval Conditions

{conditions_md(memo.get("approval_conditions", []))}

---

## 5. Board Actions

{actions_md(memo.get("board_actions", []))}

---

## 6. Priority Documents

{docs_md(memo.get("top_priority_documents", []))}

---

## 7. Key Risks

{risks_md(memo.get("top_risks", []))}

---

## 8. Key Financial Signals

{financial_md(memo.get("top_financial_signals", []))}

---

## 9. Conflicts

```json
{json.dumps(memo.get("top_conflicts", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 10. SSOT Candidates

```json
{json.dumps(memo.get("top_ssot_candidates", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 11. Governance Rule

```text
Board memo consolidates existing reports only.
It does not create new unsupported claims.
It does not modify source documents.
Decision status is a recommendation, not legal approval.
Board or authorized officers make the final decision.
JSON reports and original source files remain authoritative.
Audit precedes decision.
```
"""


def print_summary(memo: dict[str, Any], paths: BoardPaths) -> None:
    metrics = memo.get("decision_metrics", {}) if isinstance(memo.get("decision_metrics"), dict) else {}
    print("=" * 100)
    print("TITAN BOARD DECISION MEMO BUILDER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Decision status:          {memo.get('decision_status')}")
    print(f"Board stance:             {memo.get('board_stance')}")
    print(f"Audit status:             {metrics.get('audit_status')}")
    print(f"Citation status:          {metrics.get('citation_status')}")
    print(f"Critical risks:           {metrics.get('critical_risks')}")
    print(f"P0 documents:             {metrics.get('p0_documents')}")
    print("-" * 100)
    print(f"Memo Markdown:            {paths.memo_md}")
    print(f"Memo JSON:                {paths.memo_json}")
    print(f"Actions CSV:              {paths.actions_csv}")
    print(f"Conditions CSV:           {paths.conditions_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 23 — board decision memo builder.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional board memo output directory.")
    parser.add_argument(
        "--board-stance",
        default="conservative",
        choices=["conservative", "standard", "conservative_block"],
        help="Board risk stance used for decision recommendation.",
    )
    parser.add_argument("--no-copy-files", action="store_true", help="Do not copy XLSX/CSV exports into source_exports.")
    parser.add_argument("--strict", action="store_true", help="Strict metadata flag for memo governance.")
    parser.add_argument("--print", action="store_true", help="Print Markdown board memo to console.")

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
        decision_status, decision_reasons = determine_decision_status(reports, args.board_stance)
        conditions = build_approval_conditions(reports, decision_status)
        actions = build_board_actions(decision_status, conditions, reports)
        copied_files = copy_source_exports(base_dir, paths.output_dir, copy_files=not bool(args.no_copy_files))
        manifest = build_manifest(base_dir, paths.output_dir, copied_files)

        memo = build_memo(
            reports=reports,
            decision_status=decision_status,
            decision_reasons=decision_reasons,
            conditions=conditions,
            actions=actions,
            manifest=manifest,
            board_stance=args.board_stance,
            strict=bool(args.strict),
        )

        markdown = memo_to_markdown(memo)

        write_json(paths.memo_json, memo)
        write_text(paths.memo_md, markdown)
        write_actions_csv(paths.actions_csv, actions)
        write_conditions_csv(paths.conditions_csv, conditions)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "BOARD_DECISION_MEMO_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "decision_status": memo.get("decision_status"),
            "board_stance": args.board_stance,
            "memo_sha256": memo.get("board_decision_memo_sha256"),
            "manifest_sha256": manifest.get("manifest_sha256"),
            "outputs": {
                "memo_md": str(paths.memo_md),
                "memo_json": str(paths.memo_json),
                "actions_csv": str(paths.actions_csv),
                "conditions_csv": str(paths.conditions_csv),
                "manifest_json": str(paths.manifest_json),
            },
        })

        print_summary(memo, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "BOARD_DECISION_MEMO_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "board_stance": args.board_stance,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN BOARD DECISION MEMO BUILDER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
