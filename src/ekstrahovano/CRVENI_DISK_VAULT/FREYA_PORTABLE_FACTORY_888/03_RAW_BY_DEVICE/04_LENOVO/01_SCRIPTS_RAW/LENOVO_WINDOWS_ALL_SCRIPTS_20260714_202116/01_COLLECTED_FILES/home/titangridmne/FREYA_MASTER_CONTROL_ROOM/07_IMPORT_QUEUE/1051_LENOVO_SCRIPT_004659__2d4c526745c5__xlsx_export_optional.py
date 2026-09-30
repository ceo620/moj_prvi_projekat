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
# WRITE_APPROVED_FOR_XLSX_EXPORT_OPTIONAL_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Optional XLSX Export Adapter

Purpose:
- Export approved in-memory records to local XLSX.
- Require explicit human approval.
- Write only under approved runtime_local boundary.
- Use openpyxl only if already installed.
- Perform no source mutation, upload, network access, delete, move, rename, or script execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


class XLSXExportError(RuntimeError):
    """Raised when XLSX export fails safely."""


def assert_xlsx_path_allowed(
    output_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = output_path.resolve()

    if path.suffix.lower() != ".xlsx":
        raise XLSXExportError("XLSX export path must end with .xlsx.")

    policy.assert_operation_allowed(
        operation=Operation.WRITE_XLSX_EXPORT,
        target_path=path,
        approval=approval,
    )

    return path


def _safe_cell_value(value: Any) -> Any:
    """
    Prevent spreadsheet formula interpretation for exported text.

    Values beginning with =, +, -, or @ are prefixed with an apostrophe.
    """

    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value

    return value


def export_rows_to_xlsx(
    output_path: Path,
    rows: Iterable[dict[str, Any]],
    fieldnames: tuple[str, ...],
    policy: SafeIOPolicy,
    approval: Approval,
    sheet_name: str = "DELTA_EXPORT",
) -> int:
    """
    Export records to XLSX.

    This function:
    - writes only to approved runtime_local path
    - requires explicit approval
    - does not inspect source files
    - does not mutate source evidence
    - does not install dependencies
    """

    if not fieldnames:
        raise XLSXExportError("fieldnames cannot be empty.")

    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise XLSXExportError(
            "openpyxl is not installed. XLSX export is optional; use CSV export instead."
        ) from exc

    path = assert_xlsx_path_allowed(output_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name[:31] if sheet_name else "DELTA_EXPORT"

    worksheet.append(list(fieldnames))

    count = 0
    for row in rows:
        worksheet.append([_safe_cell_value(row.get(field)) for field in fieldnames])
        count += 1

    workbook.save(path)
    return count
