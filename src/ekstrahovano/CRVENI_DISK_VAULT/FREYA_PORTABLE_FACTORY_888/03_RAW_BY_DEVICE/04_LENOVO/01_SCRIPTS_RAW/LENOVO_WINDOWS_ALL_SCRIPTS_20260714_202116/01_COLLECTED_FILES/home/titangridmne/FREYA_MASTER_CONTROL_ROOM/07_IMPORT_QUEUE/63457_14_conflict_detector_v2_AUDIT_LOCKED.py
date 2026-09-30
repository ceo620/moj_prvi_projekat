#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
14_conflict_detector.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 14 — Conflict Detector
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Detect possible conflicts inside the latest evidence pack and answer:
- contradictory monetary values
- contradictory percentages
- contradictory dates
- contradictory statuses
- multiple values for the same strategic entity
- citation verification failure propagation

This script does NOT decide the final truth.
This script does NOT overwrite SSOT.
This script does NOT generate final legal/financial conclusions.
It produces conflict candidates for manual SSOT review.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json
05_reports/citation_verification_report.json   # optional but recommended

Outputs
-------
05_reports/conflict_report.json
05_reports/conflict_report.md
05_reports/conflict_report.csv
06_logs/conflict_detector_audit.jsonl
06_logs/conflict_detector_errors.jsonl

Designed for compatibility with:
15_ssot_candidate_extractor.py
17_risk_signal_extractor.py
18_document_priority_ranker.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\14_conflict_detector.py" --print

Strict mode
-----------
python ".\\08_scripts\\14_conflict_detector.py" --strict --print
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "14_conflict_detector.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
INPUT_ANSWER_JSON = Path("05_reports") / "latest_rag_answer.json"
INPUT_CITATION_REPORT = Path("05_reports") / "citation_verification_report.json"

OUTPUT_JSON = Path("05_reports") / "conflict_report.json"
OUTPUT_MD = Path("05_reports") / "conflict_report.md"
OUTPUT_CSV = Path("05_reports") / "conflict_report.csv"

AUDIT_LOG = Path("06_logs") / "conflict_detector_audit.jsonl"
ERROR_LOG = Path("06_logs") / "conflict_detector_errors.jsonl"

STATUS_NO_CONFLICTS = "NO_CONFLICTS_DETECTED"
STATUS_CONFLICTS_DETECTED = "CONFLICTS_DETECTED_REVIEW_REQUIRED"
STATUS_HIGH_CONFLICT_RISK = "HIGH_CONFLICT_RISK_MANUAL_REVIEW"
STATUS_INVALID_INPUT = "INVALID_INPUT_REVIEW_REQUIRED"

SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"

# Strategic entities used for grouping. These are intentionally conservative.
ENTITY_PATTERNS = {
    "CAPEX": [r"\bcapex\b", r"\bcapital expenditure\b", r"\binvestment cost\b"],
    "OPEX": [r"\bopex\b", r"\boperating cost\b"],
    "DSCR": [r"\bdscr\b", r"\bdebt service coverage\b"],
    "IRR": [r"\birr\b", r"\binternal rate of return\b"],
    "NPV": [r"\bnpv\b", r"\bnet present value\b"],
    "WACC": [r"\bwacc\b", r"\bweighted average cost"],
    "LOAN": [r"\bloan\b", r"\bdebt facility\b", r"\bcredit\b"],
    "EQUITY": [r"\bequity\b", r"\bshare capital\b"],
    "GRANT": [r"\bgrant\b", r"\bsubsidy\b"],
    "EIB": [r"\beib\b", r"\beuropean investment bank\b"],
    "EBRD": [r"\bebrd\b", r"\beuropean bank for reconstruction"],
    "IFC": [r"\bifc\b", r"\binternational finance corporation\b"],
    "CONTRACT": [r"\bcontract\b", r"\bagreement\b", r"\bugovor\b"],
    "PERMIT": [r"\bpermit\b", r"\blicen[cs]e\b", r"\bdozvol"],
    "DEADLINE": [r"\bdeadline\b", r"\bdue date\b", r"\bmilestone\b", r"\brok\b"],
    "STATUS": [r"\bstatus\b", r"\bapproved\b", r"\brejected\b", r"\bsigned\b", r"\bunsigned\b", r"\bdraft\b"],
    "SSOT": [r"\bssot\b", r"\bsource of truth\b", r"\bcanonical\b"],
}

STATUS_TERMS = {
    "APPROVED": [r"\bapproved\b", r"\baccepted\b", r"\bvalid\b", r"\bconfirmed\b", r"\bpotvrđen", r"\bpotvrdjen"],
    "REJECTED": [r"\brejected\b", r"\bdeclined\b", r"\binvalid\b", r"\bodbijen"],
    "SIGNED": [r"\bsigned\b", r"\bexecuted\b", r"\bpotpisan"],
    "UNSIGNED": [r"\bunsigned\b", r"\bnot signed\b", r"\bnepotpisan"],
    "DRAFT": [r"\bdraft\b", r"\bworking version\b", r"\bnacrt"],
    "FINAL": [r"\bfinal\b", r"\bapproved version\b", r"\bzaključen\b", r"\bzakljucen"],
    "MISSING": [r"\bmissing\b", r"\bnot found\b", r"\bnedostaje\b", r"\bnema\b"],
    "BLOCKED": [r"\bblocked\b", r"\bblokiran"],
    "EXPIRED": [r"\bexpired\b", r"\bistekao"],
}

CONTRADICTORY_STATUS_PAIRS = {
    frozenset(["APPROVED", "REJECTED"]),
    frozenset(["SIGNED", "UNSIGNED"]),
    frozenset(["FINAL", "DRAFT"]),
    frozenset(["VALID", "EXPIRED"]),
    frozenset(["APPROVED", "MISSING"]),
    frozenset(["SIGNED", "MISSING"]),
}

MONEY_RE = re.compile(
    r"(?P<prefix>€|eur|euro|usd|\$)?\s*"
    r"(?P<number>\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)\s*"
    r"(?P<suffix>m|mn|million|milion|k|thousand|hiljada|eur|euro|€|usd|\$)?",
    re.IGNORECASE,
)

PERCENT_RE = re.compile(
    r"(?P<number>\d{1,3}(?:[.,]\d+)?)\s*(?P<symbol>%|percent|procenat|posto)",
    re.IGNORECASE,
)

DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    r"|"
    r"\d{4}[./-]\d{1,2}[./-]\d{1,2}"
    r")\b"
)

RATIO_RE = re.compile(
    r"\b(?P<number>\d{1,2}(?:[.,]\d{1,4})?)\s*x\b|\b(?P<number2>\d{1,2}(?:[.,]\d{1,4})?)\b",
    re.IGNORECASE,
)

MIN_VALUE_DELTA_PERCENT = 0.05
MIN_MONEY_DELTA_ABSOLUTE = 1000.0
MIN_PERCENT_DELTA_ABSOLUTE = 0.25
MIN_RATIO_DELTA_ABSOLUTE = 0.02


@dataclass(frozen=True)
class ConflictPaths:
    base_dir: Path
    evidence_pack: Path
    answer_json: Path
    citation_report: Path
    output_json: Path
    output_md: Path
    output_csv: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def normalize_text(value: Any) -> str:
    text = str(value or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


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


def resolve_paths(base_dir: Path, evidence_arg: str | None, answer_arg: str | None, citation_arg: str | None) -> ConflictPaths:
    return ConflictPaths(
        base_dir=base_dir,
        evidence_pack=Path(evidence_arg) if evidence_arg else base_dir / INPUT_EVIDENCE_PACK,
        answer_json=Path(answer_arg) if answer_arg else base_dir / INPUT_ANSWER_JSON,
        citation_report=Path(citation_arg) if citation_arg else base_dir / INPUT_CITATION_REPORT,
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
    return [item for item in evidence if isinstance(item, dict)]


def get_score(item: dict[str, Any]) -> float:
    scores = item.get("scores")
    if isinstance(scores, dict):
        return safe_float(scores.get("final_score"), 0.0)
    return 0.0


def detect_entities(text: str) -> list[str]:
    lower = text.lower()
    entities = []

    for entity, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                entities.append(entity)
                break

    return sorted(set(entities)) or ["GENERAL"]


def parse_number(text: str) -> float | None:
    value = str(text or "").strip()
    if not value:
        return None

    # European/US mixed parsing.
    if "," in value and "." in value:
        # If last separator is comma, assume EU decimal: 1.234,56
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        parts = value.split(",")
        if len(parts[-1]) in {1, 2, 3} and len(parts) == 2:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")
    else:
        # 1.234.567 -> remove thousand dots if all groups after first are 3.
        parts = value.split(".")
        if len(parts) > 2 and all(len(p) == 3 for p in parts[1:]):
            value = value.replace(".", "")

    try:
        return float(value)
    except Exception:
        return None


def scale_money(number: float, prefix: str | None, suffix: str | None) -> tuple[float, str]:
    suffix_l = str(suffix or "").lower()
    prefix_l = str(prefix or "").lower()

    currency = "UNKNOWN"
    if prefix_l in {"€", "eur", "euro"} or suffix_l in {"€", "eur", "euro"}:
        currency = "EUR"
    elif prefix_l in {"$", "usd"} or suffix_l in {"$", "usd"}:
        currency = "USD"

    scaled = number
    if suffix_l in {"m", "mn", "million", "milion"}:
        scaled = number * 1_000_000
    elif suffix_l in {"k", "thousand", "hiljada"}:
        scaled = number * 1_000

    return scaled, currency


def context_window(text: str, start: int, end: int, chars: int = 150) -> str:
    left = max(0, start - chars)
    right = min(len(text), end + chars)
    return normalize_inline(text[left:right])


def extract_money_values(text: str, item: dict[str, Any], context_type: str) -> list[dict[str, Any]]:
    values = []
    for match in MONEY_RE.finditer(text):
        raw = match.group(0).strip()
        number_raw = match.group("number")
        prefix = match.group("prefix")
        suffix = match.group("suffix")

        # Avoid matching every small integer as money unless it has currency/scale indicator.
        if not prefix and not suffix:
            continue

        num = parse_number(number_raw)
        if num is None:
            continue

        amount, currency = scale_money(num, prefix, suffix)

        values.append(make_value_record(
            value_type="MONEY",
            canonical_value=amount,
            raw_value=raw,
            unit=currency,
            text=text,
            match_start=match.start(),
            match_end=match.end(),
            item=item,
            context_type=context_type,
        ))
    return values


def extract_percent_values(text: str, item: dict[str, Any], context_type: str) -> list[dict[str, Any]]:
    values = []
    for match in PERCENT_RE.finditer(text):
        raw = match.group(0).strip()
        num = parse_number(match.group("number"))
        if num is None:
            continue

        values.append(make_value_record(
            value_type="PERCENT",
            canonical_value=num,
            raw_value=raw,
            unit="%",
            text=text,
            match_start=match.start(),
            match_end=match.end(),
            item=item,
            context_type=context_type,
        ))
    return values


def extract_date_values(text: str, item: dict[str, Any], context_type: str) -> list[dict[str, Any]]:
    values = []
    for match in DATE_RE.finditer(text):
        raw = match.group(0).strip()
        values.append(make_value_record(
            value_type="DATE",
            canonical_value=normalize_date(raw),
            raw_value=raw,
            unit="DATE",
            text=text,
            match_start=match.start(),
            match_end=match.end(),
            item=item,
            context_type=context_type,
        ))
    return values


def normalize_date(raw: str) -> str:
    value = str(raw).strip()
    parts = re.split(r"[./-]", value)

    if len(parts) != 3:
        return value

    try:
        if len(parts[0]) == 4:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            if y < 100:
                y += 2000 if y < 50 else 1900
        return f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        return value


def extract_status_values(text: str, item: dict[str, Any], context_type: str) -> list[dict[str, Any]]:
    lower = text.lower()
    values = []
    for status, patterns in STATUS_TERMS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, lower, flags=re.IGNORECASE):
                values.append(make_value_record(
                    value_type="STATUS",
                    canonical_value=status,
                    raw_value=text[match.start():match.end()],
                    unit="STATUS",
                    text=text,
                    match_start=match.start(),
                    match_end=match.end(),
                    item=item,
                    context_type=context_type,
                ))
    return values


def extract_ratio_values(text: str, item: dict[str, Any], context_type: str) -> list[dict[str, Any]]:
    # Restrict ratio extraction to DSCR/WACC/IRR/NPV/loan context to reduce noise.
    lower = text.lower()
    if not any(marker in lower for marker in ["dscr", "coverage", "ratio", "wacc", "irr", "npv"]):
        return []

    values = []
    for match in RATIO_RE.finditer(text):
        raw_num = match.group("number") or match.group("number2")
        if not raw_num:
            continue
        num = parse_number(raw_num)
        if num is None:
            continue
        if num <= 0 or num > 100:
            continue

        values.append(make_value_record(
            value_type="RATIO",
            canonical_value=num,
            raw_value=match.group(0).strip(),
            unit="RATIO",
            text=text,
            match_start=match.start(),
            match_end=match.end(),
            item=item,
            context_type=context_type,
        ))
    return values


def make_value_record(
    value_type: str,
    canonical_value: Any,
    raw_value: str,
    unit: str,
    text: str,
    match_start: int,
    match_end: int,
    item: dict[str, Any],
    context_type: str,
) -> dict[str, Any]:
    ctx = context_window(text, match_start, match_end, chars=220)
    entities = detect_entities(ctx)

    return {
        "value_id": "",
        "value_type": value_type,
        "canonical_value": canonical_value,
        "raw_value": raw_value,
        "unit": unit,
        "entities": entities,
        "context": ctx,
        "context_type": context_type,
        "source_path": item.get("source_path"),
        "file_name": item.get("file_name"),
        "chunk_id": item.get("chunk_id"),
        "section_label": item.get("section_label"),
        "rank": item.get("rank"),
        "score": get_score(item),
        "excerpt_sha256": item.get("excerpt_sha256"),
    }


def finalize_value_ids(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for value in values:
        raw = json.dumps({
            "type": value.get("value_type"),
            "canonical": value.get("canonical_value"),
            "unit": value.get("unit"),
            "entities": value.get("entities"),
            "source": value.get("source_path"),
            "chunk": value.get("chunk_id"),
            "context_hash": sha256_text(value.get("context") or "")[:16],
        }, sort_keys=True, ensure_ascii=False)
        value["value_id"] = "VAL-" + sha256_text(raw)[:16]
    return values


def extract_values_from_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []

    for item in evidence:
        text = normalize_text(item.get("excerpt"))
        if not text:
            continue

        values.extend(extract_money_values(text, item=item, context_type="evidence_excerpt"))
        values.extend(extract_percent_values(text, item=item, context_type="evidence_excerpt"))
        values.extend(extract_date_values(text, item=item, context_type="evidence_excerpt"))
        values.extend(extract_status_values(text, item=item, context_type="evidence_excerpt"))
        values.extend(extract_ratio_values(text, item=item, context_type="evidence_excerpt"))

    return finalize_value_ids(values)


def extract_values_from_answer(answer: dict[str, Any]) -> list[dict[str, Any]]:
    pseudo_item = {
        "source_path": "latest_rag_answer.json",
        "file_name": "latest_rag_answer.json",
        "chunk_id": "ANSWER_SYNTHESIS",
        "section_label": "direct_answer",
        "rank": None,
        "scores": {"final_score": safe_float((answer.get("confidence") or {}).get("confidence_score"), 0.0)} if isinstance(answer.get("confidence"), dict) else {},
        "excerpt_sha256": None,
    }

    text_parts = [
        answer.get("direct_answer"),
        answer.get("risk_if_skipped"),
        answer.get("next_action"),
    ]
    text = "\n".join(str(x or "") for x in text_parts)

    values: list[dict[str, Any]] = []
    values.extend(extract_money_values(text, item=pseudo_item, context_type="answer_synthesis"))
    values.extend(extract_percent_values(text, item=pseudo_item, context_type="answer_synthesis"))
    values.extend(extract_date_values(text, item=pseudo_item, context_type="answer_synthesis"))
    values.extend(extract_status_values(text, item=pseudo_item, context_type="answer_synthesis"))
    values.extend(extract_ratio_values(text, item=pseudo_item, context_type="answer_synthesis"))

    return finalize_value_ids(values)


def group_values(values: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for value in values:
        value_type = str(value.get("value_type"))
        unit = str(value.get("unit") or "")
        entities = value.get("entities") or ["GENERAL"]
        if not isinstance(entities, list):
            entities = ["GENERAL"]

        for entity in entities:
            groups[(str(entity), value_type, unit)].append(value)

    return groups


def numeric_conflict(values: list[dict[str, Any]], delta_abs: float, delta_pct: float) -> tuple[bool, dict[str, Any]]:
    nums = []
    for value in values:
        try:
            nums.append(float(value.get("canonical_value")))
        except Exception:
            continue

    unique = sorted(set(round(x, 6) for x in nums))
    if len(unique) <= 1:
        return False, {"unique_values": unique}

    min_v = min(unique)
    max_v = max(unique)
    abs_delta = abs(max_v - min_v)
    pct_delta = abs_delta / max(abs(min_v), 1.0)

    conflict = abs_delta >= delta_abs and pct_delta >= delta_pct
    return conflict, {
        "unique_values": unique,
        "min_value": min_v,
        "max_value": max_v,
        "absolute_delta": round(abs_delta, 6),
        "relative_delta": round(pct_delta, 6),
    }


def categorical_conflict(values: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    vals = sorted(set(str(v.get("canonical_value")) for v in values if v.get("canonical_value") not in [None, ""]))
    if len(vals) <= 1:
        return False, {"unique_values": vals}

    for pair in CONTRADICTORY_STATUS_PAIRS:
        if pair.issubset(set(vals)):
            return True, {"unique_values": vals, "contradictory_pair": sorted(pair)}

    # Multiple status values still create review issue if same entity.
    return True, {"unique_values": vals, "contradictory_pair": None}


def date_conflict(values: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
    vals = sorted(set(str(v.get("canonical_value")) for v in values if v.get("canonical_value") not in [None, ""]))
    if len(vals) <= 1:
        return False, {"unique_values": vals}

    return True, {"unique_values": vals}


def severity_for_conflict(entity: str, value_type: str, stats: dict[str, Any], strict: bool) -> str:
    strategic_entities = {"CAPEX", "DSCR", "IRR", "NPV", "WACC", "LOAN", "EQUITY", "GRANT", "EIB", "EBRD", "IFC", "CONTRACT", "PERMIT", "SSOT"}

    if value_type == "STATUS":
        pair = stats.get("contradictory_pair")
        if pair:
            return SEVERITY_HIGH if entity in strategic_entities else SEVERITY_MEDIUM
        return SEVERITY_MEDIUM if strict else SEVERITY_LOW

    if value_type == "MONEY":
        abs_delta = safe_float(stats.get("absolute_delta"), 0.0)
        if abs_delta >= 1_000_000:
            return SEVERITY_HIGH if entity in strategic_entities else SEVERITY_MEDIUM
        return SEVERITY_MEDIUM if entity in strategic_entities else SEVERITY_LOW

    if value_type == "PERCENT":
        abs_delta = safe_float(stats.get("absolute_delta"), 0.0)
        if abs_delta >= 5:
            return SEVERITY_HIGH if entity in strategic_entities else SEVERITY_MEDIUM
        return SEVERITY_MEDIUM if entity in strategic_entities else SEVERITY_LOW

    if value_type == "RATIO":
        abs_delta = safe_float(stats.get("absolute_delta"), 0.0)
        if abs_delta >= 0.20:
            return SEVERITY_HIGH if entity in strategic_entities else SEVERITY_MEDIUM
        return SEVERITY_MEDIUM if entity in strategic_entities else SEVERITY_LOW

    if value_type == "DATE":
        return SEVERITY_MEDIUM if entity in strategic_entities else SEVERITY_LOW

    return SEVERITY_LOW


def build_conflict_id(entity: str, value_type: str, unit: str, values: list[dict[str, Any]], stats: dict[str, Any]) -> str:
    raw = json.dumps({
        "entity": entity,
        "value_type": value_type,
        "unit": unit,
        "unique_values": stats.get("unique_values"),
        "sources": sorted(set(str(v.get("source_path")) for v in values if v.get("source_path"))),
        "chunks": sorted(set(str(v.get("chunk_id")) for v in values if v.get("chunk_id"))),
    }, sort_keys=True, ensure_ascii=False)
    return "CONFLICT-" + sha256_text(raw)[:16]


def make_conflict(entity: str, value_type: str, unit: str, values: list[dict[str, Any]], stats: dict[str, Any], strict: bool) -> dict[str, Any]:
    severity = severity_for_conflict(entity=entity, value_type=value_type, stats=stats, strict=strict)

    sources = sorted(set(str(v.get("source_path")) for v in values if v.get("source_path")))
    chunks = sorted(set(str(v.get("chunk_id")) for v in values if v.get("chunk_id")))

    context_samples = []
    seen = set()
    for value in values:
        ctx = value.get("context")
        if not ctx:
            continue
        h = sha256_text(ctx)[:16]
        if h in seen:
            continue
        seen.add(h)
        context_samples.append({
            "raw_value": value.get("raw_value"),
            "canonical_value": value.get("canonical_value"),
            "source_path": value.get("source_path"),
            "chunk_id": value.get("chunk_id"),
            "context": ctx,
        })
        if len(context_samples) >= 5:
            break

    conflict = {
        "conflict_id": "",
        "conflict_type": f"{value_type}_CONFLICT",
        "entity": entity,
        "value_type": value_type,
        "unit": unit,
        "severity": severity,
        "unique_values": stats.get("unique_values"),
        "stats": stats,
        "source_count": len(sources),
        "chunk_count": len(chunks),
        "sources": sources,
        "chunk_ids": chunks,
        "value_ids": [v.get("value_id") for v in values],
        "context_samples": context_samples,
        "recommended_action": recommended_action(entity, value_type, severity),
    }
    conflict["conflict_id"] = build_conflict_id(entity, value_type, unit, values, stats)
    return conflict


def recommended_action(entity: str, value_type: str, severity: str) -> str:
    if severity in {SEVERITY_HIGH, SEVERITY_CRITICAL}:
        return f"Manual SSOT review required before institutional use. Resolve {entity} {value_type} conflict using source hierarchy, document date and authority."

    if value_type in {"MONEY", "PERCENT", "RATIO"}:
        return f"Review values for {entity}; confirm whether different figures refer to different scenarios, years, currencies or versions."

    if value_type == "DATE":
        return f"Review date references for {entity}; confirm whether they represent signing date, deadline, version date or event date."

    if value_type == "STATUS":
        return f"Review status references for {entity}; confirm current authoritative status."

    return "Manual review recommended."


def detect_conflicts(values: list[dict[str, Any]], strict: bool) -> list[dict[str, Any]]:
    groups = group_values(values)
    conflicts: list[dict[str, Any]] = []

    for (entity, value_type, unit), group in groups.items():
        if len(group) <= 1:
            continue

        conflict = False
        stats: dict[str, Any] = {}

        if value_type == "MONEY":
            conflict, stats = numeric_conflict(group, delta_abs=MIN_MONEY_DELTA_ABSOLUTE, delta_pct=MIN_VALUE_DELTA_PERCENT)
        elif value_type == "PERCENT":
            conflict, stats = numeric_conflict(group, delta_abs=MIN_PERCENT_DELTA_ABSOLUTE, delta_pct=0.0)
        elif value_type == "RATIO":
            conflict, stats = numeric_conflict(group, delta_abs=MIN_RATIO_DELTA_ABSOLUTE, delta_pct=0.0)
        elif value_type == "DATE":
            conflict, stats = date_conflict(group)
        elif value_type == "STATUS":
            conflict, stats = categorical_conflict(group)

        if conflict:
            conflicts.append(make_conflict(entity, value_type, unit, group, stats, strict=strict))

    conflicts.sort(key=lambda c: (severity_rank(c.get("severity")), c.get("source_count", 0), c.get("chunk_count", 0)), reverse=True)
    return conflicts


def severity_rank(severity: Any) -> int:
    return {
        SEVERITY_CRITICAL: 4,
        SEVERITY_HIGH: 3,
        SEVERITY_MEDIUM: 2,
        SEVERITY_LOW: 1,
    }.get(str(severity), 0)


def citation_report_conflicts(citation_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not citation_report:
        return []

    status = str(citation_report.get("verification_status") or "")
    if status in {"CITATION_VERIFICATION_PASS", "CITATION_VERIFICATION_PASS_WITH_WARNINGS"}:
        return []

    failures = citation_report.get("failures", [])
    warnings = citation_report.get("warnings", [])

    conflict = {
        "conflict_id": "CONFLICT-" + sha256_text("citation_report_" + status)[:16],
        "conflict_type": "CITATION_VERIFICATION_CONFLICT",
        "entity": "CITATION",
        "value_type": "CITATION_STATUS",
        "unit": "STATUS",
        "severity": SEVERITY_HIGH if "FAIL" in status or "NO_EVIDENCE" in status else SEVERITY_MEDIUM,
        "unique_values": [status],
        "stats": {
            "failures": failures,
            "warnings": warnings,
        },
        "source_count": 1,
        "chunk_count": 0,
        "sources": ["citation_verification_report.json"],
        "chunk_ids": [],
        "value_ids": [],
        "context_samples": [],
        "recommended_action": "Fix citation verification issues before institutional use.",
    }
    return [conflict]


def summarize(conflicts: list[dict[str, Any]], values: list[dict[str, Any]], citation_report: dict[str, Any] | None) -> dict[str, Any]:
    by_type: dict[str, int] = defaultdict(int)
    by_entity: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    value_type_counts: dict[str, int] = defaultdict(int)

    for conflict in conflicts:
        by_type[str(conflict.get("conflict_type"))] += 1
        by_entity[str(conflict.get("entity"))] += 1
        by_severity[str(conflict.get("severity"))] += 1

    for value in values:
        value_type_counts[str(value.get("value_type"))] += 1

    high_or_critical = by_severity.get(SEVERITY_HIGH, 0) + by_severity.get(SEVERITY_CRITICAL, 0)

    if high_or_critical > 0:
        institutional_status = STATUS_HIGH_CONFLICT_RISK
    elif conflicts:
        institutional_status = STATUS_CONFLICTS_DETECTED
    elif not values:
        institutional_status = STATUS_INVALID_INPUT
    else:
        institutional_status = STATUS_NO_CONFLICTS

    return {
        "institutional_status": institutional_status,
        "total_conflicts": len(conflicts),
        "high_or_critical_conflicts": high_or_critical,
        "values_extracted": len(values),
        "citation_report_available": citation_report is not None,
        "by_conflict_type": dict(sorted(by_type.items())),
        "by_entity": dict(sorted(by_entity.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "value_type_counts": dict(sorted(value_type_counts.items())),
    }


def build_report(evidence_pack: dict[str, Any], answer: dict[str, Any] | None, citation_report: dict[str, Any] | None, paths: ConflictPaths, strict: bool) -> dict[str, Any]:
    evidence = get_evidence(evidence_pack)
    evidence_values = extract_values_from_evidence(evidence)
    answer_values = extract_values_from_answer(answer or {})
    values = evidence_values + answer_values

    conflicts = detect_conflicts(values, strict=strict)
    conflicts.extend(citation_report_conflicts(citation_report))

    # Sort again after citation conflicts.
    conflicts.sort(key=lambda c: (severity_rank(c.get("severity")), c.get("source_count", 0), c.get("chunk_count", 0)), reverse=True)

    summary = summarize(conflicts=conflicts, values=values, citation_report=citation_report)

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "CONFLICT_DETECTION_REVIEW_CANDIDATES_AUDIT_LOCKED",
        "strict_mode": strict,
        "query": evidence_pack.get("query") or (answer or {}).get("query"),
        "inputs": {
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "citation_report": str(paths.citation_report),
            "answer_available": answer is not None,
            "citation_report_available": citation_report is not None,
        },
        "summary": summary,
        "conflicts": conflicts,
        "values": values,
        "hashes": {
            "evidence_pack_canonical_sha256": sha256_json(evidence_pack),
            "answer_canonical_sha256": sha256_json(answer) if answer else None,
            "citation_report_canonical_sha256": sha256_json(citation_report) if citation_report else None,
            "evidence_pack_declared_sha256": evidence_pack.get("evidence_pack_sha256"),
            "answer_declared_sha256": (answer or {}).get("answer_sha256"),
        },
        "governance_rule": {
            "conflict_is_candidate_not_final_truth": True,
            "manual_ssot_review_required": True,
            "source_hierarchy_required_for_resolution": True,
            "document_date_and_authority_required_for_resolution": True,
            "source_files_remain_authoritative": True,
        },
    }

    report["conflict_report_sha256"] = sha256_json(report)
    return report


def write_csv(path: Path, conflicts: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "conflict_id",
        "conflict_type",
        "entity",
        "value_type",
        "unit",
        "severity",
        "unique_values",
        "source_count",
        "chunk_count",
        "sources",
        "chunk_ids",
        "recommended_action",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for conflict in conflicts:
            row = dict(conflict)
            row["unique_values"] = json.dumps(conflict.get("unique_values"), ensure_ascii=False)
            row["sources"] = "; ".join(conflict.get("sources", []))
            row["chunk_ids"] = "; ".join(conflict.get("chunk_ids", []))
            writer.writerow(row)


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def conflicts_table_md(conflicts: list[dict[str, Any]]) -> str:
    if not conflicts:
        return "No conflicts detected."

    lines = [
        "| Severity | Type | Entity | Values | Sources | Chunks | Action |",
        "|---|---|---|---|---:|---:|---|",
    ]

    for conflict in conflicts:
        values = json.dumps(conflict.get("unique_values"), ensure_ascii=False)
        if len(values) > 250:
            values = values[:250] + " ..."
        lines.append(
            f"| {md_escape(conflict.get('severity'))} | "
            f"{md_escape(conflict.get('conflict_type'))} | "
            f"{md_escape(conflict.get('entity'))} | "
            f"{md_escape(values)} | "
            f"{conflict.get('source_count')} | "
            f"{conflict.get('chunk_count')} | "
            f"{md_escape(conflict.get('recommended_action'))} |"
        )

    return "\n".join(lines)


def conflict_samples_md(conflicts: list[dict[str, Any]]) -> str:
    if not conflicts:
        return "No context samples."

    sections = []
    for conflict in conflicts[:10]:
        samples = conflict.get("context_samples", [])
        if not samples:
            continue

        sample_lines = []
        for sample in samples[:3]:
            sample_lines.append(
                f"- `{sample.get('source_path')}` | chunk `{sample.get('chunk_id')}` | "
                f"value `{sample.get('raw_value')}` → {sample.get('context')}"
            )

        sections.append(
            f"### {conflict.get('conflict_id')} — {conflict.get('entity')} / {conflict.get('value_type')}\n\n"
            + "\n".join(sample_lines)
        )

    return "\n\n".join(sections) if sections else "No context samples."


def report_to_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    return f"""# TITAN RAG Conflict Detection Report

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Institutional Status | {summary.get("institutional_status")} |
| Query | {md_escape(report.get("query"))} |
| Strict Mode | {report.get("strict_mode")} |
| Total Conflicts | {summary.get("total_conflicts")} |
| High/Critical Conflicts | {summary.get("high_or_critical_conflicts")} |
| Values Extracted | {summary.get("values_extracted")} |
| Citation Report Available | {summary.get("citation_report_available")} |
| Report SHA-256 | `{report.get("conflict_report_sha256")}` |

---

## 2. Distribution

```json
{json.dumps({
    "by_conflict_type": summary.get("by_conflict_type"),
    "by_entity": summary.get("by_entity"),
    "by_severity": summary.get("by_severity"),
    "value_type_counts": summary.get("value_type_counts"),
}, indent=2, ensure_ascii=False)}
```

---

## 3. Conflicts

{conflicts_table_md(report.get("conflicts", []))}

---

## 4. Context Samples

{conflict_samples_md(report.get("conflicts", []))}

---

## 5. Hashes

```json
{json.dumps(report.get("hashes", {}), indent=2, ensure_ascii=False)}
```

---

## 6. Governance Rule

```text
Conflict is candidate, not final truth.
Manual SSOT review is required.
Resolve by source hierarchy, document date, authority, and canonical model.
Source files remain authoritative.
```
"""


def print_summary(report: dict[str, Any], paths: ConflictPaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    print("=" * 100)
    print("TITAN RAG CONFLICT DETECTOR v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Institutional status:     {summary.get('institutional_status')}")
    print(f"Query:                    {report.get('query')}")
    print(f"Values extracted:          {summary.get('values_extracted')}")
    print(f"Total conflicts:           {summary.get('total_conflicts')}")
    print(f"High/Critical conflicts:   {summary.get('high_or_critical_conflicts')}")
    print("-" * 100)
    print(f"Report JSON:               {paths.output_json}")
    print(f"Report Markdown:           {paths.output_md}")
    print(f"Report CSV:                {paths.output_csv}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 14 — conflict detector.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--evidence-pack", default=None, help="Optional latest_evidence_pack.json path.")
    parser.add_argument("--answer-json", default=None, help="Optional latest_rag_answer.json path.")
    parser.add_argument("--citation-report", default=None, help="Optional citation_verification_report.json path.")
    parser.add_argument("--strict", action="store_true", help="Stricter severity classification.")
    parser.add_argument("--print", action="store_true", help="Print Markdown report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        evidence_arg=args.evidence_pack,
        answer_arg=args.answer_json,
        citation_arg=args.citation_report,
    )

    try:
        evidence_pack = require_json(paths.evidence_pack)
        answer = load_json_if_exists(paths.answer_json)
        citation_report = load_json_if_exists(paths.citation_report)

        report = build_report(
            evidence_pack=evidence_pack,
            answer=answer,
            citation_report=citation_report,
            paths=paths,
            strict=bool(args.strict),
        )

        markdown = report_to_markdown(report)

        write_json(paths.output_json, report)
        write_text(paths.output_md, markdown)
        write_csv(paths.output_csv, report.get("conflicts", []))

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "CONFLICT_DETECTION_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "institutional_status": (report.get("summary") or {}).get("institutional_status"),
            "summary": report.get("summary"),
            "report_sha256": report.get("conflict_report_sha256"),
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
            "event": "CONFLICT_DETECTION_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "citation_report": str(paths.citation_report),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG CONFLICT DETECTOR FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
