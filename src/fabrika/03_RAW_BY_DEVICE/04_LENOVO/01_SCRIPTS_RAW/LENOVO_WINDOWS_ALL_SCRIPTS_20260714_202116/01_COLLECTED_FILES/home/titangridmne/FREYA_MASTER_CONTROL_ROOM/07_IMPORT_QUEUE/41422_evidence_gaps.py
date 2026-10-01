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
# WRITE_APPROVED_FOR_EVIDENCE_GAPS_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Evidence Gap Register

Purpose:
- Compare required evidence rules against observed evidence metadata.
- Produce evidence gap records.
- Perform no filesystem mutation, network access, upload, delete, move, rename, or script execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable


class EvidenceGapError(RuntimeError):
    """Raised when evidence gap analysis fails safely."""


@dataclass(frozen=True)
class EvidenceRule:
    project_area: str
    required_evidence_type: str
    minimum_count: int
    severity_if_missing: str
    rationale: str


@dataclass(frozen=True)
class ObservedEvidence:
    evidence_id: str
    evidence_type: str
    project_area: str | None = None


@dataclass(frozen=True)
class EvidenceGap:
    gap_id: str
    project_area: str
    required_evidence_type: str
    observed_count: int
    gap_status: str
    severity: str
    rationale: str
    opened_utc: str
    closed_utc: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_gap_id(project_area: str, required_evidence_type: str) -> str:
    if not project_area.strip():
        raise EvidenceGapError("Missing project_area.")

    if not required_evidence_type.strip():
        raise EvidenceGapError("Missing required_evidence_type.")

    raw = f"gap|{project_area}|{required_evidence_type}"
    return sha256(raw.encode("utf-8")).hexdigest()


def detect_evidence_gaps(
    rules: Iterable[EvidenceRule],
    observed: Iterable[ObservedEvidence],
) -> tuple[EvidenceGap, ...]:
    """
    Detect missing or insufficient evidence.

    This function:
    - uses in-memory metadata only
    - performs no filesystem access
    - performs no database writes
    - makes no readiness claims
    """

    observed_items = tuple(observed)
    gaps: list[EvidenceGap] = []

    for rule in rules:
        if not rule.project_area.strip():
            raise EvidenceGapError("Rule missing project_area.")

        if not rule.required_evidence_type.strip():
            raise EvidenceGapError("Rule missing required_evidence_type.")

        if rule.minimum_count < 1:
            raise EvidenceGapError("minimum_count must be at least 1.")

        if not rule.severity_if_missing.strip():
            raise EvidenceGapError("Rule missing severity_if_missing.")

        if not rule.rationale.strip():
            raise EvidenceGapError("Rule missing rationale.")

        count = sum(
            1
            for item in observed_items
            if item.evidence_type == rule.required_evidence_type
            and (item.project_area is None or item.project_area == rule.project_area)
        )

        if count < rule.minimum_count:
            gaps.append(
                EvidenceGap(
                    gap_id=make_gap_id(
                        project_area=rule.project_area,
                        required_evidence_type=rule.required_evidence_type,
                    ),
                    project_area=rule.project_area,
                    required_evidence_type=rule.required_evidence_type,
                    observed_count=count,
                    gap_status="OPEN",
                    severity=rule.severity_if_missing,
                    rationale=rule.rationale,
                    opened_utc=utc_now(),
                    closed_utc=None,
                )
            )

    return tuple(gaps)


def summarize_gaps(gaps: Iterable[EvidenceGap]) -> dict[str, int]:
    items = tuple(gaps)

    by_severity: dict[str, int] = {}
    for gap in items:
        by_severity[gap.severity] = by_severity.get(gap.severity, 0) + 1

    return {
        "gap_count": len(items),
        "severity_count": len(by_severity),
    }
