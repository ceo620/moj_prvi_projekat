#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07_generate_answer.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 07 — Evidence-Bound Answer Generator
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Generate a conservative, source-grounded answer using ONLY the evidence pack
created by Step 06.

This script does not search.
This script does not read arbitrary documents.
This script does not use external internet.
This script does not allow unsupported claims.

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
05_reports/latest_rag_answer.json
05_reports/latest_rag_answer.md
06_logs/generation_audit.jsonl
06_logs/generation_errors.jsonl

Operating mode
--------------
By default, this script uses a deterministic extractive/synthesis generator.
It does not require an API key.

Optional LLM mode can be enabled only if you explicitly provide --llm-provider.
The produced answer still remains bounded by the evidence pack.

Recommended command
-------------------
python ".\\08_scripts\\07_generate_answer.py" --print

Custom evidence pack
--------------------
python ".\\08_scripts\\07_generate_answer.py" --input ".\\05_reports\\latest_evidence_pack.json" --print
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "07_generate_answer.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
OUTPUT_ANSWER_JSON = Path("05_reports") / "latest_rag_answer.json"
OUTPUT_ANSWER_MD = Path("05_reports") / "latest_rag_answer.md"

AUDIT_LOG = Path("06_logs") / "generation_audit.jsonl"
ERROR_LOG = Path("06_logs") / "generation_errors.jsonl"

DEFAULT_MAX_EVIDENCE_ITEMS = 12
DEFAULT_MAX_EXCERPT_CHARS_USED = 1600

STATUS_NO_EVIDENCE = "NO_EVIDENCE_NO_ANSWER"
STATUS_LOW_CONFIDENCE = "LOW_CONFIDENCE_REVIEW_REQUIRED"
STATUS_MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE_DRAFT"
STATUS_HIGH_CONFIDENCE = "HIGH_CONFIDENCE_EVIDENCE_BASED"
STATUS_CONFLICT_REVIEW = "CONFLICT_OR_RISK_REVIEW_REQUIRED"

CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.55
CONFIDENCE_LOW = 0.35

RISK_TERMS = [
    "conflict", "konflikt", "failed", "failure", "error", "blocked", "missing",
    "unverified", "manual review", "review required", "draft", "estimate",
    "assumption", "not signed", "unsigned", "expired", "rejected",
    "nepotpisan", "neprovjeren", "neproveren", "nedostaje", "blokiran",
]

ACTION_WORDS = [
    "next", "sledeće", "sljedeće", "šta dalje", "sta dalje", "action",
    "todo", "to-do", "uradi", "pokreni", "prioritet",
]

FINANCE_WORDS = [
    "capex", "opex", "irr", "npv", "dscr", "wacc", "loan", "debt",
    "equity", "grant", "subsidy", "eur", "financial", "model", "lender",
    "eib", "ebrd", "ifc",
]

RISK_WORDS = [
    "risk", "rizik", "conflict", "missing", "blocked", "failed", "error",
    "delay", "manual review", "unverified", "expired", "not signed",
]

DOCUMENT_WORDS = [
    "document", "dokument", "file", "fajl", "source", "izvor", "gdje",
    "gde", "where", "pominje", "contains",
]


@dataclass(frozen=True)
class GenerationPaths:
    base_dir: Path
    evidence_pack: Path
    answer_json: Path
    answer_md: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_space(text: Any) -> str:
    value = str(text or "").replace("\x00", "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalize_inline(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").replace("\x00", " ")).strip()


def truncate(text: Any, max_chars: int) -> str:
    value = normalize_space(text)
    if max_chars <= 0 or len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + " ...[TRUNCATED]"


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing evidence pack: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Evidence pack root must be a JSON object.")
    return data


def resolve_paths(base_dir: Path, input_arg: str | None) -> GenerationPaths:
    return GenerationPaths(
        base_dir=base_dir,
        evidence_pack=Path(input_arg) if input_arg else base_dir / INPUT_EVIDENCE_PACK,
        answer_json=base_dir / OUTPUT_ANSWER_JSON,
        answer_md=base_dir / OUTPUT_ANSWER_MD,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def evidence_score(item: dict[str, Any]) -> float:
    scores = item.get("scores")
    if isinstance(scores, dict):
        return safe_float(scores.get("final_score"), 0.0)
    return 0.0


def get_evidence(pack: dict[str, Any], max_items: int, min_score: float | None) -> list[dict[str, Any]]:
    evidence = pack.get("evidence", [])
    if not isinstance(evidence, list):
        return []

    valid = [item for item in evidence if isinstance(item, dict)]

    if min_score is not None:
        valid = [item for item in valid if evidence_score(item) >= min_score]

    valid.sort(key=evidence_score, reverse=True)
    return valid[:max_items]


def query_intent(query: str) -> str:
    q = query.lower()

    if any(word in q for word in ACTION_WORDS):
        return "ACTION_OR_NEXT_STEPS"

    if any(word in q for word in FINANCE_WORDS):
        return "FINANCIAL_EVIDENCE"

    if any(word in q for word in RISK_WORDS):
        return "RISK_EVIDENCE"

    if any(word in q for word in DOCUMENT_WORDS):
        return "DOCUMENT_LOCATION"

    return "GENERAL_EVIDENCE_SUMMARY"


def has_risk_language(evidence: list[dict[str, Any]]) -> bool:
    text = " ".join(str(item.get("excerpt") or "") for item in evidence).lower()
    return any(term in text for term in RISK_TERMS)


def source_coverage(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    sources = sorted({str(item.get("source_path")) for item in evidence if item.get("source_path")})
    chunk_ids = [str(item.get("chunk_id")) for item in evidence if item.get("chunk_id")]
    avg_score = sum(evidence_score(item) for item in evidence) / len(evidence) if evidence else 0.0
    max_score = max((evidence_score(item) for item in evidence), default=0.0)

    return {
        "source_count": len(sources),
        "sources": sources,
        "chunk_count": len(chunk_ids),
        "chunk_ids": chunk_ids,
        "average_score": round(avg_score, 6),
        "max_score": round(max_score, 6),
    }


def calculate_confidence(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    if not evidence:
        return {
            "confidence_score": 0.0,
            "confidence_label": "NO_EVIDENCE",
            "drivers": ["No evidence items available."],
        }

    coverage = source_coverage(evidence)
    avg_score = safe_float(coverage.get("average_score"))
    max_score = safe_float(coverage.get("max_score"))
    source_count = safe_int(coverage.get("source_count"))
    chunk_count = safe_int(coverage.get("chunk_count"))

    score = avg_score * 0.62 + max_score * 0.22

    if source_count >= 3:
        score += 0.08
    elif source_count >= 2:
        score += 0.05
    elif source_count == 1:
        score += 0.02

    if chunk_count >= 5:
        score += 0.05
    elif chunk_count >= 3:
        score += 0.03

    if has_risk_language(evidence):
        score -= 0.08

    score = round(min(max(score, 0.0), 1.0), 6)

    if score >= CONFIDENCE_HIGH:
        label = "HIGH"
    elif score >= CONFIDENCE_MEDIUM:
        label = "MEDIUM"
    elif score >= CONFIDENCE_LOW:
        label = "LOW"
    else:
        label = "VERY_LOW"

    drivers = [
        f"Average evidence score: {avg_score}",
        f"Maximum evidence score: {max_score}",
        f"Source count: {source_count}",
        f"Chunk count: {chunk_count}",
    ]

    if has_risk_language(evidence):
        drivers.append("Risk/draft/conflict language detected in evidence.")

    return {
        "confidence_score": score,
        "confidence_label": label,
        "drivers": drivers,
    }


def institutional_status(evidence: list[dict[str, Any]], confidence: dict[str, Any]) -> str:
    if not evidence:
        return STATUS_NO_EVIDENCE

    if has_risk_language(evidence):
        return STATUS_CONFLICT_REVIEW

    score = safe_float(confidence.get("confidence_score"))

    if score >= CONFIDENCE_HIGH:
        return STATUS_HIGH_CONFIDENCE

    if score >= CONFIDENCE_MEDIUM:
        return STATUS_MEDIUM_CONFIDENCE

    return STATUS_LOW_CONFIDENCE


def sentence_split(text: str) -> list[str]:
    clean = normalize_space(text)
    if not clean:
        return []

    # Conservative sentence-ish segmentation.
    parts = re.split(r"(?<=[.!?])\s+|\n+", clean)
    output = []
    for part in parts:
        p = normalize_inline(part)
        if len(p) >= 25:
            output.append(p)
    return output


def select_relevant_sentences(query: str, evidence: list[dict[str, Any]], max_sentences: int = 8) -> list[dict[str, Any]]:
    tokens = [
        t.lower()
        for t in re.findall(r"[A-Za-zČĆŽŠĐčćžšđ0-9_%-]+", query)
        if len(t) >= 2
    ]

    selected: list[dict[str, Any]] = []

    for item in evidence:
        excerpt = truncate(item.get("excerpt"), DEFAULT_MAX_EXCERPT_CHARS_USED)
        sentences = sentence_split(excerpt)

        for sentence in sentences:
            lower = sentence.lower()
            hit_count = sum(1 for token in tokens if token in lower)
            if hit_count <= 0:
                # Still keep one top excerpt sentence for broad queries.
                hit_count = 0

            selected.append({
                "sentence": sentence,
                "hit_count": hit_count,
                "score": evidence_score(item),
                "chunk_id": item.get("chunk_id"),
                "source_path": item.get("source_path"),
                "file_name": item.get("file_name"),
                "section_label": item.get("section_label"),
            })

    selected.sort(key=lambda x: (safe_int(x.get("hit_count")), safe_float(x.get("score"))), reverse=True)

    # Deduplicate sentence text.
    seen = set()
    output = []
    for item in selected:
        key = sha256_text(item["sentence"].lower())[:16]
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
        if len(output) >= max_sentences:
            break

    return output


def evidence_citation_label(item: dict[str, Any]) -> str:
    rank = item.get("rank", item.get("rank_raw", "?"))
    chunk_id = str(item.get("chunk_id") or "NO_CHUNK")
    file_name = str(item.get("file_name") or "unknown file")
    return f"[E{rank}: {file_name} | {chunk_id}]"


def build_direct_answer(query: str, intent: str, evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return (
            "Nema dovoljno pronađenih dokaza za pouzdan odgovor. "
            "Pokreni Korak 6 sa širim upitom ili provjeri da li su Koraci 1–5 završeni."
        )

    selected = select_relevant_sentences(query, evidence, max_sentences=8)

    if not selected:
        top = evidence[0]
        return (
            "Pronađeni su dokazi, ali nije izdvojena dovoljno čista rečenica za direktan zaključak. "
            f"Najbliži dokaz je {evidence_citation_label(top)}."
        )

    if intent == "DOCUMENT_LOCATION":
        sources = []
        for item in evidence:
            source = item.get("source_path")
            chunk_id = item.get("chunk_id")
            score = evidence_score(item)
            if source and chunk_id:
                sources.append(f"- `{source}` | chunk `{chunk_id}` | score {score}")

        return "Pronađeni su sljedeći relevantni izvori:\n" + "\n".join(sources[:10])

    if intent == "ACTION_OR_NEXT_STEPS":
        lines = [
            "Na osnovu pronađenih dokaza, operativno najrazumniji sljedeći koraci su:"
        ]

        for i, item in enumerate(selected[:5], start=1):
            citation = f"`{item.get('source_path')}` | chunk `{item.get('chunk_id')}`"
            lines.append(f"{i}. Provjeri dokaz: {citation}. Relevantan izvod: {item.get('sentence')}")

        return "\n".join(lines)

    if intent == "FINANCIAL_EVIDENCE":
        lines = [
            "Finansijski zaključak smije ostati ograničen na pronađene dokaze:"
        ]

        for item in selected[:6]:
            lines.append(
                f"- {item.get('sentence')} "
                f"(izvor: `{item.get('source_path')}`, chunk `{item.get('chunk_id')}`)"
            )

        return "\n".join(lines)

    if intent == "RISK_EVIDENCE":
        lines = [
            "Detektovani risk/issue elementi iz dokaza:"
        ]

        for item in selected[:6]:
            lines.append(
                f"- {item.get('sentence')} "
                f"(izvor: `{item.get('source_path')}`, chunk `{item.get('chunk_id')}`)"
            )

        return "\n".join(lines)

    lines = ["Sažetak na osnovu pronađenih dokaza:"]
    for item in selected[:6]:
        lines.append(
            f"- {item.get('sentence')} "
            f"(izvor: `{item.get('source_path')}`, chunk `{item.get('chunk_id')}`)"
        )

    return "\n".join(lines)


def build_evidence_table(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []

    for item in evidence:
        scores = item.get("scores") if isinstance(item.get("scores"), dict) else {}
        rows.append({
            "rank": item.get("rank"),
            "chunk_id": item.get("chunk_id"),
            "source_path": item.get("source_path"),
            "file_name": item.get("file_name"),
            "section_label": item.get("section_label"),
            "final_score": scores.get("final_score"),
            "semantic_score": scores.get("semantic_score"),
            "keyword_overlap_score": scores.get("keyword_overlap_score"),
            "excerpt": truncate(item.get("excerpt"), 1000),
        })

    return rows


def build_risk_if_skipped(evidence: list[dict[str, Any]], status: str) -> str:
    if status == STATUS_NO_EVIDENCE:
        return "Rizik: donošenje zaključka bez dokaza. Prvo pokrenuti retrieval sa boljim upitom."

    if status == STATUS_CONFLICT_REVIEW:
        return "Rizik: evidence pack sadrži risk/draft/conflict jezik. Zaključak koristiti samo kao DRAFT do ručne provjere."

    return "Rizik je ograničen ako se zaključak koristi samo uz navedene izvore i chunk reference."


def build_next_action(intent: str, status: str) -> str:
    if status == STATUS_NO_EVIDENCE:
        return "Pokreni Korak 6 sa širim ili preciznijim query-jem, zatim ponovi Korak 7."

    if status == STATUS_CONFLICT_REVIEW:
        return "Pokreni Korak 14 Conflict Detector i Korak 17 Risk Signal Extractor prije institucionalne upotrebe."

    if intent == "FINANCIAL_EVIDENCE":
        return "Pokreni Korak 16 Financial Signal Extractor i provjeri rezultate u Control Tower-u."

    if intent == "RISK_EVIDENCE":
        return "Pokreni Korak 17 Risk Signal Extractor i prioritetizuj kritične/high rizike."

    if intent == "DOCUMENT_LOCATION":
        return "Otvori navedene izvore i provjeri chunk kontekst prije SSOT zaključavanja."

    return "Za institucionalnu upotrebu pokreni Korak 13 Citation Verifier i Korak 14 Conflict Detector."


def build_answer(pack: dict[str, Any], max_items: int, min_score: float | None) -> dict[str, Any]:
    query = str(pack.get("query") or "")
    evidence = get_evidence(pack, max_items=max_items, min_score=min_score)
    intent = query_intent(query)
    confidence = calculate_confidence(evidence)
    status = institutional_status(evidence, confidence)

    direct_answer = build_direct_answer(query, intent, evidence)

    coverage = source_coverage(evidence)

    answer = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "EVIDENCE_BOUND_GENERATION_AUDIT_LOCKED",
        "query": query,
        "intent": intent,
        "institutional_status": status,
        "confidence": confidence,
        "evidence_count_used": len(evidence),
        "source_file_count_used": coverage.get("source_count"),
        "source_files": coverage.get("sources"),
        "chunk_ids": coverage.get("chunk_ids"),
        "direct_answer": direct_answer,
        "risk_if_skipped": build_risk_if_skipped(evidence, status),
        "next_action": build_next_action(intent, status),
        "evidence": evidence,
        "evidence_table": build_evidence_table(evidence),
        "evidence_pack_reference": {
            "created_at": pack.get("created_at"),
            "evidence_pack_sha256": pack.get("evidence_pack_sha256"),
            "collection_name": pack.get("collection_name"),
            "embedding_model": pack.get("embedding_model"),
            "retrieval_parameters": pack.get("retrieval_parameters"),
        },
        "governance_rule": {
            "answer_bound_to_evidence_pack": True,
            "no_unsupported_claims": True,
            "no_external_knowledge": True,
            "source_path_required": True,
            "chunk_id_required": True,
            "citation_verification_required_for_institutional_use": True,
        },
    }

    answer["answer_sha256"] = sha256_json(answer)
    return answer


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def answer_to_markdown(answer: dict[str, Any]) -> str:
    confidence = answer.get("confidence", {}) if isinstance(answer.get("confidence"), dict) else {}
    evidence_table = answer.get("evidence_table", [])

    rows = [
        "| Rank | Score | File | Chunk | Source | Excerpt |",
        "|---:|---:|---|---|---|---|",
    ]

    for item in evidence_table:
        excerpt = md_escape(item.get("excerpt"))
        if len(excerpt) > 700:
            excerpt = excerpt[:700] + " ..."
        rows.append(
            f"| {item.get('rank')} | "
            f"{item.get('final_score')} | "
            f"{md_escape(item.get('file_name'))} | "
            f"`{md_escape(item.get('chunk_id'))}` | "
            f"`{md_escape(item.get('source_path'))}` | "
            f"{excerpt} |"
        )

    return f"""# TITAN RAG Evidence-Bound Answer

## 1. Answer Identity

| Field | Value |
|---|---|
| Created At | {answer.get("created_at")} |
| Query | {md_escape(answer.get("query"))} |
| Intent | {answer.get("intent")} |
| Institutional Status | {answer.get("institutional_status")} |
| Confidence Score | {confidence.get("confidence_score")} |
| Confidence Label | {confidence.get("confidence_label")} |
| Evidence Count Used | {answer.get("evidence_count_used")} |
| Source File Count Used | {answer.get("source_file_count_used")} |
| Answer SHA-256 | `{answer.get("answer_sha256")}` |

---

## 2. Direct Answer

{answer.get("direct_answer")}

---

## 3. Risk If Skipped

{answer.get("risk_if_skipped")}

---

## 4. Next Action

{answer.get("next_action")}

---

## 5. Evidence Used

{chr(10).join(rows)}

---

## 6. Confidence Drivers

```json
{json.dumps(confidence.get("drivers", []), indent=2, ensure_ascii=False)}
```

---

## 7. Governance Rule

```text
Answer is bounded to latest_evidence_pack.json.
No unsupported claims.
No external knowledge.
For institutional use, run Step 13 citation verification and Step 14 conflict detection.
```
"""


def print_summary(answer: dict[str, Any], paths: GenerationPaths) -> None:
    confidence = answer.get("confidence", {}) if isinstance(answer.get("confidence"), dict) else {}

    print("=" * 100)
    print("TITAN RAG EVIDENCE-BOUND ANSWER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Query:                  {answer.get('query')}")
    print(f"Intent:                 {answer.get('intent')}")
    print(f"Institutional status:   {answer.get('institutional_status')}")
    print(f"Confidence:             {confidence.get('confidence_score')} | {confidence.get('confidence_label')}")
    print(f"Evidence used:          {answer.get('evidence_count_used')}")
    print(f"Source files used:      {answer.get('source_file_count_used')}")
    print("-" * 100)
    print(f"Answer JSON:            {paths.answer_json}")
    print(f"Answer Markdown:        {paths.answer_md}")
    print(f"Audit log:              {paths.audit_log}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 07 — evidence-bound answer generator."
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
        "--max-evidence-items",
        type=int,
        default=DEFAULT_MAX_EVIDENCE_ITEMS,
        help="Maximum evidence items used in generated answer.",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Optional minimum final_score for evidence used.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print Markdown answer to console.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, input_arg=args.input)

    try:
        evidence_pack = load_json(paths.evidence_pack)

        answer = build_answer(
            pack=evidence_pack,
            max_items=int(args.max_evidence_items),
            min_score=args.min_score,
        )

        markdown = answer_to_markdown(answer)

        write_json(paths.answer_json, answer)
        write_text(paths.answer_md, markdown)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "EVIDENCE_BOUND_ANSWER_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "input_evidence_pack": str(paths.evidence_pack),
            "outputs": {
                "answer_json": str(paths.answer_json),
                "answer_md": str(paths.answer_md),
            },
            "summary": {
                "query": answer.get("query"),
                "intent": answer.get("intent"),
                "institutional_status": answer.get("institutional_status"),
                "confidence": answer.get("confidence"),
                "evidence_count_used": answer.get("evidence_count_used"),
                "source_file_count_used": answer.get("source_file_count_used"),
            },
            "answer_sha256": answer.get("answer_sha256"),
        })

        print_summary(answer, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "EVIDENCE_BOUND_ANSWER_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "input_evidence_pack": str(paths.evidence_pack),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG EVIDENCE-BOUND ANSWER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
