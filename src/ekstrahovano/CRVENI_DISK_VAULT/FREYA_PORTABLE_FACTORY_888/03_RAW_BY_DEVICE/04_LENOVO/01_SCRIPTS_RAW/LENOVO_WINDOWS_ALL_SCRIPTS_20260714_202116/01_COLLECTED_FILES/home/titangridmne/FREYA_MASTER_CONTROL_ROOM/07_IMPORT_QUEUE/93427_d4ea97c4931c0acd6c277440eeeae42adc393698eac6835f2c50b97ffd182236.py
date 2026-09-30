#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
18_document_priority_ranker.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 18 — Document Priority Ranker
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Rank documents/sources for manual review based on:
- evidence relevance from latest_evidence_pack.json
- financial signal materiality
- risk severity
- conflict exposure
- SSOT candidate importance
- citation verification quality
- source/document type importance

This script does NOT modify documents.
This script does NOT decide final truth.
This script does NOT overwrite SSOT.
It creates a prioritized review queue for operators, lenders, auditors and
Control Tower export.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/latest_evidence_pack.json
05_reports/risk_signals_report.json              # optional but recommended
05_reports/financial_signals_report.json         # optional but recommended
05_reports/conflict_report.json                  # optional
05_reports/ssot_candidates_report.json           # optional
05_reports/citation_verification_report.json     # optional
05_reports/evidence_pack_report.json             # optional

Outputs
-------
05_reports/document_priority_rank.json
05_reports/document_priority_rank.md
05_reports/document_priority_rank.csv
06_logs/document_priority_ranker_audit.jsonl
06_logs/document_priority_ranker_errors.jsonl

Designed for compatibility with:
10_morning_briefing.py
19_night_run_orchestrator.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\18_document_priority_ranker.py" --print

Strict mode
-----------
python ".\\08_scripts\\18_document_priority_ranker.py" --strict --print
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "18_document_priority_ranker.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
INPUT_RISK_REPORT = Path("05_reports") / "risk_signals_report.json"
INPUT_FINANCIAL_REPORT = Path("05_reports") / "financial_signals_report.json"
INPUT_CONFLICT_REPORT = Path("05_reports") / "conflict_report.json"
INPUT_SSOT_REPORT = Path("05_reports") / "ssot_candidates_report.json"
INPUT_CITATION_REPORT = Path("05_reports") / "citation_verification_report.json"
INPUT_EVIDENCE_REPORT = Path("05_reports") / "evidence_pack_report.json"

OUTPUT_JSON = Path("05_reports") / "document_priority_rank.json"
OUTPUT_MD = Path("05_reports") / "document_priority_rank.md"
OUTPUT_CSV = Path("05_reports") / "document_priority_rank.csv"

AUDIT_LOG = Path("06_logs") / "document_priority_ranker_audit.jsonl"
ERROR_LOG = Path("06_logs") / "document_priority_ranker_errors.jsonl"

REPORT_READY = "DOCUMENT_PRIORITY_READY"
REPORT_REVIEW_REQUIRED = "DOCUMENT_PRIORITY_REVIEW_REQUIRED"
REPORT_NO_DOCUMENTS = "NO_DOCUMENTS_TO_RANK"

CLASS_P0 = "P0_CRITICAL_REVIEW"
CLASS_P1 = "P1_HIGH_PRIORITY"
CLASS_P2 = "P2_STANDARD_REVIEW"
CLASS_P3 = "P3_LOW_PRIORITY"

STATUS_BLOCKED = "BLOCKED_BY_RISK_OR_CONFLICT"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_READY_FOR_REVIEW = "READY_FOR_REVIEW"
STATUS_MONITOR = "MONITOR"

SEVERITY_WEIGHT = {
    "CRITICAL": 45.0,
    "HIGH": 30.0,
    "MEDIUM": 15.0,
    "LOW": 5.0,
}

FINANCIAL_STATUS_WEIGHT = {
    "LOCK_CANDIDATE": 24.0,
    "REVIEW_REQUIRED": 22.0,
    "CONFLICT_BLOCKED": 35.0,
    "DRAFT": 12.0,
    "WEAK_SIGNAL": 4.0,
}

SSOT_STATUS_WEIGHT = {
    "LOCK_CANDIDATE": 22.0,
    "DRAFT_HIGH_CONFIDENCE": 16.0,
    "DRAFT": 8.0,
    "REVIEW_REQUIRED": 20.0,
    "WEAK_REVIEW_REQUIRED": 7.0,
    "CONFLICT_BLOCKED": 34.0,
}

EXTENSION_WEIGHT = {
    ".xlsx": 8.0,
    ".xlsm": 8.0,
    ".docx": 7.0,
    ".pdf": 7.0,
    ".pptx": 5.0,
    ".csv": 4.0,
    ".md": 2.0,
    ".txt": 1.0,
    ".json": 1.0,
    ".jsonl": 1.0,
    ".py": 2.0,
    ".log": 2.0,
}

SOURCE_PATH_WEIGHT_MARKERS = {
    "vdr": 8.0,
    "eib": 10.0,
    "ebrd": 10.0,
    "ifc": 8.0,
    "capex": 8.0,
    "financial": 7.0,
    "business": 5.0,
    "plan": 4.0,
    "legal": 8.0,
    "contract": 8.0,
    "permit": 7.0,
    "risk": 6.0,
    "audit": 7.0,
    "ssot": 8.0,
    "control_tower": 6.0,
    "control tower": 6.0,
}


@dataclass(frozen=True)
class RankerPaths:
    base_dir: Path
    evidence_pack: Path
    risk_report: Path
    financial_report: Path
    conflict_report: Path
    ssot_report: Path
    citation_report: Path
    evidence_report: Path
    output_json: Path
    output_md: Path
    output_csv: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return payload


def require_json(path: Path) -> dict[str, Any]:
    payload = load_json_if_exists(path)
    if payload is None:
        raise FileNotFoundError(f"Missing required JSON: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def resolve_paths(
    base_dir: Path,
    evidence_arg: str | None,
    risk_arg: str | None,
    financial_arg: str | None,
    conflict_arg: str | None,
    ssot_arg: str | None,
    citation_arg: str | None,
    evidence_report_arg: str | None,
) -> RankerPaths:
    return RankerPaths(
        base_dir=base_dir,
        evidence_pack=Path(evidence_arg) if evidence_arg else base_dir / INPUT_EVIDENCE_PACK,
        risk_report=Path(risk_arg) if risk_arg else base_dir / INPUT_RISK_REPORT,
        financial_report=Path(financial_arg) if financial_arg else base_dir / INPUT_FINANCIAL_REPORT,
        conflict_report=Path(conflict_arg) if conflict_arg else base_dir / INPUT_CONFLICT_REPORT,
        ssot_report=Path(ssot_arg) if ssot_arg else base_dir / INPUT_SSOT_REPORT,
        citation_report=Path(citation_arg) if citation_arg else base_dir / INPUT_CITATION_REPORT,
        evidence_report=Path(evidence_report_arg) if evidence_report_arg else base_dir / INPUT_EVIDENCE_REPORT,
        output_json=base_dir / OUTPUT_JSON,
        output_md=base_dir / OUTPUT_MD,
        output_csv=base_dir / OUTPUT_CSV,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def get_evidence(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        return []
    return [x for x in evidence if isinstance(x, dict)]


def score_dict(item: dict[str, Any]) -> dict[str, Any]:
    scores = item.get("scores")
    return scores if isinstance(scores, dict) else {}


def final_score(item: dict[str, Any]) -> float:
    return safe_float(score_dict(item).get("final_score"), 0.0)


def source_key(value: Any) -> str:
    return str(value or "").strip()


def init_doc_record(source_path: str, file_name: Any = None, extension: Any = None) -> dict[str, Any]:
    return {
        "Document_ID": "DOC-" + hashlib.sha256(source_path.encode("utf-8", errors="ignore")).hexdigest()[:18],
        "Document_Path": source_path,
        "File_Name": file_name or Path(source_path).name if source_path else "",
        "Extension": str(extension or Path(source_path).suffix).lower(),
        "Priority_Rank": None,
        "Priority_Class": None,
        "Priority_Score": 0.0,
        "Review_Status": None,
        "Evidence_Count": 0,
        "Evidence_Max_Score": 0.0,
        "Evidence_Avg_Score": 0.0,
        "Risk_Count": 0,
        "Critical_Risk_Count": 0,
        "High_Risk_Count": 0,
        "Financial_Signal_Count": 0,
        "Financial_Lock_Candidate_Count": 0,
        "SSOT_Candidate_Count": 0,
        "SSOT_Lock_Candidate_Count": 0,
        "Conflict_Count": 0,
        "Citation_Issue_Count": 0,
        "Chunk_IDs": [],
        "Risk_IDs": [],
        "Financial_Signal_IDs": [],
        "SSOT_Candidate_IDs": [],
        "Conflict_IDs": [],
        "Score_Breakdown": {
            "evidence": 0.0,
            "risk": 0.0,
            "financial": 0.0,
            "ssot": 0.0,
            "conflict": 0.0,
            "citation": 0.0,
            "source_type": 0.0,
            "strict_penalty": 0.0,
        },
        "Recommended_Action": "",
    }


def get_doc(records: dict[str, dict[str, Any]], source_path: Any, file_name: Any = None, extension: Any = None) -> dict[str, Any] | None:
    key = source_key(source_path)
    if not key:
        return None
    if key not in records:
        records[key] = init_doc_record(key, file_name=file_name, extension=extension)
    return records[key]


def add_unique(target: list[Any], value: Any) -> None:
    if value in [None, ""]:
        return
    text = str(value)
    if text not in target:
        target.append(text)


def build_docs_from_evidence(records: dict[str, dict[str, Any]], evidence_pack: dict[str, Any]) -> None:
    evidence = get_evidence(evidence_pack)

    score_acc: dict[str, list[float]] = defaultdict(list)

    for item in evidence:
        doc = get_doc(records, item.get("source_path"), file_name=item.get("file_name"), extension=item.get("extension"))
        if not doc:
            continue

        score = final_score(item)
        doc["Evidence_Count"] += 1
        doc["Evidence_Max_Score"] = max(safe_float(doc["Evidence_Max_Score"]), score)
        score_acc[doc["Document_Path"]].append(score)
        add_unique(doc["Chunk_IDs"], item.get("chunk_id"))

    for path, scores in score_acc.items():
        doc = records[path]
        doc["Evidence_Avg_Score"] = round(sum(scores) / len(scores), 6) if scores else 0.0


def build_docs_from_risk(records: dict[str, dict[str, Any]], risk_report: dict[str, Any] | None) -> None:
    if not risk_report:
        return

    signals = risk_report.get("signals", [])
    if not isinstance(signals, list):
        return

    for risk in signals:
        if not isinstance(risk, dict):
            continue

        # Risk Source_Path can sometimes contain semicolon-separated aggregate sources.
        sources = split_sources(risk.get("Source_Path"))
        if not sources:
            sources = ["risk_signals_report.json"]

        for source in sources:
            doc = get_doc(records, source, file_name=risk.get("File_Name"))
            if not doc:
                continue

            severity = str(risk.get("Severity") or "")
            doc["Risk_Count"] += 1
            if severity == "CRITICAL":
                doc["Critical_Risk_Count"] += 1
            elif severity == "HIGH":
                doc["High_Risk_Count"] += 1
            add_unique(doc["Risk_IDs"], risk.get("Risk_ID"))


def split_sources(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []

    parts = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    return parts


def build_docs_from_financial(records: dict[str, dict[str, Any]], financial_report: dict[str, Any] | None) -> None:
    if not financial_report:
        return

    signals = financial_report.get("signals", [])
    if not isinstance(signals, list):
        return

    for sig in signals:
        if not isinstance(sig, dict):
            continue
        doc = get_doc(records, sig.get("Source_Path"), file_name=sig.get("File_Name"))
        if not doc:
            continue

        doc["Financial_Signal_Count"] += 1
        if str(sig.get("Financial_Status") or "") == "LOCK_CANDIDATE":
            doc["Financial_Lock_Candidate_Count"] += 1
        add_unique(doc["Financial_Signal_IDs"], sig.get("Signal_ID"))


def build_docs_from_ssot(records: dict[str, dict[str, Any]], ssot_report: dict[str, Any] | None) -> None:
    if not ssot_report:
        return

    candidates = ssot_report.get("candidates", [])
    if not isinstance(candidates, list):
        return

    for cand in candidates:
        if not isinstance(cand, dict):
            continue

        doc = get_doc(records, cand.get("Source_Path"), file_name=cand.get("File_Name"))
        if not doc:
            continue

        doc["SSOT_Candidate_Count"] += 1
        if str(cand.get("SSOT_Status") or "") == "LOCK_CANDIDATE":
            doc["SSOT_Lock_Candidate_Count"] += 1
        add_unique(doc["SSOT_Candidate_IDs"], cand.get("Candidate_ID"))


def build_docs_from_conflict(records: dict[str, dict[str, Any]], conflict_report: dict[str, Any] | None) -> None:
    if not conflict_report:
        return

    conflicts = conflict_report.get("conflicts", [])
    if not isinstance(conflicts, list):
        return

    for conflict in conflicts:
        if not isinstance(conflict, dict):
            continue

        sources = conflict.get("sources", [])
        if not isinstance(sources, list):
            sources = ["conflict_report.json"]

        for source in sources:
            doc = get_doc(records, source)
            if not doc:
                continue

            doc["Conflict_Count"] += 1
            add_unique(doc["Conflict_IDs"], conflict.get("conflict_id"))


def build_docs_from_citation(records: dict[str, dict[str, Any]], citation_report: dict[str, Any] | None) -> None:
    if not citation_report:
        return

    rows = citation_report.get("rows", [])
    if not isinstance(rows, list):
        return

    for row in rows:
        if not isinstance(row, dict):
            continue

        status = str(row.get("Status") or "")
        issues = str(row.get("Issues") or "")
        warnings = str(row.get("Warnings") or "")
        if status in {"FAIL", "PASS_WITH_WARNINGS"} or issues or warnings:
            doc = get_doc(records, row.get("Source_Path"), file_name=row.get("File_Name"))
            if not doc:
                continue
            doc["Citation_Issue_Count"] += 1


def calculate_scores(records: dict[str, dict[str, Any]], strict: bool) -> list[dict[str, Any]]:
    docs = list(records.values())

    for doc in docs:
        breakdown = doc["Score_Breakdown"]

        evidence_component = (
            safe_float(doc["Evidence_Max_Score"]) * 22.0
            + min(safe_int(doc["Evidence_Count"]), 10) * 1.2
            + safe_float(doc["Evidence_Avg_Score"]) * 8.0
        )
        breakdown["evidence"] = round(evidence_component, 4)

        risk_component = (
            safe_int(doc["Critical_Risk_Count"]) * SEVERITY_WEIGHT["CRITICAL"]
            + safe_int(doc["High_Risk_Count"]) * SEVERITY_WEIGHT["HIGH"]
            + max(safe_int(doc["Risk_Count"]) - safe_int(doc["Critical_Risk_Count"]) - safe_int(doc["High_Risk_Count"]), 0) * 7.0
        )
        breakdown["risk"] = round(risk_component, 4)

        financial_component = (
            safe_int(doc["Financial_Signal_Count"]) * 5.0
            + safe_int(doc["Financial_Lock_Candidate_Count"]) * 14.0
        )
        breakdown["financial"] = round(financial_component, 4)

        ssot_component = (
            safe_int(doc["SSOT_Candidate_Count"]) * 4.0
            + safe_int(doc["SSOT_Lock_Candidate_Count"]) * 12.0
        )
        breakdown["ssot"] = round(ssot_component, 4)

        conflict_component = safe_int(doc["Conflict_Count"]) * 22.0
        breakdown["conflict"] = round(conflict_component, 4)

        citation_component = safe_int(doc["Citation_Issue_Count"]) * 12.0
        breakdown["citation"] = round(citation_component, 4)

        source_type_component = source_type_score(doc)
        breakdown["source_type"] = round(source_type_component, 4)

        strict_penalty = 0.0
        if strict and safe_int(doc["Citation_Issue_Count"]) > 0:
            strict_penalty -= 8.0
        breakdown["strict_penalty"] = round(strict_penalty, 4)

        total = sum(safe_float(v) for v in breakdown.values())
        doc["Priority_Score"] = round(max(total, 0.0), 6)

        doc["Priority_Class"] = priority_class(doc)
        doc["Review_Status"] = review_status(doc)
        doc["Recommended_Action"] = recommended_action(doc)

        # serialize lists for JSON remains list; CSV later converts.
        doc["Chunk_Count"] = len(doc["Chunk_IDs"])

    docs.sort(
        key=lambda d: (
            safe_float(d.get("Priority_Score")),
            safe_int(d.get("Critical_Risk_Count")),
            safe_int(d.get("High_Risk_Count")),
            safe_int(d.get("Conflict_Count")),
            safe_int(d.get("Financial_Signal_Count")),
            safe_int(d.get("Evidence_Count")),
        ),
        reverse=True,
    )

    for idx, doc in enumerate(docs, start=1):
        doc["Priority_Rank"] = idx

    return docs


def source_type_score(doc: dict[str, Any]) -> float:
    score = 0.0
    ext = str(doc.get("Extension") or "").lower()
    score += EXTENSION_WEIGHT.get(ext, 0.0)

    path = str(doc.get("Document_Path") or "").lower()
    for marker, weight in SOURCE_PATH_WEIGHT_MARKERS.items():
        if marker in path:
            score += weight

    return min(score, 35.0)


def priority_class(doc: dict[str, Any]) -> str:
    score = safe_float(doc.get("Priority_Score"))
    critical = safe_int(doc.get("Critical_Risk_Count"))
    conflicts = safe_int(doc.get("Conflict_Count"))
    citation = safe_int(doc.get("Citation_Issue_Count"))

    if critical > 0 or conflicts > 0 or score >= 95:
        return CLASS_P0
    if citation > 0 or safe_int(doc.get("High_Risk_Count")) > 0 or score >= 65:
        return CLASS_P1
    if score >= 25:
        return CLASS_P2
    return CLASS_P3


def review_status(doc: dict[str, Any]) -> str:
    if safe_int(doc.get("Critical_Risk_Count")) > 0 or safe_int(doc.get("Conflict_Count")) > 0:
        return STATUS_BLOCKED
    if safe_int(doc.get("High_Risk_Count")) > 0 or safe_int(doc.get("Citation_Issue_Count")) > 0:
        return STATUS_REVIEW_REQUIRED
    if safe_float(doc.get("Priority_Score")) >= 25:
        return STATUS_READY_FOR_REVIEW
    return STATUS_MONITOR


def recommended_action(doc: dict[str, Any]) -> str:
    if doc.get("Review_Status") == STATUS_BLOCKED:
        return "Review immediately. Resolve conflicts/critical risks before institutional use."
    if safe_int(doc.get("Citation_Issue_Count")) > 0:
        return "Verify citation integrity and source/chunk references."
    if safe_int(doc.get("Financial_Lock_Candidate_Count")) > 0:
        return "Review for financial SSOT/model input validation."
    if safe_int(doc.get("SSOT_Lock_Candidate_Count")) > 0:
        return "Review for SSOT lock decision."
    if safe_int(doc.get("Risk_Count")) > 0:
        return "Review risk context and decide mitigation action."
    if safe_int(doc.get("Evidence_Count")) > 0:
        return "Review source evidence for current query context."
    return "Monitor only."


def summarize(docs: list[dict[str, Any]], reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    by_class: dict[str, int] = defaultdict(int)
    by_status: dict[str, int] = defaultdict(int)
    by_extension: dict[str, int] = defaultdict(int)

    for doc in docs:
        by_class[str(doc.get("Priority_Class"))] += 1
        by_status[str(doc.get("Review_Status"))] += 1
        by_extension[str(doc.get("Extension") or "[unknown]")] += 1

    p0 = by_class.get(CLASS_P0, 0)
    p1 = by_class.get(CLASS_P1, 0)

    if not docs:
        institutional_status = REPORT_NO_DOCUMENTS
    elif p0 > 0 or p1 > 0:
        institutional_status = REPORT_REVIEW_REQUIRED
    else:
        institutional_status = REPORT_READY

    return {
        "institutional_status": institutional_status,
        "ranked_documents": len(docs),
        "p0_count": p0,
        "p1_count": p1,
        "p2_count": by_class.get(CLASS_P2, 0),
        "p3_count": by_class.get(CLASS_P3, 0),
        "blocked_count": by_status.get(STATUS_BLOCKED, 0),
        "review_required_count": by_status.get(STATUS_REVIEW_REQUIRED, 0),
        "ready_for_review_count": by_status.get(STATUS_READY_FOR_REVIEW, 0),
        "monitor_count": by_status.get(STATUS_MONITOR, 0),
        "by_class": dict(sorted(by_class.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_extension": dict(sorted(by_extension.items())),
        "input_availability": {
            name: payload is not None
            for name, payload in reports.items()
        },
    }


def build_report(
    evidence_pack: dict[str, Any],
    docs: list[dict[str, Any]],
    reports: dict[str, dict[str, Any] | None],
    paths: RankerPaths,
    strict: bool,
) -> dict[str, Any]:
    summary = summarize(docs, reports)

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "DOCUMENT_PRIORITY_RANKING_AUDIT_LOCKED",
        "strict_mode": strict,
        "query": evidence_pack.get("query"),
        "inputs": {
            "evidence_pack": str(paths.evidence_pack),
            "risk_report": str(paths.risk_report),
            "financial_report": str(paths.financial_report),
            "conflict_report": str(paths.conflict_report),
            "ssot_report": str(paths.ssot_report),
            "citation_report": str(paths.citation_report),
            "evidence_report": str(paths.evidence_report),
        },
        "summary": summary,
        "documents": docs,
        "hashes": {
            "evidence_pack_canonical_sha256": sha256_json(evidence_pack),
            "risk_report_canonical_sha256": sha256_json(reports.get("risk_report")) if reports.get("risk_report") else None,
            "financial_report_canonical_sha256": sha256_json(reports.get("financial_report")) if reports.get("financial_report") else None,
            "conflict_report_canonical_sha256": sha256_json(reports.get("conflict_report")) if reports.get("conflict_report") else None,
            "ssot_report_canonical_sha256": sha256_json(reports.get("ssot_report")) if reports.get("ssot_report") else None,
            "citation_report_canonical_sha256": sha256_json(reports.get("citation_report")) if reports.get("citation_report") else None,
        },
        "governance_rule": {
            "ranking_is_review_order_not_truth": True,
            "document_priority_does_not_modify_sources": True,
            "p0_blocks_institutional_use_until_review": True,
            "source_files_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }
    report["document_priority_rank_sha256"] = sha256_json(report)
    return report


def write_csv(path: Path, docs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Priority_Rank",
        "Document_ID",
        "Priority_Class",
        "Priority_Score",
        "Review_Status",
        "Document_Path",
        "File_Name",
        "Extension",
        "Evidence_Count",
        "Evidence_Max_Score",
        "Evidence_Avg_Score",
        "Risk_Count",
        "Critical_Risk_Count",
        "High_Risk_Count",
        "Financial_Signal_Count",
        "Financial_Lock_Candidate_Count",
        "SSOT_Candidate_Count",
        "SSOT_Lock_Candidate_Count",
        "Conflict_Count",
        "Citation_Issue_Count",
        "Chunk_Count",
        "Chunk_IDs",
        "Risk_IDs",
        "Financial_Signal_IDs",
        "SSOT_Candidate_IDs",
        "Conflict_IDs",
        "Recommended_Action",
        "Score_Breakdown",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for doc in docs:
            row = dict(doc)
            for key in ["Chunk_IDs", "Risk_IDs", "Financial_Signal_IDs", "SSOT_Candidate_IDs", "Conflict_IDs"]:
                row[key] = "; ".join(row.get(key, [])) if isinstance(row.get(key), list) else row.get(key)
            row["Score_Breakdown"] = json.dumps(row.get("Score_Breakdown", {}), ensure_ascii=False)
            writer.writerow(row)


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def docs_table_md(docs: list[dict[str, Any]], limit: int = 150) -> str:
    if not docs:
        return "No documents ranked."

    lines = [
        "| Rank | Class | Score | Status | File | Evidence | Risks | Financial | SSOT | Conflicts | Citation Issues | Action |",
        "|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for doc in docs[:limit]:
        lines.append(
            f"| {doc.get('Priority_Rank')} | "
            f"{md_escape(doc.get('Priority_Class'))} | "
            f"{doc.get('Priority_Score')} | "
            f"{md_escape(doc.get('Review_Status'))} | "
            f"`{md_escape(doc.get('Document_Path'))}` | "
            f"{doc.get('Evidence_Count')} | "
            f"{doc.get('Risk_Count')} | "
            f"{doc.get('Financial_Signal_Count')} | "
            f"{doc.get('SSOT_Candidate_Count')} | "
            f"{doc.get('Conflict_Count')} | "
            f"{doc.get('Citation_Issue_Count')} | "
            f"{md_escape(doc.get('Recommended_Action'))} |"
        )

    return "\n".join(lines)


def p0_context_md(docs: list[dict[str, Any]]) -> str:
    critical = [d for d in docs if d.get("Priority_Class") == CLASS_P0]
    if not critical:
        return "No P0 documents."

    sections = []
    for doc in critical[:25]:
        sections.append(
            f"### Rank {doc.get('Priority_Rank')} — {doc.get('File_Name')}\n\n"
            f"- Path: `{doc.get('Document_Path')}`\n"
            f"- Score: {doc.get('Priority_Score')}\n"
            f"- Review Status: {doc.get('Review_Status')}\n"
            f"- Risks: {doc.get('Risk_Count')} | Critical: {doc.get('Critical_Risk_Count')} | High: {doc.get('High_Risk_Count')}\n"
            f"- Conflicts: {doc.get('Conflict_Count')} | Citation Issues: {doc.get('Citation_Issue_Count')}\n"
            f"- Action: {doc.get('Recommended_Action')}\n"
            f"- Score Breakdown: `{json.dumps(doc.get('Score_Breakdown', {}), ensure_ascii=False)}`\n"
        )
    return "\n".join(sections)


def report_to_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    return f"""# TITAN RAG Document Priority Ranking

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Institutional Status | {summary.get("institutional_status")} |
| Query | {md_escape(report.get("query"))} |
| Strict Mode | {report.get("strict_mode")} |
| Ranked Documents | {summary.get("ranked_documents")} |
| P0 Count | {summary.get("p0_count")} |
| P1 Count | {summary.get("p1_count")} |
| Blocked Count | {summary.get("blocked_count")} |
| Review Required Count | {summary.get("review_required_count")} |
| Report SHA-256 | `{report.get("document_priority_rank_sha256")}` |

---

## 2. Distribution

```json
{json.dumps({
    "by_class": summary.get("by_class"),
    "by_status": summary.get("by_status"),
    "by_extension": summary.get("by_extension"),
    "input_availability": summary.get("input_availability"),
}, indent=2, ensure_ascii=False)}
```

---

## 3. Ranked Documents

{docs_table_md(report.get("documents", []))}

---

## 4. P0 Critical Review Context

{p0_context_md(report.get("documents", []))}

---

## 5. Governance Rule

```text
Ranking is review order, not final truth.
P0 documents block institutional use until review.
This script does not modify source documents.
Source files remain authoritative.
Audit precedes decision.
```
"""


def print_summary(report: dict[str, Any], paths: RankerPaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN RAG DOCUMENT PRIORITY RANKER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Institutional status:  {summary.get('institutional_status')}")
    print(f"Query:                 {report.get('query')}")
    print(f"Ranked documents:      {summary.get('ranked_documents')}")
    print(f"P0 count:              {summary.get('p0_count')}")
    print(f"P1 count:              {summary.get('p1_count')}")
    print(f"Blocked count:         {summary.get('blocked_count')}")
    print("-" * 100)
    print(f"Report JSON:           {paths.output_json}")
    print(f"Report Markdown:       {paths.output_md}")
    print(f"Report CSV:            {paths.output_csv}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 18 — document priority ranker.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--evidence-pack", default=None, help="Optional latest_evidence_pack.json path.")
    parser.add_argument("--risk-report", default=None, help="Optional risk_signals_report.json path.")
    parser.add_argument("--financial-report", default=None, help="Optional financial_signals_report.json path.")
    parser.add_argument("--conflict-report", default=None, help="Optional conflict_report.json path.")
    parser.add_argument("--ssot-report", default=None, help="Optional ssot_candidates_report.json path.")
    parser.add_argument("--citation-report", default=None, help="Optional citation_verification_report.json path.")
    parser.add_argument("--evidence-report", default=None, help="Optional evidence_pack_report.json path.")
    parser.add_argument("--strict", action="store_true", help="Apply stricter ranking penalties.")
    parser.add_argument("--print", action="store_true", help="Print Markdown report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        evidence_arg=args.evidence_pack,
        risk_arg=args.risk_report,
        financial_arg=args.financial_report,
        conflict_arg=args.conflict_report,
        ssot_arg=args.ssot_report,
        citation_arg=args.citation_report,
        evidence_report_arg=args.evidence_report,
    )

    try:
        evidence_pack = require_json(paths.evidence_pack)

        reports = {
            "risk_report": load_json_if_exists(paths.risk_report),
            "financial_report": load_json_if_exists(paths.financial_report),
            "conflict_report": load_json_if_exists(paths.conflict_report),
            "ssot_report": load_json_if_exists(paths.ssot_report),
            "citation_report": load_json_if_exists(paths.citation_report),
            "evidence_report": load_json_if_exists(paths.evidence_report),
        }

        records: dict[str, dict[str, Any]] = {}

        build_docs_from_evidence(records, evidence_pack)
        build_docs_from_risk(records, reports["risk_report"])
        build_docs_from_financial(records, reports["financial_report"])
        build_docs_from_ssot(records, reports["ssot_report"])
        build_docs_from_conflict(records, reports["conflict_report"])
        build_docs_from_citation(records, reports["citation_report"])

        docs = calculate_scores(records, strict=bool(args.strict))

        report = build_report(
            evidence_pack=evidence_pack,
            docs=docs,
            reports=reports,
            paths=paths,
            strict=bool(args.strict),
        )

        markdown = report_to_markdown(report)

        write_json(paths.output_json, report)
        write_text(paths.output_md, markdown)
        write_csv(paths.output_csv, docs)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "DOCUMENT_PRIORITY_RANKING_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "institutional_status": (report.get("summary") or {}).get("institutional_status"),
            "summary": report.get("summary"),
            "report_sha256": report.get("document_priority_rank_sha256"),
            "outputs": {
                "json": str(paths.output_json),
                "markdown": str(paths.output_md),
                "csv": str(paths.output_csv),
            },
        })

        print_summary(report, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "DOCUMENT_PRIORITY_RANKING_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "evidence_pack": str(paths.evidence_pack),
            "risk_report": str(paths.risk_report),
            "financial_report": str(paths.financial_report),
            "conflict_report": str(paths.conflict_report),
            "ssot_report": str(paths.ssot_report),
            "citation_report": str(paths.citation_report),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG DOCUMENT PRIORITY RANKER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
