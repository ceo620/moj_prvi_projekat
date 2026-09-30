#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08_write_audit_log.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 08 — Final Audit Log / Evidence Lock Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Create a final audit record for the latest retrieval + answer cycle.

This script does NOT search.
This script does NOT generate answers.
This script does NOT modify source documents.
This script verifies whether the latest evidence pack and latest answer are
citation-complete enough for institutional review.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json

Outputs
-------
05_reports/latest_audit_record.json
05_reports/latest_audit_record.md
06_logs/final_audit_log.jsonl
06_logs/final_audit_errors.jsonl

Designed for compatibility with:
10_morning_briefing.py
11_query_console.py
13_source_citation_verifier.py
19_night_run_orchestrator.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\08_write_audit_log.py"

Print audit report
------------------
python ".\\08_scripts\\08_write_audit_log.py" --print

Strict mode
-----------
python ".\\08_scripts\\08_write_audit_log.py" --strict
"""

from __future__ import annotations

import argparse
import hashlib
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "08_write_audit_log.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
INPUT_ANSWER_JSON = Path("05_reports") / "latest_rag_answer.json"

OUTPUT_AUDIT_JSON = Path("05_reports") / "latest_audit_record.json"
OUTPUT_AUDIT_MD = Path("05_reports") / "latest_audit_record.md"

AUDIT_LOG = Path("06_logs") / "final_audit_log.jsonl"
ERROR_LOG = Path("06_logs") / "final_audit_errors.jsonl"

AUDIT_PASS = "AUDIT_PASS"
AUDIT_PASS_WITH_WARNINGS = "AUDIT_PASS_WITH_WARNINGS"
AUDIT_REVIEW_REQUIRED = "AUDIT_REVIEW_REQUIRED"
AUDIT_FAIL = "AUDIT_FAIL"
AUDIT_NO_EVIDENCE = "AUDIT_NO_EVIDENCE"

MIN_EXCERPT_CHARS = 40
MIN_EVIDENCE_ITEMS_FOR_PASS = 1
MIN_CONFIDENCE_FOR_PASS = 0.35
MIN_CONFIDENCE_FOR_STRICT_PASS = 0.55

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

RISK_TERMS = [
    "conflict", "konflikt", "failed", "failure", "error", "blocked", "missing",
    "unverified", "manual review", "review required", "draft", "estimate",
    "assumption", "not signed", "unsigned", "expired", "rejected",
    "nepotpisan", "neprovjeren", "neproveren", "nedostaje", "blokiran",
]


@dataclass(frozen=True)
class AuditPaths:
    base_dir: Path
    evidence_pack: Path
    answer_json: Path
    audit_json: Path
    audit_md: Path
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be object: {path}")
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


def resolve_paths(base_dir: Path, evidence_arg: str | None, answer_arg: str | None) -> AuditPaths:
    return AuditPaths(
        base_dir=base_dir,
        evidence_pack=Path(evidence_arg) if evidence_arg else base_dir / INPUT_EVIDENCE_PACK,
        answer_json=Path(answer_arg) if answer_arg else base_dir / INPUT_ANSWER_JSON,
        audit_json=base_dir / OUTPUT_AUDIT_JSON,
        audit_md=base_dir / OUTPUT_AUDIT_MD,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def evidence_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        return []
    return [item for item in evidence if isinstance(item, dict)]


def score_from_item(item: dict[str, Any]) -> float:
    scores = item.get("scores")
    if isinstance(scores, dict):
        return safe_float(scores.get("final_score"), 0.0)
    return 0.0


def has_risk_language(evidence: list[dict[str, Any]], answer: dict[str, Any]) -> bool:
    haystack = " ".join([
        " ".join(str(item.get("excerpt") or "") for item in evidence),
        str(answer.get("direct_answer") or ""),
        str(answer.get("risk_if_skipped") or ""),
        str(answer.get("next_action") or ""),
        str(answer.get("institutional_status") or ""),
    ]).lower()

    return any(term in haystack for term in RISK_TERMS)


def verify_evidence_item(item: dict[str, Any], position: int, strict: bool) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_EVIDENCE_FIELDS:
        if item.get(field) in [None, ""]:
            issues.append(f"MISSING_FIELD:{field}")

    scores = item.get("scores")
    if not isinstance(scores, dict):
        issues.append("MISSING_OR_INVALID:scores")
        scores = {}

    for field in REQUIRED_SCORE_FIELDS:
        if scores.get(field) in [None, ""]:
            issues.append(f"MISSING_SCORE:{field}")

    excerpt = str(item.get("excerpt") or "").strip()
    if len(excerpt) < MIN_EXCERPT_CHARS:
        issues.append(f"EXCERPT_TOO_SHORT:{len(excerpt)}")

    final_score = safe_float(scores.get("final_score"), -1.0)
    if final_score < 0:
        issues.append("INVALID_FINAL_SCORE")
    elif strict and final_score < MIN_CONFIDENCE_FOR_STRICT_PASS:
        warnings.append(f"STRICT_LOW_FINAL_SCORE:{final_score}")
    elif final_score < MIN_CONFIDENCE_FOR_PASS:
        warnings.append(f"LOW_FINAL_SCORE:{final_score}")

    source_path = str(item.get("source_path") or "").strip()
    chunk_id = str(item.get("chunk_id") or "").strip()

    if not source_path:
        issues.append("NO_SOURCE_PATH")

    if not chunk_id:
        issues.append("NO_CHUNK_ID")

    status = "PASS" if not issues else "FAIL"
    if status == "PASS" and warnings:
        status = "PASS_WITH_WARNINGS"

    return {
        "position": position,
        "status": status,
        "chunk_id": chunk_id,
        "source_path": source_path,
        "file_name": item.get("file_name"),
        "section_label": item.get("section_label"),
        "final_score": final_score,
        "excerpt_chars": len(excerpt),
        "issues": issues,
        "warnings": warnings,
    }


def verify_answer_consistency(evidence_pack: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    pack_evidence = evidence_items(evidence_pack)
    answer_evidence = evidence_items(answer)

    pack_chunk_ids = {
        str(item.get("chunk_id"))
        for item in pack_evidence
        if item.get("chunk_id")
    }

    answer_chunk_ids = {
        str(item.get("chunk_id"))
        for item in answer_evidence
        if item.get("chunk_id")
    }

    pack_sources = {
        str(item.get("source_path"))
        for item in pack_evidence
        if item.get("source_path")
    }

    answer_source_files = answer.get("source_files", [])
    if not isinstance(answer_source_files, list):
        answer_source_files = []

    answer_sources = {
        str(item)
        for item in answer_source_files
        if item
    }

    missing_answer_chunks = sorted(pack_chunk_ids - answer_chunk_ids)
    extra_answer_chunks = sorted(answer_chunk_ids - pack_chunk_ids)

    missing_sources_in_answer = sorted(pack_sources - answer_sources)
    extra_sources_in_answer = sorted(answer_sources - pack_sources)

    same_query = str(evidence_pack.get("query") or "") == str(answer.get("query") or "")

    return {
        "same_query": same_query,
        "pack_chunk_count": len(pack_chunk_ids),
        "answer_chunk_count": len(answer_chunk_ids),
        "missing_answer_chunks": missing_answer_chunks,
        "extra_answer_chunks": extra_answer_chunks,
        "pack_source_count": len(pack_sources),
        "answer_source_count": len(answer_sources),
        "missing_sources_in_answer": missing_sources_in_answer,
        "extra_sources_in_answer": extra_sources_in_answer,
        "is_consistent": (
            same_query
            and len(extra_answer_chunks) == 0
            and len(extra_sources_in_answer) == 0
        ),
    }


def calculate_audit_status(
    evidence_checks: list[dict[str, Any]],
    consistency: dict[str, Any],
    answer: dict[str, Any],
    risk_language: bool,
    strict: bool,
) -> tuple[str, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if not evidence_checks:
        return AUDIT_NO_EVIDENCE, ["No evidence items found."], []

    failed_checks = [x for x in evidence_checks if x.get("status") == "FAIL"]
    warning_checks = [x for x in evidence_checks if x.get("status") == "PASS_WITH_WARNINGS"]

    if failed_checks:
        failures.append(f"Evidence citation failures: {len(failed_checks)}")

    if warning_checks:
        warnings.append(f"Evidence citation warnings: {len(warning_checks)}")

    if not consistency.get("same_query"):
        failures.append("Evidence pack query and answer query do not match.")

    if consistency.get("extra_answer_chunks"):
        failures.append("Answer references chunks not present in evidence pack.")

    if consistency.get("extra_sources_in_answer"):
        failures.append("Answer references sources not present in evidence pack.")

    if consistency.get("missing_answer_chunks"):
        warnings.append("Some evidence pack chunks were not used in answer.")

    if consistency.get("missing_sources_in_answer"):
        warnings.append("Some evidence pack sources were not listed in answer source_files.")

    confidence = answer.get("confidence") if isinstance(answer.get("confidence"), dict) else {}
    confidence_score = safe_float(confidence.get("confidence_score"), 0.0)

    threshold = MIN_CONFIDENCE_FOR_STRICT_PASS if strict else MIN_CONFIDENCE_FOR_PASS
    if confidence_score < threshold:
        warnings.append(f"Answer confidence below threshold: {confidence_score} < {threshold}")

    if risk_language:
        warnings.append("Risk/draft/conflict language detected. Manual review recommended.")

    institutional_status = str(answer.get("institutional_status") or "")
    if "NO_EVIDENCE" in institutional_status:
        failures.append("Answer institutional status indicates no evidence.")
    elif "REVIEW" in institutional_status or "CONFLICT" in institutional_status:
        warnings.append(f"Answer institutional status requires review: {institutional_status}")

    if failures:
        return AUDIT_FAIL, failures, warnings

    if strict and warnings:
        return AUDIT_REVIEW_REQUIRED, failures, warnings

    if warnings:
        return AUDIT_PASS_WITH_WARNINGS, failures, warnings

    return AUDIT_PASS, failures, warnings


def build_audit_record(
    evidence_pack: dict[str, Any],
    answer: dict[str, Any],
    paths: AuditPaths,
    strict: bool,
) -> dict[str, Any]:
    pack_evidence = evidence_items(evidence_pack)
    answer_evidence = evidence_items(answer)

    checks = [
        verify_evidence_item(item=item, position=i, strict=strict)
        for i, item in enumerate(pack_evidence, start=1)
    ]

    consistency = verify_answer_consistency(evidence_pack=evidence_pack, answer=answer)
    risk_language = has_risk_language(pack_evidence + answer_evidence, answer)

    status, failures, warnings = calculate_audit_status(
        evidence_checks=checks,
        consistency=consistency,
        answer=answer,
        risk_language=risk_language,
        strict=strict,
    )

    confidence = answer.get("confidence") if isinstance(answer.get("confidence"), dict) else {}

    source_files = sorted({
        str(item.get("source_path"))
        for item in pack_evidence
        if item.get("source_path")
    })

    chunk_ids = [
        str(item.get("chunk_id"))
        for item in pack_evidence
        if item.get("chunk_id")
    ]

    scores = [score_from_item(item) for item in pack_evidence]
    avg_score = round(sum(scores) / len(scores), 6) if scores else None

    record = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "FINAL_AUDIT_LOCK_AUDIT_LOCKED",
        "strict_mode": strict,
        "audit_status": status,
        "query": evidence_pack.get("query") or answer.get("query"),
        "answer_institutional_status": answer.get("institutional_status"),
        "answer_confidence_score": confidence.get("confidence_score"),
        "answer_confidence_label": confidence.get("confidence_label"),
        "evidence_pack_path": str(paths.evidence_pack),
        "answer_json_path": str(paths.answer_json),
        "evidence_count": len(pack_evidence),
        "answer_evidence_count": len(answer_evidence),
        "source_file_count": len(source_files),
        "source_files": source_files,
        "chunk_ids": chunk_ids,
        "score_summary": {
            "max_final_score": round(max(scores), 6) if scores else None,
            "min_final_score": round(min(scores), 6) if scores else None,
            "average_final_score": avg_score,
        },
        "verification": {
            "evidence_checks": checks,
            "consistency": consistency,
            "risk_language_detected": risk_language,
            "failures": failures,
            "warnings": warnings,
        },
        "hashes": {
            "evidence_pack_canonical_sha256": sha256_json(evidence_pack),
            "answer_canonical_sha256": sha256_json(answer),
            "evidence_pack_declared_sha256": evidence_pack.get("evidence_pack_sha256"),
            "answer_declared_sha256": answer.get("answer_sha256"),
        },
        "governance_rule": {
            "audit_precedes_decision": True,
            "no_source_no_conclusion": True,
            "no_chunk_no_citation": True,
            "no_score_no_confidence": True,
            "risk_or_conflict_requires_manual_review": True,
            "source_files_remain_authoritative": True,
        },
    }

    record["audit_record_sha256"] = sha256_json(record)
    return record


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def checks_to_markdown(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return "No evidence checks."

    lines = [
        "| # | Status | Score | Source | Chunk | Issues | Warnings |",
        "|---:|---|---:|---|---|---|---|",
    ]

    for item in checks:
        issues = "; ".join(item.get("issues", []))
        warnings = "; ".join(item.get("warnings", []))
        lines.append(
            f"| {item.get('position')} | "
            f"{md_escape(item.get('status'))} | "
            f"{item.get('final_score')} | "
            f"`{md_escape(item.get('source_path'))}` | "
            f"`{md_escape(item.get('chunk_id'))}` | "
            f"{md_escape(issues)} | "
            f"{md_escape(warnings)} |"
        )

    return "\n".join(lines)


def audit_to_markdown(record: dict[str, Any]) -> str:
    verification = record.get("verification", {}) if isinstance(record.get("verification"), dict) else {}
    consistency = verification.get("consistency", {}) if isinstance(verification.get("consistency"), dict) else {}

    return f"""# TITAN RAG Final Audit Record

## 1. Final Audit Status

| Field | Value |
|---|---|
| Created At | {record.get("created_at")} |
| Audit Status | {record.get("audit_status")} |
| Strict Mode | {record.get("strict_mode")} |
| Query | {md_escape(record.get("query"))} |
| Answer Institutional Status | {record.get("answer_institutional_status")} |
| Answer Confidence Score | {record.get("answer_confidence_score")} |
| Answer Confidence Label | {record.get("answer_confidence_label")} |
| Evidence Count | {record.get("evidence_count")} |
| Source File Count | {record.get("source_file_count")} |
| Audit Record SHA-256 | `{record.get("audit_record_sha256")}` |

---

## 2. Failures

```json
{json.dumps(verification.get("failures", []), indent=2, ensure_ascii=False)}
```

---

## 3. Warnings

```json
{json.dumps(verification.get("warnings", []), indent=2, ensure_ascii=False)}
```

---

## 4. Consistency Check

| Check | Value |
|---|---|
| Same Query | {consistency.get("same_query")} |
| Pack Chunk Count | {consistency.get("pack_chunk_count")} |
| Answer Chunk Count | {consistency.get("answer_chunk_count")} |
| Missing Answer Chunks | {len(consistency.get("missing_answer_chunks", []))} |
| Extra Answer Chunks | {len(consistency.get("extra_answer_chunks", []))} |
| Pack Source Count | {consistency.get("pack_source_count")} |
| Answer Source Count | {consistency.get("answer_source_count")} |
| Missing Sources in Answer | {len(consistency.get("missing_sources_in_answer", []))} |
| Extra Sources in Answer | {len(consistency.get("extra_sources_in_answer", []))} |
| Consistent | {consistency.get("is_consistent")} |

---

## 5. Evidence Citation Checks

{checks_to_markdown(verification.get("evidence_checks", []))}

---

## 6. Hashes

```json
{json.dumps(record.get("hashes", {}), indent=2, ensure_ascii=False)}
```

---

## 7. Governance Rule

```text
Audit precedes decision.
No source -> no conclusion.
No chunk_id -> no citation.
No score -> no confidence.
Risk/conflict language requires manual review.
Source files remain authoritative.
```
"""


def print_summary(record: dict[str, Any], paths: AuditPaths) -> None:
    verification = record.get("verification", {}) if isinstance(record.get("verification"), dict) else {}

    print("=" * 100)
    print("TITAN RAG FINAL AUDIT LOCK v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Audit status:             {record.get('audit_status')}")
    print(f"Query:                    {record.get('query')}")
    print(f"Evidence count:           {record.get('evidence_count')}")
    print(f"Source file count:        {record.get('source_file_count')}")
    print(f"Answer confidence:        {record.get('answer_confidence_score')} | {record.get('answer_confidence_label')}")
    print(f"Failures:                 {len(verification.get('failures', []))}")
    print(f"Warnings:                 {len(verification.get('warnings', []))}")
    print("-" * 100)
    print(f"Audit JSON:               {paths.audit_json}")
    print(f"Audit Markdown:           {paths.audit_md}")
    print(f"Audit JSONL log:          {paths.audit_log}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 08 — final audit log / evidence lock."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--evidence-pack",
        default=None,
        help="Optional latest_evidence_pack.json path.",
    )

    parser.add_argument(
        "--answer-json",
        default=None,
        help="Optional latest_rag_answer.json path.",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict audit mode. Warnings become review-required.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print Markdown audit report to console.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        evidence_arg=args.evidence_pack,
        answer_arg=args.answer_json,
    )

    try:
        evidence_pack = load_json(paths.evidence_pack)
        answer = load_json(paths.answer_json)

        record = build_audit_record(
            evidence_pack=evidence_pack,
            answer=answer,
            paths=paths,
            strict=bool(args.strict),
        )

        markdown = audit_to_markdown(record)

        write_json(paths.audit_json, record)
        write_text(paths.audit_md, markdown)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "FINAL_AUDIT_RECORD_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "audit_status": record.get("audit_status"),
            "query": record.get("query"),
            "audit_record_sha256": record.get("audit_record_sha256"),
            "record": record,
        })

        print_summary(record, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "FINAL_AUDIT_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG FINAL AUDIT LOCK FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
