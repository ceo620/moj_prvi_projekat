#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_search_rag.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 06 — Retrieval / Evidence Pack Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Search the local ChromaDB vector index built in Step 05 and produce a
source-grounded evidence pack. This is the retrieval layer only.

This script does NOT generate answers.
This script does NOT call a generative model.
This script does NOT invent facts.
This script returns evidence chunks with source_path, chunk_id, scores and excerpt.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Input
-----
04_vectors/chroma_db/
03_chunks/chunks.jsonl                  # optional metadata fallback
05_reports/embedding_summary.json       # optional configuration reference

Outputs
-------
05_reports/latest_evidence_pack.json
05_reports/latest_evidence_pack.md
05_reports/latest_evidence_pack.csv
06_logs/rag_search_audit.jsonl
06_logs/rag_search_errors.jsonl

Designed for compatibility with:
07_generate_answer.py
12_evidence_pack_reporter.py
13_source_citation_verifier.py
14_conflict_detector.py
15_ssot_candidate_extractor.py
16_financial_signal_extractor.py
17_risk_signal_extractor.py
20_rag_control_tower_export.py

Install
-------
pip install chromadb sentence-transformers

Recommended command
-------------------
python ".\\08_scripts\\06_search_rag.py" --query "Koji dokumenti pominju CAPEX?"

Higher recall
-------------
python ".\\08_scripts\\06_search_rag.py" --query "EIB EBRD CAPEX" --top-k-raw 80 --top-k-final 15

Score threshold
---------------
python ".\\08_scripts\\06_search_rag.py" --query "MISSING_GUARDIAN_SECRET" --min-score 0.45
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_NAME = "06_search_rag.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

CHROMA_DIR = Path("04_vectors") / "chroma_db"
CHUNKS_JSONL = Path("03_chunks") / "chunks.jsonl"
EMBEDDING_SUMMARY_JSON = Path("05_reports") / "embedding_summary.json"

OUTPUT_EVIDENCE_JSON = Path("05_reports") / "latest_evidence_pack.json"
OUTPUT_EVIDENCE_MD = Path("05_reports") / "latest_evidence_pack.md"
OUTPUT_EVIDENCE_CSV = Path("05_reports") / "latest_evidence_pack.csv"

AUDIT_LOG = Path("06_logs") / "rag_search_audit.jsonl"
ERROR_LOG = Path("06_logs") / "rag_search_errors.jsonl"

DEFAULT_COLLECTION_NAME = "titan_local_evidence_chunks"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_TOP_K_RAW = 50
DEFAULT_TOP_K_FINAL = 10
DEFAULT_MAX_EXCERPT_CHARS = 1800

MIN_QUERY_LENGTH = 2

KEYWORD_IMPORTANCE = {
    # finance/lender/governance
    "capex": 1.25,
    "opex": 1.10,
    "irr": 1.15,
    "npv": 1.15,
    "dscr": 1.25,
    "wacc": 1.20,
    "eib": 1.35,
    "ebrd": 1.35,
    "ifc": 1.25,
    "loan": 1.15,
    "debt": 1.10,
    "equity": 1.10,
    "grant": 1.10,
    "subsidy": 1.05,
    "ssot": 1.35,
    "audit": 1.20,
    "control": 1.05,
    "tower": 1.05,
    "risk": 1.15,
    "conflict": 1.20,
    "missing": 1.15,
    "blocked": 1.20,
    "failed": 1.15,
    "contract": 1.15,
    "permit": 1.15,
    "license": 1.05,
    "business": 1.05,
    "plan": 1.05,
    "financial": 1.10,
    "model": 1.05,
    "guardian": 1.20,
    "kernel": 1.10,
    "rag": 1.15,
    "evidence": 1.20,
}

STOPWORDS = {
    "the", "and", "or", "to", "of", "in", "on", "for", "a", "an", "is", "are",
    "je", "i", "ili", "u", "na", "za", "od", "do", "koji", "koje", "šta",
    "sta", "gdje", "gde", "kako", "mi", "se", "su", "da", "li",
}


@dataclass(frozen=True)
class SearchPaths:
    base_dir: Path
    chroma_dir: Path
    chunks_jsonl: Path
    embedding_summary_json: Path
    evidence_json: Path
    evidence_md: Path
    evidence_csv: Path
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


def read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_jsonl(path: Path, max_records: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue

            try:
                item = json.loads(raw)
                if isinstance(item, dict):
                    records.append(item)
            except Exception:
                continue

            if max_records is not None and len(records) >= max_records:
                break

    return records


def write_csv(path: Path, evidence: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "rank",
        "rank_raw",
        "final_score",
        "semantic_score",
        "keyword_overlap_score",
        "keyword_boost",
        "recency_boost",
        "source_folder_boost",
        "file_type_boost",
        "distance",
        "chunk_id",
        "source_path",
        "processed_path",
        "file_name",
        "extension",
        "section_label",
        "chunk_index",
        "chunk_count_for_file",
        "source_modified_time_utc",
        "excerpt",
        "excerpt_sha256",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for item in evidence:
            row = dict(item)
            scores = row.get("scores", {}) if isinstance(row.get("scores"), dict) else {}
            row["final_score"] = scores.get("final_score")
            row["semantic_score"] = scores.get("semantic_score")
            row["keyword_overlap_score"] = scores.get("keyword_overlap_score")
            row["keyword_boost"] = scores.get("keyword_boost")
            row["recency_boost"] = scores.get("recency_boost")
            row["source_folder_boost"] = scores.get("source_folder_boost")
            row["file_type_boost"] = scores.get("file_type_boost")
            row["excerpt"] = normalize_inline(row.get("excerpt"))
            writer.writerow(row)


def resolve_paths(
    base_dir: Path,
    chroma_dir_arg: str | None,
    chunks_arg: str | None,
) -> SearchPaths:
    return SearchPaths(
        base_dir=base_dir,
        chroma_dir=Path(chroma_dir_arg) if chroma_dir_arg else base_dir / CHROMA_DIR,
        chunks_jsonl=Path(chunks_arg) if chunks_arg else base_dir / CHUNKS_JSONL,
        embedding_summary_json=base_dir / EMBEDDING_SUMMARY_JSON,
        evidence_json=base_dir / OUTPUT_EVIDENCE_JSON,
        evidence_md=base_dir / OUTPUT_EVIDENCE_MD,
        evidence_csv=base_dir / OUTPUT_EVIDENCE_CSV,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def tokenize_query(query: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-zČĆŽŠĐčćžšđ0-9_%-]+", query.lower())
    tokens = []

    for token in raw_tokens:
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)

    # Unique, stable order.
    seen = set()
    output = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        output.append(token)

    return output


def keyword_overlap_score(query_tokens: list[str], text: str, metadata: dict[str, Any]) -> tuple[float, list[str]]:
    haystack = " ".join([
        text,
        str(metadata.get("file_name") or ""),
        str(metadata.get("source_path") or ""),
        str(metadata.get("section_label") or ""),
    ]).lower()

    if not query_tokens:
        return 0.0, []

    hit_weight = 0.0
    max_weight = 0.0
    hits: list[str] = []

    for token in query_tokens:
        weight = KEYWORD_IMPORTANCE.get(token, 1.0)
        max_weight += weight
        if token in haystack:
            hit_weight += weight
            hits.append(token)

    if max_weight <= 0:
        return 0.0, hits

    return round(min(hit_weight / max_weight, 1.0), 6), hits


def semantic_score_from_distance(distance: Any) -> float:
    """
    Chroma cosine distance generally lower is better.
    Convert conservatively into 0..1 score.
    """
    d = safe_float(distance, 1.0)
    if d < 0:
        d = 0.0
    score = 1.0 / (1.0 + d)
    return round(min(max(score, 0.0), 1.0), 6)


def recency_boost(source_modified_time_utc: Any) -> float:
    if not source_modified_time_utc:
        return 0.0

    try:
        dt = datetime.fromisoformat(str(source_modified_time_utc).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_days = max((now - dt).days, 0)

        if age_days <= 7:
            return 0.05
        if age_days <= 30:
            return 0.035
        if age_days <= 90:
            return 0.02
        if age_days <= 365:
            return 0.01
    except Exception:
        return 0.0

    return 0.0


def source_folder_boost(source_path: Any, query_tokens: list[str]) -> float:
    lower = str(source_path or "").lower().replace("/", "\\")
    boost = 0.0

    important_markers = {
        "vdr": 0.04,
        "eib": 0.05,
        "ebrd": 0.05,
        "ifc": 0.04,
        "capex": 0.04,
        "financial": 0.035,
        "business plan": 0.035,
        "ssot": 0.04,
        "audit": 0.03,
        "control_tower": 0.035,
        "control tower": 0.035,
        "legal": 0.03,
        "contract": 0.03,
        "risk": 0.03,
    }

    for marker, value in important_markers.items():
        if marker in lower:
            boost += value

    # If token appears in path, add a small path-specific boost.
    for token in query_tokens:
        if token in lower:
            boost += 0.01

    return round(min(boost, 0.12), 6)


def file_type_boost(extension: Any) -> float:
    ext = str(extension or "").lower().strip()

    weights = {
        ".xlsx": 0.04,
        ".xlsm": 0.04,
        ".docx": 0.035,
        ".pdf": 0.035,
        ".pptx": 0.025,
        ".csv": 0.025,
        ".md": 0.015,
        ".py": 0.015,
        ".json": 0.010,
        ".jsonl": 0.010,
        ".log": 0.015,
        ".txt": 0.005,
    }

    return weights.get(ext, 0.0)


def calculate_final_score(
    semantic_score: float,
    keyword_score: float,
    keyword_boost: float,
    recency: float,
    folder: float,
    file_type: float,
) -> float:
    final = (
        semantic_score * 0.62
        + keyword_score * 0.28
        + keyword_boost
        + recency
        + folder
        + file_type
    )

    return round(min(max(final, 0.0), 1.0), 6)


def make_excerpt(text: str, query_tokens: list[str], max_chars: int) -> str:
    clean = normalize_space(text)

    if max_chars <= 0 or len(clean) <= max_chars:
        return clean

    lower = clean.lower()
    best_pos = None

    for token in query_tokens:
        idx = lower.find(token.lower())
        if idx >= 0:
            best_pos = idx
            break

    if best_pos is None:
        return clean[:max_chars].rstrip() + " ...[TRUNCATED]"

    half = max_chars // 2
    start = max(0, best_pos - half)
    end = min(len(clean), start + max_chars)

    if end - start < max_chars:
        start = max(0, end - max_chars)

    prefix = "... " if start > 0 else ""
    suffix = " ...[TRUNCATED]" if end < len(clean) else ""

    return prefix + clean[start:end].strip() + suffix


def import_chromadb():
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        return chromadb, embedding_functions
    except ImportError as exc:
        raise ImportError("Missing dependencies. Install with: pip install chromadb sentence-transformers") from exc


def get_collection(
    chromadb_module: Any,
    embedding_functions_module: Any,
    paths: SearchPaths,
    collection_name: str,
    embedding_model: str,
):
    if not paths.chroma_dir.exists():
        raise FileNotFoundError(f"Missing ChromaDB directory: {paths.chroma_dir}. Run Step 05 first.")

    client = chromadb_module.PersistentClient(path=str(paths.chroma_dir))

    embedding_function = embedding_functions_module.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model
    )

    collection = client.get_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )

    return client, collection


def chroma_query(
    collection: Any,
    query: str,
    top_k_raw: int,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "query_texts": [query],
        "n_results": top_k_raw,
        "include": ["documents", "metadatas", "distances"],
    }

    if where:
        kwargs["where"] = where

    return collection.query(**kwargs)


def load_chunk_fallback_map(chunks_jsonl: Path, max_records: int | None = None) -> dict[str, dict[str, Any]]:
    chunks = read_jsonl(chunks_jsonl, max_records=max_records)
    output: dict[str, dict[str, Any]] = {}

    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "").strip()
        if chunk_id:
            output[chunk_id] = chunk

    return output


def parse_query_result(
    raw: dict[str, Any],
    query: str,
    query_tokens: list[str],
    chunk_fallback: dict[str, dict[str, Any]],
    max_excerpt_chars: int,
) -> list[dict[str, Any]]:
    ids = (raw.get("ids") or [[]])[0] if raw.get("ids") else []
    documents = (raw.get("documents") or [[]])[0] if raw.get("documents") else []
    metadatas = (raw.get("metadatas") or [[]])[0] if raw.get("metadatas") else []
    distances = (raw.get("distances") or [[]])[0] if raw.get("distances") else []

    evidence: list[dict[str, Any]] = []

    for idx, chunk_id in enumerate(ids):
        doc_text = documents[idx] if idx < len(documents) else ""
        metadata = metadatas[idx] if idx < len(metadatas) and isinstance(metadatas[idx], dict) else {}
        distance = distances[idx] if idx < len(distances) else None

        fallback = chunk_fallback.get(str(chunk_id), {})
        if not doc_text and fallback:
            doc_text = fallback.get("text") or ""

        merged_metadata = dict(fallback)
        merged_metadata.update(metadata)

        semantic = semantic_score_from_distance(distance)
        keyword_score, keyword_hits = keyword_overlap_score(query_tokens, doc_text, merged_metadata)

        # Intentional small boost for exact important keyword hits.
        keyword_boost = 0.0
        for hit in keyword_hits:
            keyword_boost += min(KEYWORD_IMPORTANCE.get(hit, 1.0) - 1.0, 0.35) * 0.04
        keyword_boost = round(min(keyword_boost, 0.10), 6)

        recency = recency_boost(merged_metadata.get("source_modified_time_utc"))
        folder = source_folder_boost(merged_metadata.get("source_path"), query_tokens)
        ftype = file_type_boost(merged_metadata.get("extension"))

        final_score = calculate_final_score(
            semantic_score=semantic,
            keyword_score=keyword_score,
            keyword_boost=keyword_boost,
            recency=recency,
            folder=folder,
            file_type=ftype,
        )

        excerpt = make_excerpt(doc_text, query_tokens=query_tokens, max_chars=max_excerpt_chars)

        evidence.append({
            "rank_raw": idx + 1,
            "chunk_id": str(chunk_id),
            "source_path": merged_metadata.get("source_path"),
            "processed_path": merged_metadata.get("processed_path"),
            "file_name": merged_metadata.get("file_name"),
            "extension": merged_metadata.get("extension"),
            "section_label": merged_metadata.get("section_label"),
            "chunk_index": safe_int(merged_metadata.get("chunk_index")),
            "chunk_count_for_file": safe_int(merged_metadata.get("chunk_count_for_file")),
            "source_modified_time_utc": merged_metadata.get("source_modified_time_utc"),
            "start_char": merged_metadata.get("start_char"),
            "end_char": merged_metadata.get("end_char"),
            "distance": safe_float(distance, None),
            "scores": {
                "final_score": final_score,
                "semantic_score": semantic,
                "keyword_overlap_score": keyword_score,
                "keyword_boost": keyword_boost,
                "recency_boost": recency,
                "source_folder_boost": folder,
                "file_type_boost": ftype,
            },
            "keyword_hits": keyword_hits,
            "excerpt": excerpt,
            "excerpt_sha256": hashlib.sha256(excerpt.encode("utf-8", errors="ignore")).hexdigest(),
            "metadata": {
                "source_sha256": merged_metadata.get("source_sha256"),
                "text_sha256": merged_metadata.get("text_sha256"),
                "chunk_sha256": merged_metadata.get("chunk_sha256"),
                "chunk_chars": merged_metadata.get("chunk_chars"),
                "chunk_words": merged_metadata.get("chunk_words"),
                "chunking_strategy": merged_metadata.get("chunking_strategy"),
            },
        })

    return evidence


def deduplicate_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_chunks: set[str] = set()
    seen_source_excerpt: set[str] = set()
    output: list[dict[str, Any]] = []

    for item in evidence:
        chunk_id = str(item.get("chunk_id") or "")
        source = str(item.get("source_path") or "")
        excerpt_hash = str(item.get("excerpt_sha256") or "")
        key = f"{source}::{excerpt_hash}"

        if chunk_id and chunk_id in seen_chunks:
            continue

        if key in seen_source_excerpt:
            continue

        if chunk_id:
            seen_chunks.add(chunk_id)
        seen_source_excerpt.add(key)
        output.append(item)

    return output


def filter_and_rank_evidence(
    evidence: list[dict[str, Any]],
    top_k_final: int,
    min_score: float | None,
) -> list[dict[str, Any]]:
    ranked = sorted(
        evidence,
        key=lambda x: safe_float((x.get("scores") or {}).get("final_score")),
        reverse=True,
    )

    if min_score is not None:
        ranked = [
            item for item in ranked
            if safe_float((item.get("scores") or {}).get("final_score")) >= min_score
        ]

    ranked = ranked[:top_k_final]

    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx

    return ranked


def build_evidence_pack(
    query: str,
    evidence: list[dict[str, Any]],
    collection_name: str,
    embedding_model: str,
    collection_count: int | None,
    parameters: dict[str, Any],
    embedding_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    source_paths = sorted({
        str(item.get("source_path"))
        for item in evidence
        if item.get("source_path")
    })

    chunk_ids = [item.get("chunk_id") for item in evidence if item.get("chunk_id")]

    score_values = [
        safe_float((item.get("scores") or {}).get("final_score"))
        for item in evidence
    ]

    pack = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "RETRIEVAL_ONLY_EVIDENCE_PACK_AUDIT_LOCKED",
        "query": query,
        "query_sha256": hashlib.sha256(query.encode("utf-8", errors="ignore")).hexdigest(),
        "collection_name": collection_name,
        "embedding_model": embedding_model,
        "collection_count": collection_count,
        "retrieval_parameters": parameters,
        "embedding_summary_reference": {
            "available": embedding_summary is not None,
            "status": (embedding_summary or {}).get("status"),
            "embedding_model": (embedding_summary or {}).get("embedding_model"),
            "collection_count_after_run": (embedding_summary or {}).get("collection_count_after_run"),
        },
        "evidence_count": len(evidence),
        "source_file_count": len(source_paths),
        "source_files": source_paths,
        "chunk_ids": chunk_ids,
        "score_summary": {
            "max_final_score": round(max(score_values), 6) if score_values else None,
            "min_final_score": round(min(score_values), 6) if score_values else None,
            "average_final_score": round(sum(score_values) / len(score_values), 6) if score_values else None,
        },
        "evidence": evidence,
        "governance_rule": {
            "retrieval_only": True,
            "no_generation": True,
            "no_evidence_no_answer": True,
            "source_path_required": True,
            "chunk_id_required": True,
            "audit_precedes_decision": True,
        },
    }

    pack["evidence_pack_sha256"] = sha256_json(pack)
    return pack


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def evidence_to_markdown(pack: dict[str, Any]) -> str:
    evidence = pack.get("evidence", [])
    score_summary = pack.get("score_summary", {})

    rows = [
        "| Rank | Score | File | Section | Chunk ID | Excerpt |",
        "|---:|---:|---|---|---|---|",
    ]

    for item in evidence:
        scores = item.get("scores", {}) if isinstance(item.get("scores"), dict) else {}
        excerpt = md_escape(item.get("excerpt"))
        if len(excerpt) > 900:
            excerpt = excerpt[:900] + " ..."
        rows.append(
            f"| {item.get('rank')} | "
            f"{scores.get('final_score')} | "
            f"{md_escape(item.get('file_name'))} | "
            f"{md_escape(item.get('section_label'))} | "
            f"`{md_escape(item.get('chunk_id'))}` | "
            f"{excerpt} |"
        )

    return f"""# TITAN RAG Latest Evidence Pack

## 1. Retrieval Identity

| Field | Value |
|---|---|
| Created At | {pack.get("created_at")} |
| Query | {md_escape(pack.get("query"))} |
| Policy | {pack.get("policy")} |
| Evidence Count | {pack.get("evidence_count")} |
| Source File Count | {pack.get("source_file_count")} |
| Collection | {pack.get("collection_name")} |
| Embedding Model | {pack.get("embedding_model")} |
| Collection Count | {pack.get("collection_count")} |
| Evidence Pack SHA-256 | `{pack.get("evidence_pack_sha256")}` |

---

## 2. Score Summary

| Metric | Value |
|---|---:|
| Max Final Score | {score_summary.get("max_final_score")} |
| Min Final Score | {score_summary.get("min_final_score")} |
| Average Final Score | {score_summary.get("average_final_score")} |

---

## 3. Evidence

{chr(10).join(rows)}

---

## 4. Governance Rule

```text
Retrieval only.
No generation.
No evidence -> no answer.
Source path and chunk ID are mandatory for institutional use.
```
"""


def print_summary(pack: dict[str, Any], paths: SearchPaths) -> None:
    score_summary = pack.get("score_summary", {})

    print("=" * 100)
    print("TITAN RAG SEARCH / RETRIEVAL v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Query:                 {pack.get('query')}")
    print(f"Evidence count:        {pack.get('evidence_count')}")
    print(f"Source file count:     {pack.get('source_file_count')}")
    print(f"Collection:            {pack.get('collection_name')}")
    print(f"Collection count:      {pack.get('collection_count')}")
    print(f"Max score:             {score_summary.get('max_final_score')}")
    print(f"Average score:         {score_summary.get('average_final_score')}")
    print("-" * 100)
    print(f"Evidence JSON:         {paths.evidence_json}")
    print(f"Evidence Markdown:     {paths.evidence_md}")
    print(f"Evidence CSV:          {paths.evidence_csv}")
    print(f"Audit log:             {paths.audit_log}")
    print("=" * 100)


def parse_where_filter(args: argparse.Namespace) -> dict[str, Any] | None:
    conditions = []

    if args.extension:
        values = [str(x).lower() for x in args.extension]
        if len(values) == 1:
            conditions.append({"extension": values[0]})
        else:
            conditions.append({"extension": {"$in": values}})

    if args.source_contains:
        # Chroma does not support contains on metadata in all versions.
        # Keep this as post-filter via source_contains_post instead.
        pass

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}


def post_filter_source_contains(evidence: list[dict[str, Any]], source_contains: list[str] | None) -> list[dict[str, Any]]:
    if not source_contains:
        return evidence

    markers = [m.lower() for m in source_contains if str(m).strip()]
    if not markers:
        return evidence

    output = []
    for item in evidence:
        source = str(item.get("source_path") or "").lower()
        if any(marker in source for marker in markers):
            output.append(item)

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 06 — retrieve source evidence from local vector index."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--query",
        required=True,
        help="Search query.",
    )

    parser.add_argument(
        "--chroma-dir",
        default=None,
        help="Optional ChromaDB directory.",
    )

    parser.add_argument(
        "--chunks",
        default=None,
        help="Optional chunks.jsonl fallback path.",
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help="ChromaDB collection name.",
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Embedding model name used by the Chroma collection.",
    )

    parser.add_argument(
        "--top-k-raw",
        type=int,
        default=DEFAULT_TOP_K_RAW,
        help="Raw vector results requested from Chroma.",
    )

    parser.add_argument(
        "--top-k-final",
        type=int,
        default=DEFAULT_TOP_K_FINAL,
        help="Final evidence items kept after reranking.",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Optional final_score threshold.",
    )

    parser.add_argument(
        "--max-excerpt-chars",
        type=int,
        default=DEFAULT_MAX_EXCERPT_CHARS,
        help="Maximum excerpt characters per evidence item.",
    )

    parser.add_argument(
        "--extension",
        action="append",
        default=None,
        help="Metadata filter by extension. Can be repeated, e.g. --extension .pdf --extension .docx",
    )

    parser.add_argument(
        "--source-contains",
        action="append",
        default=None,
        help="Post-filter results whose source_path contains marker. Can be repeated.",
    )

    parser.add_argument(
        "--fallback-max-chunks",
        type=int,
        default=None,
        help="Optional cap for loading chunks.jsonl fallback map.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print Markdown evidence pack to console.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, chroma_dir_arg=args.chroma_dir, chunks_arg=args.chunks)

    started_at = utc_now_iso()

    try:
        query = normalize_inline(args.query)

        if len(query) < MIN_QUERY_LENGTH:
            raise ValueError("Query is too short.")

        if args.top_k_raw <= 0 or args.top_k_final <= 0:
            raise ValueError("--top-k-raw and --top-k-final must be positive.")

        if args.top_k_final > args.top_k_raw:
            args.top_k_raw = args.top_k_final

        query_tokens = tokenize_query(query)

        embedding_summary = read_json_if_exists(paths.embedding_summary_json)
        chunk_fallback = load_chunk_fallback_map(paths.chunks_jsonl, max_records=args.fallback_max_chunks)

        chromadb_module, embedding_functions_module = import_chromadb()

        _, collection = get_collection(
            chromadb_module=chromadb_module,
            embedding_functions_module=embedding_functions_module,
            paths=paths,
            collection_name=str(args.collection),
            embedding_model=str(args.model),
        )

        try:
            collection_count = collection.count()
        except Exception:
            collection_count = None

        where = parse_where_filter(args)

        raw = chroma_query(
            collection=collection,
            query=query,
            top_k_raw=int(args.top_k_raw),
            where=where,
        )

        evidence_raw = parse_query_result(
            raw=raw,
            query=query,
            query_tokens=query_tokens,
            chunk_fallback=chunk_fallback,
            max_excerpt_chars=int(args.max_excerpt_chars),
        )

        evidence_raw = post_filter_source_contains(evidence_raw, args.source_contains)
        evidence_raw = deduplicate_evidence(evidence_raw)

        evidence_final = filter_and_rank_evidence(
            evidence=evidence_raw,
            top_k_final=int(args.top_k_final),
            min_score=args.min_score,
        )

        parameters = {
            "top_k_raw": int(args.top_k_raw),
            "top_k_final": int(args.top_k_final),
            "min_score": args.min_score,
            "max_excerpt_chars": int(args.max_excerpt_chars),
            "extension_filter": args.extension,
            "source_contains": args.source_contains,
            "where_filter": where,
            "query_tokens": query_tokens,
            "fallback_chunks_loaded": len(chunk_fallback),
        }

        pack = build_evidence_pack(
            query=query,
            evidence=evidence_final,
            collection_name=str(args.collection),
            embedding_model=str(args.model),
            collection_count=collection_count,
            parameters=parameters,
            embedding_summary=embedding_summary,
        )

        markdown = evidence_to_markdown(pack)

        write_json(paths.evidence_json, pack)
        write_text(paths.evidence_md, markdown)
        write_csv(paths.evidence_csv, evidence_final)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "RAG_SEARCH_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "query": query,
            "started_at": started_at,
            "ended_at": utc_now_iso(),
            "outputs": {
                "evidence_json": str(paths.evidence_json),
                "evidence_md": str(paths.evidence_md),
                "evidence_csv": str(paths.evidence_csv),
            },
            "summary": {
                "evidence_count": pack.get("evidence_count"),
                "source_file_count": pack.get("source_file_count"),
                "score_summary": pack.get("score_summary"),
                "collection_count": collection_count,
            },
            "evidence_pack_sha256": pack.get("evidence_pack_sha256"),
        })

        print_summary(pack, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "RAG_SEARCH_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "query": getattr(args, "query", None),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG SEARCH / RETRIEVAL FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
