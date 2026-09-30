#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_build_embeddings.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 05 — Embedding Build Engine
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Read evidence chunks from Step 04 and build/update a local vector index for
retrieval in Step 06.

This script does NOT use generative AI.
This script does NOT generate answers.
This script does NOT read unsafe source files.
This script indexes only controlled chunks from 03_chunks/chunks.jsonl.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Input
-----
03_chunks/chunks.jsonl

Outputs
-------
04_vectors/chroma_db/
04_vectors/embedding_manifest.jsonl
04_vectors/embedding_manifest.csv
05_reports/embedding_summary.json
06_logs/embedding_audit.jsonl
06_logs/embedding_errors.jsonl

Default embedding backend
-------------------------
sentence-transformers/all-MiniLM-L6-v2 via ChromaDB SentenceTransformerEmbeddingFunction.

Install
-------
pip install chromadb sentence-transformers

Recommended command
-------------------
python ".\\08_scripts\\05_build_embeddings.py"

Clean rebuild
-------------
python ".\\08_scripts\\05_build_embeddings.py" --reset

Smaller batch
-------------
python ".\\08_scripts\\05_build_embeddings.py" --batch-size 100
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_NAME = "05_build_embeddings.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

INPUT_CHUNKS_JSONL = Path("03_chunks") / "chunks.jsonl"

CHROMA_DIR = Path("04_vectors") / "chroma_db"
EMBEDDING_MANIFEST_JSONL = Path("04_vectors") / "embedding_manifest.jsonl"
EMBEDDING_MANIFEST_CSV = Path("04_vectors") / "embedding_manifest.csv"

SUMMARY_JSON = Path("05_reports") / "embedding_summary.json"
AUDIT_LOG = Path("06_logs") / "embedding_audit.jsonl"
ERROR_LOG = Path("06_logs") / "embedding_errors.jsonl"

DEFAULT_COLLECTION_NAME = "titan_local_evidence_chunks"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 250
DEFAULT_MAX_TEXT_CHARS = 6000

STATUS_EMBEDDED = "EMBEDDED"
STATUS_SKIPPED_EMPTY = "SKIPPED_EMPTY"
STATUS_SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"
STATUS_ERROR = "EMBEDDING_ERROR"


@dataclass(frozen=True)
class EmbeddingPaths:
    base_dir: Path
    chunks_jsonl: Path
    chroma_dir: Path
    manifest_jsonl: Path
    manifest_csv: Path
    summary_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(text: Any, max_chars: int) -> str:
    value = str(text or "").replace("\x00", "").strip()
    if max_chars > 0 and len(value) > max_chars:
        return value[:max_chars].rstrip() + "\n[TRUNCATED_FOR_EMBEDDING]"
    return value


def clean_metadata_value(value: Any) -> str | int | float | bool | None:
    """
    Chroma metadata accepts scalar primitives only.
    Convert lists/dicts to JSON strings.
    """
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


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
        "embedded_at",
        "embedding_status",
        "embedding_reason",
        "collection_name",
        "embedding_model",
        "embedding_id",
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
        "script",
        "script_version",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing chunks JSONL: {path}")

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
                        "chunk_id": f"INVALID_JSONL_LINE_{line_no}",
                        "text": "",
                        "error": "Line is not JSON object",
                    })
            except Exception as exc:
                records.append({
                    "chunk_id": f"INVALID_JSONL_LINE_{line_no}",
                    "text": "",
                    "error": f"Invalid JSONL line {line_no}: {exc}",
                })

    return records


def resolve_paths(base_dir: Path, input_arg: str | None, chroma_dir_arg: str | None) -> EmbeddingPaths:
    return EmbeddingPaths(
        base_dir=base_dir,
        chunks_jsonl=Path(input_arg) if input_arg else base_dir / INPUT_CHUNKS_JSONL,
        chroma_dir=Path(chroma_dir_arg) if chroma_dir_arg else base_dir / CHROMA_DIR,
        manifest_jsonl=base_dir / EMBEDDING_MANIFEST_JSONL,
        manifest_csv=base_dir / EMBEDDING_MANIFEST_CSV,
        summary_json=base_dir / SUMMARY_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def build_embedding_id(chunk: dict[str, Any]) -> str:
    """
    Stable Chroma ID. Prefer chunk_id from Step 04. If absent, derive deterministically.
    """
    chunk_id = str(chunk.get("chunk_id") or "").strip()
    if chunk_id:
        return chunk_id

    raw = json.dumps({
        "source_path": chunk.get("source_path"),
        "chunk_index": chunk.get("chunk_index"),
        "chunk_sha256": chunk.get("chunk_sha256"),
        "text_sha256": sha256_text(str(chunk.get("text") or "")),
    }, sort_keys=True, ensure_ascii=False)

    return "CHUNK_" + sha256_text(raw)[:24]


def metadata_from_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    keys = [
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
    ]

    metadata: dict[str, Any] = {}

    for key in keys:
        metadata[key] = clean_metadata_value(chunk.get(key))

    # Extra retrieval-friendly fields.
    metadata["titan_step"] = "04_CHUNK_TEXT"
    metadata["embedding_script"] = SCRIPT_NAME
    metadata["embedding_script_version"] = SCRIPT_VERSION

    # Chroma does not accept None values in some versions.
    return {k: v for k, v in metadata.items() if v is not None}


def manifest_record_from_chunk(
    chunk: dict[str, Any],
    status: str,
    reason: str,
    collection_name: str,
    embedding_model: str,
    embedding_id: str,
) -> dict[str, Any]:
    return {
        "embedded_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "embedding_status": status,
        "embedding_reason": reason,
        "collection_name": collection_name,
        "embedding_model": embedding_model,
        "embedding_id": embedding_id,
        "chunk_id": chunk.get("chunk_id"),
        "chunk_index": chunk.get("chunk_index"),
        "chunk_count_for_file": chunk.get("chunk_count_for_file"),
        "chunk_chars": chunk.get("chunk_chars"),
        "chunk_words": chunk.get("chunk_words"),
        "chunk_sha256": chunk.get("chunk_sha256"),
        "source_path": chunk.get("source_path"),
        "processed_path": chunk.get("processed_path"),
        "file_name": chunk.get("file_name"),
        "extension": chunk.get("extension"),
        "source_sha256": chunk.get("source_sha256"),
        "text_sha256": chunk.get("text_sha256"),
        "source_modified_time_utc": chunk.get("source_modified_time_utc"),
        "section_label": chunk.get("section_label"),
        "start_char": chunk.get("start_char"),
        "end_char": chunk.get("end_char"),
    }


def import_chromadb():
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        return chromadb, embedding_functions
    except ImportError as exc:
        raise ImportError(
            "Missing dependencies. Install with: pip install chromadb sentence-transformers"
        ) from exc


def get_collection(
    chromadb_module: Any,
    embedding_functions_module: Any,
    chroma_dir: Path,
    collection_name: str,
    embedding_model: str,
):
    chroma_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb_module.PersistentClient(path=str(chroma_dir))

    embedding_function = embedding_functions_module.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model
    )

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={
            "hnsw:space": "cosine",
            "titan_policy": "LOCAL_EVIDENCE_RAG_AUDIT_LOCKED",
            "embedding_model": embedding_model,
        },
    )

    return client, collection


def chunk_batches(items: list[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def prepare_chunks(
    chunks: list[dict[str, Any]],
    max_text_chars: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Returns valid_chunks, manifest_records_for_skips.
    Deduplicates by embedding_id and by chunk_sha/source.
    """
    valid: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_content_keys: set[str] = set()

    for chunk in chunks:
        embedding_id = build_embedding_id(chunk)
        text = normalize_text(chunk.get("text"), max_text_chars=max_text_chars)

        if not text.strip():
            skipped.append(
                manifest_record_from_chunk(
                    chunk=chunk,
                    status=STATUS_SKIPPED_EMPTY,
                    reason="Chunk text is empty",
                    collection_name="",
                    embedding_model="",
                    embedding_id=embedding_id,
                )
            )
            continue

        content_key = f"{chunk.get('source_path')}::{chunk.get('chunk_sha256') or sha256_text(text)}"

        if embedding_id in seen_ids or content_key in seen_content_keys:
            skipped.append(
                manifest_record_from_chunk(
                    chunk=chunk,
                    status=STATUS_SKIPPED_DUPLICATE,
                    reason="Duplicate embedding_id or source/chunk hash",
                    collection_name="",
                    embedding_model="",
                    embedding_id=embedding_id,
                )
            )
            continue

        seen_ids.add(embedding_id)
        seen_content_keys.add(content_key)

        prepared = dict(chunk)
        prepared["_embedding_id"] = embedding_id
        prepared["_embedding_text"] = text
        valid.append(prepared)

    return valid, skipped


def upsert_embeddings(
    collection: Any,
    chunks: list[dict[str, Any]],
    batch_size: int,
    collection_name: str,
    embedding_model: str,
    error_log: Path,
) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []

    total = len(chunks)
    processed = 0

    for batch_no, batch in enumerate(chunk_batches(chunks, batch_size), start=1):
        ids = [str(item["_embedding_id"]) for item in batch]
        documents = [str(item["_embedding_text"]) for item in batch]
        metadatas = [metadata_from_chunk(item) for item in batch]

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

            for item in batch:
                manifest.append(
                    manifest_record_from_chunk(
                        chunk=item,
                        status=STATUS_EMBEDDED,
                        reason="Chunk embedded/upserted successfully",
                        collection_name=collection_name,
                        embedding_model=embedding_model,
                        embedding_id=str(item["_embedding_id"]),
                    )
                )

        except Exception as exc:
            append_jsonl(error_log, {
                "timestamp": utc_now_iso(),
                "event": "EMBEDDING_BATCH_FAILED",
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "batch_no": batch_no,
                "batch_size": len(batch),
                "error": str(exc),
                "traceback": traceback.format_exc(),
            })

            for item in batch:
                manifest.append(
                    manifest_record_from_chunk(
                        chunk=item,
                        status=STATUS_ERROR,
                        reason=str(exc),
                        collection_name=collection_name,
                        embedding_model=embedding_model,
                        embedding_id=str(item["_embedding_id"]),
                    )
                )

        processed += len(batch)
        print(f"[EMBEDDING] batch={batch_no} processed={processed}/{total}")

    return manifest


def summarize(
    started_at: str,
    ended_at: str,
    paths: EmbeddingPaths,
    chunks_loaded: int,
    prepared_count: int,
    manifest: list[dict[str, Any]],
    collection_name: str,
    embedding_model: str,
    collection_count_after: int | None,
    reset: bool,
    batch_size: int,
    max_text_chars: int,
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    extension_counts: dict[str, int] = {}
    source_count: set[str] = set()

    embedded_count = 0
    error_count = 0
    skipped_count = 0

    for item in manifest:
        status = str(item.get("embedding_status") or "UNKNOWN")
        ext = str(item.get("extension") or "[no extension]")
        source = str(item.get("source_path") or "")

        status_counts[status] = status_counts.get(status, 0) + 1
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

        if source:
            source_count.add(source)

        if status == STATUS_EMBEDDED:
            embedded_count += 1
        elif status == STATUS_ERROR:
            error_count += 1
        elif status.startswith("SKIPPED"):
            skipped_count += 1

    final_status = "SUCCESS"
    if error_count > 0 and embedded_count > 0:
        final_status = "COMPLETED_WITH_ERRORS"
    elif error_count > 0 and embedded_count == 0:
        final_status = "FAILED"
    elif embedded_count == 0:
        final_status = "NO_EMBEDDINGS_CREATED"

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "LOCAL_VECTOR_INDEX_AUDIT_LOCKED",
        "status": final_status,
        "input_chunks_jsonl": str(paths.chunks_jsonl),
        "chroma_dir": str(paths.chroma_dir),
        "collection_name": collection_name,
        "embedding_model": embedding_model,
        "reset": reset,
        "batch_size": batch_size,
        "max_text_chars": max_text_chars,
        "chunks_loaded": chunks_loaded,
        "prepared_chunks": prepared_count,
        "manifest_records": len(manifest),
        "embedded_count": embedded_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "source_file_count": len(source_count),
        "collection_count_after_run": collection_count_after,
        "status_counts": dict(sorted(status_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "outputs": {
            "chroma_dir": str(paths.chroma_dir),
            "embedding_manifest_jsonl": str(paths.manifest_jsonl),
            "embedding_manifest_csv": str(paths.manifest_csv),
            "summary_json": str(paths.summary_json),
        },
        "governance_rule": {
            "embed_only_chunks_jsonl": True,
            "no_answer_generation": True,
            "source_file_remains_authoritative": True,
            "chunk_metadata_required_for_retrieval": True,
            "retrieval_step_requires_chroma_collection": True,
        },
    }


def print_summary(summary: dict[str, Any]) -> None:
    print("=" * 100)
    print("TITAN RAG EMBEDDING BUILD v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Started:                    {summary['started_at']}")
    print(f"Ended:                      {summary['ended_at']}")
    print(f"Status:                     {summary['status']}")
    print(f"Policy:                     {summary['policy']}")
    print(f"Collection:                 {summary['collection_name']}")
    print(f"Embedding model:            {summary['embedding_model']}")
    print(f"Chunks loaded:              {summary['chunks_loaded']}")
    print(f"Prepared chunks:            {summary['prepared_chunks']}")
    print(f"Embedded count:             {summary['embedded_count']}")
    print(f"Skipped count:              {summary['skipped_count']}")
    print(f"Error count:                {summary['error_count']}")
    print(f"Collection count after run: {summary['collection_count_after_run']}")
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
        description="TITAN RAG Step 05 — build local ChromaDB embeddings."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--input",
        default=None,
        help="Optional chunks.jsonl path.",
    )

    parser.add_argument(
        "--chroma-dir",
        default=None,
        help="Optional ChromaDB directory.",
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help="ChromaDB collection name.",
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="SentenceTransformer embedding model name.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Embedding upsert batch size.",
    )

    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=DEFAULT_MAX_TEXT_CHARS,
        help="Maximum text characters per chunk passed to embedding model.",
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap for test runs.",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing ChromaDB directory before indexing.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and validate chunks, but do not build embeddings.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, input_arg=args.input, chroma_dir_arg=args.chroma_dir)

    started_at = utc_now_iso()

    try:
        if args.batch_size <= 0:
            raise ValueError("--batch-size must be positive")

        chunks = read_jsonl(paths.chunks_jsonl)

        if args.max_records is not None:
            chunks = chunks[: int(args.max_records)]

        prepared_chunks, skipped_manifest = prepare_chunks(
            chunks=chunks,
            max_text_chars=int(args.max_text_chars),
        )

        if args.dry_run:
            payload = {
                "started_at": started_at,
                "ended_at": utc_now_iso(),
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "policy": "DRY_RUN_NO_EMBEDDINGS",
                "chunks_loaded": len(chunks),
                "prepared_chunks": len(prepared_chunks),
                "skipped_chunks": len(skipped_manifest),
                "collection_name": args.collection,
                "embedding_model": args.model,
                "chroma_dir": str(paths.chroma_dir),
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return

        if args.reset and paths.chroma_dir.exists():
            shutil.rmtree(paths.chroma_dir)

        chromadb_module, embedding_functions_module = import_chromadb()

        _, collection = get_collection(
            chromadb_module=chromadb_module,
            embedding_functions_module=embedding_functions_module,
            chroma_dir=paths.chroma_dir,
            collection_name=str(args.collection),
            embedding_model=str(args.model),
        )

        # Fill skipped manifest with collection/model after prepare stage.
        for item in skipped_manifest:
            item["collection_name"] = str(args.collection)
            item["embedding_model"] = str(args.model)

        embedded_manifest = upsert_embeddings(
            collection=collection,
            chunks=prepared_chunks,
            batch_size=int(args.batch_size),
            collection_name=str(args.collection),
            embedding_model=str(args.model),
            error_log=paths.error_log,
        )

        manifest = skipped_manifest + embedded_manifest

        try:
            collection_count = collection.count()
        except Exception:
            collection_count = None

        ended_at = utc_now_iso()

        summary = summarize(
            started_at=started_at,
            ended_at=ended_at,
            paths=paths,
            chunks_loaded=len(chunks),
            prepared_count=len(prepared_chunks),
            manifest=manifest,
            collection_name=str(args.collection),
            embedding_model=str(args.model),
            collection_count_after=collection_count,
            reset=bool(args.reset),
            batch_size=int(args.batch_size),
            max_text_chars=int(args.max_text_chars),
        )

        write_jsonl(paths.manifest_jsonl, manifest)
        write_csv(paths.manifest_csv, manifest)
        write_json(paths.summary_json, summary)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "EMBEDDING_BUILD_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "input_chunks_jsonl": str(paths.chunks_jsonl),
            "summary": summary,
        })

        print_summary(summary)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "EMBEDDING_BUILD_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "input_chunks_jsonl": str(paths.chunks_jsonl),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG EMBEDDING BUILD FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
