#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN KERNEL — STEP 96: P0 PATCH PLAN BUILDER
Version: v3.1 ZERO-TRUST / REPORT-ONLY / OWNER-APPROVAL GATE / ULTRA-HARDENED

Purpose:
    Builds a patch-plan package from STEP 95 outputs.
    It never patches, executes, deletes, archives, syncs, writes to Monolith,
    approves lender use, approves SSOT lock, or makes breach claims.

Primary input folder:
    C:\\Users\\Korisnik\\Desktop\\GEMINI SKRIPTE\\TITAN_KERNEL\\VDR_ROOT\\REPORTS\\SYSTEM_HARMONIZATION\\P0_ACTION_COMMANDER

Expected Step95 artifacts:
    - titan_step95_p0_command_queue_*.csv
    - titan_step95_top20_manual_review_*.csv
    - titan_step95_risk_lane_summary_*.csv
    - titan_step95_dry_run_unlock_requirements_*.json
    - titan_step95_validation_*.csv

Outputs:
    - titan_step96_v31_patch_plan_report_*.md
    - titan_step96_v31_patch_plan_manifest_*.json
    - titan_step96_v31_owner_approval_queue_*.csv
    - titan_step96_v31_patch_diff_preview_*.csv
    - titan_step96_v31_allowlist_template_*.csv
    - titan_step96_v31_rollback_plan_*.csv
    - titan_step96_v31_html_dashboard_*.html
    - titan_step96_v31_validation_*.csv
    - memory_fragment_titan_step96_v31_patch_plan_builder_*.json

Usage:
    python titan_step96_p0_patch_plan_builder_v31.py

    python titan_step96_p0_patch_plan_builder_v31.py ^
      --step95-dir "C:\\path\\P0_ACTION_COMMANDER" ^
      --output-dir "C:\\path\\PATCH_PLAN_BUILDER_V31" ^
      --max-rows 200

Boundary:
    REPORT_ONLY_PATCH_PLAN_NO_PATCH_NO_DELETE_NO_EXECUTE_V31
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import html
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ==================== CONFIG ====================

MODE = "REPORT_ONLY_PATCH_PLAN_NO_PATCH_NO_DELETE_NO_EXECUTE_V31"
VERDICT = "PATCH_PLAN_CREATED__OWNER_APPROVAL_REQUIRED__ALL_WRITES_BLOCKED__V31"
VERSION = "3.1.0"

DEFAULT_STEP95_DIR = (
    r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL\VDR_ROOT\REPORTS"
    r"\SYSTEM_HARMONIZATION\P0_ACTION_COMMANDER"
)
DEFAULT_OUTPUT_DIR = (
    r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL\VDR_ROOT\REPORTS"
    r"\SYSTEM_HARMONIZATION\PATCH_PLAN_BUILDER_V31"
)
DEFAULT_MEMORY_DIR = (
    r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL\CORE"
    r"\MEMORY_REGISTER\FRAGMENTS"
)

DENY_FLAGS = {
    "patch_allowed": "NO",
    "script_execution_allowed": "NO",
    "delete_allowed": "NO",
    "archive_allowed": "NO",
    "sync_allowed": "NO",
    "monolith_write_allowed": "NO",
    "lender_use_allowed": "NO",
    "ssot_lock_allowed": "NO",
    "breach_claim_allowed": "NO"
}

BLOCKED_EXTENSIONS = {
    ".xlsx", ".xlsm", ".xls", ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".zip", ".7z", ".rar", ".db", ".sqlite", ".sqlite3",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".exe", ".dll", ".bin"
}
TEXT_EXTENSIONS = {
    ".py", ".ps1", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".csv", ".sql", ".bat", ".cmd", ".html", ".css", ".js"
}

STEP95_PATTERNS = {
    "command_queue": "titan_step95_p0_command_queue_*.csv",
    "top20_manual_review": "titan_step95_top20_manual_review_*.csv",
    "risk_lane_summary": "titan_step95_risk_lane_summary_*.csv",
    "dry_run_unlock": "titan_step95_dry_run_unlock_requirements_*.json",
    "validation": "titan_step95_validation_*.csv"
}


# ==================== ENUMS / MODELS ====================

class PatchType(str, Enum):
    HEADER_GOVERNANCE = "HEADER_GOVERNANCE"
    VALIDATION_MANIFEST = "VALIDATION_MANIFEST"
    SECURITY_BOUNDARY = "SECURITY_BOUNDARY"
    EXECUTION_ALLOWLIST = "EXECUTION_ALLOWLIST"
    CONFIG_REFACTOR = "CONFIG_REFACTOR"
    SYNC_DISABLE = "SYNC_DISABLE"
    LEGACY_REVIEW_ONLY = "LEGACY_REVIEW_ONLY"
    COMPLIANCE_TAG = "COMPLIANCE_TAG"
    PERFORMANCE_REVIEW = "PERFORMANCE_REVIEW"
    BINARY_MANUAL_REVIEW = "BINARY_MANUAL_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ComplianceTag(str, Enum):
    EU_AI_ACT = "EU_AI_ACT"
    NIS2 = "NIS2"
    GDPR = "GDPR"
    ISO27001 = "ISO27001"
    EIB_SOVEREIGN = "EIB_SOVEREIGN"
    EBRD_DD = "EBRD_DD"
    NONE = "NONE"


@dataclass
class ArtifactRow:
    logical_name: str
    path: str
    found: str
    rows: int
    sha256: str
    status: str


@dataclass
class PlanRow:
    plan_id: str
    source_command_id: str
    lane: str
    priority: str
    severity: str
    affected_item: str
    file_exists: str
    file_ext: str
    file_sha256: str
    patch_type: str
    proposed_patch_code: str
    proposed_patch_summary: str
    risk_score: int
    compliance_tags: str
    diff_preview_status: str
    allowed_now: str
    owner_approval_required: str
    owner: str
    required_evidence: str
    approval_decision: str
    approval_comment: str
    rollback_required: str
    rollback_plan_id: str
    blocked_actions: str
    risk_if_auto_applied: str
    source_reason: str


# ==================== LOW-LEVEL UTILS ====================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_stamp(dt: datetime) -> str:
    return dt.strftime("%Y%m%d-%H%M%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    if not path.exists() or not path.is_file():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as exc:
        return f"HASH_FAILED::{type(exc).__name__}"


def latest(path: Path, pattern: str) -> Optional[Path]:
    candidates = list(path.glob(pattern))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def read_csv_safe(path: Optional[Path]) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except Exception:
        return []


def read_json_safe(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    ensure_dir(path.parent)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for k in row.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def norm(row: Dict[str, Any], key: str, default: str = "") -> str:
    return str(row.get(key, default) or default).strip()


def lower_blob(row: Dict[str, Any]) -> str:
    return " | ".join(f"{k}={v}" for k, v in row.items()).lower()


def safe_read_text(path: Path, max_chars: int = 400_000) -> Tuple[str, str]:
    if not path.exists():
        return "", "FILE_NOT_FOUND"
    if path.suffix.lower() in BLOCKED_EXTENSIONS:
        return "", "BINARY_OR_OFFICE_BLOCKED"
    if path.suffix.lower() and path.suffix.lower() not in TEXT_EXTENSIONS:
        return "", "UNKNOWN_EXTENSION_BLOCKED_FOR_PREVIEW"
    try:
        data = path.read_text(encoding="utf-8")
        if len(data) > max_chars:
            return data[:max_chars], "TEXT_TRUNCATED_FOR_PREVIEW"
        return data, "TEXT_READ_OK"
    except UnicodeDecodeError:
        try:
            data = path.read_text(encoding="utf-8-sig")
            if len(data) > max_chars:
                return data[:max_chars], "TEXT_TRUNCATED_FOR_PREVIEW"
            return data, "TEXT_READ_OK_UTF8SIG"
        except Exception as exc:
            return "", f"TEXT_READ_FAILED::{type(exc).__name__}"
    except Exception as exc:
        return "", f"TEXT_READ_FAILED::{type(exc).__name__}"


def csv_safe_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(v.value if isinstance(v, Enum) else v) for v in value)
    if isinstance(value, Enum):
        return value.value
    return str(value)


# ==================== INPUT DISCOVERY ====================

def discover_step95_inputs(step95_dir: Path) -> Tuple[Dict[str, Optional[Path]], List[ArtifactRow]]:
    found: Dict[str, Optional[Path]] = {}
    artifacts: List[ArtifactRow] = []

    for logical, pattern in STEP95_PATTERNS.items():
        p = latest(step95_dir, pattern)
        found[logical] = p

        if p and p.exists():
            rows = len(read_csv_safe(p)) if p.suffix.lower() == ".csv" else 1
            artifacts.append(ArtifactRow(
                logical_name=logical,
                path=str(p),
                found="YES",
                rows=rows,
                sha256=sha256_file(p),
                status="FOUND"
            ))
        else:
            artifacts.append(ArtifactRow(
                logical_name=logical,
                path="",
                found="NO",
                rows=0,
                sha256="",
                status="MISSING"
            ))

    return found, artifacts


def select_plan_source_rows(
    command_rows: List[Dict[str, str]],
    top20_rows: List[Dict[str, str]],
    max_rows: int
) -> List[Dict[str, str]]:
    """
    Top20 manual review first, then command queue.
    Dedup: command_id + affected_item.
    """
    selected: List[Dict[str, str]] = []
    seen = set()

    def add(row: Dict[str, str]) -> None:
        cid = norm(row, "command_id") or norm(row, "source_command_id") or "NO_COMMAND_ID"
        item = norm(row, "affected_item") or norm(row, "file") or norm(row, "path") or "UNKNOWN_ITEM"
        key = (cid, item)
        if key in seen:
            return
        seen.add(key)
        selected.append(row)

    for row in top20_rows:
        add(row)
    for row in command_rows:
        if len(selected) >= max_rows:
            break
        add(row)

    return selected[:max_rows]


# ==================== PATCH INFERENCE ====================

def infer_patch_plan_v31(row: Dict[str, str], affected: Path) -> Tuple[PatchType, str, str, int, List[ComplianceTag]]:
    lane = norm(row, "lane")
    reason = (norm(row, "source_reason") + " " + norm(row, "recommended_action") + " " + lower_blob(row)).lower()
    ext = affected.suffix.lower()

    if ext in BLOCKED_EXTENSIONS:
        return (
            PatchType.BINARY_MANUAL_REVIEW,
            "MANUAL_REVIEW_BINARY_OR_OFFICE_FILE",
            "Binary/Office/PDF/DB files require manual document-controller review; no text patch allowed.",
            90,
            [ComplianceTag.ISO27001]
        )

    if lane == "SECURITY_BOUNDARY" or any(x in reason for x in ["security", "destructive", "delete", "remove", "secret", "credential", "token", "password"]):
        return (
            PatchType.SECURITY_BOUNDARY,
            "ADD_DESTRUCTIVE_ACTION_BLOCKERS_V31",
            "Add explicit owner-approved allowlist for destructive or secret-handling operations.",
            85,
            [ComplianceTag.NIS2, ComplianceTag.GDPR, ComplianceTag.ISO27001]
        )

    if lane == "EXECUTION_BOUNDARY" or any(x in reason for x in ["execution", "live run", "subprocess", "eval(", "exec(", "popen", "invoke-expression"]):
        return (
            PatchType.EXECUTION_ALLOWLIST,
            "ADD_DRY_RUN_AND_EXECUTION_ALLOWLIST_V31",
            "Force DRY_RUN=True by default and require explicit allowlist before live execution.",
            75,
            [ComplianceTag.EU_AI_ACT, ComplianceTag.ISO27001]
        )

    if lane == "MONOLITH_SYNC_BOUNDARY" or any(x in reason for x in ["sync", "monolith", "ssot write", "database write"]):
        return (
            PatchType.SYNC_DISABLE,
            "DISABLE_SYNC_WRITE_BY_DEFAULT_V31",
            "Disable sync/write by default until signed owner approval exists.",
            70,
            [ComplianceTag.EIB_SOVEREIGN, ComplianceTag.ISO27001]
        )

    if lane == "MISSING_GOVERNANCE_HEADER" or any(x in reason for x in ["header", "mode missing", "boundary missing", "governance"]):
        return (
            PatchType.HEADER_GOVERNANCE,
            "ADD_TITAN_GOVERNANCE_HEADER_V31",
            "Add TITAN governance header with mode and all denied actions.",
            35,
            [ComplianceTag.EIB_SOVEREIGN, ComplianceTag.ISO27001]
        )

    if lane == "MISSING_VALIDATION" or any(x in reason for x in ["validation", "manifest", "hash", "audit", "checksum"]):
        return (
            PatchType.VALIDATION_MANIFEST,
            "ADD_VALIDATION_MANIFEST_HASH_OUTPUTS_V31",
            "Add validation CSV, manifest JSON and SHA-256 output contract.",
            45,
            [ComplianceTag.EIB_SOVEREIGN, ComplianceTag.ISO27001]
        )

    if lane == "PATH_HARDCODE_RISK" or any(x in reason for x in ["hardcoded", "path", "c:\\", "desktop"]):
        return (
            PatchType.CONFIG_REFACTOR,
            "MOVE_PATHS_TO_CONFIG_V31",
            "Move hardcoded paths to configuration and add path-existence validation.",
            50,
            [ComplianceTag.ISO27001]
        )

    if lane == "DUPLICATE_LEGACY_REVIEW" or any(x in reason for x in ["duplicate", "legacy", "copy", "arhiva", "stari", "(1)"]):
        return (
            PatchType.LEGACY_REVIEW_ONLY,
            "DUPLICATE_LEGACY_CLASSIFICATION_ONLY_V31",
            "Do not patch; classify duplicate/legacy status and route to archive review without deletion.",
            30,
            [ComplianceTag.NONE]
        )

    if any(x in reason for x in ["gdpr", "nis2", "iso27001", "compliance", "eu ai act"]):
        return (
            PatchType.COMPLIANCE_TAG,
            "ADD_COMPLIANCE_TAGS_V31",
            "Add compliance tagging for review; no legal compliance claim is final without evidence.",
            40,
            [ComplianceTag.EU_AI_ACT, ComplianceTag.NIS2, ComplianceTag.GDPR, ComplianceTag.ISO27001]
        )

    if any(x in reason for x in ["slow", "performance", "timeout", "large file"]):
        return (
            PatchType.PERFORMANCE_REVIEW,
            "PERFORMANCE_REVIEW_ONLY_V31",
            "Review performance issue; no code change without owner-approved patch design.",
            40,
            [ComplianceTag.NONE]
        )

    return (
        PatchType.MANUAL_REVIEW,
        "MANUAL_REVIEW_REQUIRED_V31",
        "Manual owner must define exact safe patch before any execution.",
        55,
        [ComplianceTag.NONE]
    )


def proposed_preview(original: str, patch_code: str, affected: Path) -> Tuple[str, str]:
    """
    Produces text preview only.
    It does not write.
    """
    if not original:
        return original, "NO_CONTENT_FOR_PREVIEW"

    if patch_code == "ADD_TITAN_GOVERNANCE_HEADER_V31":
        if "TITAN GOVERNANCE HEADER" in original[:5000] or "REPORT_ONLY" in original[:3000]:
            return original, "SIMILAR_GOVERNANCE_BOUNDARY_ALREADY_PRESENT"
        header = (
            "# TITAN GOVERNANCE HEADER — AUTO-PREVIEW ONLY\n"
            "# Mode: REPORT_ONLY_PENDING_OWNER_APPROVAL\n"
            "# Boundaries: NO_PATCH, NO_DELETE, NO_EXECUTE, NO_ARCHIVE, NO_SYNC, NO_MONOLITH_WRITE, NO_SSOT_LOCK, NO_LENDER_USE, NO_BREACH_CLAIM\n"
            "# Status: PATCH_PLAN_ONLY — owner approval required before any operational use.\n\n"
        )
        if affected.suffix.lower() in {".json"}:
            return original, "JSON_HEADER_PATCH_BLOCKED_USE_MANUAL_METADATA_FIELD"
        return header + original, "PREVIEW_CREATED"

    marker_map = {
        "ADD_DESTRUCTIVE_ACTION_BLOCKERS_V31": "# TITAN TODO: Guard destructive operations with explicit owner-approved allowlist.",
        "ADD_DRY_RUN_AND_EXECUTION_ALLOWLIST_V31": "# TITAN TODO: Add DRY_RUN=True default and execution allowlist before live run.",
        "DISABLE_SYNC_WRITE_BY_DEFAULT_V31": "# TITAN TODO: Ensure sync/write paths default to disabled until owner approval.",
        "ADD_VALIDATION_MANIFEST_HASH_OUTPUTS_V31": "# TITAN TODO: Add validation CSV, manifest JSON and SHA-256 output contract.",
        "MOVE_PATHS_TO_CONFIG_V31": "# TITAN TODO: Move hardcoded paths to config and validate existence.",
        "ADD_COMPLIANCE_TAGS_V31": "# TITAN TODO: Add compliance tags as metadata only; do not make final compliance claim.",
        "PERFORMANCE_REVIEW_ONLY_V31": "# TITAN TODO: Review performance bottleneck manually before patch design.",
        "MANUAL_REVIEW_REQUIRED_V31": "# TITAN TODO: Manual owner must define exact patch design.",
    }

    marker = marker_map.get(patch_code)
    if marker:
        if affected.suffix.lower() == ".json":
            return original, "JSON_TODO_PATCH_BLOCKED_USE_MANUAL_METADATA_FIELD"
        return original.rstrip() + "\n\n" + marker + "\n", "PREVIEW_CREATED_TODO_MARKER_ONLY"

    return original, "NO_AUTOMATIC_PREVIEW_FOR_PATCH_CODE"


def make_diff_preview(path: Path, patch_code: str) -> Tuple[str, str]:
    original, status = safe_read_text(path)
    if status not in {"TEXT_READ_OK", "TEXT_READ_OK_UTF8SIG", "TEXT_TRUNCATED_FOR_PREVIEW"}:
        return status, ""

    proposed, preview_status = proposed_preview(original, patch_code, path)
    if proposed == original:
        return preview_status, ""

    diff_iter = difflib.unified_diff(
        original.splitlines(),
        proposed.splitlines(),
        fromfile=f"{path.name}::current",
        tofile=f"{path.name}::proposed_preview_only",
        lineterm=""
    )
    diff_lines = list(diff_iter)[:250]
    return preview_status, "\n".join(diff_lines)


# ==================== PLAN BUILDING ====================

def build_plan_rows(rows: List[Dict[str, str]]) -> Tuple[List[PlanRow], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    plan: List[PlanRow] = []
    diff_rows: List[Dict[str, Any]] = []
    allowlist_rows: List[Dict[str, Any]] = []
    rollback_rows: List[Dict[str, Any]] = []

    for idx, row in enumerate(rows, start=1):
        item = norm(row, "affected_item") or norm(row, "file") or norm(row, "path") or "UNKNOWN_ITEM"
        p = Path(item)
        exists = "YES" if p.exists() and p.is_file() else "NO"
        ext = p.suffix.lower() if p.suffix else ""
        digest = sha256_file(p) if exists == "YES" else "FILE_NOT_FOUND"

        patch_type, patch_code, patch_summary, risk_score, compliance_tags = infer_patch_plan_v31(row, p)
        diff_status, diff_preview = make_diff_preview(p, patch_code) if exists == "YES" else ("FILE_NOT_FOUND", "")

        plan_id = f"STEP96V31-PLAN-{idx:05d}"
        rollback_id = f"STEP96V31-ROLLBACK-{idx:05d}"
        source_command_id = norm(row, "command_id") or norm(row, "source_command_id") or f"ROW-{idx}"
        lane = norm(row, "lane", "UNKNOWN")
        priority = norm(row, "priority", "LOW")
        severity = norm(row, "severity", "P2")
        owner = norm(row, "owner", "Manual Review Owner")
        source_reason = norm(row, "source_reason") or norm(row, "recommended_action") or "Derived from Step95 row."

        risk_if_auto = (
            "Automatic patching could modify an unapproved or misclassified P0 item, "
            "break auditability, contaminate SSOT evidence, or create false lender/governance confidence."
        )

        plan_row = PlanRow(
            plan_id=plan_id,
            source_command_id=source_command_id,
            lane=lane,
            priority=priority,
            severity=severity,
            affected_item=item,
            file_exists=exists,
            file_ext=ext,
            file_sha256=digest,
            patch_type=patch_type.value,
            proposed_patch_code=patch_code,
            proposed_patch_summary=patch_summary,
            risk_score=risk_score,
            compliance_tags=";".join(tag.value for tag in compliance_tags),
            diff_preview_status=diff_status,
            allowed_now="REPORT_ONLY_PATCH_PLAN",
            owner_approval_required="YES",
            owner=owner,
            required_evidence="Owner approval + exact file hash + diff review + rollback plan + validation result.",
            approval_decision="PENDING",
            approval_comment="",
            rollback_required="YES",
            rollback_plan_id=rollback_id,
            blocked_actions="PATCH;EXECUTE;DELETE;ARCHIVE;SYNC;MONOLITH_WRITE;SSOT_LOCK;LENDER_USE;BREACH_CLAIM",
            risk_if_auto_applied=risk_if_auto,
            source_reason=source_reason
        )
        plan.append(plan_row)

        diff_rows.append({
            "plan_id": plan_id,
            "affected_item": item,
            "file_sha256": digest,
            "proposed_patch_code": patch_code,
            "diff_preview_status": diff_status,
            "diff_preview_truncated": "YES_250_LINES_MAX",
            "diff_preview": diff_preview
        })

        allowlist_rows.append({
            "plan_id": plan_id,
            "source_command_id": source_command_id,
            "affected_item": item,
            "file_sha256_before_patch": digest,
            "proposed_patch_code": patch_code,
            "owner": owner,
            "approval_decision": "PENDING",
            "approved_by": "",
            "approved_at_utc": "",
            "allowed_for_step97": "NO",
            "approval_comment": "",
            "required_before_yes": "Verify hash, review diff, confirm rollback plan, owner signs approval."
        })

        rollback_rows.append({
            "rollback_plan_id": rollback_id,
            "plan_id": plan_id,
            "affected_item": item,
            "file_sha256_before_patch": digest,
            "backup_required_before_patch": "YES",
            "backup_location_expected_step97": "STEP97_BACKUP_VAULT_TIMESTAMPED_FOLDER",
            "restore_method": "Restore exact pre-patch file from backup vault after hash verification.",
            "rollback_allowed_now": "NO",
            "rollback_owner_approval_required": "YES"
        })

    return plan, diff_rows, allowlist_rows, rollback_rows


# ==================== VALIDATION / REPORTS ====================

def build_validation(artifacts: List[ArtifactRow], plan: List[PlanRow], allowlist_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    missing = [a.logical_name for a in artifacts if a.found != "YES"]
    allowlist_all_no = all(str(r.get("allowed_for_step97")) == "NO" for r in allowlist_rows)
    owner_all_required = all(r.owner_approval_required == "YES" for r in plan)

    return [
        {
            "check_id": "VAL-001",
            "check_name": "Step95 inputs present",
            "status": "PASS" if not missing else "FAIL",
            "severity": "P0" if missing else "INFO",
            "detail": "All expected Step95 artifacts found." if not missing else "Missing: " + ", ".join(missing)
        },
        {
            "check_id": "VAL-002",
            "check_name": "Patch execution blocked",
            "status": "PASS",
            "severity": "P0",
            "detail": "No patch is executed by this script."
        },
        {
            "check_id": "VAL-003",
            "check_name": "Delete/archive/sync/lock blocked",
            "status": "PASS",
            "severity": "P0",
            "detail": "Delete, archive, sync, Monolith write, SSOT lock, lender use and breach claim remain blocked."
        },
        {
            "check_id": "VAL-004",
            "check_name": "Owner approval required on all plan rows",
            "status": "PASS" if owner_all_required else "FAIL",
            "severity": "P0",
            "detail": f"{len(plan)} plan rows checked."
        },
        {
            "check_id": "VAL-005",
            "check_name": "Allowlist default blocks Step97",
            "status": "PASS" if allowlist_all_no else "FAIL",
            "severity": "P0",
            "detail": "All allowlist rows default to allowed_for_step97=NO."
        },
        {
            "check_id": "VAL-006",
            "check_name": "Plan generated",
            "status": "PASS" if len(plan) > 0 else "WARN",
            "severity": "P1" if len(plan) == 0 else "INFO",
            "detail": f"{len(plan)} patch-plan rows generated."
        }
    ]


def lane_summary(plan: List[PlanRow]) -> List[Dict[str, Any]]:
    counter = Counter(r.lane for r in plan)
    risk_by_lane: Dict[str, List[int]] = {}
    for r in plan:
        risk_by_lane.setdefault(r.lane, []).append(r.risk_score)

    rows: List[Dict[str, Any]] = []
    for lane, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        risks = risk_by_lane.get(lane, [])
        rows.append({
            "lane": lane,
            "rows": count,
            "avg_risk_score": round(sum(risks) / len(risks), 2) if risks else 0,
            "max_risk_score": max(risks) if risks else 0
        })
    return rows


def render_markdown(created: datetime, step95_dir: Path, output_dir: Path, artifacts: List[ArtifactRow], plan: List[PlanRow], outputs: Dict[str, str]) -> str:
    summary = lane_summary(plan)

    lines = [
        "# TITAN STEP 96 v3.1 — P0 PATCH PLAN BUILDER",
        "",
        f"Created UTC: `{created.isoformat()}`",
        "",
        "## Status",
        "",
        f"- Version: `{VERSION}`",
        f"- Mode: `{MODE}`",
        f"- Verdict: `{VERDICT}`",
    ]
    for k, v in DENY_FLAGS.items():
        lines.append(f"- {k}: `{v}`")

    lines += [
        "",
        "## Input",
        "",
        f"- Step95 folder: `{step95_dir}`",
        f"- Output folder: `{output_dir}`",
        "",
        "## Summary",
        "",
        f"- Patch-plan rows: `{len(plan)}`",
        "- Owner approval required: `YES`",
        "- Allowlist default: `allowed_for_step97 = NO`",
        "- Writes performed by this script: `0`",
        "",
        "## Lane Summary",
        "",
        "| Lane | Rows | Avg Risk | Max Risk |",
        "|---|---:|---:|---:|"
    ]
    for r in summary:
        lines.append(f"| {r['lane']} | {r['rows']} | {r['avg_risk_score']} | {r['max_risk_score']} |")

    lines += [
        "",
        "## Input Artifacts",
        "",
        "| Artifact | Found | Rows | Status | Path |",
        "|---|---:|---:|---|---|"
    ]
    for a in artifacts:
        lines.append(f"| {a.logical_name} | {a.found} | {a.rows} | {a.status} | `{a.path}` |")

    lines += [
        "",
        "## Governance Boundary",
        "",
        "This script creates a patch plan only. It does not patch, execute, delete, archive, sync, write to Monolith, approve lender use, approve SSOT lock or make breach claims.",
        "",
        "Step97 may only be drafted after owner-approved allowlist rows are signed and hash-checked.",
        "",
        "## Outputs",
        ""
    ]
    for k, v in outputs.items():
        lines.append(f"- {k}: `{v}`")

    lines.append("")
    return "\n".join(lines)


def render_html_dashboard(created: datetime, plan: List[PlanRow]) -> str:
    avg_risk = (sum(r.risk_score for r in plan) / len(plan)) if plan else 0
    rows_html = []

    for r in plan:
        if r.risk_score >= 70:
            risk_class = "risk-high"
        elif r.risk_score >= 40:
            risk_class = "risk-medium"
        else:
            risk_class = "risk-low"

        rows_html.append(
            "<tr class='{cls}'>"
            "<td>{plan_id}</td><td>{lane}</td><td>{priority}</td><td>{severity}</td>"
            "<td>{risk}</td><td>{ptype}</td><td>{item}</td><td>{approval}</td>"
            "</tr>".format(
                cls=risk_class,
                plan_id=html.escape(r.plan_id),
                lane=html.escape(r.lane),
                priority=html.escape(r.priority),
                severity=html.escape(r.severity),
                risk=r.risk_score,
                ptype=html.escape(r.patch_type),
                item=html.escape(r.affected_item),
                approval=html.escape(r.owner_approval_required)
            )
        )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>TITAN Step96 v3.1 Patch Plan</title>
<style>
body {{ font-family: Calibri, Arial, sans-serif; margin: 24px; color: #111; }}
h1 {{ margin-bottom: 4px; }}
.meta {{ color: #444; margin-bottom: 20px; }}
.badge {{ display: inline-block; padding: 4px 8px; border-radius: 6px; background: #111; color: #fff; margin-right: 6px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #ccc; padding: 7px; text-align: left; vertical-align: top; }}
th {{ background: #0f2742; color: white; }}
.risk-high {{ background: #ffd6d6; }}
.risk-medium {{ background: #fff1c2; }}
.risk-low {{ background: #dff2df; }}
.boundary {{ border-left: 5px solid #0f2742; padding: 10px; background: #f5f7fa; margin: 15px 0; }}
</style>
</head>
<body>
<h1>TITAN STEP 96 v3.1 — P0 PATCH PLAN BUILDER</h1>
<div class="meta">Generated UTC: {html.escape(created.isoformat())}</div>
<div>
<span class="badge">{html.escape(MODE)}</span>
<span class="badge">ALL WRITES BLOCKED</span>
<span class="badge">OWNER APPROVAL REQUIRED</span>
</div>
<div class="boundary">
<strong>Boundary:</strong> No patch, no execution, no delete, no archive, no sync, no Monolith write,
no lender use, no SSOT lock, no breach claim.
</div>
<h2>Summary</h2>
<p>Total plan rows: <strong>{len(plan)}</strong> | Average risk score: <strong>{avg_risk:.1f}</strong></p>
<h2>Plan Rows</h2>
<table>
<tr>
<th>Plan ID</th><th>Lane</th><th>Priority</th><th>Severity</th><th>Risk</th>
<th>Patch Type</th><th>Affected Item</th><th>Owner Approval</th>
</tr>
{''.join(rows_html)}
</table>
</body>
</html>
"""


# ==================== MAIN ====================

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN Step96 v3.1 P0 Patch Plan Builder — report-only")
    parser.add_argument("--step95-dir", default=DEFAULT_STEP95_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR)
    parser.add_argument("--max-rows", type=int, default=200)
    parser.add_argument("--stamp", default="")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    created = utc_now()
    stamp = args.stamp or make_stamp(created)

    step95_dir = Path(args.step95_dir)
    output_dir = Path(args.output_dir)
    memory_dir = Path(args.memory_dir)
    ensure_dir(output_dir)
    ensure_dir(memory_dir)

    found, artifacts = discover_step95_inputs(step95_dir)
    command_rows = read_csv_safe(found.get("command_queue"))
    top20_rows = read_csv_safe(found.get("top20_manual_review"))
    dry_run_unlock = read_json_safe(found.get("dry_run_unlock"))

    selected_rows = select_plan_source_rows(command_rows, top20_rows, args.max_rows)
    plan, diff_rows, allowlist_rows, rollback_rows = build_plan_rows(selected_rows)
    validation_rows = build_validation(artifacts, plan, allowlist_rows)
    lane_rows = lane_summary(plan)

    outputs = {
        "md": str(output_dir / f"titan_step96_v31_patch_plan_report_{stamp}.md"),
        "json": str(output_dir / f"titan_step96_v31_patch_plan_manifest_{stamp}.json"),
        "owner_approval_queue_csv": str(output_dir / f"titan_step96_v31_owner_approval_queue_{stamp}.csv"),
        "patch_diff_preview_csv": str(output_dir / f"titan_step96_v31_patch_diff_preview_{stamp}.csv"),
        "allowlist_template_csv": str(output_dir / f"titan_step96_v31_allowlist_template_{stamp}.csv"),
        "rollback_plan_csv": str(output_dir / f"titan_step96_v31_rollback_plan_{stamp}.csv"),
        "risk_lane_summary_csv": str(output_dir / f"titan_step96_v31_risk_lane_summary_{stamp}.csv"),
        "input_artifact_index_csv": str(output_dir / f"titan_step96_v31_input_artifact_index_{stamp}.csv"),
        "validation_csv": str(output_dir / f"titan_step96_v31_validation_{stamp}.csv"),
        "html_dashboard": str(output_dir / f"titan_step96_v31_html_dashboard_{stamp}.html"),
        "memory_fragment": str(memory_dir / f"memory_fragment_titan_step96_v31_patch_plan_builder_{stamp}.json")
    }

    write_csv(Path(outputs["owner_approval_queue_csv"]), [asdict(r) for r in plan])
    write_csv(Path(outputs["patch_diff_preview_csv"]), diff_rows)
    write_csv(Path(outputs["allowlist_template_csv"]), allowlist_rows)
    write_csv(Path(outputs["rollback_plan_csv"]), rollback_rows)
    write_csv(Path(outputs["risk_lane_summary_csv"]), lane_rows)
    write_csv(Path(outputs["input_artifact_index_csv"]), [asdict(a) for a in artifacts])
    write_csv(Path(outputs["validation_csv"]), validation_rows)
    write_text(Path(outputs["html_dashboard"]), render_html_dashboard(created, plan))

    manifest = {
        "created_utc": created.isoformat(),
        "version": VERSION,
        "mode": MODE,
        "verdict": VERDICT,
        **DENY_FLAGS,
        "step95_dir": str(step95_dir),
        "output_dir": str(output_dir),
        "summary": {
            "step95_command_rows_seen": len(command_rows),
            "step95_top20_rows_seen": len(top20_rows),
            "selected_plan_rows": len(plan),
            "lane_rows": len(lane_rows),
            "all_rows_require_owner_approval": all(r.owner_approval_required == "YES" for r in plan),
            "allowlist_default_allowed_for_step97": "NO",
            "dry_run_unlock_source_loaded": bool(dry_run_unlock)
        },
        "risk_lane_summary": lane_rows,
        "outputs": outputs,
        "boundary": "REPORT_ONLY. No patch, execution, delete, archive, sync, Monolith write, lender use, SSOT lock or breach claim."
    }
    write_json(Path(outputs["json"]), manifest)
    write_text(Path(outputs["md"]), render_markdown(created, step95_dir, output_dir, artifacts, plan, outputs))

    memory = {
        "export_source": "TITAN_STEP96_V31_P0_PATCH_PLAN_BUILDER",
        "created_utc": created.isoformat(),
        "analysis_type": "p0_patch_plan_builder",
        "version": VERSION,
        "mode": MODE,
        "verdict": VERDICT,
        **DENY_FLAGS,
        "summary": manifest["summary"],
        "verified_facts": [
            "Step96 v3.1 created a report-only patch plan from Step95 outputs.",
            "No files were modified.",
            "All proposed patches require owner approval.",
            "Allowlist template defaults every row to allowed_for_step97=NO."
        ],
        "recommended_next_actions": [
            "Open owner approval queue.",
            "Review diff preview for Top20 first.",
            "Do not approve any row until hash, diff and rollback plan are accepted.",
            "Draft Step97 only from signed allowlist rows."
        ],
        "red_flags": [
            "Live remediator remains rejected.",
            "Any automatic patch without signed allowlist violates governance.",
            "SSOT lock and lender use remain blocked."
        ]
    }
    write_json(Path(outputs["memory_fragment"]), memory)

    print("TITAN STEP 96 v3.1 — P0 PATCH PLAN BUILDER")
    print(f"Mode: {MODE}")
    print(f"Verdict: {VERDICT}")
    print(f"Step95 command rows seen: {len(command_rows)}")
    print(f"Step95 top20 rows seen: {len(top20_rows)}")
    print(f"Selected plan rows: {len(plan)}")
    print("Patch allowed: NO")
    print("Script execution allowed: NO")
    print("Delete allowed: NO")
    print("Archive allowed: NO")
    print("Sync allowed: NO")
    print("Monolith write allowed: NO")
    print("Lender use allowed: NO")
    print("SSOT lock allowed: NO")
    print("Breach claim allowed: NO")
    print(f"MD: {outputs['md']}")
    print(f"JSON: {outputs['json']}")
    print(f"Owner approval queue CSV: {outputs['owner_approval_queue_csv']}")
    print(f"Patch diff preview CSV: {outputs['patch_diff_preview_csv']}")
    print(f"Allowlist template CSV: {outputs['allowlist_template_csv']}")
    print(f"Rollback plan CSV: {outputs['rollback_plan_csv']}")
    print(f"HTML dashboard: {outputs['html_dashboard']}")
    print(f"Validation CSV: {outputs['validation_csv']}")
    print(f"Memory fragment: {outputs['memory_fragment']}")

    missing = [a.logical_name for a in artifacts if a.found != "YES"]
    return 2 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
