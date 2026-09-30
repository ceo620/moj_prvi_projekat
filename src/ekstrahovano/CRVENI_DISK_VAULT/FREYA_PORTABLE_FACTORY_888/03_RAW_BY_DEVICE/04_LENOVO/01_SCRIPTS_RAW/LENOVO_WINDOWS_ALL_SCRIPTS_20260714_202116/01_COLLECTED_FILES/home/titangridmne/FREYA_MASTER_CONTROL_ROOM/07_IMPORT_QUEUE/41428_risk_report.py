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
# WRITE_APPROVED_FOR_RISK_REPORT_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Risk Report Module

Purpose:
- Generate local, review-only risk reports from approved in-memory records.
- Write review packets only under approved runtime_local boundary.
- Make no readiness, financing, lender, or approval claims.
- Perform no source mutation, upload, network access, delete, move, rename, or script execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


POLICY_MARKERS = (
    "PROPOSAL_ONLY",
    "HUMAN_REVIEW_REQUIRED",
    "NO_EXECUTION_AUTHORIZED",
)


class RiskReportError(RuntimeError):
    """Raised when risk report generation fails safely."""


@dataclass(frozen=True)
class RiskItem:
    risk_id: str
    title: str
    severity: str
    evidence: str
    mitigation: str
    status: str = "OPEN"


@dataclass(frozen=True)
class RejectedRuntimeItem:
    name: str
    extension: str
    length: int
    sha256: str | None
    reason: str
    safe_action: str = "DO_NOT_EXECUTE_DO_NOT_UPLOAD_DO_NOT_DELETE"


def _markdown_escape(value: str) -> str:
    return (
        value.replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def render_risk_report_markdown(
    risk_items: Iterable[RiskItem],
    rejected_runtime_items: Iterable[RejectedRuntimeItem],
    report_title: str = "DELTA v0.1 Risk Report",
) -> str:
    """
    Render a review-only markdown risk report.

    No filesystem access.
    No writes.
    No readiness claims.
    """

    risks = tuple(risk_items)
    rejected = tuple(rejected_runtime_items)

    lines: list[str] = [
        "PROPOSAL_ONLY",
        "HUMAN_REVIEW_REQUIRED",
        "NO_EXECUTION_AUTHORIZED",
        "",
        f"# {_markdown_escape(report_title)}",
        "",
        "This report is a local review packet only.",
        "",
        "It does not authorize execution, deletion, movement, rename, upload, cloud sync, token exposure, or autonomous operation.",
        "",
        "## Risk Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Open risk items | {sum(1 for item in risks if item.status.upper() == 'OPEN')} |",
        f"| Rejected runtime items | {len(rejected)} |",
        "",
        "## Risk Items",
        "",
        "| Risk ID | Severity | Status | Title | Evidence | Mitigation |",
        "|---|---|---|---|---|---|",
    ]

    if risks:
        for item in risks:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_escape(item.risk_id),
                        _markdown_escape(item.severity),
                        _markdown_escape(item.status),
                        _markdown_escape(item.title),
                        _markdown_escape(item.evidence),
                        _markdown_escape(item.mitigation),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| NONE_RECORDED | INFO | REVIEW | No risk items supplied | Metadata-only report | Continue human review |")

    lines.extend(
        [
            "",
            "## Rejected Runtime Register",
            "",
            "| Name | Extension | Length | SHA256 | Reason | Safe Action |",
            "|---|---|---:|---|---|---|",
        ]
    )

    if rejected:
        for item in rejected:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_escape(item.name),
                        _markdown_escape(item.extension),
                        str(item.length),
                        _markdown_escape(item.sha256 or ""),
                        _markdown_escape(item.reason),
                        _markdown_escape(item.safe_action),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| NONE_RECORDED |  | 0 |  | No rejected runtime items supplied | Continue review |")

    lines.extend(
        [
            "",
            "## Required Safety Controls",
            "",
            "- No delete.",
            "- No move.",
            "- No rename.",
            "- No unknown script execution.",
            "- No network upload.",
            "- No cloud sync.",
            "- No token exposure.",
            "- No autonomous agents.",
            "- No daemons.",
            "- No watchdogs.",
            "- No auto-patch.",
            "",
        ]
    )

    return "\n".join(lines)


def assert_review_packet_path_allowed(
    output_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = output_path.resolve()

    if path.suffix.lower() not in {".md", ".txt"}:
        raise RiskReportError("Risk report output must end with .md or .txt.")

    policy.assert_operation_allowed(
        operation=Operation.WRITE_REVIEW_PACKET,
        target_path=path,
        approval=approval,
    )

    return path


def write_risk_report_markdown(
    output_path: Path,
    markdown: str,
    policy: SafeIOPolicy,
    approval: Approval,
) -> int:
    """
    Write markdown risk report to approved runtime_local path.

    Requires explicit approval.
    """

    path = assert_review_packet_path_allowed(output_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(markdown, encoding="utf-8")
    return len(markdown.encode("utf-8"))
