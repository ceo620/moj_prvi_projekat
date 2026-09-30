#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10_morning_briefing.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 10 — Morning Briefing Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Create a daily operational briefing from the latest TITAN RAG summaries, audit
records, logs, risk signals, financial signals and document priority ranking.

This script does NOT scan files.
This script does NOT extract text.
This script does NOT build embeddings.
This script does NOT generate factual conclusions outside existing reports.
It summarizes pipeline state and operational next actions.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/discovery_summary.json
05_reports/safety_filter_summary.json
05_reports/extraction_summary.json
05_reports/chunking_summary.json
05_reports/embedding_summary.json
05_reports/incremental_refresh_summary.json
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json
05_reports/latest_audit_record.json
05_reports/conflict_report.json
05_reports/financial_signals_report.json
05_reports/risk_signals_report.json
05_reports/document_priority_rank.json
06_logs/*.jsonl

Outputs
-------
05_reports/morning_briefing.json
05_reports/morning_briefing.md
05_reports/morning_briefing_tasks.csv
06_logs/morning_briefing_audit.jsonl
06_logs/morning_briefing_errors.jsonl

Designed for compatibility with:
19_night_run_orchestrator.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\10_morning_briefing.py" --print
"""

from __future__ import annotations

import argparse
import csv
import json
import traceback
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "10_morning_briefing.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

REPORT_FILES = {
    "discovery": Path("05_reports") / "discovery_summary.json",
    "safety": Path("05_reports") / "safety_filter_summary.json",
    "extraction": Path("05_reports") / "extraction_summary.json",
    "chunking": Path("05_reports") / "chunking_summary.json",
    "embedding": Path("05_reports") / "embedding_summary.json",
    "incremental": Path("05_reports") / "incremental_refresh_summary.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
    "latest_rag_answer": Path("05_reports") / "latest_rag_answer.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "ssot_candidates_report": Path("05_reports") / "ssot_candidates_report.json",
    "financial_signals_report": Path("05_reports") / "financial_signals_report.json",
    "risk_signals_report": Path("05_reports") / "risk_signals_report.json",
    "document_priority_rank": Path("05_reports") / "document_priority_rank.json",
    "night_run_summary": Path("05_reports") / "night_run_summary.json",
}

LOG_FILES = [
    Path("06_logs") / "discovery_errors.jsonl",
    Path("06_logs") / "safety_filter_errors.jsonl",
    Path("06_logs") / "extraction_errors.jsonl",
    Path("06_logs") / "chunking_errors.jsonl",
    Path("06_logs") / "embedding_errors.jsonl",
    Path("06_logs") / "rag_search_errors.jsonl",
    Path("06_logs") / "generation_errors.jsonl",
    Path("06_logs") / "final_audit_errors.jsonl",
    Path("06_logs") / "incremental_refresh_errors.jsonl",
    Path("06_logs") / "risk_signal_extractor_errors.jsonl",
    Path("06_logs") / "financial_signal_extractor_errors.jsonl",
    Path("06_logs") / "document_priority_ranker_errors.jsonl",
    Path("06_logs") / "night_run_orchestrator_errors.jsonl",
]

OUTPUT_JSON = Path("05_reports") / "morning_briefing.json"
OUTPUT_MD = Path("05_reports") / "morning_briefing.md"
OUTPUT_TASKS_CSV = Path("05_reports") / "morning_briefing_tasks.csv"

AUDIT_LOG = Path("06_logs") / "morning_briefing_audit.jsonl"
ERROR_LOG = Path("06_logs") / "morning_briefing_errors.jsonl"

STATUS_GREEN = "GREEN_OPERATIONAL"
STATUS_AMBER = "AMBER_REVIEW_REQUIRED"
STATUS_RED = "RED_BLOCKED"
STATUS_GRAY = "GRAY_INCOMPLETE"

DEFAULT_MAX_LOG_LINES_PER_FILE = 50
DEFAULT_TOP_TASKS = 25
DEFAULT_TOP_DOCUMENTS = 20
DEFAULT_TOP_RISKS = 20


@dataclass(frozen=True)
class BriefingPaths:
    base_dir: Path
    output_json: Path
    output_md: Path
    output_tasks_csv: Path
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
        return int(value)
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def short_text(value: Any, max_chars: int = 400) -> str:
    text = normalize_inline(value)
    if len(text) > max_chars:
        return text[:max_chars] + " ..."
    return text


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def read_jsonl_tail(path: Path, max_lines: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    tail = lines[-max_lines:] if max_lines > 0 else lines

    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(tail, start=1):
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                records.append(payload)
            else:
                records.append({"raw": raw[:500], "parse_status": "NON_OBJECT"})
        except Exception as exc:
            records.append({"raw": raw[:500], "parse_status": "INVALID_JSON", "error": str(exc)})

    return records


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_tasks_csv(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Priority",
        "Task_ID",
        "Category",
        "Severity",
        "Action",
        "Reason",
        "Source",
        "Owner",
        "Due_Logic",
        "Status",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for task in tasks:
            writer.writerow(task)


def resolve_paths(base_dir: Path) -> BriefingPaths:
    return BriefingPaths(
        base_dir=base_dir,
        output_json=base_dir / OUTPUT_JSON,
        output_md=base_dir / OUTPUT_MD,
        output_tasks_csv=base_dir / OUTPUT_TASKS_CSV,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in REPORT_FILES.items()
    }


def load_error_logs(base_dir: Path, max_lines_per_file: int) -> dict[str, list[dict[str, Any]]]:
    return {
        rel_path.name: read_jsonl_tail(base_dir / rel_path, max_lines=max_lines_per_file)
        for rel_path in LOG_FILES
    }


def file_presence(base_dir: Path) -> dict[str, bool]:
    presence: dict[str, bool] = {}
    for name, rel_path in REPORT_FILES.items():
        presence[name] = (base_dir / rel_path).exists()
    return presence


def report_statuses(reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    discovery = reports.get("discovery") or {}
    safety = reports.get("safety") or {}
    extraction = reports.get("extraction") or {}
    chunking = reports.get("chunking") or {}
    embedding = reports.get("embedding") or {}
    incremental = reports.get("incremental") or {}
    audit = reports.get("latest_audit_record") or {}
    conflict = reports.get("conflict_report") or {}
    risk = reports.get("risk_signals_report") or {}
    financial = reports.get("financial_signals_report") or {}
    priority = reports.get("document_priority_rank") or {}
    night = reports.get("night_run_summary") or {}

    statuses = {
        "discovery_records": discovery.get("total_records"),
        "safe_for_extraction": safety.get("safe_for_extraction"),
        "extracted_count": extraction.get("extracted_count"),
        "extraction_errors": extraction.get("error_count"),
        "total_chunks": chunking.get("total_chunks"),
        "chunking_errors": chunking.get("error_files"),
        "embedding_status": embedding.get("status"),
        "embedded_count": embedding.get("embedded_count"),
        "embedding_errors": embedding.get("error_count"),
        "collection_count": embedding.get("collection_count_after_run"),
        "incremental_records": incremental.get("incremental_records"),
        "incremental_safe_records": incremental.get("incremental_safe_records"),
        "audit_status": audit.get("audit_status"),
        "conflict_status": (conflict.get("summary") or {}).get("institutional_status") if isinstance(conflict.get("summary"), dict) else None,
        "total_conflicts": (conflict.get("summary") or {}).get("total_conflicts") if isinstance(conflict.get("summary"), dict) else None,
        "risk_status": (risk.get("summary") or {}).get("institutional_status") if isinstance(risk.get("summary"), dict) else None,
        "critical_risks": (risk.get("summary") or {}).get("critical_count") if isinstance(risk.get("summary"), dict) else None,
        "high_risks": (risk.get("summary") or {}).get("high_count") if isinstance(risk.get("summary"), dict) else None,
        "financial_status": (financial.get("summary") or {}).get("institutional_status") if isinstance(financial.get("summary"), dict) else None,
        "financial_signals": (financial.get("summary") or {}).get("total_signals") if isinstance(financial.get("summary"), dict) else None,
        "document_priority_status": (priority.get("summary") or {}).get("institutional_status") if isinstance(priority.get("summary"), dict) else None,
        "ranked_documents": (priority.get("summary") or {}).get("ranked_documents") if isinstance(priority.get("summary"), dict) else None,
        "night_run_status": night.get("final_status"),
        "night_run_critical_failures": night.get("critical_failure_count"),
        "night_run_noncritical_failures": night.get("noncritical_failure_count"),
    }

    return statuses


def derive_overall_status(reports: dict[str, dict[str, Any] | None], logs: dict[str, list[dict[str, Any]]]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    statuses = report_statuses(reports)

    if not reports.get("discovery") or not reports.get("safety"):
        reasons.append("Discovery or safety summary missing.")
        return STATUS_GRAY, reasons

    if not reports.get("chunking") or not reports.get("embedding"):
        reasons.append("Chunking or embedding summary missing.")
        return STATUS_GRAY, reasons

    if safe_int(statuses.get("night_run_critical_failures"), 0) > 0:
        reasons.append("Night run has critical failures.")
        return STATUS_RED, reasons

    if str(statuses.get("night_run_status") or "").upper() == "FAILED_CRITICAL_STEP":
        reasons.append("Night run status is FAILED_CRITICAL_STEP.")
        return STATUS_RED, reasons

    if safe_int(statuses.get("critical_risks"), 0) > 0:
        reasons.append("Critical risk signals detected.")
        return STATUS_RED, reasons

    if str(statuses.get("audit_status") or "").upper() in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE"}:
        reasons.append(f"Latest audit status is {statuses.get('audit_status')}.")
        return STATUS_RED, reasons

    if safe_int(statuses.get("embedding_errors"), 0) > 0 and safe_int(statuses.get("embedded_count"), 0) == 0:
        reasons.append("Embedding failed with no embedded chunks.")
        return STATUS_RED, reasons

    error_log_count = sum(len(items) for items in logs.values())
    if error_log_count > 0:
        reasons.append(f"Recent error log records detected: {error_log_count}.")

    if safe_int(statuses.get("high_risks"), 0) > 0:
        reasons.append("High risk signals detected.")

    if safe_int(statuses.get("total_conflicts"), 0) > 0:
        reasons.append("Conflicts detected.")

    if str(statuses.get("audit_status") or "").upper() in {"AUDIT_PASS_WITH_WARNINGS", "AUDIT_REVIEW_REQUIRED"}:
        reasons.append(f"Latest audit has warnings/review status: {statuses.get('audit_status')}.")

    if reasons:
        return STATUS_AMBER, reasons

    reasons.append("Core pipeline summaries available and no critical blockers detected.")
    return STATUS_GREEN, reasons


def make_task(priority: int, category: str, severity: str, action: str, reason: str, source: str) -> dict[str, Any]:
    return {
        "Priority": priority,
        "Task_ID": f"TASK-{priority:03d}-{abs(hash((category, severity, action, source))) % 100000:05d}",
        "Category": category,
        "Severity": severity,
        "Action": action,
        "Reason": reason,
        "Source": source,
        "Owner": "Danijela / TITAN Operator",
        "Due_Logic": "Today" if priority <= 5 else "Next review cycle",
        "Status": "OPEN",
    }


def extract_top_risks(reports: dict[str, dict[str, Any] | None], limit: int) -> list[dict[str, Any]]:
    risk_report = reports.get("risk_signals_report") or {}
    signals = risk_report.get("signals", [])
    if not isinstance(signals, list):
        return []

    rows = [x for x in signals if isinstance(x, dict)]

    def rank(signal: dict[str, Any]) -> tuple[int, float]:
        severity = str(signal.get("Severity") or "")
        sev_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(severity, 0)
        return sev_rank, safe_float(signal.get("Confidence_Score"), 0.0)

    rows.sort(key=rank, reverse=True)
    return rows[:limit]


def extract_top_documents(reports: dict[str, dict[str, Any] | None], limit: int) -> list[dict[str, Any]]:
    doc_report = reports.get("document_priority_rank") or {}
    docs = doc_report.get("documents", [])
    if not isinstance(docs, list):
        return []
    rows = [x for x in docs if isinstance(x, dict)]
    rows.sort(key=lambda x: safe_int(x.get("Priority_Rank"), 999999))
    return rows[:limit]


def extract_top_financial(reports: dict[str, dict[str, Any] | None], limit: int = 20) -> list[dict[str, Any]]:
    report = reports.get("financial_signals_report") or {}
    signals = report.get("signals", [])
    if not isinstance(signals, list):
        return []
    rows = [x for x in signals if isinstance(x, dict)]
    rows.sort(key=lambda x: safe_float(x.get("Confidence_Score"), 0.0), reverse=True)
    return rows[:limit]


def recent_log_summary(logs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    counts = {name: len(items) for name, items in logs.items()}
    event_counter: Counter[str] = Counter()
    latest_errors: list[dict[str, Any]] = []

    for name, items in logs.items():
        for item in items:
            event = str(item.get("event") or item.get("parse_status") or "UNKNOWN")
            event_counter[event] += 1
            latest_errors.append({
                "log_file": name,
                "timestamp": item.get("timestamp"),
                "event": event,
                "error": short_text(item.get("error") or item.get("raw") or item.get("message"), 300),
            })

    latest_errors = latest_errors[-25:]

    return {
        "total_recent_error_records": sum(counts.values()),
        "by_log_file": dict(sorted(counts.items())),
        "by_event": dict(event_counter.most_common(20)),
        "latest_errors": latest_errors,
    }


def build_tasks(
    overall_status: str,
    status_reasons: list[str],
    reports: dict[str, dict[str, Any] | None],
    logs: dict[str, list[dict[str, Any]]],
    top_tasks: int,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    priority = 1

    if overall_status == STATUS_RED:
        tasks.append(make_task(
            priority=priority,
            category="BLOCKER",
            severity="CRITICAL",
            action="Stop institutional use until RED blockers are resolved.",
            reason="; ".join(status_reasons),
            source="morning_briefing.overall_status",
        ))
        priority += 1

    risk_summary = ((reports.get("risk_signals_report") or {}).get("summary") or {})
    if safe_int(risk_summary.get("critical_count"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="RISK",
            severity="CRITICAL",
            action="Open risk_signals_report and resolve CRITICAL_ACTION_REQUIRED items.",
            reason=f"Critical risks: {risk_summary.get('critical_count')}",
            source="risk_signals_report.json",
        ))
        priority += 1

    if safe_int(risk_summary.get("high_count"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="RISK",
            severity="HIGH",
            action="Review HIGH risk items before lender/board use.",
            reason=f"High risks: {risk_summary.get('high_count')}",
            source="risk_signals_report.json",
        ))
        priority += 1

    conflict_summary = ((reports.get("conflict_report") or {}).get("summary") or {})
    if safe_int(conflict_summary.get("total_conflicts"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="CONFLICT",
            severity="HIGH",
            action="Run SSOT review for detected conflicts before using conclusions.",
            reason=f"Total conflicts: {conflict_summary.get('total_conflicts')}",
            source="conflict_report.json",
        ))
        priority += 1

    audit = reports.get("latest_audit_record") or {}
    audit_status = str(audit.get("audit_status") or "")
    if audit_status in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE", "AUDIT_REVIEW_REQUIRED", "AUDIT_PASS_WITH_WARNINGS"}:
        severity = "HIGH" if audit_status in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE"} else "MEDIUM"
        tasks.append(make_task(
            priority=priority,
            category="AUDIT",
            severity=severity,
            action="Review latest_audit_record before relying on latest answer.",
            reason=f"Audit status: {audit_status}",
            source="latest_audit_record.json",
        ))
        priority += 1

    embedding = reports.get("embedding") or {}
    if str(embedding.get("status") or "") in {"FAILED", "NO_EMBEDDINGS_CREATED"} or safe_int(embedding.get("error_count"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="VECTOR_INDEX",
            severity="HIGH",
            action="Review embedding_errors and rerun Step 05.",
            reason=f"Embedding status: {embedding.get('status')} errors={embedding.get('error_count')}",
            source="embedding_summary.json",
        ))
        priority += 1

    extraction = reports.get("extraction") or {}
    if safe_int(extraction.get("error_count"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="EXTRACTION",
            severity="MEDIUM",
            action="Review extraction_errors and rerun Step 03 for failed files.",
            reason=f"Extraction errors: {extraction.get('error_count')}",
            source="extraction_summary.json",
        ))
        priority += 1

    log_summary = recent_log_summary(logs)
    if safe_int(log_summary.get("total_recent_error_records"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="LOGS",
            severity="MEDIUM",
            action="Review recent error logs and classify recurring failures.",
            reason=f"Recent error log records: {log_summary.get('total_recent_error_records')}",
            source="06_logs/*.jsonl",
        ))
        priority += 1

    incremental = reports.get("incremental") or {}
    if safe_int(incremental.get("incremental_safe_records"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="INCREMENTAL",
            severity="MEDIUM",
            action="Run Step 03 with incremental_safe_file_index.jsonl, then Step 04 and Step 05.",
            reason=f"Incremental safe records: {incremental.get('incremental_safe_records')}",
            source="incremental_refresh_summary.json",
        ))
        priority += 1

    doc_summary = ((reports.get("document_priority_rank") or {}).get("summary") or {})
    if safe_int(doc_summary.get("ranked_documents"), 0) > 0:
        tasks.append(make_task(
            priority=priority,
            category="DOCUMENT_PRIORITY",
            severity="MEDIUM",
            action="Review P0/P1 documents from document_priority_rank before SSOT/lender work.",
            reason=f"Ranked documents: {doc_summary.get('ranked_documents')}",
            source="document_priority_rank.json",
        ))
        priority += 1

    # Fill operational baseline if no tasks.
    if not tasks:
        tasks.append(make_task(
            priority=1,
            category="OPERATIONAL",
            severity="LOW",
            action="Pipeline appears operational. Continue with targeted query/search cycle.",
            reason="No blockers detected in available summaries.",
            source="morning_briefing.overall_status",
        ))

    return tasks[:top_tasks]


def build_briefing(
    base_dir: Path,
    reports: dict[str, dict[str, Any] | None],
    logs: dict[str, list[dict[str, Any]]],
    max_tasks: int,
    top_documents: int,
    top_risks: int,
) -> dict[str, Any]:
    presence = file_presence(base_dir)
    statuses = report_statuses(reports)
    overall_status, reasons = derive_overall_status(reports, logs)

    tasks = build_tasks(
        overall_status=overall_status,
        status_reasons=reasons,
        reports=reports,
        logs=logs,
        top_tasks=max_tasks,
    )

    briefing = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "MORNING_BRIEFING_AUDIT_LOCKED",
        "base_dir": str(base_dir),
        "overall_status": overall_status,
        "overall_status_reasons": reasons,
        "report_presence": presence,
        "pipeline_statuses": statuses,
        "recent_log_summary": recent_log_summary(logs),
        "top_tasks": tasks,
        "top_risks": extract_top_risks(reports, limit=top_risks),
        "top_financial_signals": extract_top_financial(reports, limit=20),
        "top_priority_documents": extract_top_documents(reports, limit=top_documents),
        "latest_answer_snapshot": {
            "query": (reports.get("latest_rag_answer") or {}).get("query"),
            "institutional_status": (reports.get("latest_rag_answer") or {}).get("institutional_status"),
            "confidence": (reports.get("latest_rag_answer") or {}).get("confidence"),
            "direct_answer": short_text((reports.get("latest_rag_answer") or {}).get("direct_answer"), 1200),
            "next_action": (reports.get("latest_rag_answer") or {}).get("next_action"),
        },
        "governance_rule": {
            "briefing_is_operational_summary_not_truth": True,
            "source_reports_remain_authoritative": True,
            "red_or_critical_requires_manual_review": True,
            "audit_precedes_decision": True,
        },
    }

    briefing["briefing_sha256"] = hashlib.sha256(
        json.dumps(briefing, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return briefing


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def tasks_to_markdown(tasks: list[dict[str, Any]]) -> str:
    if not tasks:
        return "No tasks."

    lines = [
        "| Priority | Category | Severity | Action | Reason | Source |",
        "|---:|---|---|---|---|---|",
    ]

    for task in tasks:
        lines.append(
            f"| {task.get('Priority')} | "
            f"{md_escape(task.get('Category'))} | "
            f"{md_escape(task.get('Severity'))} | "
            f"{md_escape(task.get('Action'))} | "
            f"{md_escape(task.get('Reason'))} | "
            f"{md_escape(task.get('Source'))} |"
        )

    return "\n".join(lines)


def risks_to_markdown(risks: list[dict[str, Any]]) -> str:
    if not risks:
        return "No risk signals available."

    lines = [
        "| Severity | Type | Confidence | Status | Source | Action |",
        "|---|---|---:|---|---|---|",
    ]

    for item in risks:
        lines.append(
            f"| {md_escape(item.get('Severity'))} | "
            f"{md_escape(item.get('Risk_Type'))} | "
            f"{item.get('Confidence_Score')} | "
            f"{md_escape(item.get('Risk_Status'))} | "
            f"`{md_escape(item.get('Source_Path'))}` | "
            f"{md_escape(item.get('Recommended_Action'))} |"
        )

    return "\n".join(lines)


def docs_to_markdown(docs: list[dict[str, Any]]) -> str:
    if not docs:
        return "No document priority ranking available."

    lines = [
        "| Rank | Class | Score | File | Review Status | Path |",
        "|---:|---|---:|---|---|---|",
    ]

    for item in docs:
        lines.append(
            f"| {item.get('Priority_Rank')} | "
            f"{md_escape(item.get('Priority_Class'))} | "
            f"{item.get('Priority_Score')} | "
            f"{md_escape(item.get('File_Name'))} | "
            f"{md_escape(item.get('Review_Status'))} | "
            f"`{md_escape(item.get('Document_Path'))}` |"
        )

    return "\n".join(lines)


def statuses_to_markdown(statuses: dict[str, Any]) -> str:
    lines = [
        "| Metric | Value |",
        "|---|---|",
    ]

    for key, value in statuses.items():
        lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    return "\n".join(lines)


def briefing_to_markdown(briefing: dict[str, Any]) -> str:
    latest = briefing.get("latest_answer_snapshot", {}) if isinstance(briefing.get("latest_answer_snapshot"), dict) else {}
    log_summary = briefing.get("recent_log_summary", {}) if isinstance(briefing.get("recent_log_summary"), dict) else {}

    return f"""# TITAN RAG Morning Briefing

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {briefing.get("created_at")} |
| Overall Status | {briefing.get("overall_status")} |
| Briefing SHA-256 | `{briefing.get("briefing_sha256")}` |
| Policy | {briefing.get("policy")} |
| Script | {SCRIPT_NAME} {SCRIPT_VERSION} |

**Status reasons:**

```json
{json.dumps(briefing.get("overall_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Pipeline Statuses

{statuses_to_markdown(briefing.get("pipeline_statuses", {}))}

---

## 3. Top Tasks

{tasks_to_markdown(briefing.get("top_tasks", []))}

---

## 4. Top Risks

{risks_to_markdown(briefing.get("top_risks", []))}

---

## 5. Priority Documents

{docs_to_markdown(briefing.get("top_priority_documents", []))}

---

## 6. Latest Answer Snapshot

| Field | Value |
|---|---|
| Query | {md_escape(latest.get("query"))} |
| Institutional Status | {md_escape(latest.get("institutional_status"))} |
| Confidence | `{json.dumps(latest.get("confidence"), ensure_ascii=False)}` |
| Next Action | {md_escape(latest.get("next_action"))} |

**Direct Answer Snapshot**

```text
{latest.get("direct_answer") or ""}
```

---

## 7. Recent Log Summary

| Field | Value |
|---|---|
| Total Recent Error Records | {log_summary.get("total_recent_error_records")} |

```json
{json.dumps({
    "by_log_file": log_summary.get("by_log_file"),
    "by_event": log_summary.get("by_event"),
}, indent=2, ensure_ascii=False)}
```

---

## 8. Governance Rule

```text
Morning briefing is an operational summary, not final truth.
Source reports remain authoritative.
RED/CRITICAL status requires manual review.
Audit precedes decision.
```
"""


def print_summary(briefing: dict[str, Any], paths: BriefingPaths) -> None:
    print("=" * 100)
    print("TITAN RAG MORNING BRIEFING v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Created at:        {briefing.get('created_at')}")
    print(f"Overall status:    {briefing.get('overall_status')}")
    print(f"Tasks:             {len(briefing.get('top_tasks', []))}")
    print(f"Top risks:         {len(briefing.get('top_risks', []))}")
    print(f"Top documents:     {len(briefing.get('top_priority_documents', []))}")
    print("-" * 100)
    print(f"Briefing JSON:     {paths.output_json}")
    print(f"Briefing MD:       {paths.output_md}")
    print(f"Tasks CSV:         {paths.output_tasks_csv}")
    print(f"Audit log:         {paths.audit_log}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 10 — morning briefing."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--max-log-lines-per-file",
        type=int,
        default=DEFAULT_MAX_LOG_LINES_PER_FILE,
        help="Tail lines to read from each error log.",
    )

    parser.add_argument(
        "--top-tasks",
        type=int,
        default=DEFAULT_TOP_TASKS,
        help="Maximum tasks in briefing.",
    )

    parser.add_argument(
        "--top-documents",
        type=int,
        default=DEFAULT_TOP_DOCUMENTS,
        help="Maximum priority documents shown.",
    )

    parser.add_argument(
        "--top-risks",
        type=int,
        default=DEFAULT_TOP_RISKS,
        help="Maximum risk signals shown.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print Markdown briefing to console.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir)

    try:
        reports = load_reports(base_dir)
        logs = load_error_logs(
            base_dir=base_dir,
            max_lines_per_file=int(args.max_log_lines_per_file),
        )

        briefing = build_briefing(
            base_dir=base_dir,
            reports=reports,
            logs=logs,
            max_tasks=int(args.top_tasks),
            top_documents=int(args.top_documents),
            top_risks=int(args.top_risks),
        )

        markdown = briefing_to_markdown(briefing)

        write_json(paths.output_json, briefing)
        write_text(paths.output_md, markdown)
        write_tasks_csv(paths.output_tasks_csv, briefing.get("top_tasks", []))

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "MORNING_BRIEFING_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "overall_status": briefing.get("overall_status"),
            "briefing_sha256": briefing.get("briefing_sha256"),
            "outputs": {
                "json": str(paths.output_json),
                "markdown": str(paths.output_md),
                "tasks_csv": str(paths.output_tasks_csv),
            },
        })

        print_summary(briefing, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "MORNING_BRIEFING_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG MORNING BRIEFING FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
