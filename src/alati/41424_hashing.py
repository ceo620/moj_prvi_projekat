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
# WRITE_APPROVED_FOR_HASHING_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Hashing Module

Purpose:
- Compute SHA-256 for approved local files.
- Use chunked read-only file access.
- Produce deterministic evidence IDs.
- Perform no writes, deletes, moves, renames, network calls, or script execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from delta_ecs.contracts.safe_io import Operation, SafeIOPolicy


DEFAULT_CHUNK_SIZE = 1024 * 1024


class HashingError(RuntimeError):
    """Raised when hashing fails safely."""


@dataclass(frozen=True)
class HashResult:
    source_root_id: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    sha256: str
    evidence_id: str


def compute_sha256_for_file(
    file_path: Path,
    policy: SafeIOPolicy,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """
    Compute SHA-256 for one approved local file.

    This function:
    - reads bytes only
    - does not modify the file
    - does not execute the file
    - does not upload anything
    """

    path = file_path.resolve()

    policy.assert_operation_allowed(
        operation=Operation.READ_BYTES_FOR_HASHING,
        target_path=path,
        approval=None,
    )

    if not path.exists():
        raise HashingError(f"File does not exist: {path}")

    if not path.is_file():
        raise HashingError(f"Target is not a file: {path}")

    if chunk_size <= 0:
        raise HashingError("chunk_size must be greater than zero.")

    digest = sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def make_evidence_id(
    source_root_id: str,
    normalized_relative_path: str,
    size_bytes: int,
    file_sha256: str,
) -> str:
    """
    Deterministic evidence ID.

    Avoids absolute private paths.
    """

    if not source_root_id.strip():
        raise HashingError("Missing source_root_id.")

    if not normalized_relative_path.strip():
        raise HashingError("Missing normalized_relative_path.")

    if size_bytes < 0:
        raise HashingError("size_bytes cannot be negative.")

    if len(file_sha256) != 64:
        raise HashingError("file_sha256 must be a 64-character SHA-256 hex digest.")

    raw = f"{source_root_id}|{normalized_relative_path}|{size_bytes}|{file_sha256}"
    return sha256(raw.encode("utf-8")).hexdigest()


def hash_evidence_file(
    file_path: Path,
    source_root: Path,
    source_root_id: str,
    policy: SafeIOPolicy,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> HashResult:
    """
    Hash one approved evidence file and return metadata.

    No database write.
    No audit write.
    No filesystem mutation.
    """

    path = file_path.resolve()
    root = source_root.resolve()

    if not policy.is_under_approved_source_root(path):
        raise HashingError(f"File outside approved source roots: {path}")

    if not (path == root or root in path.parents):
        raise HashingError(f"File is not under declared source_root: {path}")

    file_sha256 = compute_sha256_for_file(
        file_path=path,
        policy=policy,
        chunk_size=chunk_size,
    )

    size_bytes = path.stat().st_size
    relative_path = path.relative_to(root).as_posix()

    evidence_id = make_evidence_id(
        source_root_id=source_root_id,
        normalized_relative_path=relative_path,
        size_bytes=size_bytes,
        file_sha256=file_sha256,
    )

    return HashResult(
        source_root_id=source_root_id,
        relative_path=relative_path,
        filename=path.name,
        extension=path.suffix.lower(),
        size_bytes=size_bytes,
        sha256=file_sha256,
        evidence_id=evidence_id,
    )
