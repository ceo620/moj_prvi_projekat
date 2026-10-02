# ==============================================================
# 🛡️ BEBA DELTA OMNI-ENFORCER | KROVNI CFO KANON (NEPROBOJNO)
# ==============================================================
import os

TITAN_CANON = {
    "TOTAL_CAPEX": "27,800,000.00 EUR",
    "EQUIPMENT": "18,200,000.00 EUR",
    "KNOW_HOW": "6,500,000.00 EUR",
    "ESG": "3,100,000.00 EUR"
}

# Zakucavanje varijabli u sistemsko okruzenje OS-a
for key, val in TITAN_CANON.items():
    os.environ[f"BEBA_DELTA_{key}"] = val
# ==============================================================

﻿# PROPOSAL_ONLY
# HUMAN_REVIEW_REQUIRED
# WRITE_APPROVED_FOR_SQLITE_REGISTER_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 SQLite Evidence Register

Purpose:
- Define local SQLite schema helpers.
- Create/register evidence metadata only under approved runtime_local/db.
- No source evidence mutation.
- No delete, move, rename, upload, network, or script execution.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


class SQLiteRegisterError(RuntimeError):
    """Raised when SQLite register operations fail safely."""


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS evidence_file (
    evidence_id TEXT PRIMARY KEY,
    source_root_id TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    mtime_utc TEXT,
    first_seen_utc TEXT NOT NULL,
    last_seen_utc TEXT NOT NULL,
    inventory_status TEXT NOT NULL,
    content_scanned INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_file_root_path
ON evidence_file(source_root_id, relative_path);

CREATE INDEX IF NOT EXISTS idx_evidence_file_sha256
ON evidence_file(sha256);

CREATE TABLE IF NOT EXISTS duplicate_group (
    duplicate_group_id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    file_count INTEGER NOT NULL,
    detected_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS duplicate_member (
    duplicate_group_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    PRIMARY KEY (duplicate_group_id, evidence_id),
    FOREIGN KEY (duplicate_group_id) REFERENCES duplicate_group(duplicate_group_id),
    FOREIGN KEY (evidence_id) REFERENCES evidence_file(evidence_id)
);

CREATE TABLE IF NOT EXISTS forbidden_language_finding (
    finding_id TEXT PRIMARY KEY,
    evidence_id TEXT,
    source_field TEXT NOT NULL,
    term_key TEXT NOT NULL,
    severity TEXT NOT NULL,
    matched_text_redacted TEXT NOT NULL,
    finding_utc TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'OPEN',
    FOREIGN KEY (evidence_id) REFERENCES evidence_file(evidence_id)
);

CREATE TABLE IF NOT EXISTS evidence_gap (
    gap_id TEXT PRIMARY KEY,
    project_area TEXT NOT NULL,
    required_evidence_type TEXT NOT NULL,
    observed_count INTEGER NOT NULL DEFAULT 0,
    gap_status TEXT NOT NULL,
    severity TEXT NOT NULL,
    rationale TEXT NOT NULL,
    opened_utc TEXT NOT NULL,
    closed_utc TEXT
);

CREATE TABLE IF NOT EXISTS export_register (
    export_id TEXT PRIMARY KEY,
    export_type TEXT NOT NULL,
    output_relative_path TEXT NOT NULL,
    generated_utc TEXT NOT NULL,
    generated_by TEXT NOT NULL,
    approval_reference TEXT NOT NULL,
    sha256 TEXT
);
"""


@dataclass(frozen=True)
class EvidenceFileRow:
    evidence_id: str
    source_root_id: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    sha256: str
    mtime_utc: str | None
    first_seen_utc: str
    last_seen_utc: str
    inventory_status: str
    content_scanned: int = 0
    notes: str | None = None


def assert_db_path_allowed(
    db_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = db_path.resolve()

    if path.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise SQLiteRegisterError("SQLite register path must end with .db, .sqlite, or .sqlite3.")

    policy.assert_operation_allowed(
        operation=Operation.WRITE_SQLITE_REGISTER,
        target_path=path,
        approval=approval,
    )

    return path


def connect_register(
    db_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> sqlite3.Connection:
    path = assert_db_path_allowed(db_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_register(
    db_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> None:
    with connect_register(db_path, policy, approval) as connection:
        connection.executescript(SCHEMA_SQL)


def upsert_evidence_files(
    db_path: Path,
    rows: Iterable[EvidenceFileRow],
    policy: SafeIOPolicy,
    approval: Approval,
) -> int:
    with connect_register(db_path, policy, approval) as connection:
        count = 0
        for row in rows:
            if row.size_bytes < 0:
                raise SQLiteRegisterError("size_bytes cannot be negative.")

            connection.execute(
                """
                INSERT INTO evidence_file (
                    evidence_id,
                    source_root_id,
                    relative_path,
                    filename,
                    extension,
                    size_bytes,
                    sha256,
                    mtime_utc,
                    first_seen_utc,
                    last_seen_utc,
                    inventory_status,
                    content_scanned,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                    last_seen_utc = excluded.last_seen_utc,
                    inventory_status = excluded.inventory_status,
                    content_scanned = excluded.content_scanned,
                    notes = excluded.notes
                """,
                (
                    row.evidence_id,
                    row.source_root_id,
                    row.relative_path,
                    row.filename,
                    row.extension,
                    row.size_bytes,
                    row.sha256,
                    row.mtime_utc,
                    row.first_seen_utc,
                    row.last_seen_utc,
                    row.inventory_status,
                    row.content_scanned,
                    row.notes,
                ),
            )
            count += 1

        return count


def list_duplicate_candidates(
    db_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> list[tuple[str, int, int]]:
    with connect_register(db_path, policy, approval) as connection:
        cursor = connection.execute(
            """
            SELECT sha256, size_bytes, COUNT(*) AS file_count
            FROM evidence_file
            GROUP BY sha256, size_bytes
            HAVING COUNT(*) > 1
            ORDER BY file_count DESC, size_bytes DESC
            """
        )
        return [(row[0], int(row[1]), int(row[2])) for row in cursor.fetchall()]
