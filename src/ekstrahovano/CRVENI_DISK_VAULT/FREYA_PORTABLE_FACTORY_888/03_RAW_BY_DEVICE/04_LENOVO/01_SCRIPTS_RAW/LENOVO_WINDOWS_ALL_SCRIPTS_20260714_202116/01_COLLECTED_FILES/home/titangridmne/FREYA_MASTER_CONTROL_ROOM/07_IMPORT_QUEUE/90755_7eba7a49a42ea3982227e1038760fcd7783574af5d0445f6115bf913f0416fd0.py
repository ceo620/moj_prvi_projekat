#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15_ssot_candidate_extractor.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 15 — SSOT Candidate Extractor
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Extract Single Source of Truth (SSOT) candidates from:
- latest_evidence_pack.json
- latest_rag_answer.json
- conflict_report.json

This script does NOT lock final truth.
This script does NOT overwrite a master SSOT register.
This script does NOT resolve conflicts automatically.
It creates traceable SSOT candidate records for manual review or later SSOT locking.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/latest_evidence_pack.json
05_reports/latest_rag_answer.json                 # optional but recommended
05_reports/conflict_report.json                   # optional but recommended
05_reports/citation_verification_report.json      # optional

Outputs
-------
05_reports/ssot_candidates.jsonl
05_reports/ssot_candidates.csv
05_reports/ssot_candidates_report.json
05_reports/ssot_candidates_report.md
06_logs/ssot_candidate_extractor_audit.jsonl
06_logs/ssot_candidate_extractor_errors.jsonl

Designed for compatibility with:
16_financial_signal_extractor.py
17_risk_signal_extractor.py
18_document_priority_ranker.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\15_ssot_candidate_extractor.py" --print

Strict mode
-----------
python ".\\08_scripts\\15_ssot_candidate_extractor.py" --strict --print
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
from typing import Any, Iterable


SCRIPT_NAME = "15_ssot_candidate_extractor.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
INPUT_ANSWER_JSON = Path("05_reports") / "latest_rag_answer.json"
INPUT_CONFLICT_REPORT = Path("05_reports") / "conflict_report.json"
INPUT_CITATION_REPORT = Path("05_reports") / "citation_verification_report.json"

OUTPUT_JSONL = Path("05_reports") / "ssot_candidates.jsonl"
OUTPUT_CSV = Path("05_reports") / "ssot_candidates.csv"
OUTPUT_REPORT_JSON = Path("05_reports") / "ssot_candidates_report.json"
OUTPUT_REPORT_MD = Path("05_reports") / "ssot_candidates_report.md"

AUDIT_LOG = Path("06_logs") / "ssot_candidate_extractor_audit.jsonl"
ERROR_LOG = Path("06_logs") / "ssot_candidate_extractor_errors.jsonl"

STATUS_LOCK_CANDIDATE = "LOCK_CANDIDATE"
STATUS_DRAFT_HIGH_CONFIDENCE = "DRAFT_HIGH_CONFIDENCE"
STATUS_DRAFT = "DRAFT"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_WEAK_REVIEW_REQUIRED = "WEAK_REVIEW_REQUIRED"
STATUS_CONFLICT_BLOCKED = "CONFLICT_BLOCKED"

REPORT_READY = "SSOT_CANDIDATES_READY"
REPORT_REVIEW_REQUIRED = "SSOT_REVIEW_REQUIRED"
REPORT_CONFLICT_BLOCKED = "SSOT_CONFLICT_BLOCKED"
REPORT_NO_CANDIDATES = "NO_SSOT_CANDIDATES"

MIN_LOCK_SCORE = 0.72
MIN_DRAFT_HIGH_SCORE = 0.58
MIN_DRAFT_SCORE = 0.40

VALUE_TYPES = ["EUR_AMOUNT", "PERCENT", "DATE", "RATIO", "STATUS", "TEXT_VALUE"]

ENTITY_PATTERNS = {
    "CAPEX": [r"\bcapex\b", r"\bcapital expenditure\b", r"\binvestment cost\b"],
    "OPEX": [r"\bopex\b", r"\boperating cost\b"],
    "DSCR": [r"\bdscr\b", r"\bdebt service coverage\b"],
    "IRR": [r"\birr\b", r"\binternal rate of return\b"],
    "NPV": [r"\bnpv\b", r"\bnet present value\b"],
    "WACC": [r"\bwacc\b", r"\bweighted average cost"],
    "LOAN": [r"\bloan\b", r"\bdebt\b", r"\bcredit facility\b", r"\bdebt facility\b"],
    "EQUITY": [r"\bequity\b", r"\bshare capital\b"],
    "GRANT": [r"\bgrant\b", r"\bsubsidy\b"],
    "EIB": [r"\beib\b", r"\beuropean investment bank\b"],
    "EBRD": [r"\bebrd\b", r"\beuropean bank for reconstruction"],
    "IFC": [r"\bifc\b", r"\binternational finance corporation\b"],
    "CONTRACT": [r"\bcontract\b", r"\bagreement\b", r"\bugovor\b"],
    "PERMIT": [r"\bpermit\b", r"\blicen[cs]e\b", r"\bdozvol"],
    "DEADLINE": [r"\bdeadline\b", r"\bdue date\b", r"\bmilestone\b", r"\brok\b"],
    "DOCUMENT_STATUS": [r"\bstatus\b", r"\bapproved\b", r"\brejected\b", r"\bsigned\b", r"\bunsigned\b", r"\bdraft\b"],
    "OWNER": [r"\bowner\b", r"\bresponsible\b", r"\bprepared by\b", r"\bvlasnik\b", r"\bodgovoran"],
    "PROJECT_NAME": [r"\bproject\b", r"\bprojekat\b", r"\btitan\b"],
    "SSOT": [r"\bssot\b", r"\bsource of truth\b", r"\bcanonical\b"],
}

STRATEGIC_ENTITIES = {
    "CAPEX", "OPEX", "DSCR", "IRR", "NPV", "WACC", "LOAN", "EQUITY", "GRANT",
    "EIB", "EBRD", "IFC", "CONTRACT", "PERMIT", "DEADLINE", "DOCUMENT_STATUS",
    "OWNER", "PROJECT_NAME", "SSOT",
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

TEXT_VALUE_PATTERNS = {
    "OWNER": [
        r"(?:owner|responsible|prepared by|vlasnik|odgovoran)\s*[:=-]\s*(?P<value>[A-ZČĆŽŠĐA-Za-zčćžšđ0-9 .,_/-]{3,80})",
    ],
    "PROJECT_NAME": [
        r"(?:project name|project|projekat|naziv projekta)\s*[:=-]\s*(?P<value>[A-ZČĆŽŠĐA-Za-zčćžšđ0-9 .,_/-]{3,120})",
    ],
    "CONTRACT": [
        r"(?:contract no\.?|agreement no\.?|ugovor br\.?)\s*[:=-]\s*(?P<value>[A-Z0-9._/-]{3,80})",
    ],
    "PERMIT": [
        r"(?:permit no\.?|license no\.?|dozvola br\.?)\s*[:=-]\s*(?P<value>[A-Z0-9._/-]{3,80})",
    ],
}


@dataclass(frozen=True)
class SSOTPaths:
    base_dir: Path
    evidence_pack: Path
    answer_json: Path
    conflict_report: Path
    citation_report: Path
    output_jsonl: Path
    output_csv: Path
    output_report_json: Path
    output_report_md: Path
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


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


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def resolve_paths(
    base_dir: Path,
    evidence_arg: str | None,
    answer_arg: str | None,
    conflict_arg: str | None,
    citation_arg: str | None,
) -> SSOTPaths:
    return SSOTPaths(
        base_dir=base_dir,
        evidence_pack=Path(evidence_arg) if evidence_arg else base_dir / INPUT_EVIDENCE_PACK,
        answer_json=Path(answer_arg) if answer_arg else base_dir / INPUT_ANSWER_JSON,
        conflict_report=Path(conflict_arg) if conflict_arg else base_dir / INPUT_CONFLICT_REPORT,
        citation_report=Path(citation_arg) if citation_arg else base_dir / INPUT_CITATION_REPORT,
        output_jsonl=base_dir / OUTPUT_JSONL,
        output_csv=base_dir / OUTPUT_CSV,
        output_report_json=base_dir / OUTPUT_REPORT_JSON,
        output_report_md=base_dir / OUTPUT_REPORT_MD,
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


def get_score(item: dict[str, Any]) -> float:
    scores = item.get("scores")
    if isinstance(scores, dict):
        return safe_float(scores.get("final_score"), 0.0)
    return 0.0


def parse_number(text: str) -> float | None:
    value = str(text or "").strip()
    if not value:
        return None

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        parts = value.split(",")
        if len(parts) == 2 and len(parts[-1]) in {1, 2, 3}:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")
    else:
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


def context_window(text: str, start: int, end: int, chars: int = 220) -> str:
    left = max(0, start - chars)
    right = min(len(text), end + chars)
    return normalize_inline(text[left:right])


def detect_entities(text: str) -> list[str]:
    lower = text.lower()
    entities: list[str] = []

    for entity, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                entities.append(entity)
                break

    return sorted(set(entities))


def candidate_id(payload: dict[str, Any]) -> str:
    raw = json.dumps({
        "entity": payload.get("Entity_Name"),
        "value_type": payload.get("Value_Type"),
        "canonical": payload.get("Canonical_Value"),
        "source": payload.get("Source_Path"),
        "chunk": payload.get("Chunk_ID"),
        "context_hash": sha256_text(str(payload.get("Context") or ""))[:16],
    }, sort_keys=True, ensure_ascii=False)
    return "SSOT-" + sha256_text(raw)[:18]


def make_candidate(
    entity: str,
    value_type: str,
    canonical_value: Any,
    raw_value: Any,
    unit: str,
    context: str,
    item: dict[str, Any],
    extraction_rule: str,
) -> dict[str, Any]:
    score = get_score(item)
    confidence = calculate_candidate_confidence(
        score=score,
        entity=entity,
        value_type=value_type,
        source_path=item.get("source_path"),
        context=context,
    )

    record = {
        "Candidate_ID": "",
        "Created_At": utc_now_iso(),
        "Script": SCRIPT_NAME,
        "Script_Version": SCRIPT_VERSION,
        "Entity_Name": entity,
        "Value_Type": value_type,
        "Canonical_Value": canonical_value,
        "Raw_Value": raw_value,
        "Unit": unit,
        "Confidence_Score": confidence,
        "SSOT_Status": "UNCLASSIFIED",
        "Conflict_Flag": False,
        "Conflict_IDs": "",
        "Source_Path": item.get("source_path"),
        "File_Name": item.get("file_name"),
        "Chunk_ID": item.get("chunk_id"),
        "Section_Label": item.get("section_label"),
        "Evidence_Rank": item.get("rank"),
        "Evidence_Score": score,
        "Context": context,
        "Extraction_Rule": extraction_rule,
        "Recommended_Action": "",
    }

    record["Candidate_ID"] = candidate_id(record)
    return record


def calculate_candidate_confidence(score: float, entity: str, value_type: str, source_path: Any, context: str) -> float:
    confidence = score * 0.72

    if entity in STRATEGIC_ENTITIES:
        confidence += 0.08

    if value_type in {"EUR_AMOUNT", "PERCENT", "DATE", "RATIO", "STATUS"}:
        confidence += 0.06

    lower_path = str(source_path or "").lower()
    if any(marker in lower_path for marker in ["vdr", "eib", "ebrd", "ifc", "ssot", "audit", "control_tower", "control tower", "legal", "contract", "financial"]):
        confidence += 0.06

    lower_context = context.lower()
    if any(marker in lower_context for marker in ["signed", "approved", "final", "confirmed", "audited", "official", "potpisan", "odobren"]):
        confidence += 0.05

    if any(marker in lower_context for marker in ["draft", "estimate", "assumption", "unverified", "missing", "not signed", "nepotpisan"]):
        confidence -= 0.10

    return round(min(max(confidence, 0.0), 1.0), 6)


def extract_money_candidates(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for match in MONEY_RE.finditer(text):
        raw = match.group(0).strip()
        prefix = match.group("prefix")
        suffix = match.group("suffix")
        number = parse_number(match.group("number"))

        if number is None:
            continue

        # Avoid all plain numbers as money.
        if not prefix and not suffix:
            continue

        amount, currency = scale_money(number, prefix, suffix)
        context = context_window(text, match.start(), match.end())
        entities = detect_entities(context) or ["GENERAL"]

        for entity in entities:
            if entity == "GENERAL" and currency == "UNKNOWN":
                continue

            records.append(make_candidate(
                entity=entity,
                value_type="EUR_AMOUNT" if currency == "EUR" else "MONEY_AMOUNT",
                canonical_value=round(amount, 2),
                raw_value=raw,
                unit=currency,
                context=context,
                item=item,
                extraction_rule="money_regex_context_entity",
            ))

    return records


def extract_percent_candidates(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for match in PERCENT_RE.finditer(text):
        raw = match.group(0).strip()
        number = parse_number(match.group("number"))
        if number is None:
            continue

        context = context_window(text, match.start(), match.end())
        entities = detect_entities(context) or ["GENERAL"]

        for entity in entities:
            records.append(make_candidate(
                entity=entity,
                value_type="PERCENT",
                canonical_value=round(number, 4),
                raw_value=raw,
                unit="%",
                context=context,
                item=item,
                extraction_rule="percent_regex_context_entity",
            ))

    return records


def extract_date_candidates(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for match in DATE_RE.finditer(text):
        raw = match.group(0).strip()
        context = context_window(text, match.start(), match.end())
        entities = detect_entities(context) or ["DATE"]

        for entity in entities:
            records.append(make_candidate(
                entity=entity,
                value_type="DATE",
                canonical_value=normalize_date(raw),
                raw_value=raw,
                unit="DATE",
                context=context,
                item=item,
                extraction_rule="date_regex_context_entity",
            ))

    return records


def extract_status_candidates(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    lower = text.lower()

    for status, patterns in STATUS_TERMS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, lower, flags=re.IGNORECASE):
                raw = text[match.start():match.end()]
                context = context_window(text, match.start(), match.end())
                entities = detect_entities(context) or ["DOCUMENT_STATUS"]

                for entity in entities:
                    records.append(make_candidate(
                        entity=entity,
                        value_type="STATUS",
                        canonical_value=status,
                        raw_value=raw,
                        unit="STATUS",
                        context=context,
                        item=item,
                        extraction_rule="status_regex_context_entity",
                    ))

    return records


def extract_ratio_candidates(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    lower = text.lower()

    if not any(marker in lower for marker in ["dscr", "coverage", "ratio", "wacc", "irr", "npv"]):
        return records

    for match in re.finditer(r"\b\d{1,2}(?:[.,]\d{1,4})?\s*x\b|\b\d{1,2}(?:[.,]\d{1,4})\b", text, flags=re.IGNORECASE):
        raw = match.group(0).strip()
        num_text = raw.lower().replace("x", "").strip()
        number = parse_number(num_text)
        if number is None or number <= 0 or number > 100:
            continue

        context = context_window(text, match.start(), match.end())
        entities = detect_entities(context) or ["RATIO"]

        for entity in entities:
            if entity not in {"DSCR", "IRR", "NPV", "WACC", "LOAN", "GENERAL", "RATIO"}:
                continue

            records.append(make_candidate(
                entity=entity,
                value_type="RATIO",
                canonical_value=round(number, 6),
                raw_value=raw,
                unit="RATIO",
                context=context,
                item=item,
                extraction_rule="ratio_regex_financial_context",
            ))

    return records


def extract_text_value_candidates(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for entity, patterns in TEXT_VALUE_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                raw_value = normalize_inline(match.group("value"))
                if len(raw_value) < 3:
                    continue
                context = context_window(text, match.start(), match.end())

                records.append(make_candidate(
                    entity=entity,
                    value_type="TEXT_VALUE",
                    canonical_value=raw_value[:180],
                    raw_value=raw_value,
                    unit="TEXT",
                    context=context,
                    item=item,
                    extraction_rule="text_value_key_value_regex",
                ))

    return records


def extract_candidates_from_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for item in evidence:
        text = normalize_text(item.get("excerpt"))
        if not text:
            continue

        records.extend(extract_money_candidates(text, item))
        records.extend(extract_percent_candidates(text, item))
        records.extend(extract_date_candidates(text, item))
        records.extend(extract_status_candidates(text, item))
        records.extend(extract_ratio_candidates(text, item))
        records.extend(extract_text_value_candidates(text, item))

    return records


def extract_candidates_from_answer(answer: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not answer:
        return []

    pseudo_item = {
        "source_path": "latest_rag_answer.json",
        "file_name": "latest_rag_answer.json",
        "chunk_id": "ANSWER_SYNTHESIS",
        "section_label": "direct_answer",
        "rank": None,
        "scores": {"final_score": safe_float((answer.get("confidence") or {}).get("confidence_score"), 0.0)} if isinstance(answer.get("confidence"), dict) else {},
    }

    text = "\n".join(str(answer.get(k) or "") for k in ["direct_answer", "risk_if_skipped", "next_action"])
    if not text.strip():
        return []

    records: list[dict[str, Any]] = []
    records.extend(extract_money_candidates(text, pseudo_item))
    records.extend(extract_percent_candidates(text, pseudo_item))
    records.extend(extract_date_candidates(text, pseudo_item))
    records.extend(extract_status_candidates(text, pseudo_item))
    records.extend(extract_ratio_candidates(text, pseudo_item))
    records.extend(extract_text_value_candidates(text, pseudo_item))

    for record in records:
        record["Extraction_Rule"] = "answer_synthesis_" + str(record.get("Extraction_Rule"))

    return records


def conflict_index(conflict_report: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)

    if not conflict_report:
        return output

    conflicts = conflict_report.get("conflicts", [])
    if not isinstance(conflicts, list):
        return output

    for conflict in conflicts:
        if not isinstance(conflict, dict):
            continue

        entity = str(conflict.get("entity") or "")
        value_type = str(conflict.get("value_type") or "")

        output[entity].append(conflict)
        output[f"{entity}:{value_type}"].append(conflict)

        for chunk_id in conflict.get("chunk_ids", []) if isinstance(conflict.get("chunk_ids"), list) else []:
            output[f"CHUNK:{chunk_id}"].append(conflict)

        for source in conflict.get("sources", []) if isinstance(conflict.get("sources"), list) else []:
            output[f"SOURCE:{source}"].append(conflict)

    return output


def apply_conflict_flags(candidates: list[dict[str, Any]], conflict_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    idx = conflict_index(conflict_report)

    for cand in candidates:
        entity = str(cand.get("Entity_Name") or "")
        value_type = str(cand.get("Value_Type") or "")
        chunk_id = str(cand.get("Chunk_ID") or "")
        source = str(cand.get("Source_Path") or "")

        found: list[dict[str, Any]] = []
        for key in [entity, f"{entity}:{value_type}", f"CHUNK:{chunk_id}", f"SOURCE:{source}"]:
            found.extend(idx.get(key, []))

        # Deduplicate by conflict_id.
        seen = set()
        unique = []
        for c in found:
            cid = c.get("conflict_id")
            if cid in seen:
                continue
            seen.add(cid)
            unique.append(c)

        if unique:
            cand["Conflict_Flag"] = True
            cand["Conflict_IDs"] = "; ".join(str(c.get("conflict_id")) for c in unique if c.get("conflict_id"))
        else:
            cand["Conflict_Flag"] = False
            cand["Conflict_IDs"] = ""

    return candidates


def citation_status(citation_report: dict[str, Any] | None) -> str:
    if not citation_report:
        return "NOT_AVAILABLE"
    return str(citation_report.get("verification_status") or "UNKNOWN")


def classify_candidate(candidate: dict[str, Any], citation_report: dict[str, Any] | None, strict: bool) -> dict[str, Any]:
    confidence = safe_float(candidate.get("Confidence_Score"), 0.0)
    conflict = bool(candidate.get("Conflict_Flag"))
    cite_status = citation_status(citation_report)
    context = str(candidate.get("Context") or "").lower()

    if conflict:
        status = STATUS_CONFLICT_BLOCKED
        action = "Resolve conflict in Step 14 before SSOT locking."
    elif cite_status in {"CITATION_VERIFICATION_FAIL", "NO_EVIDENCE_NO_CITATION", "CITATION_REVIEW_REQUIRED"}:
        status = STATUS_REVIEW_REQUIRED
        action = "Fix citation verification before SSOT review."
    elif any(marker in context for marker in ["draft", "estimate", "assumption", "unverified", "not signed", "nepotpisan"]):
        status = STATUS_REVIEW_REQUIRED
        action = "Manual review required because context contains draft/estimate/unverified language."
    elif confidence >= MIN_LOCK_SCORE and not strict:
        status = STATUS_LOCK_CANDIDATE
        action = "Eligible for SSOT lock review; verify source authority and date."
    elif confidence >= MIN_LOCK_SCORE and strict and cite_status == "CITATION_VERIFICATION_PASS":
        status = STATUS_LOCK_CANDIDATE
        action = "Eligible for strict SSOT lock review; verify source authority and date."
    elif confidence >= MIN_DRAFT_HIGH_SCORE:
        status = STATUS_DRAFT_HIGH_CONFIDENCE
        action = "Use as high-confidence draft candidate; validate before lock."
    elif confidence >= MIN_DRAFT_SCORE:
        status = STATUS_DRAFT
        action = "Use as draft candidate only."
    else:
        status = STATUS_WEAK_REVIEW_REQUIRED
        action = "Weak candidate; rerun retrieval or inspect source manually."

    candidate["SSOT_Status"] = status
    candidate["Recommended_Action"] = action
    return candidate


def deduplicate_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}

    for cand in candidates:
        key = json.dumps({
            "entity": cand.get("Entity_Name"),
            "value_type": cand.get("Value_Type"),
            "canonical": cand.get("Canonical_Value"),
            "source": cand.get("Source_Path"),
            "chunk": cand.get("Chunk_ID"),
        }, sort_keys=True, ensure_ascii=False)

        existing = best.get(key)
        if existing is None or safe_float(cand.get("Confidence_Score")) > safe_float(existing.get("Confidence_Score")):
            best[key] = cand

    rows = list(best.values())
    rows.sort(
        key=lambda x: (
            status_rank(str(x.get("SSOT_Status"))),
            safe_float(x.get("Confidence_Score")),
            safe_float(x.get("Evidence_Score")),
        ),
        reverse=True,
    )
    return rows


def status_rank(status: str) -> int:
    return {
        STATUS_LOCK_CANDIDATE: 6,
        STATUS_DRAFT_HIGH_CONFIDENCE: 5,
        STATUS_DRAFT: 4,
        STATUS_REVIEW_REQUIRED: 3,
        STATUS_CONFLICT_BLOCKED: 2,
        STATUS_WEAK_REVIEW_REQUIRED: 1,
    }.get(status, 0)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Candidate_ID",
        "Created_At",
        "Entity_Name",
        "Value_Type",
        "Canonical_Value",
        "Raw_Value",
        "Unit",
        "Confidence_Score",
        "SSOT_Status",
        "Conflict_Flag",
        "Conflict_IDs",
        "Source_Path",
        "File_Name",
        "Chunk_ID",
        "Section_Label",
        "Evidence_Rank",
        "Evidence_Score",
        "Context",
        "Extraction_Rule",
        "Recommended_Action",
        "Script",
        "Script_Version",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["Context"] = normalize_inline(out.get("Context"))
            writer.writerow(out)


def summarize(candidates: list[dict[str, Any]], conflict_report: dict[str, Any] | None, citation_report: dict[str, Any] | None) -> dict[str, Any]:
    by_status: dict[str, int] = defaultdict(int)
    by_entity: dict[str, int] = defaultdict(int)
    by_value_type: dict[str, int] = defaultdict(int)

    for cand in candidates:
        by_status[str(cand.get("SSOT_Status"))] += 1
        by_entity[str(cand.get("Entity_Name"))] += 1
        by_value_type[str(cand.get("Value_Type"))] += 1

    conflict_blocked = by_status.get(STATUS_CONFLICT_BLOCKED, 0)
    review_required = by_status.get(STATUS_REVIEW_REQUIRED, 0) + by_status.get(STATUS_WEAK_REVIEW_REQUIRED, 0)
    lock_candidates = by_status.get(STATUS_LOCK_CANDIDATE, 0)

    if conflict_blocked > 0:
        institutional_status = REPORT_CONFLICT_BLOCKED
    elif review_required > 0:
        institutional_status = REPORT_REVIEW_REQUIRED
    elif candidates:
        institutional_status = REPORT_READY
    else:
        institutional_status = REPORT_NO_CANDIDATES

    return {
        "institutional_status": institutional_status,
        "total_candidates": len(candidates),
        "lock_candidates": lock_candidates,
        "conflict_blocked": conflict_blocked,
        "review_required": review_required,
        "citation_status": citation_status(citation_report),
        "conflict_report_available": conflict_report is not None,
        "citation_report_available": citation_report is not None,
        "by_status": dict(sorted(by_status.items())),
        "by_entity": dict(sorted(by_entity.items())),
        "by_value_type": dict(sorted(by_value_type.items())),
    }


def build_report(
    evidence_pack: dict[str, Any],
    answer: dict[str, Any] | None,
    conflict_report: dict[str, Any] | None,
    citation_report: dict[str, Any] | None,
    candidates: list[dict[str, Any]],
    paths: SSOTPaths,
    strict: bool,
) -> dict[str, Any]:
    summary = summarize(
        candidates=candidates,
        conflict_report=conflict_report,
        citation_report=citation_report,
    )

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "SSOT_CANDIDATE_EXTRACTION_AUDIT_LOCKED",
        "strict_mode": strict,
        "query": evidence_pack.get("query") or (answer or {}).get("query"),
        "inputs": {
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "conflict_report": str(paths.conflict_report),
            "citation_report": str(paths.citation_report),
            "answer_available": answer is not None,
            "conflict_report_available": conflict_report is not None,
            "citation_report_available": citation_report is not None,
        },
        "summary": summary,
        "candidates": candidates,
        "hashes": {
            "evidence_pack_canonical_sha256": sha256_json(evidence_pack),
            "answer_canonical_sha256": sha256_json(answer) if answer else None,
            "conflict_report_canonical_sha256": sha256_json(conflict_report) if conflict_report else None,
            "citation_report_canonical_sha256": sha256_json(citation_report) if citation_report else None,
            "evidence_pack_declared_sha256": evidence_pack.get("evidence_pack_sha256"),
            "answer_declared_sha256": (answer or {}).get("answer_sha256"),
            "conflict_report_declared_sha256": (conflict_report or {}).get("conflict_report_sha256"),
            "citation_report_declared_sha256": (citation_report or {}).get("citation_verification_sha256"),
        },
        "governance_rule": {
            "candidate_is_not_final_truth": True,
            "manual_ssot_lock_required": True,
            "conflict_blocks_ssot_lock": True,
            "citation_verification_required": True,
            "source_files_remain_authoritative": True,
        },
    }

    report["ssot_candidates_report_sha256"] = sha256_json(report)
    return report


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def candidates_table_md(rows: list[dict[str, Any]], limit: int = 120) -> str:
    if not rows:
        return "No SSOT candidates."

    lines = [
        "| Status | Entity | Type | Value | Confidence | Conflict | Source | Chunk | Action |",
        "|---|---|---|---|---:|---:|---|---|---|",
    ]

    for row in rows[:limit]:
        value = md_escape(row.get("Canonical_Value"))
        if len(value) > 160:
            value = value[:160] + " ..."
        lines.append(
            f"| {md_escape(row.get('SSOT_Status'))} | "
            f"{md_escape(row.get('Entity_Name'))} | "
            f"{md_escape(row.get('Value_Type'))} | "
            f"{value} | "
            f"{row.get('Confidence_Score')} | "
            f"{row.get('Conflict_Flag')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"`{md_escape(row.get('Chunk_ID'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )

    return "\n".join(lines)


def report_to_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    return f"""# TITAN RAG SSOT Candidate Report

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Institutional Status | {summary.get("institutional_status")} |
| Query | {md_escape(report.get("query"))} |
| Strict Mode | {report.get("strict_mode")} |
| Total Candidates | {summary.get("total_candidates")} |
| Lock Candidates | {summary.get("lock_candidates")} |
| Conflict Blocked | {summary.get("conflict_blocked")} |
| Review Required | {summary.get("review_required")} |
| Citation Status | {summary.get("citation_status")} |
| Report SHA-256 | `{report.get("ssot_candidates_report_sha256")}` |

---

## 2. Distribution

```json
{json.dumps({
    "by_status": summary.get("by_status"),
    "by_entity": summary.get("by_entity"),
    "by_value_type": summary.get("by_value_type"),
}, indent=2, ensure_ascii=False)}
```

---

## 3. Candidates

{candidates_table_md(report.get("candidates", []))}

---

## 4. Hashes

```json
{json.dumps(report.get("hashes", {}), indent=2, ensure_ascii=False)}
```

---

## 5. Governance Rule

```text
SSOT candidate is not final truth.
Manual SSOT lock is required.
Conflict blocks SSOT lock.
Citation verification is required.
Source files remain authoritative.
```
"""


def print_summary(report: dict[str, Any], paths: SSOTPaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    print("=" * 100)
    print("TITAN RAG SSOT CANDIDATE EXTRACTOR v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Institutional status:  {summary.get('institutional_status')}")
    print(f"Query:                 {report.get('query')}")
    print(f"Total candidates:      {summary.get('total_candidates')}")
    print(f"Lock candidates:       {summary.get('lock_candidates')}")
    print(f"Conflict blocked:      {summary.get('conflict_blocked')}")
    print(f"Review required:       {summary.get('review_required')}")
    print("-" * 100)
    print(f"Candidates JSONL:      {paths.output_jsonl}")
    print(f"Candidates CSV:        {paths.output_csv}")
    print(f"Report JSON:           {paths.output_report_json}")
    print(f"Report Markdown:       {paths.output_report_md}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 15 — SSOT candidate extractor.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--evidence-pack", default=None, help="Optional latest_evidence_pack.json path.")
    parser.add_argument("--answer-json", default=None, help="Optional latest_rag_answer.json path.")
    parser.add_argument("--conflict-report", default=None, help="Optional conflict_report.json path.")
    parser.add_argument("--citation-report", default=None, help="Optional citation_verification_report.json path.")
    parser.add_argument("--strict", action="store_true", help="Strict SSOT candidate classification.")
    parser.add_argument("--print", action="store_true", help="Print Markdown report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        evidence_arg=args.evidence_pack,
        answer_arg=args.answer_json,
        conflict_arg=args.conflict_report,
        citation_arg=args.citation_report,
    )

    try:
        evidence_pack = require_json(paths.evidence_pack)
        answer = load_json_if_exists(paths.answer_json)
        conflict_report = load_json_if_exists(paths.conflict_report)
        citation_report = load_json_if_exists(paths.citation_report)

        evidence = get_evidence(evidence_pack)

        candidates = []
        candidates.extend(extract_candidates_from_evidence(evidence))
        candidates.extend(extract_candidates_from_answer(answer))

        candidates = apply_conflict_flags(candidates, conflict_report)

        classified = [
            classify_candidate(cand, citation_report=citation_report, strict=bool(args.strict))
            for cand in candidates
        ]

        deduped = deduplicate_candidates(classified)

        report = build_report(
            evidence_pack=evidence_pack,
            answer=answer,
            conflict_report=conflict_report,
            citation_report=citation_report,
            candidates=deduped,
            paths=paths,
            strict=bool(args.strict),
        )

        markdown = report_to_markdown(report)

        write_jsonl(paths.output_jsonl, deduped)
        write_csv(paths.output_csv, deduped)
        write_json(paths.output_report_json, report)
        write_text(paths.output_report_md, markdown)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "SSOT_CANDIDATE_EXTRACTION_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "institutional_status": (report.get("summary") or {}).get("institutional_status"),
            "summary": report.get("summary"),
            "report_sha256": report.get("ssot_candidates_report_sha256"),
            "outputs": {
                "jsonl": str(paths.output_jsonl),
                "csv": str(paths.output_csv),
                "report_json": str(paths.output_report_json),
                "report_md": str(paths.output_report_md),
            },
        })

        print_summary(report, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "SSOT_CANDIDATE_EXTRACTION_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "evidence_pack": str(paths.evidence_pack),
            "answer_json": str(paths.answer_json),
            "conflict_report": str(paths.conflict_report),
            "citation_report": str(paths.citation_report),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG SSOT CANDIDATE EXTRACTOR FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
