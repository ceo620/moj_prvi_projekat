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
# WRITE_APPROVED_FOR_DEPENDENCY_MAP_REPORT_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Dependency Map Report

Purpose:
- Render local review-only dependency map.
- Keep core standard-library-first.
- Identify optional adapters separately.
- Perform no source mutation, upload, network access, delete, move, rename, or script execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


class DependencyMapReportError(RuntimeError):
    """Raised when dependency map report generation fails safely."""


@dataclass(frozen=True)
class DependencyItem:
    name: str
    dependency_type: str
    used_for: str
    boundary: str
    required: bool


DEFAULT_DEPENDENCIES: tuple[DependencyItem, ...] = (
    DependencyItem(
        name="Python 3.11+",
        dependency_type="Runtime",
        used_for="Local application runtime",
        boundary="Required local runtime",
        required=True,
    ),
    DependencyItem(
        name="hashlib",
        dependency_type="Python standard library",
        used_for="SHA-256 hashing and deterministic IDs",
        boundary="Core",
        required=True,
    ),
    DependencyItem(
        name="sqlite3",
        dependency_type="Python standard library",
        used_for="SQLite evidence register",
        boundary="Storage",
        required=True,
    ),
    DependencyItem(
        name="json",
        dependency_type="Python standard library",
        used_for="JSONL audit ledger and local config",
        boundary="Storage/config",
        required=True,
    ),
    DependencyItem(
        name="csv",
        dependency_type="Python standard library",
        used_for="CSV exports",
        boundary="Export adapter",
        required=True,
    ),
    DependencyItem(
        name="pathlib",
        dependency_type="Python standard library",
        used_for="Safe local path handling",
        boundary="Core/contracts",
        required=True,
    ),
    DependencyItem(
        name="datetime",
        dependency_type="Python standard library",
        used_for="UTC timestamps",
        boundary="Core/storage",
        required=True,
    ),
    DependencyItem(
        name="uuid",
        dependency_type="Python standard library",
        used_for="Audit and approval IDs",
        boundary="Storage/contracts",
        required=True,
    ),
    DependencyItem(
        name="re",
        dependency_type="Python standard library",
        used_for="Forbidden-language detection",
        boundary="Core",
        required=True,
    ),
    DependencyItem(
        name="openpyxl",
        dependency_type="Optional third-party",
        used_for="Optional XLSX export only",
        boundary="Optional adapter only",
        required=False,
    ),
)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def render_dependency_map_markdown(
    dependencies: Iterable[DependencyItem] = DEFAULT_DEPENDENCIES,
    title: str = "DELTA v0.1 Dependency Map",
) -> str:
    items = tuple(dependencies)

    lines = [
        "PROPOSAL_ONLY",
        "HUMAN_REVIEW_REQUIRED",
        "NO_EXECUTION_AUTHORIZED",
        "",
        f"# {_escape(title)}",
        "",
        "| Dependency | Type | Used For | Boundary | Required |",
        "|---|---|---|---|---|",
    ]

    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(item.name),
                    _escape(item.dependency_type),
                    _escape(item.used_for),
                    _escape(item.boundary),
                    "YES" if item.required else "NO",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Dependency Policy",
            "",
            "- Core modules use Python standard library only.",
            "- Optional XLSX export is isolated behind `adapters.xlsx_export_optional`.",
            "- No dependency may perform network upload, telemetry, cloud sync, script execution, or source evidence mutation.",
            "- Existing TITAN artifacts are reference-only and are not imported directly.",
            "- No package installation is authorized by this module.",
            "",
        ]
    )

    return "\n".join(lines)


def assert_dependency_map_path_allowed(
    output_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = output_path.resolve()

    if path.suffix.lower() not in {".md", ".txt"}:
        raise DependencyMapReportError("Dependency map output must end with .md or .txt.")

    policy.assert_operation_allowed(
        operation=Operation.WRITE_REVIEW_PACKET,
        target_path=path,
        approval=approval,
    )

    return path


def write_dependency_map_markdown(
    output_path: Path,
    markdown: str,
    policy: SafeIOPolicy,
    approval: Approval,
) -> int:
    path = assert_dependency_map_path_allowed(output_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return len(markdown.encode("utf-8"))
