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
# WRITE_APPROVED_FOR_MODULE_MAP_REPORT_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Module Map Report

Purpose:
- Render a local review-only module map.
- Document module boundaries, allowed inputs, outputs, and write permissions.
- Perform no source mutation, upload, network access, delete, move, rename, or script execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


class ModuleMapReportError(RuntimeError):
    """Raised when module map report generation fails safely."""


@dataclass(frozen=True)
class ModuleMapItem:
    module_name: str
    responsibility: str
    inputs: str
    outputs: str
    write_permission: str
    status: str = "PROPOSAL_ONLY"


DEFAULT_MODULE_MAP: tuple[ModuleMapItem, ...] = (
    ModuleMapItem(
        module_name="contracts.safe_io",
        responsibility="Enforce allowed and blocked IO operations",
        inputs="Approved source roots, runtime root, operation request",
        outputs="Allow or block decision",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="contracts.approvals",
        responsibility="Represent explicit human approvals",
        inputs="Approval reference, actor, scope, reason",
        outputs="Validated approval record",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="core.hashing",
        responsibility="Compute SHA-256 and deterministic evidence IDs",
        inputs="Approved local file path",
        outputs="HashResult metadata",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="core.inventory",
        responsibility="Collect read-only file metadata",
        inputs="Approved source root",
        outputs="InventoryRecord metadata",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="core.duplicate_detection",
        responsibility="Detect duplicate records by SHA-256 and size",
        inputs="Evidence metadata rows",
        outputs="DuplicateGroup records",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="core.forbidden_language",
        responsibility="Detect prohibited wording in approved text snippets",
        inputs="Approved text snippet",
        outputs="Redacted findings",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="core.evidence_gaps",
        responsibility="Detect missing required evidence from rules",
        inputs="Evidence rules and observed evidence metadata",
        outputs="EvidenceGap records",
        write_permission="No direct writes",
    ),
    ModuleMapItem(
        module_name="storage.sqlite_register",
        responsibility="Persist evidence metadata to local SQLite",
        inputs="Validated evidence rows",
        outputs="SQLite register rows",
        write_permission="Approved runtime_local/db only",
    ),
    ModuleMapItem(
        module_name="storage.audit_jsonl",
        responsibility="Append JSONL audit events",
        inputs="Validated audit event",
        outputs="JSONL audit line",
        write_permission="Approved runtime_local/audit only",
    ),
    ModuleMapItem(
        module_name="adapters.csv_export",
        responsibility="Export approved rows to CSV",
        inputs="In-memory rows",
        outputs="CSV file",
        write_permission="Approved runtime_local/exports only",
    ),
    ModuleMapItem(
        module_name="adapters.xlsx_export_optional",
        responsibility="Export approved rows to XLSX when openpyxl is installed",
        inputs="In-memory rows",
        outputs="XLSX file",
        write_permission="Approved runtime_local/exports only",
    ),
    ModuleMapItem(
        module_name="reports.risk_report",
        responsibility="Render review-only risk report",
        inputs="Risk items and rejected runtime items",
        outputs="Markdown review packet",
        write_permission="Approved runtime_local/review_packets only",
    ),
)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def render_module_map_markdown(
    module_items: Iterable[ModuleMapItem] = DEFAULT_MODULE_MAP,
    title: str = "DELTA v0.1 Module Map",
) -> str:
    items = tuple(module_items)

    lines = [
        "PROPOSAL_ONLY",
        "HUMAN_REVIEW_REQUIRED",
        "NO_EXECUTION_AUTHORIZED",
        "",
        f"# {_escape(title)}",
        "",
        "| Module | Responsibility | Inputs | Outputs | Write Permission | Status |",
        "|---|---|---|---|---|---|",
    ]

    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(item.module_name),
                    _escape(item.responsibility),
                    _escape(item.inputs),
                    _escape(item.outputs),
                    _escape(item.write_permission),
                    _escape(item.status),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Boundary Rules",
            "",
            "- Core modules do not write files.",
            "- Storage modules write only under approved runtime_local boundaries.",
            "- Export adapters write only approved report outputs.",
            "- Existing TITAN artifacts are reference-only.",
            "- No unknown script execution is authorized.",
            "",
        ]
    )

    return "\n".join(lines)


def assert_module_map_path_allowed(
    output_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = output_path.resolve()

    if path.suffix.lower() not in {".md", ".txt"}:
        raise ModuleMapReportError("Module map output must end with .md or .txt.")

    policy.assert_operation_allowed(
        operation=Operation.WRITE_REVIEW_PACKET,
        target_path=path,
        approval=approval,
    )

    return path


def write_module_map_markdown(
    output_path: Path,
    markdown: str,
    policy: SafeIOPolicy,
    approval: Approval,
) -> int:
    path = assert_module_map_path_allowed(output_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return len(markdown.encode("utf-8"))
