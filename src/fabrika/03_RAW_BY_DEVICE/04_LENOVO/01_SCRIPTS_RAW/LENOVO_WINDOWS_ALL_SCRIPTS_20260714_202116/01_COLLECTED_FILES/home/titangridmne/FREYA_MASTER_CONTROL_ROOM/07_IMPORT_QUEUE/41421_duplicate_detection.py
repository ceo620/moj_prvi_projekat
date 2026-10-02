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
# WRITE_APPROVED_FOR_DUPLICATE_DETECTION_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Duplicate Detection Module

Purpose:
- Detect duplicate evidence records by SHA-256 + size_bytes.
- Report duplicates only.
- Never delete, move, rename, consolidate, upload, or mutate files.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


class DuplicateDetectionError(RuntimeError):
    """Raised when duplicate detection fails safely."""


@dataclass(frozen=True)
class EvidenceIdentity:
    evidence_id: str
    sha256: str
    size_bytes: int
    source_root_id: str
    relative_path: str


@dataclass(frozen=True)
class DuplicateGroup:
    duplicate_group_id: str
    sha256: str
    size_bytes: int
    file_count: int
    evidence_ids: tuple[str, ...]
    relative_paths: tuple[str, ...]


def make_duplicate_group_id(file_sha256: str, size_bytes: int) -> str:
    if len(file_sha256) != 64:
        raise DuplicateDetectionError("file_sha256 must be a 64-character SHA-256 hex digest.")
    if size_bytes < 0:
        raise DuplicateDetectionError("size_bytes cannot be negative.")

    raw = f"duplicate|{file_sha256}|{size_bytes}"
    return sha256(raw.encode("utf-8")).hexdigest()


def detect_duplicate_groups(
    evidence_rows: Iterable[EvidenceIdentity],
) -> tuple[DuplicateGroup, ...]:
    """
    Detect duplicates by SHA-256 + size_bytes.

    This function:
    - reads in-memory metadata only
    - performs no filesystem access
    - performs no database writes
    - performs no file mutation
    """

    grouped: dict[tuple[str, int], list[EvidenceIdentity]] = defaultdict(list)

    for row in evidence_rows:
        if not row.evidence_id.strip():
            raise DuplicateDetectionError("Missing evidence_id.")

        if len(row.sha256) != 64:
            raise DuplicateDetectionError(
                f"Invalid SHA-256 for evidence_id={row.evidence_id}"
            )

        if row.size_bytes < 0:
            raise DuplicateDetectionError(
                f"Negative size_bytes for evidence_id={row.evidence_id}"
            )

        grouped[(row.sha256, row.size_bytes)].append(row)

    duplicate_groups: list[DuplicateGroup] = []

    for (file_sha256, size_bytes), members in grouped.items():
        if len(members) <= 1:
            continue

        duplicate_groups.append(
            DuplicateGroup(
                duplicate_group_id=make_duplicate_group_id(file_sha256, size_bytes),
                sha256=file_sha256,
                size_bytes=size_bytes,
                file_count=len(members),
                evidence_ids=tuple(member.evidence_id for member in members),
                relative_paths=tuple(member.relative_path for member in members),
            )
        )

    return tuple(
        sorted(
            duplicate_groups,
            key=lambda group: (group.file_count, group.size_bytes, group.sha256),
            reverse=True,
        )
    )


def summarize_duplicate_groups(
    duplicate_groups: Iterable[DuplicateGroup],
) -> dict[str, int]:
    """
    Return metadata-only duplicate summary.

    No filesystem access.
    No writes.
    """

    groups = tuple(duplicate_groups)
    duplicate_file_count = sum(group.file_count for group in groups)

    return {
        "duplicate_group_count": len(groups),
        "duplicate_file_count": duplicate_file_count,
    }
