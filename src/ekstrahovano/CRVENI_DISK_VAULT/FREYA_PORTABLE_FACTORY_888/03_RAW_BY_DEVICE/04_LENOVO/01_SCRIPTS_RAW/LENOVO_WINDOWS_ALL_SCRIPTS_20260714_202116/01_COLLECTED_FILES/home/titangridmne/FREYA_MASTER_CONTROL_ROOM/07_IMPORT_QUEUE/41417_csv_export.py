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
# WRITE_APPROVED_FOR_CSV_EXPORT_ADAPTER_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 CSV Export Adapter

Purpose:
- Export approved in-memory records to local CSV.
- Require explicit human approval.
- Write only under approved runtime_local boundary.
- Perform no source mutation, upload, network access, delete, move, rename, or script execution.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


class CSVExportError(RuntimeError):
    """Raised when CSV export fails safely."""


def assert_csv_path_allowed(
    output_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = output_path.resolve()

    if path.suffix.lower() != ".csv":
        raise CSVExportError("CSV export path must end with .csv.")

    policy.assert_operation_allowed(
        operation=Operation.WRITE_CSV_EXPORT,
        target_path=path,
        approval=approval,
    )

    return path


def export_rows_to_csv(
    output_path: Path,
    rows: Iterable[dict[str, Any]],
    fieldnames: tuple[str, ...],
    policy: SafeIOPolicy,
    approval: Approval,
) -> int:
    """
    Export records to CSV.

    This function:
    - writes only to approved runtime_local path
    - requires explicit approval
    - does not inspect source files
    - does not mutate source evidence
    """

    if not fieldnames:
        raise CSVExportError("fieldnames cannot be empty.")

    path = assert_csv_path_allowed(output_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)
            count += 1

    return count


def export_summary_to_csv(
    output_path: Path,
    summary: dict[str, Any],
    policy: SafeIOPolicy,
    approval: Approval,
) -> int:
    """
    Export key-value summary rows to CSV.

    No source evidence access.
    """

    rows = [
        {
            "key": key,
            "value": value,
        }
        for key, value in summary.items()
    ]

    return export_rows_to_csv(
        output_path=output_path,
        rows=rows,
        fieldnames=("key", "value"),
        policy=policy,
        approval=approval,
    )
