#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
13_source_citation_verifier.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 13 — Source Citation Verifier
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Verify citation integrity between:
- latest_evidence_pack.json from Step 06
- latest_rag_answer.json from Step 07
- evidence_pack_report.json from Step 12, if available

This script does NOT search.
This script does NOT generate answers.
This script does NOT modify evidence.
It verifies whether every answer/evidence item is traceable through source_path,
chunk_id, score and excerpt.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json
05_reports/evidence_pack_report.json     # optional

Outputs
-------
05_reports/citation_verification_report.json
05_reports/citation_verification_report.md
05_reports/citation_verification_report.csv
06_logs/source_citation_verifier_audit.jsonl
06_logs/source_citation_verifier_errors.jsonl

Designed for compatibility with:
14_conflict_detector.py
15_ssot_candidate_extractor.py
16_financial_signal_extractor.py
17_risk_signal_extractor.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\13_source_citation_verifier.py" --print

Strict mode
-----------
python ".\\08_scripts\\13_source_citation_verifier.py" --strict --print
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


SCRIPT_NAME = "13_source_citation_verifier.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
INPUT_ANSWER_JSON = Path("05_reports") / "latest_rag_answer.json"
INPUT_EVIDENCE_REPORT = Path("05_reports") / "evidence_pack_report.json"

OUTPUT_JSON = Path("05_reports") / "citation_verification_report.json"
OUTPUT_MD = Path("05_reports") / "citation_verification_report.md"
OUTPUT_CSV = Path("05_reports") / "citation_verification_report.csv"

AUDIT_LOG = Path("06_logs") / "source_citation_verifier_audit.jsonl"
ERROR_LOG = Path("06_logs") / "source_citation_verifier_errors.jsonl"

STATUS_PASS = "CITATION_VERIFICATION_PASS"
STATUS_PASS_WITH_WARNINGS = "CITATION_VERIFICATION_PASS_WITH_WARNINGS"
STATUS_REVIEW_REQUIRED = "CITATION_REVIEW_REQUIRED"
STATUS_FAIL = "CITATION_VERIFICATION_FAIL"
STATUS_NO_EVIDENCE = "NO_EVIDENCE_NO_CITATION"

MIN_EXCERPT_CHARS = 40
MIN_SCORE_DEFAULT = 0.0
MIN_SCORE_STRICT = 0.35

REQUIRED_EVIDENCE_FIELDS = [
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


@dataclass(frozen=True)
class VerifierPaths:
    base_dir: Path
    evidence_pack: Path
    answer_json: Path
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


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


def resolve_paths(base_dir: Path, evidence_arg: str | None, answer_arg: str | None, report_arg: str | None) -> VerifierPaths:
    return VerifierPaths(
        base_dir=base_dir,
        evidence_pack=Path(evidence_arg) if evidence_arg else base_dir / INPUT_EVIDENCE_PACK,
        answer_json=Path(answer_arg) if answer_arg else base_dir / INPUT_ANSWER_JSON,
        evidence_report=Path(report_arg) if report_arg else base_dir / INPUT_EVIDENCE_REPORT,
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


def evidence_key(item: dict[str, Any]) -> str:
    return str(item.get("chunk_id") or "").strip()


def build_pack_index(evidence_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in get_evidence(evidence_pack):
        key = evidence_key(item)
        if key:
            output[key] = item
    return output


def validate_single_citation(item: dict[str, Any], context: str, strict: bool, pack_index: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    chunk_id = str(item.get("chunk_id") or "").strip()
    source_path = str(item.get("source_path") or "").strip()
    file_name = str(item.get("file_name") or "").strip()
    excerpt = str(item.get("excerpt") or "").strip()
    scores = score_dict(item)

    for field in REQUIRED_EVIDENCE_FIELDS:
        if item.get(field) in [None, ""]:
            issues.append(f"MISSING_FIELD:{field}")

    if not isinstance(item.get("scores"), dict):
        issues.append("SCORES_NOT_OBJECT")

    for field in REQUIRED_SCORE_FIELDS:
        if scores.get(field) in [None, ""]:
            issues.append(f"MISSING_SCORE:{field}")

    if not chunk_id:
        issues.append("NO_CHUNK_ID")

    if not source_path:
        issues.append("NO_SOURCE_PATH")

    if not file_name:
        warnings.append("NO_FILE_NAME")

    if len(excerpt) < MIN_EXCERPT_CHARS:
        issues.append(f"EXCERPT_TOO_SHORT:{len(excerpt)}")

    threshold = MIN_SCORE_STRICT if strict else MIN_SCORE_DEFAULT
    score = final_score(item)
    if score < threshold:
        issues.append(f"FINAL_SCORE_BELOW_THRESHOLD:{score}<{threshold}")

    if pack_index is not None:
        if not chunk_id:
            issues.append("CANNOT_VERIFY_PACK_MEMBERSHIP_WITHOUT_CHUNK_ID")
        elif chunk_id not in pack_index:
            issues.append("CHUNK_ID_NOT_FOUND_IN_EVIDENCE_PACK")
        else:
            pack_item = pack_index[chunk_id]
            pack_source = str(pack_item.get("source_path") or "").strip()
            if source_path and pack_source and source_path != pack_source:
                issues.append("SOURCE_PATH_MISMATCH_WITH_EVIDENCE_PACK")

            pack_excerpt_hash = sha256_text(str(pack_item.get("excerpt") or ""))
            current_excerpt_hash = sha256_text(excerpt)
            if excerpt and pack_item.get("excerpt") and pack_excerpt_hash != current_excerpt_hash:
                warnings.append("EXCERPT_DIFFERS_FROM_EVIDENCE_PACK")

    status = "PASS" if not issues else "FAIL"
    if status == "PASS" and warnings:
        status = "PASS_WITH_WARNINGS"

    return {
        "context": context,
        "status": status,
        "chunk_id": chunk_id,
        "source_path": source_path,
        "file_name": file_name,
        "section_label": item.get("section_label"),
        "final_score": score,
        "excerpt_chars": len(excerpt),
        "issues": issues,
        "warnings": warnings,
    }


def verify_pack_evidence(evidence_pack: dict[str, Any], strict: bool) -> list[dict[str, Any]]:
    checks = []
    for item in get_evidence(evidence_pack):
        checks.append(
            validate_single_citation(
                item=item,
                context="latest_evidence_pack",
                strict=strict,
                pack_index=None,
            )
        )
    return checks


def verify_answer_evidence(answer: dict[str, Any], pack_index: dict[str, dict[str, Any]], strict: bool) -> list[dict[str, Any]]:
    checks = []
    for item in get_evidence(answer):
        checks.append(
            validate_single_citation(
                item=item,
                context="latest_rag_answer",
                strict=strict,
                pack_index=pack_index,
            )
        )
    return checks


def verify_answer_lists(answer: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    pack_evidence = get_evidence(evidence_pack)

    pack_chunks = {
        str(item.get("chunk_id"))
        for item in pack_evidence
        if item.get("chunk_id")
    }

    pack_sources = {
        str(item.get("source_path"))
        for item in pack_evidence
        if item.get("source_path")
    }

    answer_chunks = set()
    answer_chunk_list = answer.get("chunk_ids", [])
    if isinstance(answer_chunk_list, list):
        answer_chunks = {str(x) for x in answer_chunk_list if x}

    answer_sources = set()
    answer_source_list = answer.get("source_files", [])
    if isinstance(answer_source_list, list):
        answer_sources = {str(x) for x in answer_source_list if x}

    answer_evidence_chunks = {
        str(item.get("chunk_id"))
        for item in get_evidence(answer)
        if item.get("chunk_id")
    }

    return {
        "pack_chunk_count": len(pack_chunks),
        "pack_source_count": len(pack_sources),
        "answer_chunk_list_count": len(answer_chunks),
        "answer_source_list_count": len(answer_sources),
        "answer_evidence_chunk_count": len(answer_evidence_chunks),
        "answer_chunk_list_extra": sorted(answer_chunks - pack_chunks),
        "answer_source_list_extra": sorted(answer_sources - pack_sources),
        "answer_evidence_chunk_extra": sorted(answer_evidence_chunks - pack_chunks),
        "pack_chunks_missing_from_answer_lists": sorted(pack_chunks - answer_chunks),
        "pack_sources_missing_from_answer_lists": sorted(pack_sources - answer_sources),
        "is_list_consistent": (
            len(answer_chunks - pack_chunks) == 0
            and len(answer_sources - pack_sources) == 0
            and len(answer_evidence_chunks - pack_chunks) == 0
        ),
    }


def verify_evidence_report(evidence_report: dict[str, Any] | None, evidence_pack: dict[str, Any]) -> dict[str, Any]:
    if not evidence_report:
        return {
            "available": False,
            "status": "NOT_AVAILABLE",
            "issues": [],
            "warnings": ["evidence_pack_report.json not found; run Step 12 for richer reporting."],
        }

    issues: list[str] = []
    warnings: list[str] = []

    report_summary = evidence_report.get("summary", {}) if isinstance(evidence_report.get("summary"), dict) else {}
    report_evidence = evidence_report.get("evidence", [])
    if not isinstance(report_evidence, list):
        issues.append("REPORT_EVIDENCE_NOT_LIST")
        report_evidence = []

    pack_evidence = get_evidence(evidence_pack)

    if safe_int(report_summary.get("evidence_count"), -1) != len(pack_evidence):
        warnings.append("REPORT_EVIDENCE_COUNT_DIFFERS_FROM_PACK")

    report_sha = report_summary.get("evidence_pack_sha256")
    pack_sha = evidence_pack.get("evidence_pack_sha256")
    if report_sha and pack_sha and report_sha != pack_sha:
        issues.append("REPORT_REFERENCES_DIFFERENT_EVIDENCE_PACK_SHA256")

    status = "PASS" if not issues else "FAIL"
    if status == "PASS" and warnings:
        status = "PASS_WITH_WARNINGS"

    return {
        "available": True,
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "report_evidence_count": len(report_evidence),
        "pack_evidence_count": len(pack_evidence),
        "report_status": report_summary.get("report_status"),
    }


def collect_rows(pack_checks: list[dict[str, Any]], answer_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for check in pack_checks + answer_checks:
        rows.append({
            "Context": check.get("context"),
            "Status": check.get("status"),
            "Chunk_ID": check.get("chunk_id"),
            "Source_Path": check.get("source_path"),
            "File_Name": check.get("file_name"),
            "Section_Label": check.get("section_label"),
            "Final_Score": check.get("final_score"),
            "Excerpt_Chars": check.get("excerpt_chars"),
            "Issues": "; ".join(check.get("issues", [])),
            "Warnings": "; ".join(check.get("warnings", [])),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Context",
        "Status",
        "Chunk_ID",
        "Source_Path",
        "File_Name",
        "Section_Label",
        "Final_Score",
        "Excerpt_Chars",
        "Issues",
        "Warnings",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def determine_status(
    pack_checks: list[dict[str, Any]],
    answer_checks: list[dict[str, Any]],
    list_check: dict[str, Any],
    report_check: dict[str, Any],
    strict: bool,
) -> tuple[str, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if not pack_checks:
        return STATUS_NO_EVIDENCE, ["No evidence items in latest_evidence_pack.json"], []

    pack_failed = [x for x in pack_checks if x.get("status") == "FAIL"]
    answer_failed = [x for x in answer_checks if x.get("status") == "FAIL"]

    pack_warn = [x for x in pack_checks if x.get("status") == "PASS_WITH_WARNINGS"]
    answer_warn = [x for x in answer_checks if x.get("status") == "PASS_WITH_WARNINGS"]

    if pack_failed:
        failures.append(f"Evidence pack citation failures: {len(pack_failed)}")

    if answer_failed:
        failures.append(f"Answer citation failures: {len(answer_failed)}")

    if pack_warn:
        warnings.append(f"Evidence pack citation warnings: {len(pack_warn)}")

    if answer_warn:
        warnings.append(f"Answer citation warnings: {len(answer_warn)}")

    if not list_check.get("is_list_consistent"):
        if list_check.get("answer_chunk_list_extra") or list_check.get("answer_source_list_extra") or list_check.get("answer_evidence_chunk_extra"):
            failures.append("Answer references chunks/sources not found in evidence pack.")
        if list_check.get("pack_chunks_missing_from_answer_lists") or list_check.get("pack_sources_missing_from_answer_lists"):
            warnings.append("Some evidence pack chunks/sources are not listed in answer summary lists.")

    if report_check.get("status") == "FAIL":
        warnings.append("Evidence report check failed. Rerun Step 12.")
    elif report_check.get("status") == "PASS_WITH_WARNINGS":
        warnings.append("Evidence report has warnings.")

    if failures:
        return STATUS_FAIL, failures, warnings

    if strict and warnings:
        return STATUS_REVIEW_REQUIRED, failures, warnings

    if warnings:
        return STATUS_PASS_WITH_WARNINGS, failures, warnings

    return STATUS_PASS, failures, warnings


def build_report(
    evidence_pack: dict[str, Any],
    answer: dict[str, Any],
    evidence_report: dict[str, Any] | None,
    paths: VerifierPaths,
    strict: bool,
) -> dict[str, Any]:
    pack_index = build_pack_index(evidence_pack)

    pack_checks = verify_pack_evidence(evidence_pack=evidence_pack, strict=strict)
    answer_checks = verify_answer_evidence(answer=answer, pack_index=pack_index, strict=strict)
    list_check = verify_answer_lists(answer=answer, evidence_pack=evidence_pack)
    report_check = verify_evidence_report(evidence_report=evidence_report, evidence_pack=evidence_pack)

    status, failures, warnings = determine_status(
        pack_checks=pack_checks,
        answer_checks=answer_checks,
        list_check=list_check,
        report_check=report_check,
        strict=strict,
    )

    rows = collect_rows(pack_checks, answer_checks)

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "SOURCE_CITATION_VERIFICATION_AUDIT_LOCKED",
        "strict_mode": strict,
        "verification_status": status,
        "query": evidence_pack.get("query") or answer.get("query"),
        "inputs": {
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "evidence_report": str(paths.evidence_report),
            "evidence_report_available": evidence_report is not None,
        },
        "summary": {
            "pack_evidence_count": len(pack_checks),
            "answer_evidence_count": len(answer_checks),
            "csv_rows": len(rows),
            "failure_count": len(failures),
            "warning_count": len(warnings),
            "pack_failed_count": sum(1 for x in pack_checks if x.get("status") == "FAIL"),
            "answer_failed_count": sum(1 for x in answer_checks if x.get("status") == "FAIL"),
            "pack_warning_count": sum(1 for x in pack_checks if x.get("status") == "PASS_WITH_WARNINGS"),
            "answer_warning_count": sum(1 for x in answer_checks if x.get("status") == "PASS_WITH_WARNINGS"),
        },
        "failures": failures,
        "warnings": warnings,
        "pack_checks": pack_checks,
        "answer_checks": answer_checks,
        "answer_list_consistency": list_check,
        "evidence_report_check": report_check,
        "rows": rows,
        "hashes": {
            "evidence_pack_canonical_sha256": sha256_json(evidence_pack),
            "answer_canonical_sha256": sha256_json(answer),
            "evidence_report_canonical_sha256": sha256_json(evidence_report) if evidence_report else None,
            "evidence_pack_declared_sha256": evidence_pack.get("evidence_pack_sha256"),
            "answer_declared_sha256": answer.get("answer_sha256"),
        },
        "governance_rule": {
            "source_path_required": True,
            "chunk_id_required": True,
            "score_required": True,
            "excerpt_required": True,
            "answer_must_not_reference_unknown_chunks": True,
            "citation_verification_precedes_institutional_use": True,
        },
    }

    report["citation_verification_sha256"] = sha256_json(report)
    return report


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def checks_table_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No citation rows."

    lines = [
        "| Context | Status | Score | Source | Chunk | Issues | Warnings |",
        "|---|---|---:|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Context'))} | "
            f"{md_escape(row.get('Status'))} | "
            f"{row.get('Final_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"`{md_escape(row.get('Chunk_ID'))}` | "
            f"{md_escape(row.get('Issues'))} | "
            f"{md_escape(row.get('Warnings'))} |"
        )

    return "\n".join(lines)


def report_to_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    return f"""# TITAN RAG Source Citation Verification Report

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Verification Status | {report.get("verification_status")} |
| Strict Mode | {report.get("strict_mode")} |
| Query | {md_escape(report.get("query"))} |
| Pack Evidence Count | {summary.get("pack_evidence_count")} |
| Answer Evidence Count | {summary.get("answer_evidence_count")} |
| Failure Count | {summary.get("failure_count")} |
| Warning Count | {summary.get("warning_count")} |
| Report SHA-256 | `{report.get("citation_verification_sha256")}` |

---

## 2. Failures

```json
{json.dumps(report.get("failures", []), indent=2, ensure_ascii=False)}
```

---

## 3. Warnings

```json
{json.dumps(report.get("warnings", []), indent=2, ensure_ascii=False)}
```

---

## 4. Citation Rows

{checks_table_md(report.get("rows", []))}

---

## 5. Answer List Consistency

```json
{json.dumps(report.get("answer_list_consistency", {}), indent=2, ensure_ascii=False)}
```

---

## 6. Evidence Report Check

```json
{json.dumps(report.get("evidence_report_check", {}), indent=2, ensure_ascii=False)}
```

---

## 7. Hashes

```json
{json.dumps(report.get("hashes", {}), indent=2, ensure_ascii=False)}
```

---

## 8. Governance Rule

```text
source_path is mandatory.
chunk_id is mandatory.
score is mandatory.
excerpt is mandatory.
Answer must not reference unknown chunks or unknown sources.
Citation verification precedes institutional use.
```
"""


def print_summary(report: dict[str, Any], paths: VerifierPaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN RAG SOURCE CITATION VERIFIER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Verification status:   {report.get('verification_status')}")
    print(f"Query:                 {report.get('query')}")
    print(f"Pack evidence count:   {summary.get('pack_evidence_count')}")
    print(f"Answer evidence count: {summary.get('answer_evidence_count')}")
    print(f"Failures:              {summary.get('failure_count')}")
    print(f"Warnings:              {summary.get('warning_count')}")
    print("-" * 100)
    print(f"Report JSON:           {paths.output_json}")
    print(f"Report Markdown:       {paths.output_md}")
    print(f"Report CSV:            {paths.output_csv}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 13 — source citation verifier."
    )

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--evidence-pack", default=None, help="Optional latest_evidence_pack.json path.")
    parser.add_argument("--answer-json", default=None, help="Optional latest_rag_answer.json path.")
    parser.add_argument("--evidence-report", default=None, help="Optional evidence_pack_report.json path.")
    parser.add_argument("--strict", action="store_true", help="Strict mode: warnings require review.")
    parser.add_argument("--print", action="store_true", help="Print Markdown report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        evidence_arg=args.evidence_pack,
        answer_arg=args.answer_json,
        report_arg=args.evidence_report,
    )

    try:
        evidence_pack = require_json(paths.evidence_pack)
        answer = require_json(paths.answer_json)
        evidence_report = load_json_if_exists(paths.evidence_report)

        report = build_report(
            evidence_pack=evidence_pack,
            answer=answer,
            evidence_report=evidence_report,
            paths=paths,
            strict=bool(args.strict),
        )

        markdown = report_to_markdown(report)

        write_json(paths.output_json, report)
        write_text(paths.output_md, markdown)
        write_csv(paths.output_csv, report.get("rows", []))

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "SOURCE_CITATION_VERIFICATION_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "verification_status": report.get("verification_status"),
            "summary": report.get("summary"),
            "report_sha256": report.get("citation_verification_sha256"),
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
            "event": "SOURCE_CITATION_VERIFICATION_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "evidence_report": str(paths.evidence_report),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG SOURCE CITATION VERIFIER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
