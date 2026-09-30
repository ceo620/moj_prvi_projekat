#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12_evidence_pack_reporter.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 12 — Evidence Pack Reporter
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Convert latest_evidence_pack.json from Step 06 into review-ready reports:
Markdown, CSV and normalized JSON.

This script does NOT search.
This script does NOT generate new conclusions.
This script does NOT alter evidence.
This script only formats, validates and summarizes the retrieved evidence pack.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Input
-----
05_reports/latest_evidence_pack.json

Outputs
-------
05_reports/evidence_pack_report.json
05_reports/evidence_pack_report.md
05_reports/evidence_pack_report.csv
05_reports/evidence_sources.csv
06_logs/evidence_pack_reporter_audit.jsonl
06_logs/evidence_pack_reporter_errors.jsonl

Designed for compatibility with:
13_source_citation_verifier.py
14_conflict_detector.py
15_ssot_candidate_extractor.py
16_financial_signal_extractor.py
17_risk_signal_extractor.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\12_evidence_pack_reporter.py" --print
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "12_evidence_pack_reporter.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"

OUTPUT_REPORT_JSON = Path("05_reports") / "evidence_pack_report.json"
OUTPUT_REPORT_MD = Path("05_reports") / "evidence_pack_report.md"
OUTPUT_REPORT_CSV = Path("05_reports") / "evidence_pack_report.csv"
OUTPUT_SOURCES_CSV = Path("05_reports") / "evidence_sources.csv"

AUDIT_LOG = Path("06_logs") / "evidence_pack_reporter_audit.jsonl"
ERROR_LOG = Path("06_logs") / "evidence_pack_reporter_errors.jsonl"

DEFAULT_MAX_EXCERPT_CHARS_MD = 1200
DEFAULT_TOP_SOURCES = 100

REQUIRED_EVIDENCE_FIELDS = [
    "rank",
    "chunk_id",
    "source_path",
    "file_name",
    "scores",
    "excerpt",
]

REQUIRED_SCORE_FIELDS = [
    "final_score",
    "semantic_score",
    "keyword_overlap_score",
]

STATUS_REPORT_READY = "EVIDENCE_REPORT_READY"
STATUS_REPORT_READY_WITH_WARNINGS = "EVIDENCE_REPORT_READY_WITH_WARNINGS"
STATUS_NO_EVIDENCE = "NO_EVIDENCE_FOUND"
STATUS_INVALID_EVIDENCE = "INVALID_EVIDENCE_PACK"


@dataclass(frozen=True)
class ReporterPaths:
    base_dir: Path
    input_evidence_pack: Path
    output_report_json: Path
    output_report_md: Path
    output_report_csv: Path
    output_sources_csv: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def normalize_multiline(value: Any) -> str:
    text = str(value or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(value: Any, max_chars: int) -> str:
    text = normalize_multiline(value)
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " ...[TRUNCATED]"


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing evidence pack: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Evidence pack root must be a JSON object.")

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


def resolve_paths(base_dir: Path, input_arg: str | None) -> ReporterPaths:
    return ReporterPaths(
        base_dir=base_dir,
        input_evidence_pack=Path(input_arg) if input_arg else base_dir / INPUT_EVIDENCE_PACK,
        output_report_json=base_dir / OUTPUT_REPORT_JSON,
        output_report_md=base_dir / OUTPUT_REPORT_MD,
        output_report_csv=base_dir / OUTPUT_REPORT_CSV,
        output_sources_csv=base_dir / OUTPUT_SOURCES_CSV,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def get_evidence(pack: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = pack.get("evidence", [])
    if not isinstance(evidence, list):
        return []
    return [item for item in evidence if isinstance(item, dict)]


def score_dict(item: dict[str, Any]) -> dict[str, Any]:
    scores = item.get("scores")
    return scores if isinstance(scores, dict) else {}


def final_score(item: dict[str, Any]) -> float:
    return safe_float(score_dict(item).get("final_score"), 0.0)


def validate_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_EVIDENCE_FIELDS:
        if item.get(field) in [None, ""]:
            issues.append(f"MISSING_FIELD:{field}")

    scores = score_dict(item)
    if not scores:
        issues.append("MISSING_OR_INVALID:scores")

    for field in REQUIRED_SCORE_FIELDS:
        if scores.get(field) in [None, ""]:
            issues.append(f"MISSING_SCORE:{field}")

    excerpt = str(item.get("excerpt") or "")
    if len(excerpt.strip()) < 40:
        warnings.append("SHORT_EXCERPT")

    source_path = str(item.get("source_path") or "")
    if not source_path:
        issues.append("NO_SOURCE_PATH")

    chunk_id = str(item.get("chunk_id") or "")
    if not chunk_id:
        issues.append("NO_CHUNK_ID")

    score = final_score(item)
    if score <= 0:
        warnings.append("ZERO_OR_MISSING_FINAL_SCORE")

    status = "PASS" if not issues else "FAIL"
    if status == "PASS" and warnings:
        status = "PASS_WITH_WARNINGS"

    return {
        "rank": item.get("rank"),
        "chunk_id": item.get("chunk_id"),
        "source_path": item.get("source_path"),
        "status": status,
        "issues": issues,
        "warnings": warnings,
    }


def normalized_evidence_rows(evidence: list[dict[str, Any]], max_excerpt_chars: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in sorted(evidence, key=lambda x: safe_int(x.get("rank"), 999999)):
        scores = score_dict(item)
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}

        excerpt = truncate(item.get("excerpt"), max_excerpt_chars)

        rows.append({
            "rank": item.get("rank"),
            "rank_raw": item.get("rank_raw"),
            "chunk_id": item.get("chunk_id"),
            "source_path": item.get("source_path"),
            "processed_path": item.get("processed_path"),
            "file_name": item.get("file_name"),
            "extension": item.get("extension"),
            "section_label": item.get("section_label"),
            "chunk_index": item.get("chunk_index"),
            "chunk_count_for_file": item.get("chunk_count_for_file"),
            "source_modified_time_utc": item.get("source_modified_time_utc"),
            "start_char": item.get("start_char"),
            "end_char": item.get("end_char"),
            "distance": item.get("distance"),
            "final_score": scores.get("final_score"),
            "semantic_score": scores.get("semantic_score"),
            "keyword_overlap_score": scores.get("keyword_overlap_score"),
            "keyword_boost": scores.get("keyword_boost"),
            "recency_boost": scores.get("recency_boost"),
            "source_folder_boost": scores.get("source_folder_boost"),
            "file_type_boost": scores.get("file_type_boost"),
            "keyword_hits": ", ".join(item.get("keyword_hits", [])) if isinstance(item.get("keyword_hits"), list) else item.get("keyword_hits"),
            "excerpt": excerpt,
            "excerpt_sha256": item.get("excerpt_sha256") or sha256_text(excerpt),
            "source_sha256": metadata.get("source_sha256"),
            "text_sha256": metadata.get("text_sha256"),
            "chunk_sha256": metadata.get("chunk_sha256"),
            "chunk_chars": metadata.get("chunk_chars"),
            "chunk_words": metadata.get("chunk_words"),
        })

    return rows


def build_source_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for row in evidence_rows:
        source_path = str(row.get("source_path") or "UNKNOWN_SOURCE")
        if source_path not in grouped:
            grouped[source_path] = {
                "source_path": source_path,
                "file_name": row.get("file_name"),
                "extension": row.get("extension"),
                "source_modified_time_utc": row.get("source_modified_time_utc"),
                "evidence_count": 0,
                "chunk_ids": [],
                "sections": set(),
                "max_final_score": 0.0,
                "avg_final_score_accumulator": 0.0,
            }

        group = grouped[source_path]
        group["evidence_count"] += 1
        group["avg_final_score_accumulator"] += safe_float(row.get("final_score"), 0.0)
        group["max_final_score"] = max(group["max_final_score"], safe_float(row.get("final_score"), 0.0))

        if row.get("chunk_id"):
            group["chunk_ids"].append(str(row.get("chunk_id")))

        if row.get("section_label"):
            group["sections"].add(str(row.get("section_label")))

    source_rows: list[dict[str, Any]] = []

    for group in grouped.values():
        count = safe_int(group.get("evidence_count"), 0)
        source_rows.append({
            "source_path": group.get("source_path"),
            "file_name": group.get("file_name"),
            "extension": group.get("extension"),
            "source_modified_time_utc": group.get("source_modified_time_utc"),
            "evidence_count": count,
            "max_final_score": round(safe_float(group.get("max_final_score")), 6),
            "average_final_score": round(safe_float(group.get("avg_final_score_accumulator")) / count, 6) if count else 0.0,
            "chunk_ids": "; ".join(group.get("chunk_ids", [])),
            "sections": "; ".join(sorted(group.get("sections", set()))),
        })

    source_rows.sort(
        key=lambda x: (
            safe_int(x.get("evidence_count")),
            safe_float(x.get("max_final_score")),
        ),
        reverse=True,
    )

    return source_rows


def write_evidence_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "rank",
        "rank_raw",
        "chunk_id",
        "source_path",
        "processed_path",
        "file_name",
        "extension",
        "section_label",
        "chunk_index",
        "chunk_count_for_file",
        "source_modified_time_utc",
        "start_char",
        "end_char",
        "distance",
        "final_score",
        "semantic_score",
        "keyword_overlap_score",
        "keyword_boost",
        "recency_boost",
        "source_folder_boost",
        "file_type_boost",
        "keyword_hits",
        "excerpt",
        "excerpt_sha256",
        "source_sha256",
        "text_sha256",
        "chunk_sha256",
        "chunk_chars",
        "chunk_words",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["excerpt"] = normalize_inline(out.get("excerpt"))
            writer.writerow(out)


def write_sources_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source_path",
        "file_name",
        "extension",
        "source_modified_time_utc",
        "evidence_count",
        "max_final_score",
        "average_final_score",
        "chunk_ids",
        "sections",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_pack(pack: dict[str, Any], evidence_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]], validation: list[dict[str, Any]]) -> dict[str, Any]:
    issue_count = sum(len(item.get("issues", [])) for item in validation)
    warning_count = sum(len(item.get("warnings", [])) for item in validation)
    failed_count = sum(1 for item in validation if item.get("status") == "FAIL")

    scores = [safe_float(row.get("final_score"), 0.0) for row in evidence_rows]
    extensions = Counter(str(row.get("extension") or "[unknown]") for row in evidence_rows)

    if not evidence_rows:
        status = STATUS_NO_EVIDENCE
    elif failed_count > 0:
        status = STATUS_INVALID_EVIDENCE
    elif warning_count > 0:
        status = STATUS_REPORT_READY_WITH_WARNINGS
    else:
        status = STATUS_REPORT_READY

    return {
        "report_status": status,
        "query": pack.get("query"),
        "evidence_pack_created_at": pack.get("created_at"),
        "evidence_pack_sha256": pack.get("evidence_pack_sha256"),
        "collection_name": pack.get("collection_name"),
        "embedding_model": pack.get("embedding_model"),
        "collection_count": pack.get("collection_count"),
        "evidence_count": len(evidence_rows),
        "source_file_count": len(source_rows),
        "validation_failed_count": failed_count,
        "validation_issue_count": issue_count,
        "validation_warning_count": warning_count,
        "score_summary": {
            "max_final_score": round(max(scores), 6) if scores else None,
            "min_final_score": round(min(scores), 6) if scores else None,
            "average_final_score": round(sum(scores) / len(scores), 6) if scores else None,
        },
        "extension_distribution": dict(sorted(extensions.items())),
    }


def build_report(pack: dict[str, Any], max_excerpt_chars_md: int) -> dict[str, Any]:
    evidence = get_evidence(pack)
    evidence_rows = normalized_evidence_rows(evidence, max_excerpt_chars=max_excerpt_chars_md)
    source_rows = build_source_rows(evidence_rows)
    validation = [
        validate_evidence_item(item)
        for item in evidence
    ]

    summary = summarize_pack(
        pack=pack,
        evidence_rows=evidence_rows,
        source_rows=source_rows,
        validation=validation,
    )

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "EVIDENCE_PACK_REPORTING_AUDIT_LOCKED",
        "summary": summary,
        "retrieval_parameters": pack.get("retrieval_parameters"),
        "source_files": source_rows,
        "evidence": evidence_rows,
        "validation": validation,
        "governance_rule": {
            "report_formats_existing_evidence_only": True,
            "no_new_conclusions": True,
            "source_path_required": True,
            "chunk_id_required": True,
            "latest_evidence_pack_remains_authoritative": True,
        },
    }

    report["evidence_pack_report_sha256"] = sha256_json(report)
    return report


def evidence_table_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No evidence rows."

    lines = [
        "| Rank | Score | File | Section | Chunk ID | Source | Excerpt |",
        "|---:|---:|---|---|---|---|---|",
    ]

    for row in rows:
        excerpt = md_escape(row.get("excerpt"))
        if len(excerpt) > 800:
            excerpt = excerpt[:800] + " ..."
        lines.append(
            f"| {row.get('rank')} | "
            f"{row.get('final_score')} | "
            f"{md_escape(row.get('file_name'))} | "
            f"{md_escape(row.get('section_label'))} | "
            f"`{md_escape(row.get('chunk_id'))}` | "
            f"`{md_escape(row.get('source_path'))}` | "
            f"{excerpt} |"
        )

    return "\n".join(lines)


def source_table_md(rows: list[dict[str, Any]], limit: int) -> str:
    if not rows:
        return "No source rows."

    lines = [
        "| # | Evidence Count | Max Score | File | Extension | Source | Sections |",
        "|---:|---:|---:|---|---|---|---|",
    ]

    for idx, row in enumerate(rows[:limit], start=1):
        sections = md_escape(row.get("sections"))
        if len(sections) > 220:
            sections = sections[:220] + " ..."
        lines.append(
            f"| {idx} | "
            f"{row.get('evidence_count')} | "
            f"{row.get('max_final_score')} | "
            f"{md_escape(row.get('file_name'))} | "
            f"{md_escape(row.get('extension'))} | "
            f"`{md_escape(row.get('source_path'))}` | "
            f"{sections} |"
        )

    return "\n".join(lines)


def validation_table_md(validation: list[dict[str, Any]]) -> str:
    if not validation:
        return "No validation records."

    lines = [
        "| Rank | Status | Source | Chunk ID | Issues | Warnings |",
        "|---:|---|---|---|---|---|",
    ]

    for item in validation:
        lines.append(
            f"| {item.get('rank')} | "
            f"{md_escape(item.get('status'))} | "
            f"`{md_escape(item.get('source_path'))}` | "
            f"`{md_escape(item.get('chunk_id'))}` | "
            f"{md_escape('; '.join(item.get('issues', [])))} | "
            f"{md_escape('; '.join(item.get('warnings', [])))} |"
        )

    return "\n".join(lines)


def report_to_markdown(report: dict[str, Any], top_sources: int) -> str:
    summary = report.get("summary", {})
    score_summary = summary.get("score_summary", {}) if isinstance(summary.get("score_summary"), dict) else {}

    return f"""# TITAN RAG Evidence Pack Report

## 1. Executive Summary

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Report Status | {summary.get("report_status")} |
| Query | {md_escape(summary.get("query"))} |
| Evidence Count | {summary.get("evidence_count")} |
| Source File Count | {summary.get("source_file_count")} |
| Validation Failed Count | {summary.get("validation_failed_count")} |
| Validation Issue Count | {summary.get("validation_issue_count")} |
| Validation Warning Count | {summary.get("validation_warning_count")} |
| Collection | {summary.get("collection_name")} |
| Embedding Model | {summary.get("embedding_model")} |
| Evidence Pack SHA-256 | `{summary.get("evidence_pack_sha256")}` |
| Report SHA-256 | `{report.get("evidence_pack_report_sha256")}` |

---

## 2. Score Summary

| Metric | Value |
|---|---:|
| Max Final Score | {score_summary.get("max_final_score")} |
| Min Final Score | {score_summary.get("min_final_score")} |
| Average Final Score | {score_summary.get("average_final_score")} |

---

## 3. Extension Distribution

```json
{json.dumps(summary.get("extension_distribution", {}), indent=2, ensure_ascii=False)}
```

---

## 4. Source Files

{source_table_md(report.get("source_files", []), limit=top_sources)}

---

## 5. Evidence Table

{evidence_table_md(report.get("evidence", []))}

---

## 6. Validation

{validation_table_md(report.get("validation", []))}

---

## 7. Retrieval Parameters

```json
{json.dumps(report.get("retrieval_parameters", {}), indent=2, ensure_ascii=False)}
```

---

## 8. Governance Rule

```text
This report formats existing evidence only.
It does not create new conclusions.
Source path and chunk_id are mandatory.
latest_evidence_pack.json remains authoritative.
```
"""


def print_summary(report: dict[str, Any], paths: ReporterPaths) -> None:
    summary = report.get("summary", {})
    print("=" * 100)
    print("TITAN RAG EVIDENCE PACK REPORTER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Report status:        {summary.get('report_status')}")
    print(f"Query:                {summary.get('query')}")
    print(f"Evidence count:       {summary.get('evidence_count')}")
    print(f"Source file count:    {summary.get('source_file_count')}")
    print(f"Validation failures:  {summary.get('validation_failed_count')}")
    print(f"Validation warnings:  {summary.get('validation_warning_count')}")
    print("-" * 100)
    print(f"Report JSON:          {paths.output_report_json}")
    print(f"Report Markdown:      {paths.output_report_md}")
    print(f"Evidence CSV:         {paths.output_report_csv}")
    print(f"Sources CSV:          {paths.output_sources_csv}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 12 — evidence pack reporter."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--input",
        default=None,
        help="Optional latest_evidence_pack.json path.",
    )

    parser.add_argument(
        "--max-excerpt-chars-md",
        type=int,
        default=DEFAULT_MAX_EXCERPT_CHARS_MD,
        help="Maximum excerpt characters preserved in report rows.",
    )

    parser.add_argument(
        "--top-sources",
        type=int,
        default=DEFAULT_TOP_SOURCES,
        help="Maximum source rows shown in Markdown source table.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print Markdown report to console.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir=base_dir, input_arg=args.input)

    try:
        pack = load_json(paths.input_evidence_pack)
        report = build_report(pack=pack, max_excerpt_chars_md=int(args.max_excerpt_chars_md))
        markdown = report_to_markdown(report, top_sources=int(args.top_sources))

        write_json(paths.output_report_json, report)
        write_text(paths.output_report_md, markdown)
        write_evidence_csv(paths.output_report_csv, report.get("evidence", []))
        write_sources_csv(paths.output_sources_csv, report.get("source_files", []))

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "EVIDENCE_PACK_REPORT_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "input_evidence_pack": str(paths.input_evidence_pack),
            "outputs": {
                "report_json": str(paths.output_report_json),
                "report_md": str(paths.output_report_md),
                "report_csv": str(paths.output_report_csv),
                "sources_csv": str(paths.output_sources_csv),
            },
            "summary": report.get("summary"),
            "report_sha256": report.get("evidence_pack_report_sha256"),
        })

        print_summary(report, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "EVIDENCE_PACK_REPORT_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "input_evidence_pack": str(paths.input_evidence_pack),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG EVIDENCE PACK REPORTER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
