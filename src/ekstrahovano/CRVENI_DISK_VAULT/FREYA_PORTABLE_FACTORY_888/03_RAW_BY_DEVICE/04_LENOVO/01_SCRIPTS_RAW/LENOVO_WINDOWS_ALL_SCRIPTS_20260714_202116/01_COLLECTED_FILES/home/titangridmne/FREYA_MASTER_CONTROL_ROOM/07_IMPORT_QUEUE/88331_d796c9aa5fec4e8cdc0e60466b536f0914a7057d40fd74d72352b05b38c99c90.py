#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_chunk_text.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 04 — Evidence Chunking Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Read only extraction_manifest.jsonl records from Step 03 where chunking_allowed=True
and produce deterministic, traceable text chunks for Step 05 embeddings.

This script does NOT use AI.
This script does NOT generate answers.
This script does NOT read unsafe source files.
This script reads only controlled extracted .txt artifacts.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Input
-----
02_extracted/extraction_manifest.jsonl
02_extracted/texts/*.txt

Outputs
-------
03_chunks/chunks.jsonl
03_chunks/chunks.csv
03_chunks/chunk_manifest.json
05_reports/chunking_summary.json
06_logs/chunking_audit.jsonl
06_logs/chunking_errors.jsonl

Designed for compatibility with:
05_build_embeddings.py
06_search_rag.py
09_incremental_refresh.py
18_document_priority_ranker.py
20_rag_control_tower_export.py

Recommended command
-------------------
python ".\\08_scripts\\04_chunk_text.py"

Custom chunk size
-----------------
python ".\\08_scripts\\04_chunk_text.py" --chunk-size 1200 --overlap 180
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


SCRIPT_NAME = "04_chunk_text.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_MANIFEST = Path("02_extracted") / "extraction_manifest.jsonl"

OUTPUT_CHUNKS_JSONL = Path("03_chunks") / "chunks.jsonl"
OUTPUT_CHUNKS_CSV = Path("03_chunks") / "chunks.csv"
OUTPUT_CHUNK_MANIFEST = Path("03_chunks") / "chunk_manifest.json"

SUMMARY_JSON = Path("05_reports") / "chunking_summary.json"
AUDIT_LOG = Path("06_logs") / "chunking_audit.jsonl"
ERROR_LOG = Path("06_logs") / "chunking_errors.jsonl"

STATUS_CHUNKED = "CHUNKED"
STATUS_SKIPPED_NOT_ALLOWED = "SKIPPED_NOT_ALLOWED"
STATUS_SKIPPED_MISSING_TEXT = "SKIPPED_MISSING_TEXT"
STATUS_SKIPPED_EMPTY_TEXT = "SKIPPED_EMPTY_TEXT"
STATUS_CHUNKING_ERROR = "CHUNKING_ERROR"

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_OVERLAP = 180
DEFAULT_MIN_CHUNK_CHARS = 120
DEFAULT_MAX_CHUNKS_PER_FILE = 5000


@dataclass(frozen=True)
class ChunkPaths:
    base_dir: Path
    input_manifest: Path
    chunks_jsonl: Path
    chunks_csv: Path
    chunk_manifest: Path
    summary_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_space(text: str) -> str:
    text = str(text or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Keep paragraph boundaries but normalize excessive blank lines.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_chunk_text(text: str) -> str:
    text = normalize_space(text)
    # Remove extremely repetitive separator noise.
    text = re.sub(r"[-_=]{8,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def short_hash(value: str, length: int = 16) -> str:
    return sha256_text(value)[:length]


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "chunk_id",
        "chunk_index",
        "chunk_count_for_file",
        "chunk_chars",
        "chunk_words",
        "chunk_sha256",
        "source_path",
        "processed_path",
        "file_name",
        "extension",
        "source_sha256",
        "text_sha256",
        "source_modified_time_utc",
        "section_label",
        "start_char",
        "end_char",
        "overlap_chars",
        "chunking_strategy",
        "created_at",
        "script",
        "script_version",
        "text_preview",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for record in records:
            row = dict(record)
            row["text_preview"] = str(row.get("text") or "")[:500].replace("\n", " ")
            writer.writerow(row)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing extraction manifest: {path}")

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
                else:
                    records.append({
                        "processed_path": None,
                        "chunking_allowed": False,
                        "extraction_status": "INVALID_JSONL",
                        "extraction_reason": f"Line {line_no} is not JSON object",
                    })
            except Exception as exc:
                records.append({
                    "processed_path": None,
                    "chunking_allowed": False,
                    "extraction_status": "INVALID_JSONL",
                    "extraction_reason": f"Invalid JSONL line {line_no}: {exc}",
                })

    return records


def resolve_paths(base_dir: Path, input_arg: str | None) -> ChunkPaths:
    return ChunkPaths(
        base_dir=base_dir,
        input_manifest=Path(input_arg) if input_arg else base_dir / INPUT_MANIFEST,
        chunks_jsonl=base_dir / OUTPUT_CHUNKS_JSONL,
        chunks_csv=base_dir / OUTPUT_CHUNKS_CSV,
        chunk_manifest=base_dir / OUTPUT_CHUNK_MANIFEST,
        summary_json=base_dir / SUMMARY_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def count_words(text: str) -> int:
    return len([x for x in text.split() if x.strip()])


def read_text_artifact(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Processed text artifact missing: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def find_section_label(text: str, position: int) -> str:
    """
    Conservative section label detection.
    Looks backward near the chunk start for document markers from previous steps:
    [SHEET: X], [PDF_PAGE N], [SLIDE N], [TABLE N], or a short heading-like line.
    """
    left = max(0, position - 2500)
    before = text[left:position]
    lines = [line.strip() for line in before.splitlines() if line.strip()]

    marker_patterns = [
        r"^\[SHEET:\s?.+\]$",
        r"^\[PDF_PAGE\s+\d+\]$",
        r"^\[SLIDE\s+\d+\]$",
        r"^\[TABLE\s+\d+\]$",
    ]

    for line in reversed(lines[-30:]):
        for pattern in marker_patterns:
            if re.match(pattern, line, flags=re.IGNORECASE):
                return line[:120]

    for line in reversed(lines[-15:]):
        if 4 <= len(line) <= 120:
            # Heading-like: not too much punctuation/noise.
            if len(re.findall(r"[A-Za-zČĆŽŠĐčćžšđ0-9]", line)) >= max(3, len(line) // 3):
                if not line.endswith(".") or line.isupper():
                    return line[:120]

    return "UNLABELED_SECTION"


def sentence_boundaries(text: str, target_start: int, target_end: int, hard_left: int, hard_right: int) -> tuple[int, int]:
    """
    Adjust boundaries lightly to avoid cutting mid-sentence, without exceeding hard bounds.
    """
    start = target_start
    end = target_end

    if start > hard_left:
        window_left = max(hard_left, start - 160)
        snippet = text[window_left:start]
        candidates = [snippet.rfind(x) for x in [". ", "\n", "; "]]
        best = max(candidates)
        if best >= 0:
            start = window_left + best + 1

    if end < hard_right:
        window_right = min(hard_right, end + 220)
        snippet = text[end:window_right]
        candidates = []
        for sep in [". ", "\n", "; "]:
            idx = snippet.find(sep)
            if idx >= 0:
                candidates.append(idx + len(sep))
        if candidates:
            end = end + min(candidates)

    start = max(hard_left, min(start, hard_right))
    end = max(start, min(end, hard_right))
    return start, end


def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int,
    min_chunk_chars: int,
    max_chunks_per_file: int,
    preserve_sentences: bool,
) -> list[dict[str, Any]]:
    text = normalize_space(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[dict[str, Any]] = []
    text_len = len(text)
    step = chunk_size - overlap
    raw_index = 0
    start = 0

    while start < text_len and raw_index < max_chunks_per_file:
        raw_index += 1
        target_end = min(text_len, start + chunk_size)

        adjusted_start = start
        adjusted_end = target_end

        if preserve_sentences:
            adjusted_start, adjusted_end = sentence_boundaries(
                text=text,
                target_start=start,
                target_end=target_end,
                hard_left=max(0, start - overlap),
                hard_right=min(text_len, target_end + overlap),
            )

        chunk_raw = text[adjusted_start:adjusted_end]
        chunk_clean = clean_chunk_text(chunk_raw)

        if len(chunk_clean) >= min_chunk_chars or target_end >= text_len:
            chunks.append({
                "text": chunk_clean,
                "start_char": adjusted_start,
                "end_char": adjusted_end,
            })

        if target_end >= text_len:
            break

        start += step

    return chunks


def build_chunk_id(
    source_path: Any,
    processed_path: Any,
    source_sha256: Any,
    text_sha256: Any,
    chunk_index: int,
    chunk_sha256: str,
) -> str:
    raw = json.dumps({
        "source_path": source_path,
        "processed_path": processed_path,
        "source_sha256": source_sha256,
        "text_sha256": text_sha256,
        "chunk_index": chunk_index,
        "chunk_sha256": chunk_sha256,
    }, sort_keys=True, ensure_ascii=False)

    return "CHUNK_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def process_manifest_record(
    manifest_record: dict[str, Any],
    chunk_size: int,
    overlap: int,
    min_chunk_chars: int,
    max_chunks_per_file: int,
    preserve_sentences: bool,
    error_log: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_path = manifest_record.get("source_path")
    processed_path_value = manifest_record.get("processed_path")
    chunking_allowed = bool(manifest_record.get("chunking_allowed"))
    extraction_status = str(manifest_record.get("extraction_status") or "")

    base_file_result = {
        "source_path": source_path,
        "processed_path": processed_path_value,
        "file_name": manifest_record.get("file_name"),
        "extension": manifest_record.get("extension"),
        "extraction_status": extraction_status,
        "chunking_status": None,
        "chunking_reason": None,
        "chunks_created": 0,
        "text_chars": manifest_record.get("text_chars"),
        "text_words": manifest_record.get("text_words"),
    }

    if not chunking_allowed:
        base_file_result["chunking_status"] = STATUS_SKIPPED_NOT_ALLOWED
        base_file_result["chunking_reason"] = "Manifest record chunking_allowed is not true"
        return [], base_file_result

    if not processed_path_value:
        base_file_result["chunking_status"] = STATUS_SKIPPED_MISSING_TEXT
        base_file_result["chunking_reason"] = "Missing processed_path"
        return [], base_file_result

    processed_path = Path(str(processed_path_value))

    if not processed_path.exists():
        base_file_result["chunking_status"] = STATUS_SKIPPED_MISSING_TEXT
        base_file_result["chunking_reason"] = "Processed text file does not exist"
        return [], base_file_result

    try:
        text = read_text_artifact(processed_path)
        text = normalize_space(text)

        if not text:
            base_file_result["chunking_status"] = STATUS_SKIPPED_EMPTY_TEXT
            base_file_result["chunking_reason"] = "Processed text is empty"
            return [], base_file_result

        raw_chunks = chunk_text(
            text=text,
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_chars=min_chunk_chars,
            max_chunks_per_file=max_chunks_per_file,
            preserve_sentences=preserve_sentences,
        )

        chunk_records: list[dict[str, Any]] = []
        chunk_count = len(raw_chunks)

        for idx, chunk in enumerate(raw_chunks, start=1):
            chunk_body = chunk["text"]
            chunk_sha = sha256_text(chunk_body)
            section_label = find_section_label(text, safe_int(chunk.get("start_char")))

            chunk_id = build_chunk_id(
                source_path=source_path,
                processed_path=processed_path_value,
                source_sha256=manifest_record.get("source_sha256"),
                text_sha256=manifest_record.get("text_sha256"),
                chunk_index=idx,
                chunk_sha256=chunk_sha,
            )

            chunk_records.append({
                "chunk_id": chunk_id,
                "chunk_index": idx,
                "chunk_count_for_file": chunk_count,
                "text": chunk_body,
                "chunk_chars": len(chunk_body),
                "chunk_words": count_words(chunk_body),
                "chunk_sha256": chunk_sha,
                "source_path": source_path,
                "processed_path": processed_path_value,
                "file_name": manifest_record.get("file_name"),
                "extension": manifest_record.get("extension"),
                "source_sha256": manifest_record.get("source_sha256"),
                "text_sha256": manifest_record.get("text_sha256"),
                "source_modified_time_utc": manifest_record.get("source_modified_time_utc"),
                "section_label": section_label,
                "start_char": chunk.get("start_char"),
                "end_char": chunk.get("end_char"),
                "overlap_chars": overlap,
                "chunking_strategy": "sliding_window_sentence_aware" if preserve_sentences else "sliding_window_fixed",
                "created_at": utc_now_iso(),
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "metadata": {
                    "extractor": manifest_record.get("extractor"),
                    "source_size_bytes": manifest_record.get("source_size_bytes"),
                    "source_record_safety_status": manifest_record.get("source_record_safety_status"),
                    "extraction_status": extraction_status,
                },
            })

        base_file_result["chunking_status"] = STATUS_CHUNKED
        base_file_result["chunking_reason"] = "Chunks created successfully"
        base_file_result["chunks_created"] = chunk_count

        return chunk_records, base_file_result

    except Exception as exc:
        base_file_result["chunking_status"] = STATUS_CHUNKING_ERROR
        base_file_result["chunking_reason"] = str(exc)

        append_jsonl(error_log, {
            "timestamp": utc_now_iso(),
            "event": "FILE_CHUNKING_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "source_path": source_path,
            "processed_path": processed_path_value,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        return [], base_file_result


def deduplicate_chunks(chunks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen_ids: set[str] = set()
    seen_hash_source: set[str] = set()
    output: list[dict[str, Any]] = []
    duplicate_count = 0

    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "")
        key = f"{chunk.get('source_path')}::{chunk.get('chunk_sha256')}"

        if chunk_id in seen_ids or key in seen_hash_source:
            duplicate_count += 1
            continue

        seen_ids.add(chunk_id)
        seen_hash_source.add(key)
        output.append(chunk)

    return output, duplicate_count


def summarize(
    started_at: str,
    ended_at: str,
    paths: ChunkPaths,
    manifest_records: int,
    file_results: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    duplicate_chunks_removed: int,
    chunk_size: int,
    overlap: int,
    min_chunk_chars: int,
    max_chunks_per_file: int,
    preserve_sentences: bool,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    extension_counts: dict[str, int] = {}
    chunk_size_stats: list[int] = []

    chunked_files = 0
    skipped_files = 0
    error_files = 0

    for result in file_results:
        status = str(result.get("chunking_status") or "UNKNOWN")
        ext = str(result.get("extension") or "[no extension]")

        status_counts[status] = status_counts.get(status, 0) + 1
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

        if status == STATUS_CHUNKED:
            chunked_files += 1
        elif status == STATUS_CHUNKING_ERROR:
            error_files += 1
        else:
            skipped_files += 1

    for chunk in chunks:
        chunk_size_stats.append(safe_int(chunk.get("chunk_chars")))

    total_chunk_chars = sum(chunk_size_stats)
    avg_chunk_chars = round(total_chunk_chars / len(chunk_size_stats), 2) if chunk_size_stats else 0.0

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "EVIDENCE_CHUNKING_AUDIT_LOCKED",
        "input_manifest": str(paths.input_manifest),
        "manifest_records": manifest_records,
        "file_results": len(file_results),
        "chunked_files": chunked_files,
        "skipped_files": skipped_files,
        "error_files": error_files,
        "total_chunks": len(chunks),
        "duplicate_chunks_removed": duplicate_chunks_removed,
        "total_chunk_chars": total_chunk_chars,
        "average_chunk_chars": avg_chunk_chars,
        "min_chunk_chars_actual": min(chunk_size_stats) if chunk_size_stats else 0,
        "max_chunk_chars_actual": max(chunk_size_stats) if chunk_size_stats else 0,
        "parameters": {
            "chunk_size": chunk_size,
            "overlap": overlap,
            "min_chunk_chars": min_chunk_chars,
            "max_chunks_per_file": max_chunks_per_file,
            "preserve_sentences": preserve_sentences,
        },
        "status_counts": dict(sorted(status_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "outputs": {
            "chunks_jsonl": str(paths.chunks_jsonl),
            "chunks_csv": str(paths.chunks_csv),
            "chunk_manifest": str(paths.chunk_manifest),
            "summary_json": str(paths.summary_json),
        },
        "governance_rule": {
            "chunk_only_extracted_text": True,
            "source_file_remains_authoritative": True,
            "stable_chunk_ids_required": True,
            "chunk_metadata_required_for_citations": True,
            "embedding_step_requires_chunks_jsonl": True,
        },
    }


def print_summary(summary: dict[str, Any]) -> None:
    print("=" * 100)
    print("TITAN RAG EVIDENCE CHUNKING v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Started:                    {summary['started_at']}")
    print(f"Ended:                      {summary['ended_at']}")
    print(f"Policy:                     {summary['policy']}")
    print(f"Manifest records:            {summary['manifest_records']}")
    print(f"Chunked files:               {summary['chunked_files']}")
    print(f"Skipped files:               {summary['skipped_files']}")
    print(f"Error files:                 {summary['error_files']}")
    print(f"Total chunks:                {summary['total_chunks']}")
    print(f"Duplicate chunks removed:    {summary['duplicate_chunks_removed']}")
    print(f"Average chunk chars:         {summary['average_chunk_chars']}")
    print("-" * 100)
    print("Status counts:")
    for key, value in summary["status_counts"].items():
        print(f" - {key}: {value}")
    print("-" * 100)
    for key, value in summary["outputs"].items():
        print(f"{key}: {value}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 04 — evidence chunking engine."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--input",
        default=None,
        help="Optional extraction_manifest.jsonl path.",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Target chunk size in characters.",
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP,
        help="Overlap in characters between chunks.",
    )

    parser.add_argument(
        "--min-chunk-chars",
        type=int,
        default=DEFAULT_MIN_CHUNK_CHARS,
        help="Minimum chunk size in characters, except final chunk.",
    )

    parser.add_argument(
        "--max-chunks-per-file",
        type=int,
        default=DEFAULT_MAX_CHUNKS_PER_FILE,
        help="Safety cap for chunks per extracted file.",
    )

    parser.add_argument(
        "--no-sentence-preserve",
        action="store_true",
        help="Disable light sentence-aware boundary adjustment.",
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap for testing.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read manifest and estimate eligible files without writing chunks.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, input_arg=args.input)

    started_at = utc_now_iso()

    try:
        if args.chunk_size <= 0:
            raise ValueError("--chunk-size must be positive")

        if args.overlap < 0:
            raise ValueError("--overlap cannot be negative")

        if args.overlap >= args.chunk_size:
            raise ValueError("--overlap must be smaller than --chunk-size")

        manifest_records = read_jsonl(paths.input_manifest)

        if args.max_records is not None:
            manifest_records = manifest_records[: int(args.max_records)]

        eligible_count = sum(1 for r in manifest_records if bool(r.get("chunking_allowed")))

        if args.dry_run:
            payload = {
                "started_at": started_at,
                "ended_at": utc_now_iso(),
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "policy": "DRY_RUN_NO_CHUNK_WRITE",
                "input_manifest": str(paths.input_manifest),
                "manifest_records": len(manifest_records),
                "eligible_chunking_records": eligible_count,
                "parameters": {
                    "chunk_size": args.chunk_size,
                    "overlap": args.overlap,
                    "min_chunk_chars": args.min_chunk_chars,
                    "max_chunks_per_file": args.max_chunks_per_file,
                    "preserve_sentences": not bool(args.no_sentence_preserve),
                },
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return

        all_chunks: list[dict[str, Any]] = []
        file_results: list[dict[str, Any]] = []

        preserve_sentences = not bool(args.no_sentence_preserve)

        for index, record in enumerate(manifest_records, start=1):
            chunks, file_result = process_manifest_record(
                manifest_record=record,
                chunk_size=int(args.chunk_size),
                overlap=int(args.overlap),
                min_chunk_chars=int(args.min_chunk_chars),
                max_chunks_per_file=int(args.max_chunks_per_file),
                preserve_sentences=preserve_sentences,
                error_log=paths.error_log,
            )

            all_chunks.extend(chunks)
            file_results.append(file_result)

            if index % 250 == 0:
                print(f"[CHUNKING] processed_files={index} chunks={len(all_chunks)}")

        all_chunks, duplicate_chunks_removed = deduplicate_chunks(all_chunks)

        ended_at = utc_now_iso()

        summary = summarize(
            started_at=started_at,
            ended_at=ended_at,
            paths=paths,
            manifest_records=len(manifest_records),
            file_results=file_results,
            chunks=all_chunks,
            duplicate_chunks_removed=duplicate_chunks_removed,
            chunk_size=int(args.chunk_size),
            overlap=int(args.overlap),
            min_chunk_chars=int(args.min_chunk_chars),
            max_chunks_per_file=int(args.max_chunks_per_file),
            preserve_sentences=preserve_sentences,
        )

        chunk_manifest = {
            "created_at": utc_now_iso(),
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "summary": summary,
            "file_results": file_results,
        }

        write_jsonl(paths.chunks_jsonl, all_chunks)
        write_csv(paths.chunks_csv, all_chunks)
        write_json(paths.chunk_manifest, chunk_manifest)
        write_json(paths.summary_json, summary)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "CHUNKING_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "input_manifest": str(paths.input_manifest),
            "summary": summary,
        })

        print_summary(summary)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "CHUNKING_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "input_manifest": str(paths.input_manifest),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG EVIDENCE CHUNKING FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
