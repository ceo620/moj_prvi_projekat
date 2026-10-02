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
# WRITE_APPROVED_FOR_APPROVALS_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Approval Contract

Purpose:
- Represent explicit human approvals.
- Validate approval scope before any write action.
- Preserve policy markers on approval records.

This module must not perform filesystem writes, network calls, scanning, or script execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


POLICY_MARKERS = (
    "PROPOSAL_ONLY",
    "HUMAN_REVIEW_REQUIRED",
    "NO_EXECUTION_AUTHORIZED",
)


class ApprovalError(RuntimeError):
    """Raised when approval validation fails."""


class ApprovalScope(str, Enum):
    PROJECT_SKELETON = "DELTA_V0.1_PROJECT_SKELETON"
    SAFE_IO_CONTRACT = "DELTA_V0.1_SAFE_IO_CONTRACT"
    APPROVALS_MODULE = "DELTA_V0.1_APPROVALS_MODULE"
    SQLITE_SCHEMA = "DELTA_V0.1_SQLITE_SCHEMA"
    JSONL_AUDIT = "DELTA_V0.1_JSONL_AUDIT"
    HASHING_MODULE = "DELTA_V0.1_HASHING_MODULE"
    INVENTORY_MODULE = "DELTA_V0.1_INVENTORY_MODULE"
    CSV_EXPORT = "DELTA_V0.1_CSV_EXPORT"
    XLSX_EXPORT_OPTIONAL = "DELTA_V0.1_XLSX_EXPORT_OPTIONAL"
    REVIEW_PACKET = "DELTA_V0.1_REVIEW_PACKET"


@dataclass(frozen=True)
class ApprovalRecord:
    approval_reference: str
    scope: ApprovalScope
    actor: str
    reason: str
    created_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    approval_id: str = field(default_factory=lambda: str(uuid4()))
    policy_markers: tuple[str, ...] = POLICY_MARKERS

    def validate(self, expected_scope: ApprovalScope | None = None) -> None:
        if not self.approval_reference.strip():
            raise ApprovalError("Missing approval_reference.")

        if not self.actor.strip():
            raise ApprovalError("Missing actor.")

        if not self.reason.strip():
            raise ApprovalError("Missing approval reason.")

        missing_markers = set(POLICY_MARKERS) - set(self.policy_markers)
        if missing_markers:
            raise ApprovalError(f"Missing policy markers: {sorted(missing_markers)}")

        if expected_scope is not None and self.scope != expected_scope:
            raise ApprovalError(
                f"Approval scope mismatch. Expected {expected_scope.value}, got {self.scope.value}."
            )


def make_local_approval(
    approval_reference: str,
    scope: ApprovalScope,
    actor: str,
    reason: str,
) -> ApprovalRecord:
    record = ApprovalRecord(
        approval_reference=approval_reference,
        scope=scope,
        actor=actor,
        reason=reason,
    )
    record.validate(expected_scope=scope)
    return record
