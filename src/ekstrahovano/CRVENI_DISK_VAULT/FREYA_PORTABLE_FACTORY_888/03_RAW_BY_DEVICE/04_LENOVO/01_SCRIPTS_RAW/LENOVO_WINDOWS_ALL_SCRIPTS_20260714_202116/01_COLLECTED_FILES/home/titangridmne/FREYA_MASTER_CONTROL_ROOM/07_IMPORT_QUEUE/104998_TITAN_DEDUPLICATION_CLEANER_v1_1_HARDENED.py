#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_DEDUPLICATION_CLEANER.py

TITAN 11 - Deduplication & Data Quality Cleaner v1.1 HARDENED
Phase:
    PRE_PROCESSING_DATA_QUALITY / Step 4.5

Purpose:
    Acts as the gatekeeper between reconstruction/indexing and expensive signal
    extraction.

Responsibilities:
    - Compute content hash for each indexed file.
    - Detect exact binary duplicates.
    - Detect missing, unreadable, empty, suspicious, encrypted-like files.
    - Copy bad files into quarantine without deleting originals.
    - Update SQLite document status safely.
    - Write audit JSONL, manifest JSON, and CSV/JSON reports.
    - Never crash the whole run because of one bad file.

Design:
    - Standard library only.
    - No python-magic dependency.
    - Conservative file checks.
    - Supports multiple likely TITAN schemas:
        documents(document_id, source_path, file_name, status, ...)
        documents(id, file_path, status, ...)
    - Adds missing dedup/data-quality columns one-by-one.
    - Batch commits.
    - Optional fuzzy filename candidate report, not used for automatic exclusion.

Recommended usage:
    python TITAN_DEDUPLICATION_CLEANER_v1_1_HARDENED.py ^
        --db-path "C:\\TITAN\\TITAN_11\\KERNEL\\03_ORCHESTRATION\\v29_state.db" ^
        --quarantine-dir "C:\\TITAN\\TITAN_11\\GRID\\09_ARCHIVE_BACKUP\\QUARANTINE"

Dry run:
    python TITAN_DEDUPLICATION_CLEANER_v1_1_HARDENED.py --db-path "...\\v29_state.db" --dry-run

Next step:
    03_v31_producer_v1_EXPORT.py should select only:
        data_quality_status='VALID'
        and duplicate_of_document_id IS NULL
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCRIPT_NAME = "TITAN_DEDUPLICATION_CLEANER.py"
SCRIPT_VERSION = "1.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

DEFAULT_BATCH_SIZE = 500
DEFAULT_HASH_ALGO = "blake2b"
READ_CHUNK_SIZE = 8 * 1024 * 1024
DEFAULT_MIN_FUZZY_RATIO = 0.92


@dataclass
class AuditEvent:
    timestamp_utc: str
    event_type: str
    object_id: str
    path: str
    status: str
    details: str


@dataclass
class FileDecision:
    document_id: str
    source_path: str
    file_name: str
    file_size_bytes: int
    content_hash: str
    data_quality_status: str
    duplicate_of_document_id: str
    quarantine_reason: str
    quarantine_path: str
    processed_at_utc: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def setup_logging(log_path: Path, verbose: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.commit()
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> Dict[str, sqlite3.Row]:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return {row["name"]: row for row in rows}


def add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl_type: str) -> None:
    cols = table_columns(conn, table)
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type};")
        conn.commit()


def ensure_schema(conn: sqlite3.Connection) -> None:
    cols = table_columns(conn, "documents")
    if not cols:
        raise RuntimeError("Table 'documents' does not exist or has no columns.")

    # Add columns one-by-one. Never hide a partial ALTER failure.
    add_column_if_missing(conn, "documents", "content_hash", "TEXT")
    add_column_if_missing(conn, "documents", "hash_algorithm", "TEXT")
    add_column_if_missing(conn, "documents", "data_quality_status", "TEXT")
    add_column_if_missing(conn, "documents", "duplicate_of_document_id", "TEXT")
    add_column_if_missing(conn, "documents", "quarantine_reason", "TEXT")
    add_column_if_missing(conn, "documents", "quarantine_path", "TEXT")
    add_column_if_missing(conn, "documents", "data_quality_checked_at", "TEXT")
    add_column_if_missing(conn, "documents", "file_size_checked_bytes", "INTEGER")
    add_column_if_missing(conn, "documents", "fuzzy_name_group", "TEXT")

    # Best-effort indexes.
    for sql in [
        "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);",
        "CREATE INDEX IF NOT EXISTS idx_documents_dq_status ON documents(data_quality_status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_duplicate_of ON documents(duplicate_of_document_id);",
    ]:
        conn.execute(sql)
    conn.commit()


def detect_document_columns(conn: sqlite3.Connection) -> Tuple[str, str, Optional[str], Optional[str]]:
    cols = table_columns(conn, "documents")
    names = set(cols.keys())

    # ID column.
    if "document_id" in names:
        id_col = "document_id"
    elif "id" in names:
        id_col = "id"
    else:
        raise RuntimeError("documents table needs either document_id or id column.")

    # Path column.
    if "source_path" in names:
        path_col = "source_path"
    elif "file_path" in names:
        path_col = "file_path"
    elif "path" in names:
        path_col = "path"
    else:
        raise RuntimeError("documents table needs source_path, file_path, or path column.")

    name_col = "file_name" if "file_name" in names else None
    status_col = "status" if "status" in names else None
    return id_col, path_col, name_col, status_col


def load_documents(conn: sqlite3.Connection, limit: Optional[int] = None) -> List[sqlite3.Row]:
    id_col, path_col, name_col, status_col = detect_document_columns(conn)

    select_cols = [f"{id_col} AS document_id", f"{path_col} AS source_path"]
    if name_col:
        select_cols.append(f"{name_col} AS file_name")
    else:
        select_cols.append("'' AS file_name")

    if status_col:
        where = (
            "WHERE COALESCE(data_quality_status, '') NOT IN "
            "('VALID','DUPLICATE','REVIEW_REQUIRED','MISSING','HASH_FAILED','ERROR')"
        )
    else:
        where = (
            "WHERE COALESCE(data_quality_status, '') NOT IN "
            "('VALID','DUPLICATE','REVIEW_REQUIRED','MISSING','HASH_FAILED','ERROR')"
        )

    sql = f"""
        SELECT {", ".join(select_cols)}
        FROM documents
        {where}
        ORDER BY {id_col}
    """
    if limit:
        sql += f" LIMIT {int(limit)}"

    return conn.execute(sql).fetchall()


def file_hash(path: Path, algo: str) -> Tuple[Optional[str], Optional[str], int]:
    try:
        h = hashlib.new(algo)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algo}")

    total = 0
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(READ_CHUNK_SIZE), b""):
                total += len(chunk)
                h.update(chunk)
        return h.hexdigest(), None, total
    except PermissionError as exc:
        return None, f"PERMISSION_DENIED: {exc}", total
    except OSError as exc:
        return None, f"READ_ERROR: {exc}", total


def sniff_file_quality(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    if not path.is_file():
        return False, "NOT_A_FILE"

    try:
        size = path.stat().st_size
    except OSError as exc:
        return False, f"STAT_ERROR: {exc}"

    if size == 0:
        return False, "EMPTY_FILE"

    # Conservative magic-byte checks using only standard library.
    try:
        with path.open("rb") as f:
            head = f.read(8192)
            tail = b""
            if size > 8192:
                try:
                    f.seek(max(0, size - 8192))
                    tail = f.read(8192)
                except OSError:
                    tail = b""
    except PermissionError as exc:
        return False, f"PERMISSION_DENIED: {exc}"
    except OSError as exc:
        return False, f"READ_ERROR: {exc}"

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        if not head.startswith(b"%PDF"):
            return False, "CORRUPT_OR_NONSTANDARD_PDF_HEADER"
        sample = (head + tail).lower()
        if b"/encrypt" in sample or b"encrypt" in sample:
            return False, "ENCRYPTED_PDF"
        return True, "VALID"

    # Office legacy encrypted files may use CFB header.
    cfb_header = bytes.fromhex("D0CF11E0A1B11AE1")
    if head.startswith(cfb_header):
        lowered = head.lower()
        if b"encrypted" in lowered or b"password" in lowered:
            return False, "POSSIBLY_ENCRYPTED_OFFICE"
        return True, "VALID"

    # OOXML zip-based files.
    if suffix in {".docx", ".xlsx", ".pptx", ".xlsm", ".docm", ".pptm"}:
        if not head.startswith(b"PK"):
            return False, "CORRUPT_OOXML_ZIP_HEADER"
        return True, "VALID"

    # Generic file: readable and non-empty.
    return True, "VALID"


def copy_to_quarantine(source: Path, quarantine_dir: Path, reason: str, document_id: str, dry_run: bool) -> str:
    safe_reason = "".join(c if c.isalnum() or c in "-_" else "_" for c in reason)[:80]
    name = source.name if source.name else f"document_{document_id}"
    target = quarantine_dir / safe_reason / f"{document_id}__{name}"

    if dry_run:
        return str(target)

    target.parent.mkdir(parents=True, exist_ok=True)

    # Avoid overwrite.
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        target = target.with_name(f"{stem}__{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}")

    shutil.copy2(str(source), str(target))
    return str(target)


def update_document(
    conn: sqlite3.Connection,
    document_id: str,
    id_col: str,
    decision: FileDecision,
    hash_algo: str,
    dry_run: bool,
) -> None:
    if dry_run:
        return

    conn.execute(
        f"""
        UPDATE documents
        SET
            content_hash = ?,
            hash_algorithm = ?,
            data_quality_status = ?,
            duplicate_of_document_id = ?,
            quarantine_reason = ?,
            quarantine_path = ?,
            data_quality_checked_at = ?,
            file_size_checked_bytes = ?
        WHERE {id_col} = ?
        """,
        (
            decision.content_hash or None,
            hash_algo,
            decision.data_quality_status,
            decision.duplicate_of_document_id or None,
            decision.quarantine_reason or None,
            decision.quarantine_path or None,
            decision.processed_at_utc,
            decision.file_size_bytes,
            document_id,
        ),
    )


def find_duplicate(conn: sqlite3.Connection, content_hash: str, document_id: str, id_col: str) -> Optional[str]:
    row = conn.execute(
        f"""
        SELECT {id_col} AS document_id
        FROM documents
        WHERE content_hash = ?
          AND CAST({id_col} AS TEXT) != CAST(? AS TEXT)
          AND COALESCE(data_quality_status, '') = 'VALID'
        LIMIT 1
        """,
        (content_hash, document_id),
    ).fetchone()
    return safe_text(row["document_id"]) if row else None


def filename_fuzzy_report(records: List[FileDecision], min_ratio: float) -> List[Dict[str, Any]]:
    # Candidate-only report. Does not affect statuses.
    valid = [r for r in records if r.data_quality_status == "VALID"]
    grouped: List[Dict[str, Any]] = []

    max_compare = min(len(valid), 2500)  # Avoid combinatorial blow-up.
    valid = valid[:max_compare]

    for i in range(len(valid)):
        a = valid[i]
        a_name = a.file_name.lower()
        if not a_name:
            continue
        for j in range(i + 1, len(valid)):
            b = valid[j]
            b_name = b.file_name.lower()
            if not b_name:
                continue
            ratio = SequenceMatcher(None, a_name, b_name).ratio()
            if ratio >= min_ratio and a.content_hash != b.content_hash:
                grouped.append(
                    {
                        "document_id_a": a.document_id,
                        "file_name_a": a.file_name,
                        "document_id_b": b.document_id,
                        "file_name_b": b.file_name,
                        "similarity_ratio": round(ratio, 4),
                        "note": "Candidate near-duplicate by filename only; manual review required.",
                    }
                )
    return grouped


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


class DeduplicationCleaner:
    def __init__(
        self,
        db_path: Path,
        quarantine_dir: Path,
        output_dir: Path,
        batch_size: int,
        hash_algo: str,
        dry_run: bool,
        limit: Optional[int],
        enable_fuzzy_report: bool,
        min_fuzzy_ratio: float,
    ) -> None:
        self.db_path = db_path.resolve()
        self.quarantine_dir = quarantine_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.batch_size = batch_size
        self.hash_algo = hash_algo
        self.dry_run = dry_run
        self.limit = limit
        self.enable_fuzzy_report = enable_fuzzy_report
        self.min_fuzzy_ratio = min_fuzzy_ratio
        self.events: List[AuditEvent] = []
        self.decisions: List[FileDecision] = []

    def event(self, event_type: str, object_id: str, path: str, status: str, details: str) -> None:
        evt = AuditEvent(utc_now(), event_type, object_id, path, status, details)
        self.events.append(evt)
        logging.info("%s | %s | %s | %s", event_type, status, object_id, details)

    def run(self) -> Dict[str, Any]:
        started = time.time()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.dry_run:
            self.quarantine_dir.mkdir(parents=True, exist_ok=True)

        conn = connect_db(self.db_path)
        id_col, _, _, _ = detect_document_columns(conn)
        try:
            ensure_schema(conn)
            docs = load_documents(conn, self.limit)
            self.event("LOAD", "documents", str(self.db_path), "OK", f"Loaded {len(docs)} candidate documents.")

            valid = duplicate = review = missing = hash_failed = errors = 0

            for start in range(0, len(docs), self.batch_size):
                batch = docs[start:start + self.batch_size]

                for row in batch:
                    document_id = safe_text(row["document_id"])
                    source_path = Path(safe_text(row["source_path"]))
                    file_name = safe_text(row["file_name"]) or source_path.name
                    processed_at = utc_now()

                    try:
                        is_ok, reason = sniff_file_quality(source_path)

                        if not is_ok:
                            qpath = ""
                            if source_path.exists() and source_path.is_file():
                                qpath = copy_to_quarantine(source_path, self.quarantine_dir, reason, document_id, self.dry_run)
                            size = source_path.stat().st_size if source_path.exists() and source_path.is_file() else 0
                            status = "MISSING" if reason == "MISSING" else "REVIEW_REQUIRED"
                            if status == "MISSING":
                                missing += 1
                            else:
                                review += 1

                            decision = FileDecision(
                                document_id=document_id,
                                source_path=str(source_path),
                                file_name=file_name,
                                file_size_bytes=size,
                                content_hash="",
                                data_quality_status=status,
                                duplicate_of_document_id="",
                                quarantine_reason=reason,
                                quarantine_path=qpath,
                                processed_at_utc=processed_at,
                            )
                            update_document(conn, document_id, id_col, decision, self.hash_algo, self.dry_run)
                            self.decisions.append(decision)
                            self.event("QUALITY", document_id, str(source_path), status, reason)
                            continue

                        content_hash, hash_error, size = file_hash(source_path, self.hash_algo)
                        if hash_error or not content_hash:
                            hash_failed += 1
                            decision = FileDecision(
                                document_id=document_id,
                                source_path=str(source_path),
                                file_name=file_name,
                                file_size_bytes=size,
                                content_hash="",
                                data_quality_status="HASH_FAILED",
                                duplicate_of_document_id="",
                                quarantine_reason=hash_error or "HASH_FAILED",
                                quarantine_path="",
                                processed_at_utc=processed_at,
                            )
                            update_document(conn, document_id, id_col, decision, self.hash_algo, self.dry_run)
                            self.decisions.append(decision)
                            self.event("HASH", document_id, str(source_path), "HASH_FAILED", hash_error or "")
                            continue

                        duplicate_of = find_duplicate(conn, content_hash, document_id, id_col)
                        if duplicate_of:
                            duplicate += 1
                            decision = FileDecision(
                                document_id=document_id,
                                source_path=str(source_path),
                                file_name=file_name,
                                file_size_bytes=size,
                                content_hash=content_hash,
                                data_quality_status="DUPLICATE",
                                duplicate_of_document_id=duplicate_of,
                                quarantine_reason="DUPLICATE_BINARY_CONTENT",
                                quarantine_path="",
                                processed_at_utc=processed_at,
                            )
                            update_document(conn, document_id, id_col, decision, self.hash_algo, self.dry_run)
                            self.decisions.append(decision)
                            self.event("DEDUP", document_id, str(source_path), "DUPLICATE", f"duplicate_of={duplicate_of}")
                            continue

                        valid += 1
                        decision = FileDecision(
                            document_id=document_id,
                            source_path=str(source_path),
                            file_name=file_name,
                            file_size_bytes=size,
                            content_hash=content_hash,
                            data_quality_status="VALID",
                            duplicate_of_document_id="",
                            quarantine_reason="",
                            quarantine_path="",
                            processed_at_utc=processed_at,
                        )
                        update_document(conn, document_id, id_col, decision, self.hash_algo, self.dry_run)
                        self.decisions.append(decision)
                        self.event("DEDUP", document_id, str(source_path), "VALID", "File accepted.")

                    except Exception as exc:
                        errors += 1
                        decision = FileDecision(
                            document_id=document_id,
                            source_path=str(source_path),
                            file_name=file_name,
                            file_size_bytes=0,
                            content_hash="",
                            data_quality_status="ERROR",
                            duplicate_of_document_id="",
                            quarantine_reason=f"UNEXPECTED_ERROR: {exc}",
                            quarantine_path="",
                            processed_at_utc=processed_at,
                        )
                        update_document(conn, document_id, id_col, decision, self.hash_algo, self.dry_run)
                        self.decisions.append(decision)
                        self.event("ERROR", document_id, str(source_path), "ERROR", str(exc))

                if not self.dry_run:
                    conn.commit()
                self.event("BATCH", str(start // self.batch_size + 1), "", "COMMITTED" if not self.dry_run else "DRY_RUN", f"Processed {len(batch)} rows.")

            fuzzy_rows: List[Dict[str, Any]] = []
            if self.enable_fuzzy_report:
                fuzzy_rows = filename_fuzzy_report(self.decisions, self.min_fuzzy_ratio)

            elapsed = round(time.time() - started, 4)
            summary = {
                "system_name": SYSTEM_NAME,
                "script_name": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "generated_at_utc": utc_now(),
                "db_path": str(self.db_path),
                "quarantine_dir": str(self.quarantine_dir),
                "dry_run": self.dry_run,
                "hash_algorithm": self.hash_algo,
                "total_candidates": len(docs),
                "valid": valid,
                "duplicates": duplicate,
                "review_required": review,
                "missing": missing,
                "hash_failed": hash_failed,
                "errors": errors,
                "fuzzy_candidate_pairs": len(fuzzy_rows),
                "elapsed_seconds": elapsed,
                "next_step": "03_v31_producer_v1_EXPORT.py should process data_quality_status='VALID' only.",
            }

            self.export(summary, fuzzy_rows)
            return summary

        finally:
            conn.close()

    def export(self, summary: Dict[str, Any], fuzzy_rows: List[Dict[str, Any]]) -> None:
        decisions_rows = [asdict(d) for d in self.decisions]
        events_rows = [asdict(e) for e in self.events]

        write_json(self.output_dir / "deduplication_summary_v1_1.json", summary)
        write_json(self.output_dir / "deduplication_decisions_v1_1.json", decisions_rows)
        write_csv(self.output_dir / "deduplication_decisions_v1_1.csv", decisions_rows)
        write_json(self.output_dir / "deduplication_audit_log_v1_1.json", events_rows)
        write_csv(self.output_dir / "fuzzy_filename_candidates_v1_1.csv", fuzzy_rows)

        audit_jsonl = self.output_dir / "deduplication_audit_log_v1_1.jsonl"
        with audit_jsonl.open("w", encoding="utf-8") as f:
            for evt in self.events:
                f.write(json.dumps(asdict(evt), ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN Deduplication Cleaner v1.1 HARDENED")
    parser.add_argument("--db-path", required=True, help="SQLite database path.")
    parser.add_argument("--quarantine-dir", default="./GRID/QUARANTINE", help="Quarantine output directory.")
    parser.add_argument("--output-dir", default="./KERNEL/05_FORENSIC_AUDIT/deduplication_reports", help="Report output directory.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--hash-algo", default=DEFAULT_HASH_ALGO, help="hashlib algorithm, e.g. blake2b or sha256.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--enable-fuzzy-report", action="store_true", help="Generate candidate near-duplicate filename report only.")
    parser.add_argument("--min-fuzzy-ratio", type=float, default=DEFAULT_MIN_FUZZY_RATIO)
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    setup_logging(output_dir / "deduplication_cleaner.log", args.verbose)

    try:
        cleaner = DeduplicationCleaner(
            db_path=Path(args.db_path).expanduser(),
            quarantine_dir=Path(args.quarantine_dir).expanduser(),
            output_dir=output_dir,
            batch_size=args.batch_size,
            hash_algo=args.hash_algo,
            dry_run=args.dry_run,
            limit=args.limit,
            enable_fuzzy_report=args.enable_fuzzy_report,
            min_fuzzy_ratio=args.min_fuzzy_ratio,
        )
        summary = cleaner.run()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print("\nTITAN_DEDUPLICATION_CLEANER completed.")
        return 0 if summary["errors"] == 0 else 2

    except Exception as exc:
        logging.exception("Deduplication cleaner failed: %s", exc)
        print(f"\nTITAN_DEDUPLICATION_CLEANER failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
