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
# WRITE_APPROVED_FOR_JSONL_AUDIT_LEDGER_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 JSONL Audit Ledger

Purpose:
- Append local audit events to JSONL.
- Require explicit human approval for every append.
- Write only under approved runtime_local/audit boundary.
- No source evidence mutation.
- No delete, move, rename, upload, network, daemon, watchdog, or script execution.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from delta_ecs.contracts.safe_io import Approval, Operation, SafeIOPolicy


POLICY_MARKERS = (
    "PROPOSAL_ONLY",
    "HUMAN_REVIEW_REQUIRED",
    "NO_EXECUTION_AUTHORIZED",
)


class AuditLedgerError(RuntimeError):
    """Raised when audit ledger operations fail safely."""


@dataclass(frozen=True)
class AuditEvent:
    action: str
    actor: str
    target_type: str
    target_id: str
    outcome: str
    approval_reference: str
    details: dict[str, Any] = field(default_factory=dict)
    source_root_id: str | None = None
    relative_path_redacted: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    policy_flags: tuple[str, ...] = POLICY_MARKERS

    def validate(self) -> None:
        if not self.action.strip():
            raise AuditLedgerError("Missing audit action.")
        if not self.actor.strip():
            raise AuditLedgerError("Missing audit actor.")
        if not self.target_type.strip():
            raise AuditLedgerError("Missing target_type.")
        if not self.target_id.strip():
            raise AuditLedgerError("Missing target_id.")
        if not self.outcome.strip():
            raise AuditLedgerError("Missing outcome.")
        if not self.approval_reference.strip():
            raise AuditLedgerError("Missing approval_reference.")

        missing = set(POLICY_MARKERS) - set(self.policy_flags)
        if missing:
            raise AuditLedgerError(f"Missing policy flags: {sorted(missing)}")


def assert_ledger_path_allowed(
    ledger_path: Path,
    policy: SafeIOPolicy,
    approval: Approval,
) -> Path:
    path = ledger_path.resolve()

    if path.suffix.lower() != ".jsonl":
        raise AuditLedgerError("Audit ledger path must end with .jsonl.")

    policy.assert_operation_allowed(
        operation=Operation.APPEND_JSONL_AUDIT,
        target_path=path,
        approval=approval,
    )

    return path


def append_audit_event(
    ledger_path: Path,
    event: AuditEvent,
    policy: SafeIOPolicy,
    approval: Approval,
) -> None:
    """
    Append one audit event as one JSON object line.

    This function:
    - appends only
    - requires approval
    - writes only under runtime_local
    - does not inspect source content
    - does not upload or execute anything
    """

    event.validate()
    path = assert_ledger_path_allowed(ledger_path, policy, approval)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(event)

    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def read_audit_events_metadata_only(ledger_path: Path) -> tuple[dict[str, Any], ...]:
    """
    Read existing JSONL audit events.

    This performs local file read only.
    It does not modify the ledger.
    """

    path = ledger_path.resolve()

    if not path.exists():
        return tuple()

    if path.suffix.lower() != ".jsonl":
        raise AuditLedgerError("Audit ledger path must end with .jsonl.")

    events: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                events.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise AuditLedgerError(
                    f"Invalid JSONL at line {line_number}: {exc}"
                ) from exc

    return tuple(events)
