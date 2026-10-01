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
# WRITE_APPROVED_FOR_SAFE_IO_CONTRACT_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Safe IO Contract

Purpose:
- Define allowed read-only source operations.
- Define approved runtime-local write boundaries.
- Block delete, move, rename, unknown execution, network/cloud, daemon/watchdog behavior.

This module defines policy checks only.
It must not scan files, execute scripts, upload data, or mutate source evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


POLICY_MARKERS = (
    "PROPOSAL_ONLY",
    "HUMAN_REVIEW_REQUIRED",
    "NO_EXECUTION_AUTHORIZED",
)


class SafeIOError(RuntimeError):
    """Raised when a DELTA v0.1 IO policy rule is violated."""


class Operation(str, Enum):
    READ_METADATA = "READ_METADATA"
    READ_BYTES_FOR_HASHING = "READ_BYTES_FOR_HASHING"
    READ_TEXT_FOR_APPROVED_SCAN = "READ_TEXT_FOR_APPROVED_SCAN"
    WRITE_SQLITE_REGISTER = "WRITE_SQLITE_REGISTER"
    APPEND_JSONL_AUDIT = "APPEND_JSONL_AUDIT"
    WRITE_CSV_EXPORT = "WRITE_CSV_EXPORT"
    WRITE_XLSX_EXPORT = "WRITE_XLSX_EXPORT"
    WRITE_REVIEW_PACKET = "WRITE_REVIEW_PACKET"
    DELETE = "DELETE"
    MOVE = "MOVE"
    RENAME = "RENAME"
    EXECUTE_UNKNOWN_SCRIPT = "EXECUTE_UNKNOWN_SCRIPT"
    NETWORK_UPLOAD = "NETWORK_UPLOAD"
    CLOUD_SYNC = "CLOUD_SYNC"


FORBIDDEN_OPERATIONS = {
    Operation.DELETE,
    Operation.MOVE,
    Operation.RENAME,
    Operation.EXECUTE_UNKNOWN_SCRIPT,
    Operation.NETWORK_UPLOAD,
    Operation.CLOUD_SYNC,
}


@dataclass(frozen=True)
class Approval:
    approval_reference: str
    actor: str
    scope: str

    def require_valid(self) -> None:
        if not self.approval_reference.strip():
            raise SafeIOError("Missing approval_reference.")
        if not self.actor.strip():
            raise SafeIOError("Missing actor.")
        if not self.scope.strip():
            raise SafeIOError("Missing approval scope.")


@dataclass(frozen=True)
class SafeIOPolicy:
    project_root: Path
    runtime_root: Path
    approved_source_roots: tuple[Path, ...]

    def normalized(self) -> "SafeIOPolicy":
        return SafeIOPolicy(
            project_root=self.project_root.resolve(),
            runtime_root=self.runtime_root.resolve(),
            approved_source_roots=tuple(p.resolve() for p in self.approved_source_roots),
        )

    def is_under_runtime_root(self, path: Path) -> bool:
        candidate = path.resolve()
        runtime = self.runtime_root.resolve()
        return candidate == runtime or runtime in candidate.parents

    def is_under_approved_source_root(self, path: Path) -> bool:
        candidate = path.resolve()
        for root in self.approved_source_roots:
            resolved_root = root.resolve()
            if candidate == resolved_root or resolved_root in candidate.parents:
                return True
        return False

    def assert_operation_allowed(
        self,
        operation: Operation,
        target_path: Path,
        approval: Approval | None = None,
    ) -> None:
        if operation in FORBIDDEN_OPERATIONS:
            raise SafeIOError(f"Forbidden operation blocked: {operation.value}")

        if operation in {
            Operation.READ_METADATA,
            Operation.READ_BYTES_FOR_HASHING,
            Operation.READ_TEXT_FOR_APPROVED_SCAN,
        }:
            if not self.is_under_approved_source_root(target_path):
                raise SafeIOError(f"Read target outside approved source roots: {target_path}")
            return

        if operation in {
            Operation.WRITE_SQLITE_REGISTER,
            Operation.APPEND_JSONL_AUDIT,
            Operation.WRITE_CSV_EXPORT,
            Operation.WRITE_XLSX_EXPORT,
            Operation.WRITE_REVIEW_PACKET,
        }:
            if approval is None:
                raise SafeIOError(f"Write operation requires human approval: {operation.value}")
            approval.require_valid()

            if not self.is_under_runtime_root(target_path):
                raise SafeIOError(f"Write target outside runtime_local boundary: {target_path}")
            return

        raise SafeIOError(f"Unknown or unsupported operation: {operation}")


def default_policy(project_root: Path, approved_source_roots: tuple[Path, ...]) -> SafeIOPolicy:
    return SafeIOPolicy(
        project_root=project_root,
        runtime_root=project_root / "runtime_local",
        approved_source_roots=approved_source_roots,
    ).normalized()
