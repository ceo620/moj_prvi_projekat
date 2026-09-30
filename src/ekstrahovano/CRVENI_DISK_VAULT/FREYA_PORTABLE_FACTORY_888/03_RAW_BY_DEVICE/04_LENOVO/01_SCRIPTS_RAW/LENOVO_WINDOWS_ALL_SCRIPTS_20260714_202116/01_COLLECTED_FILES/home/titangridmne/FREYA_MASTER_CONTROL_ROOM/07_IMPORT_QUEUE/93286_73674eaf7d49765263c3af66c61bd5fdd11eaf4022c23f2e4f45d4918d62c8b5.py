#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16_financial_signal_extractor.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 16 — Financial Signal Extractor
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Extract finance/lender-relevant signals from the latest evidence base:
- CAPEX / OPEX
- Loan / debt / equity / grant
- DSCR / WACC / IRR / NPV
- EBITDA / revenue / margin / interest / repayment
- currency / amount / percent / ratio / dates
- SSOT candidate alignment
- conflict/citation blocking status

This script does NOT decide final truth.
This script does NOT overwrite SSOT.
This script does NOT generate a financial model.
It creates evidence-linked financial signal records for review and Control Tower.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/latest_evidence_pack.json
05_reports/ssot_candidates.jsonl                  # optional but recommended
05_reports/ssot_candidates_report.json            # optional
05_reports/conflict_report.json                   # optional
05_reports/citation_verification_report.json      # optional

Outputs
-------
05_reports/financial_signals.jsonl
05_reports/financial_signals.csv
05_reports/financial_signals_report.json
05_reports/financial_signals_report.md
06_logs/financial_signal_extractor_audit.jsonl
06_logs/financial_signal_extractor_errors.jsonl

Designed for compatibility with:
17_risk_signal_extractor.py
18_document_priority_ranker.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\16_financial_signal_extractor.py" --print

Strict mode
-----------
python ".\\08_scripts\\16_financial_signal_extractor.py" --strict --print
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


SCRIPT_NAME = "16_financial_signal_extractor.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
INPUT_SSOT_JSONL = Path("05_reports") / "ssot_candidates.jsonl"
INPUT_SSOT_REPORT = Path("05_reports") / "ssot_candidates_report.json"
INPUT_CONFLICT_REPORT = Path("05_reports") / "conflict_report.json"
INPUT_CITATION_REPORT = Path("05_reports") / "citation_verification_report.json"

OUTPUT_JSONL = Path("05_reports") / "financial_signals.jsonl"
OUTPUT_CSV = Path("05_reports") / "financial_signals.csv"
OUTPUT_REPORT_JSON = Path("05_reports") / "financial_signals_report.json"
OUTPUT_REPORT_MD = Path("05_reports") / "financial_signals_report.md"

AUDIT_LOG = Path("06_logs") / "financial_signal_extractor_audit.jsonl"
ERROR_LOG = Path("06_logs") / "financial_signal_extractor_errors.jsonl"

STATUS_LOCK_CANDIDATE = "LOCK_CANDIDATE"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_CONFLICT_BLOCKED = "CONFLICT_BLOCKED"
STATUS_DRAFT = "DRAFT"
STATUS_WEAK = "WEAK_SIGNAL"

REPORT_READY = "FINANCIAL_SIGNALS_READY"
REPORT_REVIEW_REQUIRED = "FINANCIAL_REVIEW_REQUIRED"
REPORT_CONFLICT_BLOCKED = "FINANCIAL_CONFLICT_BLOCKED"
REPORT_NO_SIGNALS = "NO_FINANCIAL_SIGNALS"

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

FINANCIAL_CATEGORIES = {
    "CAPEX": [
        r"\bcapex\b", r"\bcapital expenditure\b", r"\binvestment cost\b",
        r"\bconstruction cost\b", r"\bequipment cost\b", r"\bproject cost\b",
    ],
    "OPEX": [
        r"\bopex\b", r"\boperating expense\b", r"\boperating cost\b",
        r"\bmaintenance cost\b", r"\bpersonnel cost\b",
    ],
    "REVENUE": [
        r"\brevenue\b", r"\bsales\b", r"\bturnover\b", r"\bprihod",
    ],
    "EBITDA": [
        r"\bebitda\b", r"\boperating profit\b",
    ],
    "NET_PROFIT": [
        r"\bnet profit\b", r"\bnet income\b", r"\bprofit after tax\b",
    ],
    "DSCR": [
        r"\bdscr\b", r"\bdebt service coverage\b", r"\bcoverage ratio\b",
    ],
    "WACC": [
        r"\bwacc\b", r"\bweighted average cost\b",
    ],
    "IRR": [
        r"\birr\b", r"\binternal rate of return\b",
    ],
    "NPV": [
        r"\bnpv\b", r"\bnet present value\b",
    ],
    "LOAN": [
        r"\bloan\b", r"\bdebt\b", r"\bcredit facility\b", r"\bdebt facility\b",
        r"\bborrowing\b", r"\bfinancing facility\b",
    ],
    "EQUITY": [
        r"\bequity\b", r"\bshare capital\b", r"\bcapital contribution\b",
    ],
    "GRANT": [
        r"\bgrant\b", r"\bsubsidy\b", r"\bincentive\b",
    ],
    "INTEREST_RATE": [
        r"\binterest rate\b", r"\bcoupon\b", r"\bmargin\b", r"\beuribor\b",
    ],
    "MATURITY": [
        r"\bmaturity\b", r"\btenor\b", r"\brepayment period\b",
    ],
    "DEPRECIATION": [
        r"\bdepreciation\b", r"\bamortization\b", r"\basset life\b",
    ],
    "CONTINGENCY": [
        r"\bcontingency\b", r"\brisk reserve\b", r"\breserve\b",
    ],
    "CURRENCY": [
        r"\beur\b", r"\beuro\b", r"€", r"\busd\b", r"\$",
    ],
    "LENDER": [
        r"\beib\b", r"\bebrd\b", r"\bifc\b", r"\bbank\b", r"\blender\b",
    ],
}

CRITICAL_CATEGORIES = {"CAPEX", "DSCR", "WACC", "IRR", "NPV", "LOAN", "EQUITY", "GRANT", "LENDER"}
BANKABILITY_CATEGORIES = {"DSCR", "WACC", "IRR", "NPV", "LOAN", "EQUITY", "GRANT", "INTEREST_RATE", "MATURITY"}
PROJECT_COST_CATEGORIES = {"CAPEX", "OPEX", "CONTINGENCY", "DEPRECIATION"}

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

RATIO_RE = re.compile(r"\b(?P<num>\d{1,3}(?:[.,]\d{1,4})?)\s*x\b|\b(?P<num2>\d{1,3}(?:[.,]\d{1,4})?)\b", re.IGNORECASE)

RISK_CONTEXT_TERMS = [
    "draft", "estimate", "assumption", "unverified", "missing", "conflict",
    "manual review", "not signed", "unsigned", "rejected", "blocked",
    "nacrt", "procjena", "pretpostavka", "nedostaje", "nepotpisan",
]

AUTHORITY_CONTEXT_TERMS = [
    "signed", "approved", "final", "confirmed", "audited", "official",
    "board", "bank", "lender", "eib", "ebrd", "ifc", "potpisan", "odobren",
]


@dataclass(frozen=True)
class FinancialPaths:
    base_dir: Path
    evidence_pack: Path
    ssot_jsonl: Path
    ssot_report: Path
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
                if isinstance(item, dict):
                    rows.append(item)
            except Exception:
                continue
    return rows


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
    ssot_jsonl_arg: str | None,
    ssot_report_arg: str | None,
    conflict_arg: str | None,
    citation_arg: str | None,
) -> FinancialPaths:
    return FinancialPaths(
        base_dir=base_dir,
        evidence_pack=Path(evidence_arg) if evidence_arg else base_dir / INPUT_EVIDENCE_PACK,
        ssot_jsonl=Path(ssot_jsonl_arg) if ssot_jsonl_arg else base_dir / INPUT_SSOT_JSONL,
        ssot_report=Path(ssot_report_arg) if ssot_report_arg else base_dir / INPUT_SSOT_REPORT,
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


def evidence_score(item: dict[str, Any]) -> float:
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


def detect_financial_categories(text: str) -> list[str]:
    lower = text.lower()
    categories = []
    for category, patterns in FINANCIAL_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                categories.append(category)
                break
    return sorted(set(categories))


def make_signal_id(payload: dict[str, Any]) -> str:
    raw = json.dumps({
        "cat": payload.get("Signal_Category"),
        "type": payload.get("Value_Type"),
        "value": payload.get("Canonical_Value"),
        "source": payload.get("Source_Path"),
        "chunk": payload.get("Chunk_ID"),
        "context_hash": sha256_text(str(payload.get("Context") or ""))[:16],
    }, sort_keys=True, ensure_ascii=False)
    return "FIN-" + sha256_text(raw)[:18]


def confidence_score(base_score: float, category: str, value_type: str, source_path: Any, context: str) -> float:
    confidence = base_score * 0.70

    if category in CRITICAL_CATEGORIES:
        confidence += 0.08

    if value_type in {"MONEY_AMOUNT", "EUR_AMOUNT", "PERCENT", "RATIO", "DATE"}:
        confidence += 0.07

    lower_path = str(source_path or "").lower()
    if any(marker in lower_path for marker in ["financial", "model", "capex", "vdr", "eib", "ebrd", "ifc", "business", "plan", "ssot", "audit"]):
        confidence += 0.07

    lower_context = context.lower()
    if any(marker in lower_context for marker in AUTHORITY_CONTEXT_TERMS):
        confidence += 0.05

    if any(marker in lower_context for marker in RISK_CONTEXT_TERMS):
        confidence -= 0.12

    return round(min(max(confidence, 0.0), 1.0), 6)


def make_signal(
    category: str,
    value_type: str,
    canonical_value: Any,
    raw_value: Any,
    unit: str,
    context: str,
    item: dict[str, Any],
    extraction_rule: str,
) -> dict[str, Any]:
    base_score = evidence_score(item)
    confidence = confidence_score(
        base_score=base_score,
        category=category,
        value_type=value_type,
        source_path=item.get("source_path"),
        context=context,
    )

    signal = {
        "Signal_ID": "",
        "Created_At": utc_now_iso(),
        "Script": SCRIPT_NAME,
        "Script_Version": SCRIPT_VERSION,
        "Signal_Category": category,
        "Value_Type": value_type,
        "Canonical_Value": canonical_value,
        "Raw_Value": raw_value,
        "Unit": unit,
        "Confidence_Score": confidence,
        "Financial_Status": "UNCLASSIFIED",
        "Severity": "UNCLASSIFIED",
        "Conflict_Flag": False,
        "Conflict_IDs": "",
        "SSOT_Alignment": "UNKNOWN",
        "SSOT_Candidate_IDs": "",
        "Source_Path": item.get("source_path"),
        "File_Name": item.get("file_name"),
        "Chunk_ID": item.get("chunk_id"),
        "Section_Label": item.get("section_label"),
        "Evidence_Rank": item.get("rank"),
        "Evidence_Score": base_score,
        "Context": context,
        "Extraction_Rule": extraction_rule,
        "Recommended_Action": "",
    }
    signal["Signal_ID"] = make_signal_id(signal)
    return signal


def extract_money_signals(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for match in MONEY_RE.finditer(text):
        raw = match.group(0).strip()
        prefix = match.group("prefix")
        suffix = match.group("suffix")
        number = parse_number(match.group("number"))

        if number is None:
            continue

        if not prefix and not suffix:
            continue

        amount, currency = scale_money(number, prefix, suffix)
        context = context_window(text, match.start(), match.end())
        categories = detect_financial_categories(context) or ["FINANCIAL_AMOUNT"]

        for category in categories:
            if category == "CURRENCY":
                continue
            signals.append(make_signal(
                category=category,
                value_type="EUR_AMOUNT" if currency == "EUR" else "MONEY_AMOUNT",
                canonical_value=round(amount, 2),
                raw_value=raw,
                unit=currency,
                context=context,
                item=item,
                extraction_rule="money_regex_financial_context",
            ))
    return signals


def extract_percent_signals(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for match in PERCENT_RE.finditer(text):
        raw = match.group(0).strip()
        number = parse_number(match.group("number"))
        if number is None:
            continue

        context = context_window(text, match.start(), match.end())
        categories = detect_financial_categories(context) or ["FINANCIAL_PERCENT"]

        for category in categories:
            signals.append(make_signal(
                category=category,
                value_type="PERCENT",
                canonical_value=round(number, 4),
                raw_value=raw,
                unit="%",
                context=context,
                item=item,
                extraction_rule="percent_regex_financial_context",
            ))
    return signals


def extract_date_signals(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for match in DATE_RE.finditer(text):
        raw = match.group(0).strip()
        context = context_window(text, match.start(), match.end())
        categories = detect_financial_categories(context)
        if not categories:
            continue

        for category in categories:
            signals.append(make_signal(
                category=category,
                value_type="DATE",
                canonical_value=normalize_date(raw),
                raw_value=raw,
                unit="DATE",
                context=context,
                item=item,
                extraction_rule="date_regex_financial_context",
            ))
    return signals


def extract_ratio_signals(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    lower = text.lower()

    if not any(marker in lower for marker in ["dscr", "coverage", "ratio", "wacc", "irr", "npv", "interest"]):
        return signals

    for match in RATIO_RE.finditer(text):
        raw = match.group(0).strip()
        number_text = match.group("num") or match.group("num2")
        number = parse_number(number_text or "")
        if number is None or number <= 0 or number > 100:
            continue

        context = context_window(text, match.start(), match.end())
        categories = detect_financial_categories(context) or ["FINANCIAL_RATIO"]
        for category in categories:
            if category in {"DSCR", "WACC", "IRR", "NPV", "INTEREST_RATE", "LOAN", "FINANCIAL_RATIO"}:
                signals.append(make_signal(
                    category=category,
                    value_type="RATIO",
                    canonical_value=round(number, 6),
                    raw_value=raw,
                    unit="RATIO",
                    context=context,
                    item=item,
                    extraction_rule="ratio_regex_financial_context",
                ))
    return signals


def extract_keyword_signals(text: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    categories = detect_financial_categories(text)

    for category in categories:
        # Avoid duplicating pure currency marker as text.
        if category == "CURRENCY":
            continue

        # Create text signal for category even if no numeric value found.
        lower = text.lower()
        matched_phrase = category
        for pattern in FINANCIAL_CATEGORIES.get(category, []):
            m = re.search(pattern, lower, flags=re.IGNORECASE)
            if m:
                matched_phrase = text[m.start():m.end()]
                context = context_window(text, m.start(), m.end())
                signals.append(make_signal(
                    category=category,
                    value_type="TEXT_SIGNAL",
                    canonical_value=category,
                    raw_value=matched_phrase,
                    unit="TEXT",
                    context=context,
                    item=item,
                    extraction_rule="financial_keyword_context",
                ))
                break

    return signals


def extract_signals_from_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for item in evidence:
        text = normalize_text(item.get("excerpt"))
        if not text:
            continue

        signals.extend(extract_money_signals(text, item))
        signals.extend(extract_percent_signals(text, item))
        signals.extend(extract_date_signals(text, item))
        signals.extend(extract_ratio_signals(text, item))
        signals.extend(extract_keyword_signals(text, item))

    return signals


def ssot_index(ssot_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    idx: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in ssot_rows:
        entity = str(row.get("Entity_Name") or "")
        value_type = str(row.get("Value_Type") or "")
        source = str(row.get("Source_Path") or "")
        chunk = str(row.get("Chunk_ID") or "")

        for key in [
            entity,
            f"{entity}:{value_type}",
            f"SOURCE:{source}",
            f"CHUNK:{chunk}",
        ]:
            if key.strip(":"):
                idx[key].append(row)

    return idx


def conflict_index(conflict_report: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    idx: dict[str, list[dict[str, Any]]] = defaultdict(list)

    if not conflict_report:
        return idx

    conflicts = conflict_report.get("conflicts", [])
    if not isinstance(conflicts, list):
        return idx

    for conflict in conflicts:
        if not isinstance(conflict, dict):
            continue

        entity = str(conflict.get("entity") or "")
        value_type = str(conflict.get("value_type") or "")

        for key in [entity, f"{entity}:{value_type}"]:
            if key.strip(":"):
                idx[key].append(conflict)

        for chunk in conflict.get("chunk_ids", []) if isinstance(conflict.get("chunk_ids"), list) else []:
            idx[f"CHUNK:{chunk}"].append(conflict)

        for source in conflict.get("sources", []) if isinstance(conflict.get("sources"), list) else []:
            idx[f"SOURCE:{source}"].append(conflict)

    return idx


def map_category_to_ssot_entity(category: str) -> str:
    mapping = {
        "REVENUE": "REVENUE",
        "EBITDA": "EBITDA",
        "NET_PROFIT": "NET_PROFIT",
        "INTEREST_RATE": "LOAN",
        "MATURITY": "LOAN",
        "CONTINGENCY": "CAPEX",
        "DEPRECIATION": "CAPEX",
        "LENDER": "LENDER",
        "FINANCIAL_AMOUNT": "GENERAL",
        "FINANCIAL_PERCENT": "GENERAL",
        "FINANCIAL_RATIO": "GENERAL",
    }
    return mapping.get(category, category)


def apply_alignment(signals: list[dict[str, Any]], ssot_rows: list[dict[str, Any]], conflict_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    sidx = ssot_index(ssot_rows)
    cidx = conflict_index(conflict_report)

    for signal in signals:
        category = str(signal.get("Signal_Category") or "")
        entity = map_category_to_ssot_entity(category)
        value_type = str(signal.get("Value_Type") or "")
        source = str(signal.get("Source_Path") or "")
        chunk = str(signal.get("Chunk_ID") or "")

        ssot_matches: list[dict[str, Any]] = []
        for key in [entity, f"{entity}:{value_type}", f"SOURCE:{source}", f"CHUNK:{chunk}"]:
            ssot_matches.extend(sidx.get(key, []))

        seen_ssot = set()
        unique_ssot = []
        for row in ssot_matches:
            cid = row.get("Candidate_ID")
            if cid in seen_ssot:
                continue
            seen_ssot.add(cid)
            unique_ssot.append(row)

        conflicts: list[dict[str, Any]] = []
        for key in [entity, f"{entity}:{value_type}", f"SOURCE:{source}", f"CHUNK:{chunk}"]:
            conflicts.extend(cidx.get(key, []))

        seen_conflict = set()
        unique_conflicts = []
        for row in conflicts:
            cid = row.get("conflict_id")
            if cid in seen_conflict:
                continue
            seen_conflict.add(cid)
            unique_conflicts.append(row)

        if unique_conflicts:
            signal["Conflict_Flag"] = True
            signal["Conflict_IDs"] = "; ".join(str(x.get("conflict_id")) for x in unique_conflicts if x.get("conflict_id"))
        else:
            signal["Conflict_Flag"] = False
            signal["Conflict_IDs"] = ""

        if unique_ssot:
            signal["SSOT_Alignment"] = "MATCHED_SSOT_CANDIDATE"
            signal["SSOT_Candidate_IDs"] = "; ".join(str(x.get("Candidate_ID")) for x in unique_ssot if x.get("Candidate_ID"))
        else:
            signal["SSOT_Alignment"] = "NO_SSOT_CANDIDATE"

    return signals


def citation_status(citation_report: dict[str, Any] | None) -> str:
    if not citation_report:
        return "NOT_AVAILABLE"
    return str(citation_report.get("verification_status") or "UNKNOWN")


def classify_signal(signal: dict[str, Any], citation_report: dict[str, Any] | None, strict: bool) -> dict[str, Any]:
    confidence = safe_float(signal.get("Confidence_Score"), 0.0)
    category = str(signal.get("Signal_Category") or "")
    value_type = str(signal.get("Value_Type") or "")
    conflict = bool(signal.get("Conflict_Flag"))
    cite_status = citation_status(citation_report)
    context = str(signal.get("Context") or "").lower()

    if conflict:
        status = STATUS_CONFLICT_BLOCKED
        severity = SEVERITY_HIGH if category in CRITICAL_CATEGORIES else SEVERITY_MEDIUM
        action = "Resolve conflict before financial use."
    elif cite_status in {"CITATION_VERIFICATION_FAIL", "NO_EVIDENCE_NO_CITATION", "CITATION_REVIEW_REQUIRED"}:
        status = STATUS_REVIEW_REQUIRED
        severity = SEVERITY_HIGH if category in CRITICAL_CATEGORIES else SEVERITY_MEDIUM
        action = "Fix citation verification before using this financial signal."
    elif any(term in context for term in RISK_CONTEXT_TERMS):
        status = STATUS_REVIEW_REQUIRED
        severity = SEVERITY_MEDIUM
        action = "Manual review required due to draft/estimate/unverified context."
    elif confidence >= 0.72 and category in CRITICAL_CATEGORIES and value_type != "TEXT_SIGNAL":
        status = STATUS_LOCK_CANDIDATE if not strict or cite_status == "CITATION_VERIFICATION_PASS" else STATUS_REVIEW_REQUIRED
        severity = SEVERITY_HIGH
        action = "Candidate for financial SSOT review and model input validation."
    elif confidence >= 0.58:
        status = STATUS_DRAFT
        severity = SEVERITY_MEDIUM if category in CRITICAL_CATEGORIES else SEVERITY_LOW
        action = "Use as draft signal; validate before financial model use."
    elif confidence >= 0.40:
        status = STATUS_DRAFT
        severity = SEVERITY_LOW
        action = "Weak draft signal; retrieve stronger evidence if material."
    else:
        status = STATUS_WEAK
        severity = SEVERITY_LOW
        action = "Weak signal; do not use for model input without better evidence."

    if category in BANKABILITY_CATEGORIES and status in {STATUS_REVIEW_REQUIRED, STATUS_CONFLICT_BLOCKED}:
        severity = SEVERITY_HIGH

    signal["Financial_Status"] = status
    signal["Severity"] = severity
    signal["Recommended_Action"] = action
    return signal


def deduplicate_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}

    for sig in signals:
        key = json.dumps({
            "category": sig.get("Signal_Category"),
            "value_type": sig.get("Value_Type"),
            "value": sig.get("Canonical_Value"),
            "source": sig.get("Source_Path"),
            "chunk": sig.get("Chunk_ID"),
        }, sort_keys=True, ensure_ascii=False)

        existing = best.get(key)
        if existing is None or safe_float(sig.get("Confidence_Score")) > safe_float(existing.get("Confidence_Score")):
            best[key] = sig

    rows = list(best.values())
    rows.sort(
        key=lambda x: (
            severity_rank(str(x.get("Severity"))),
            status_rank(str(x.get("Financial_Status"))),
            safe_float(x.get("Confidence_Score")),
            safe_float(x.get("Evidence_Score")),
        ),
        reverse=True,
    )
    return rows


def severity_rank(severity: str) -> int:
    return {
        SEVERITY_CRITICAL: 4,
        SEVERITY_HIGH: 3,
        SEVERITY_MEDIUM: 2,
        SEVERITY_LOW: 1,
    }.get(severity, 0)


def status_rank(status: str) -> int:
    return {
        STATUS_LOCK_CANDIDATE: 5,
        STATUS_DRAFT: 4,
        STATUS_REVIEW_REQUIRED: 3,
        STATUS_CONFLICT_BLOCKED: 2,
        STATUS_WEAK: 1,
    }.get(status, 0)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Signal_ID",
        "Created_At",
        "Signal_Category",
        "Value_Type",
        "Canonical_Value",
        "Raw_Value",
        "Unit",
        "Confidence_Score",
        "Financial_Status",
        "Severity",
        "Conflict_Flag",
        "Conflict_IDs",
        "SSOT_Alignment",
        "SSOT_Candidate_IDs",
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


def summarize(signals: list[dict[str, Any]], ssot_rows: list[dict[str, Any]], conflict_report: dict[str, Any] | None, citation_report: dict[str, Any] | None) -> dict[str, Any]:
    by_status: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    by_category: dict[str, int] = defaultdict(int)
    by_value_type: dict[str, int] = defaultdict(int)

    for sig in signals:
        by_status[str(sig.get("Financial_Status"))] += 1
        by_severity[str(sig.get("Severity"))] += 1
        by_category[str(sig.get("Signal_Category"))] += 1
        by_value_type[str(sig.get("Value_Type"))] += 1

    conflict_blocked = by_status.get(STATUS_CONFLICT_BLOCKED, 0)
    review_required = by_status.get(STATUS_REVIEW_REQUIRED, 0)
    high_count = by_severity.get(SEVERITY_HIGH, 0) + by_severity.get(SEVERITY_CRITICAL, 0)
    lock_candidates = by_status.get(STATUS_LOCK_CANDIDATE, 0)

    if conflict_blocked > 0:
        institutional_status = REPORT_CONFLICT_BLOCKED
    elif review_required > 0 or high_count > 0:
        institutional_status = REPORT_REVIEW_REQUIRED
    elif signals:
        institutional_status = REPORT_READY
    else:
        institutional_status = REPORT_NO_SIGNALS

    return {
        "institutional_status": institutional_status,
        "total_signals": len(signals),
        "lock_candidates": lock_candidates,
        "review_required": review_required,
        "conflict_blocked": conflict_blocked,
        "high_count": high_count,
        "ssot_candidates_loaded": len(ssot_rows),
        "conflict_report_available": conflict_report is not None,
        "citation_report_available": citation_report is not None,
        "citation_status": citation_status(citation_report),
        "by_status": dict(sorted(by_status.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_value_type": dict(sorted(by_value_type.items())),
    }


def build_report(
    evidence_pack: dict[str, Any],
    ssot_rows: list[dict[str, Any]],
    ssot_report: dict[str, Any] | None,
    conflict_report: dict[str, Any] | None,
    citation_report: dict[str, Any] | None,
    signals: list[dict[str, Any]],
    paths: FinancialPaths,
    strict: bool,
) -> dict[str, Any]:
    summary = summarize(signals, ssot_rows, conflict_report, citation_report)

    report = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "FINANCIAL_SIGNAL_EXTRACTION_AUDIT_LOCKED",
        "strict_mode": strict,
        "query": evidence_pack.get("query"),
        "inputs": {
            "evidence_pack": str(paths.evidence_pack),
            "ssot_jsonl": str(paths.ssot_jsonl),
            "ssot_report": str(paths.ssot_report),
            "conflict_report": str(paths.conflict_report),
            "citation_report": str(paths.citation_report),
            "ssot_jsonl_available": paths.ssot_jsonl.exists(),
            "ssot_report_available": ssot_report is not None,
            "conflict_report_available": conflict_report is not None,
            "citation_report_available": citation_report is not None,
        },
        "summary": summary,
        "signals": signals,
        "hashes": {
            "evidence_pack_canonical_sha256": sha256_json(evidence_pack),
            "ssot_report_canonical_sha256": sha256_json(ssot_report) if ssot_report else None,
            "conflict_report_canonical_sha256": sha256_json(conflict_report) if conflict_report else None,
            "citation_report_canonical_sha256": sha256_json(citation_report) if citation_report else None,
            "evidence_pack_declared_sha256": evidence_pack.get("evidence_pack_sha256"),
            "ssot_report_declared_sha256": (ssot_report or {}).get("ssot_candidates_report_sha256"),
            "conflict_report_declared_sha256": (conflict_report or {}).get("conflict_report_sha256"),
            "citation_report_declared_sha256": (citation_report or {}).get("citation_verification_sha256"),
        },
        "governance_rule": {
            "financial_signal_is_not_final_model_input": True,
            "manual_financial_review_required": True,
            "conflict_blocks_financial_use": True,
            "citation_verification_required": True,
            "source_files_remain_authoritative": True,
        },
    }
    report["financial_signals_report_sha256"] = sha256_json(report)
    return report


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def signals_table_md(rows: list[dict[str, Any]], limit: int = 150) -> str:
    if not rows:
        return "No financial signals."

    lines = [
        "| Severity | Status | Category | Type | Value | Confidence | SSOT | Conflict | Source | Chunk | Action |",
        "|---|---|---|---|---|---:|---|---:|---|---|---|",
    ]

    for row in rows[:limit]:
        value = md_escape(row.get("Canonical_Value"))
        if len(value) > 140:
            value = value[:140] + " ..."
        lines.append(
            f"| {md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Financial_Status'))} | "
            f"{md_escape(row.get('Signal_Category'))} | "
            f"{md_escape(row.get('Value_Type'))} | "
            f"{value} | "
            f"{row.get('Confidence_Score')} | "
            f"{md_escape(row.get('SSOT_Alignment'))} | "
            f"{row.get('Conflict_Flag')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"`{md_escape(row.get('Chunk_ID'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )

    return "\n".join(lines)


def report_to_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    return f"""# TITAN RAG Financial Signal Report

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {report.get("created_at")} |
| Institutional Status | {summary.get("institutional_status")} |
| Query | {md_escape(report.get("query"))} |
| Strict Mode | {report.get("strict_mode")} |
| Total Signals | {summary.get("total_signals")} |
| Lock Candidates | {summary.get("lock_candidates")} |
| Review Required | {summary.get("review_required")} |
| Conflict Blocked | {summary.get("conflict_blocked")} |
| High/Critical Count | {summary.get("high_count")} |
| Citation Status | {summary.get("citation_status")} |
| Report SHA-256 | `{report.get("financial_signals_report_sha256")}` |

---

## 2. Distribution

```json
{json.dumps({
    "by_status": summary.get("by_status"),
    "by_severity": summary.get("by_severity"),
    "by_category": summary.get("by_category"),
    "by_value_type": summary.get("by_value_type"),
}, indent=2, ensure_ascii=False)}
```

---

## 3. Financial Signals

{signals_table_md(report.get("signals", []))}

---

## 4. Hashes

```json
{json.dumps(report.get("hashes", {}), indent=2, ensure_ascii=False)}
```

---

## 5. Governance Rule

```text
Financial signal is not final model input.
Manual financial review is required.
Conflict blocks financial use.
Citation verification is required.
Source files remain authoritative.
```
"""


def print_summary(report: dict[str, Any], paths: FinancialPaths) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN RAG FINANCIAL SIGNAL EXTRACTOR v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Institutional status:  {summary.get('institutional_status')}")
    print(f"Query:                 {report.get('query')}")
    print(f"Total signals:         {summary.get('total_signals')}")
    print(f"Lock candidates:       {summary.get('lock_candidates')}")
    print(f"Review required:       {summary.get('review_required')}")
    print(f"Conflict blocked:      {summary.get('conflict_blocked')}")
    print(f"High/Critical count:   {summary.get('high_count')}")
    print("-" * 100)
    print(f"Signals JSONL:         {paths.output_jsonl}")
    print(f"Signals CSV:           {paths.output_csv}")
    print(f"Report JSON:           {paths.output_report_json}")
    print(f"Report Markdown:       {paths.output_report_md}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 16 — financial signal extractor.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--evidence-pack", default=None, help="Optional latest_evidence_pack.json path.")
    parser.add_argument("--ssot-jsonl", default=None, help="Optional ssot_candidates.jsonl path.")
    parser.add_argument("--ssot-report", default=None, help="Optional ssot_candidates_report.json path.")
    parser.add_argument("--conflict-report", default=None, help="Optional conflict_report.json path.")
    parser.add_argument("--citation-report", default=None, help="Optional citation_verification_report.json path.")
    parser.add_argument("--strict", action="store_true", help="Strict financial signal classification.")
    parser.add_argument("--print", action="store_true", help="Print Markdown report to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    paths = resolve_paths(
        base_dir=base_dir,
        evidence_arg=args.evidence_pack,
        ssot_jsonl_arg=args.ssot_jsonl,
        ssot_report_arg=args.ssot_report,
        conflict_arg=args.conflict_report,
        citation_arg=args.citation_report,
    )

    try:
        evidence_pack = require_json(paths.evidence_pack)
        ssot_rows = read_jsonl(paths.ssot_jsonl)
        ssot_report = load_json_if_exists(paths.ssot_report)
        conflict_report = load_json_if_exists(paths.conflict_report)
        citation_report = load_json_if_exists(paths.citation_report)

        evidence = get_evidence(evidence_pack)
        signals = extract_signals_from_evidence(evidence)
        signals = apply_alignment(signals, ssot_rows, conflict_report)

        classified = [
            classify_signal(signal, citation_report=citation_report, strict=bool(args.strict))
            for signal in signals
        ]

        deduped = deduplicate_signals(classified)

        report = build_report(
            evidence_pack=evidence_pack,
            ssot_rows=ssot_rows,
            ssot_report=ssot_report,
            conflict_report=conflict_report,
            citation_report=citation_report,
            signals=deduped,
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
            "event": "FINANCIAL_SIGNAL_EXTRACTION_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "institutional_status": (report.get("summary") or {}).get("institutional_status"),
            "summary": report.get("summary"),
            "report_sha256": report.get("financial_signals_report_sha256"),
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
            "event": "FINANCIAL_SIGNAL_EXTRACTION_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "evidence_pack": str(paths.evidence_pack),
            "ssot_jsonl": str(paths.ssot_jsonl),
            "conflict_report": str(paths.conflict_report),
            "citation_report": str(paths.citation_report),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG FINANCIAL SIGNAL EXTRACTOR FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
