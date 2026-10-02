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
# WRITE_APPROVED_FOR_INVENTORY_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Inventory Module

Purpose:
- Collect read-only file metadata from approved source roots.
- Never read full content.
- Never execute files.
- Never delete, move, rename, upload, or modify source evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from delta_ecs.contracts.safe_io import Operation, SafeIOPolicy


class InventoryError(RuntimeError):
    """Raised when inventory collection fails safely."""


@dataclass(frozen=True)
class InventoryRecord:
    source_root_id: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    mtime_utc: str
    is_symlink: bool
    inventory_status: str = "DISCOVERED_METADATA_ONLY"


def _utc_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _extension_allowed(path: Path, allowed_extensions: set[str] | None) -> bool:
    if allowed_extensions is None:
        return True
    return path.suffix.lower() in allowed_extensions


def inventory_source_root(
    source_root: Path,
    source_root_id: str,
    policy: SafeIOPolicy,
    allowed_extensions: set[str] | None = None,
    max_files: int | None = None,
) -> tuple[InventoryRecord, ...]:
    """
    Return read-only metadata inventory for an approved source root.

    This function:
    - reads metadata only
    - skips symlinks
    - does not read file contents
    - does not hash files
    - does not write output files
    - does not execute discovered files
    """

    if not source_root_id.strip():
        raise InventoryError("Missing source_root_id.")

    root = source_root.resolve()

    policy.assert_operation_allowed(
        operation=Operation.READ_METADATA,
        target_path=root,
        approval=None,
    )

    if not root.exists():
        raise InventoryError(f"Source root does not exist: {root}")

    if not root.is_dir():
        raise InventoryError(f"Source root is not a directory: {root}")

    if max_files is not None and max_files <= 0:
        raise InventoryError("max_files must be greater than zero when provided.")

    records: list[InventoryRecord] = []

    for path in sorted(root.rglob("*")):
        if max_files is not None and len(records) >= max_files:
            break

        try:
            resolved = path.resolve()

            if path.is_symlink():
                continue

            if not path.is_file():
                continue

            if not _extension_allowed(path, allowed_extensions):
                continue

            policy.assert_operation_allowed(
                operation=Operation.READ_METADATA,
                target_path=resolved,
                approval=None,
            )

            stat = path.stat()
            relative_path = resolved.relative_to(root).as_posix()

            records.append(
                InventoryRecord(
                    source_root_id=source_root_id,
                    relative_path=relative_path,
                    filename=path.name,
                    extension=path.suffix.lower(),
                    size_bytes=stat.st_size,
                    mtime_utc=_utc_from_timestamp(stat.st_mtime),
                    is_symlink=False,
                )
            )

        except OSError:
            continue
        except ValueError:
            continue

    return tuple(records)


def summarize_inventory(records: tuple[InventoryRecord, ...]) -> dict[str, int]:
    """
    Return simple metadata-only inventory summary.

    No filesystem access.
    No writes.
    """

    total_files = len(records)
    total_bytes = sum(record.size_bytes for record in records)

    by_extension: dict[str, int] = {}
    for record in records:
        ext = record.extension or "[no_extension]"
        by_extension[ext] = by_extension.get(ext, 0) + 1

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "unique_extensions": len(by_extension),
    }
