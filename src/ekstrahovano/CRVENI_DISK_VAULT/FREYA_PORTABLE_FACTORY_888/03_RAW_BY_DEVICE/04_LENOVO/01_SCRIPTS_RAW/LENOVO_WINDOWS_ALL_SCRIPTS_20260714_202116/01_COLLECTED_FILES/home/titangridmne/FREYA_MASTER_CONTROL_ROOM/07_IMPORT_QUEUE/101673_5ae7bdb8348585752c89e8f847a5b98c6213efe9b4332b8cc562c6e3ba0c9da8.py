#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
28_distribution_readiness_gatekeeper.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 28 — Distribution Readiness Gatekeeper
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Perform final distribution-readiness control before any investor/lender/board
data-room package is sent outside the working environment.

This script does NOT send files.
This script does NOT upload files.
This script does NOT modify original source documents.
This script does NOT override board/legal/finance/ESG/lender decisions.
It creates a formal readiness decision record:
- GO
- GO_WITH_CONDITIONS
- HOLD
- BLOCKED
- INCOMPLETE

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.
Freeze precedes distribution.
Gatekeeping precedes external release.

Inputs
------
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json
05_reports/investor_data_room_freeze/TITAN_INVESTOR_DATA_ROOM_FREEZE_REPORT.json
05_reports/board_decision_memo/TITAN_BOARD_DECISION_MEMO.json
05_reports/lender_due_diligence_pack/TITAN_LENDER_DD_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/legal_compliance_gap_analysis/TITAN_LEGAL_COMPLIANCE_MEMO.json
05_reports/esg_permitting_risk_analysis/TITAN_ESG_PERMITTING_MEMO.json
05_reports/capex_loan_bankability_analysis/TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json
05_reports/latest_audit_record.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json
05_reports/risk_signals_report.json
05_reports/document_priority_rank.json

Outputs
-------
05_reports/distribution_readiness/TITAN_DISTRIBUTION_READINESS_DECISION.md
05_reports/distribution_readiness/TITAN_DISTRIBUTION_READINESS_DECISION.json
05_reports/distribution_readiness/TITAN_DISTRIBUTION_BLOCKER_REGISTER.csv
05_reports/distribution_readiness/TITAN_DISTRIBUTION_CONDITION_REGISTER.csv
05_reports/distribution_readiness/TITAN_DISTRIBUTION_RELEASE_INDEX.csv
05_reports/distribution_readiness/TITAN_DISTRIBUTION_READINESS_MANIFEST.json
06_logs/distribution_readiness_gatekeeper_audit.jsonl
06_logs/distribution_readiness_gatekeeper_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\28_distribution_readiness_gatekeeper.py" --print

Strict gate:
------------
python ".\\08_scripts\\28_distribution_readiness_gatekeeper.py" --strict --print

Target examples:
----------------
python ".\\08_scripts\\28_distribution_readiness_gatekeeper.py" --target EBRD --print
python ".\\08_scripts\\28_distribution_readiness_gatekeeper.py" --target BOARD --print
python ".\\08_scripts\\28_distribution_readiness_gatekeeper.py" --target INVESTOR --print
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "28_distribution_readiness_gatekeeper.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
DEFAULT_OUTPUT_DIR = Path("05_reports") / "distribution_readiness"

OUTPUT_DECISION_MD = "TITAN_DISTRIBUTION_READINESS_DECISION.md"
OUTPUT_DECISION_JSON = "TITAN_DISTRIBUTION_READINESS_DECISION.json"
OUTPUT_BLOCKERS_CSV = "TITAN_DISTRIBUTION_BLOCKER_REGISTER.csv"
OUTPUT_CONDITIONS_CSV = "TITAN_DISTRIBUTION_CONDITION_REGISTER.csv"
OUTPUT_RELEASE_INDEX_CSV = "TITAN_DISTRIBUTION_RELEASE_INDEX.csv"
OUTPUT_MANIFEST_JSON = "TITAN_DISTRIBUTION_READINESS_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "distribution_readiness_gatekeeper_audit.jsonl"
ERROR_LOG = Path("06_logs") / "distribution_readiness_gatekeeper_errors.jsonl"

DECISION_GO = "GO_FOR_DISTRIBUTION"
DECISION_GO_WITH_CONDITIONS = "GO_WITH_CONDITIONS"
DECISION_HOLD = "HOLD_PENDING_REVIEW"
DECISION_BLOCKED = "BLOCKED_DO_NOT_DISTRIBUTE"
DECISION_INCOMPLETE = "INCOMPLETE_NO_DISTRIBUTION_DECISION"

BLOCKER_CRITICAL = "CRITICAL_BLOCKER"
BLOCKER_HIGH = "HIGH_BLOCKER"
BLOCKER_MEDIUM = "MEDIUM_REVIEW_ITEM"

CONDITION_PRECEDENT = "CONDITION_PRECEDENT"
CONDITION_SUBSEQUENT = "CONDITION_SUBSEQUENT"
CONDITION_MONITOR = "MONITORING_CONDITION"

SOURCE_JSON_FILES = {
    "freeze_manifest": Path("05_reports") / "investor_data_room_freeze" / "TITAN_INVESTOR_DATA_ROOM_FREEZE_MANIFEST.json",
    "freeze_report": Path("05_reports") / "investor_data_room_freeze" / "TITAN_INVESTOR_DATA_ROOM_FREEZE_REPORT.json",
    "board_memo": Path("05_reports") / "board_decision_memo" / "TITAN_BOARD_DECISION_MEMO.json",
    "lender_dd_pack": Path("05_reports") / "lender_due_diligence_pack" / "TITAN_LENDER_DD_PACK.json",
    "executive_pack": Path("05_reports") / "executive_pack" / "TITAN_RAG_EXECUTIVE_PACK.json",
    "legal_compliance": Path("05_reports") / "legal_compliance_gap_analysis" / "TITAN_LEGAL_COMPLIANCE_MEMO.json",
    "esg_permitting": Path("05_reports") / "esg_permitting_risk_analysis" / "TITAN_ESG_PERMITTING_MEMO.json",
    "capex_bankability": Path("05_reports") / "capex_loan_bankability_analysis" / "TITAN_CAPEX_LOAN_BANKABILITY_MEMO.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
}

REQUIRED_FOR_TARGET = {
    "EBRD": [
        "freeze_manifest", "freeze_report", "lender_dd_pack", "executive_pack",
        "legal_compliance", "esg_permitting", "capex_bankability",
        "latest_audit_record", "citation_verification", "risk_signals",
    ],
    "EIB": [
        "freeze_manifest", "freeze_report", "lender_dd_pack", "executive_pack",
        "legal_compliance", "esg_permitting", "capex_bankability",
        "latest_audit_record", "citation_verification", "risk_signals",
    ],
    "IFC": [
        "freeze_manifest", "freeze_report", "lender_dd_pack", "executive_pack",
        "legal_compliance", "esg_permitting", "capex_bankability",
        "latest_audit_record", "citation_verification", "risk_signals",
    ],
    "BOARD": [
        "freeze_manifest", "freeze_report", "board_memo", "executive_pack",
        "latest_audit_record", "citation_verification", "risk_signals",
        "document_priority",
    ],
    "INVESTOR": [
        "freeze_manifest", "freeze_report", "executive_pack", "board_memo",
        "capex_bankability", "latest_audit_record", "citation_verification",
    ],
    "INTERNAL": [
        "freeze_manifest", "freeze_report", "executive_pack", "latest_audit_record",
    ],
}


@dataclass(frozen=True)
class GatePaths:
    base_dir: Path
    output_dir: Path
    decision_md: Path
    decision_json: Path
    blockers_csv: Path
    conditions_csv: Path
    release_index_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def nested_get(payload: dict[str, Any] | None, path: str, default: Any = None) -> Any:
    if not isinstance(payload, dict):
        return default
    cur: Any = payload
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
    return default if cur is None else cur


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> GatePaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return GatePaths(
        base_dir=base_dir,
        output_dir=output_dir,
        decision_md=output_dir / OUTPUT_DECISION_MD,
        decision_json=output_dir / OUTPUT_DECISION_JSON,
        blockers_csv=output_dir / OUTPUT_BLOCKERS_CSV,
        conditions_csv=output_dir / OUTPUT_CONDITIONS_CSV,
        release_index_csv=output_dir / OUTPUT_RELEASE_INDEX_CSV,
        manifest_json=output_dir / OUTPUT_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_reports(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in SOURCE_JSON_FILES.items()
    }


def build_source_manifest(base_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for name, rel_path in SOURCE_JSON_FILES.items():
        path = base_dir / rel_path
        rows.append({
            "Name": name,
            "Path": str(path),
            "Exists": path.exists() and path.is_file(),
            "Size_Bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            "Modified_UTC": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if path.exists() and path.is_file() else None,
            "SHA256": sha256_file(path),
        })
    return rows


def add_blocker(blockers: list[dict[str, Any]], severity: str, area: str, issue: str, source: str, action: str) -> None:
    raw = f"{severity}|{area}|{issue}|{source}|{action}"
    blockers.append({
        "Blocker_ID": "DIST-BLOCK-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12],
        "Severity": severity,
        "Area": area,
        "Issue": issue,
        "Source": source,
        "Recommended_Action": action,
        "Owner": "Danijela / TITAN Operator",
        "Status": "OPEN",
    })


def add_condition(conditions: list[dict[str, Any]], condition_type: str, area: str, condition: str, source: str, closure_rule: str) -> None:
    raw = f"{condition_type}|{area}|{condition}|{source}"
    conditions.append({
        "Condition_ID": "DIST-COND-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12],
        "Condition_Type": condition_type,
        "Area": area,
        "Condition": condition,
        "Source": source,
        "Closure_Rule": closure_rule,
        "Owner": "Danijela / TITAN Operator",
        "Status": "OPEN",
    })


def evaluate_readiness(reports: dict[str, dict[str, Any] | None], target: str, strict: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    conditions: list[dict[str, Any]] = []

    target = target.upper()
    required = REQUIRED_FOR_TARGET.get(target, REQUIRED_FOR_TARGET["INVESTOR"])
    for name in required:
        if reports.get(name) is None:
            add_blocker(
                blockers,
                BLOCKER_CRITICAL,
                "Missing Required Report",
                f"Required report is missing for target {target}: {name}",
                name,
                "Generate the missing upstream report before distribution.",
            )

    freeze_status = nested_get(reports.get("freeze_manifest"), "freeze_status")
    freeze_summary = nested_get(reports.get("freeze_manifest"), "summary", {})
    freeze_report_status = nested_get(reports.get("freeze_report"), "freeze_status")

    if freeze_status in {None, "DATA_ROOM_FREEZE_INCOMPLETE"} or freeze_report_status in {None, "DATA_ROOM_FREEZE_INCOMPLETE"}:
        add_blocker(blockers, BLOCKER_CRITICAL, "Freeze", f"Freeze is incomplete: manifest={freeze_status}, report={freeze_report_status}", "freeze", "Rebuild Step 27 freeze after mandatory outputs exist.")
    elif freeze_status == "DATA_ROOM_FREEZE_BLOCKED" or freeze_report_status == "DATA_ROOM_FREEZE_BLOCKED":
        add_blocker(blockers, BLOCKER_CRITICAL, "Freeze", f"Freeze is blocked: manifest={freeze_status}, report={freeze_report_status}", "freeze", "Resolve freeze blockers and hash issues before distribution.")
    elif freeze_status == "DATA_ROOM_FREEZE_REVIEW_REQUIRED" or freeze_report_status == "DATA_ROOM_FREEZE_REVIEW_REQUIRED":
        add_condition(conditions, CONDITION_PRECEDENT, "Freeze", f"Freeze review required: manifest={freeze_status}, report={freeze_report_status}", "freeze", "Authorized operator must review freeze warnings before release.")

    if isinstance(freeze_summary, dict):
        if safe_int(freeze_summary.get("hash_mismatch_items"), 0) > 0:
            add_blocker(blockers, BLOCKER_CRITICAL, "Hash Integrity", f"Hash mismatch count: {freeze_summary.get('hash_mismatch_items')}", "freeze_manifest", "Rebuild freeze and verify source/frozen hashes.")
        if safe_int(freeze_summary.get("missing_mandatory_items"), 0) > 0:
            add_blocker(blockers, BLOCKER_CRITICAL, "Mandatory Files", f"Missing mandatory freeze items: {freeze_summary.get('missing_mandatory_items')}", "freeze_manifest", "Generate missing mandatory files and rebuild freeze.")

    audit_status = nested_get(reports.get("latest_audit_record"), "audit_status")
    citation_status = nested_get(reports.get("citation_verification"), "verification_status")
    conflict_status = nested_get(reports.get("conflict_report"), "summary.institutional_status")
    risk_status = nested_get(reports.get("risk_signals"), "summary.institutional_status")
    critical_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0))
    high_risks = safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0))
    p0_documents = safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0))
    p1_documents = safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0))

    if audit_status != "AUDIT_PASS":
        if audit_status in {None, "AUDIT_FAIL", "AUDIT_NO_EVIDENCE"}:
            add_blocker(blockers, BLOCKER_CRITICAL, "Audit", f"Audit status is not distributable: {audit_status}", "latest_audit_record", "Rerun Step 08 and resolve audit failures.")
        else:
            add_condition(conditions, CONDITION_PRECEDENT, "Audit", f"Audit status requires review: {audit_status}", "latest_audit_record", "Authorized reviewer must accept audit warning before release.")

    if citation_status != "CITATION_VERIFICATION_PASS":
        if citation_status in {None, "CITATION_VERIFICATION_FAIL", "NO_EVIDENCE_NO_CITATION"}:
            add_blocker(blockers, BLOCKER_CRITICAL, "Citation", f"Citation status is not distributable: {citation_status}", "citation_verification", "Rerun Step 13 and repair citation/source traceability.")
        else:
            add_condition(conditions, CONDITION_PRECEDENT, "Citation", f"Citation status requires review: {citation_status}", "citation_verification", "Review citation warnings before release.")

    if conflict_status in {"HIGH_CONFLICT_RISK_MANUAL_REVIEW", "CONFLICTS_DETECTED_REVIEW_REQUIRED"}:
        add_condition(conditions, CONDITION_PRECEDENT, "Conflict", f"Conflict status requires review: {conflict_status}", "conflict_report", "Resolve or formally accept material conflicts before release.")
        if strict:
            add_blocker(blockers, BLOCKER_HIGH, "Conflict", f"Strict mode blocks conflict status: {conflict_status}", "conflict_report", "Resolve conflicts or run non-strict gate with formal exception.")

    if critical_risks > 0 or risk_status == "CRITICAL_RISK_REVIEW_REQUIRED":
        add_blocker(blockers, BLOCKER_CRITICAL, "Risk", f"Critical risks detected: {critical_risks}; status={risk_status}", "risk_signals", "Close or formally exception critical risks before distribution.")
    if high_risks > 0:
        add_condition(conditions, CONDITION_PRECEDENT, "Risk", f"High risks require review: {high_risks}", "risk_signals", "Assign owner/mitigation or formally accept high risks before distribution.")
        if strict:
            add_blocker(blockers, BLOCKER_HIGH, "Risk", f"Strict mode blocks high risks: {high_risks}", "risk_signals", "Close high risks or disable strict mode with sign-off.")

    if p0_documents > 0:
        add_blocker(blockers, BLOCKER_CRITICAL, "Document Priority", f"P0 documents remain open: {p0_documents}", "document_priority", "Review P0 documents and rebuild Step 18/27/28.")
    if p1_documents > 0:
        add_condition(conditions, CONDITION_PRECEDENT, "Document Priority", f"P1 documents require review: {p1_documents}", "document_priority", "Confirm P1 documents are acceptable for distribution.")
        if strict:
            add_blocker(blockers, BLOCKER_HIGH, "Document Priority", f"Strict mode blocks P1 documents: {p1_documents}", "document_priority", "Review P1 documents or disable strict mode with sign-off.")

    status_checks = [
        ("Executive Pack", nested_get(reports.get("executive_pack"), "pack_status"), "executive_pack"),
        ("Lender DD", nested_get(reports.get("lender_dd_pack"), "dd_status"), "lender_dd_pack"),
        ("Board Memo", nested_get(reports.get("board_memo"), "decision_status"), "board_memo"),
        ("Legal Compliance", nested_get(reports.get("legal_compliance"), "legal_status"), "legal_compliance"),
        ("ESG/Permitting", nested_get(reports.get("esg_permitting"), "esg_status"), "esg_permitting"),
        ("CAPEX/Loan Bankability", nested_get(reports.get("capex_bankability"), "bankability_status"), "capex_bankability"),
    ]

    blocked_tokens = ["BLOCKED", "INCOMPLETE", "DO_NOT_APPROVE"]
    warning_tokens = ["REVIEW_REQUIRED", "WITH_CONDITIONS", "DEFER", "HOLD"]

    for area, status, source in status_checks:
        if status is None:
            if source in required:
                add_blocker(blockers, BLOCKER_CRITICAL, area, f"Missing status for required source: {source}", source, "Regenerate upstream report.")
            continue
        if any(token in str(status) for token in blocked_tokens):
            add_blocker(blockers, BLOCKER_CRITICAL, area, f"{area} status blocks distribution: {status}", source, "Resolve upstream blocker before distribution.")
        elif any(token in str(status) for token in warning_tokens):
            add_condition(conditions, CONDITION_PRECEDENT, area, f"{area} status requires review: {status}", source, "Authorized reviewer must accept condition before release.")
            if strict and area in {"Legal Compliance", "ESG/Permitting", "CAPEX/Loan Bankability", "Lender DD"}:
                add_blocker(blockers, BLOCKER_HIGH, area, f"Strict mode blocks warning status: {status}", source, "Resolve warning status or use non-strict release with sign-off.")

    return blockers, conditions


def determine_decision(blockers: list[dict[str, Any]], conditions: list[dict[str, Any]], reports: dict[str, dict[str, Any] | None]) -> tuple[str, list[str]]:
    critical = [b for b in blockers if b["Severity"] == BLOCKER_CRITICAL]
    high = [b for b in blockers if b["Severity"] == BLOCKER_HIGH]

    if any("Missing Required Report" in b["Area"] for b in blockers):
        return DECISION_INCOMPLETE, [f"Missing required reports: {sum(1 for b in blockers if b['Area'] == 'Missing Required Report')}"]

    if critical:
        return DECISION_BLOCKED, [f"Critical blockers present: {len(critical)}"]

    if high:
        return DECISION_HOLD, [f"High blockers present: {len(high)}"]

    if conditions:
        return DECISION_GO_WITH_CONDITIONS, [f"Release allowed only after conditions are reviewed/accepted: {len(conditions)}"]

    return DECISION_GO, ["All required distribution gates are clean."]


def build_release_index(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    freeze_manifest = reports.get("freeze_manifest")
    rows = nested_get(freeze_manifest, "freeze_index", [])
    if not isinstance(rows, list):
        return []

    release_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        exists = bool(row.get("Exists"))
        copied = bool(row.get("Copied"))
        frozen_path = row.get("Frozen_Path")
        release_rows.append({
            "Release_Item_ID": row.get("Freeze_Item_ID"),
            "Name": row.get("Name"),
            "Category": row.get("Category"),
            "Mandatory": row.get("Mandatory"),
            "Exists": exists,
            "Copied": copied,
            "Source_Path": row.get("Source_Path"),
            "Frozen_Path": frozen_path,
            "Source_SHA256": row.get("Source_SHA256"),
            "Frozen_SHA256": row.get("Frozen_SHA256"),
            "Hash_OK": row.get("Source_SHA256") == row.get("Frozen_SHA256") if row.get("Frozen_SHA256") else None,
            "Release_Eligible": bool(exists and (copied or row.get("Copy_Status") == "MANIFEST_ONLY") and row.get("Source_SHA256")),
            "Copy_Status": row.get("Copy_Status"),
        })
    return release_rows


def build_manifest(paths: GatePaths, reports: dict[str, dict[str, Any] | None], source_manifest: list[dict[str, Any]], release_index: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "base_dir": str(paths.base_dir),
        "output_dir": str(paths.output_dir),
        "source_manifest": source_manifest,
        "release_index_count": len(release_index),
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "governance_rule": {
            "gatekeeper_does_not_send_files": True,
            "gatekeeper_does_not_modify_sources": True,
            "distribution_requires_authorized_signoff": True,
            "frozen_hashes_must_match": True,
            "audit_precedes_decision": True,
            "gatekeeping_precedes_external_release": True,
        },
    }
    manifest["distribution_readiness_manifest_sha256"] = sha256_json(manifest)
    return manifest


def build_decision_record(
    paths: GatePaths,
    target: str,
    strict: bool,
    reports: dict[str, dict[str, Any] | None],
    blockers: list[dict[str, Any]],
    conditions: list[dict[str, Any]],
    release_index: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    decision, reasons = determine_decision(blockers, conditions, reports)
    freeze_status = nested_get(reports.get("freeze_manifest"), "freeze_status")
    snapshot = {
        "target": target.upper(),
        "strict_mode": strict,
        "freeze_status": freeze_status,
        "audit_status": nested_get(reports.get("latest_audit_record"), "audit_status"),
        "citation_status": nested_get(reports.get("citation_verification"), "verification_status"),
        "conflict_status": nested_get(reports.get("conflict_report"), "summary.institutional_status"),
        "risk_status": nested_get(reports.get("risk_signals"), "summary.institutional_status"),
        "critical_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.critical_count", 0)),
        "high_risks": safe_int(nested_get(reports.get("risk_signals"), "summary.high_count", 0)),
        "p0_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p0_count", 0)),
        "p1_documents": safe_int(nested_get(reports.get("document_priority"), "summary.p1_count", 0)),
        "executive_pack_status": nested_get(reports.get("executive_pack"), "pack_status"),
        "lender_dd_status": nested_get(reports.get("lender_dd_pack"), "dd_status"),
        "board_decision_status": nested_get(reports.get("board_memo"), "decision_status"),
        "legal_status": nested_get(reports.get("legal_compliance"), "legal_status"),
        "esg_status": nested_get(reports.get("esg_permitting"), "esg_status"),
        "bankability_status": nested_get(reports.get("capex_bankability"), "bankability_status"),
    }

    record = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "DISTRIBUTION_READINESS_GATE_AUDIT_LOCKED",
        "target": target.upper(),
        "strict_mode": strict,
        "distribution_decision": decision,
        "decision_reasons": reasons,
        "recommended_action": recommended_action(decision),
        "status_snapshot": snapshot,
        "summary": {
            "blocker_count": len(blockers),
            "critical_blockers": sum(1 for b in blockers if b["Severity"] == BLOCKER_CRITICAL),
            "high_blockers": sum(1 for b in blockers if b["Severity"] == BLOCKER_HIGH),
            "condition_count": len(conditions),
            "release_index_count": len(release_index),
            "release_eligible_count": sum(1 for r in release_index if r.get("Release_Eligible")),
            "hash_ok_count": sum(1 for r in release_index if r.get("Hash_OK") is True),
            "hash_not_ok_count": sum(1 for r in release_index if r.get("Hash_OK") is False),
        },
        "blockers": blockers,
        "conditions": conditions,
        "release_index": release_index,
        "outputs": {
            "decision_md": str(paths.decision_md),
            "decision_json": str(paths.decision_json),
            "blockers_csv": str(paths.blockers_csv),
            "conditions_csv": str(paths.conditions_csv),
            "release_index_csv": str(paths.release_index_csv),
            "manifest_json": str(paths.manifest_json),
        },
        "manifest_sha256": manifest.get("distribution_readiness_manifest_sha256"),
        "governance_rule": {
            "does_not_send_files": True,
            "does_not_upload_files": True,
            "does_not_modify_original_sources": True,
            "distribution_requires_authorized_signoff": True,
            "decision_record_is_operational_gate_not_legal_approval": True,
            "audit_precedes_decision": True,
        },
    }
    record["distribution_readiness_decision_sha256"] = sha256_json(record)
    return record


def recommended_action(decision: str) -> str:
    if decision == DECISION_GO:
        return "Proceed to authorized sign-off and external distribution using the frozen package only."
    if decision == DECISION_GO_WITH_CONDITIONS:
        return "Review and accept/close all listed conditions before distribution."
    if decision == DECISION_HOLD:
        return "Hold distribution until high blockers are resolved or formally exceptioned."
    if decision == DECISION_BLOCKED:
        return "Do not distribute. Resolve critical blockers and regenerate Steps 27 and 28."
    if decision == DECISION_INCOMPLETE:
        return "Do not distribute. Generate missing required reports and rerun gatekeeper."
    return "Manual review required."


def write_blockers_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Blocker_ID", "Severity", "Area", "Issue", "Source", "Recommended_Action", "Owner", "Status"
    ])


def write_conditions_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Condition_ID", "Condition_Type", "Area", "Condition", "Source", "Closure_Rule", "Owner", "Status"
    ])


def write_release_index_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows, [
        "Release_Item_ID", "Name", "Category", "Mandatory", "Exists", "Copied",
        "Source_Path", "Frozen_Path", "Source_SHA256", "Frozen_SHA256",
        "Hash_OK", "Release_Eligible", "Copy_Status"
    ])


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def blockers_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No blockers."
    lines = ["| Severity | Area | Issue | Source | Action |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Severity'))} | {md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Issue'))} | {md_escape(row.get('Source'))} | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def conditions_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No conditions."
    lines = ["| Type | Area | Condition | Source | Closure Rule |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Condition_Type'))} | {md_escape(row.get('Area'))} | "
            f"{md_escape(row.get('Condition'))} | {md_escape(row.get('Source'))} | "
            f"{md_escape(row.get('Closure_Rule'))} |"
        )
    return "\n".join(lines)


def release_index_md(rows: list[dict[str, Any]], limit: int = 80) -> str:
    if not rows:
        return "No release index rows."
    lines = ["| Eligible | Hash OK | Category | Name | Frozen Path |", "|---:|---:|---|---|---|"]
    for row in rows[:limit]:
        lines.append(
            f"| {row.get('Release_Eligible')} | {row.get('Hash_OK')} | "
            f"{md_escape(row.get('Category'))} | {md_escape(row.get('Name'))} | "
            f"`{md_escape(row.get('Frozen_Path'))}` |"
        )
    return "\n".join(lines)


def decision_to_markdown(record: dict[str, Any]) -> str:
    snapshot = record.get("status_snapshot", {}) if isinstance(record.get("status_snapshot"), dict) else {}
    summary = record.get("summary", {}) if isinstance(record.get("summary"), dict) else {}

    snapshot_lines = ["| Field | Value |", "|---|---|"]
    for key, value in snapshot.items():
        snapshot_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    summary_lines = ["| Metric | Value |", "|---|---|"]
    for key, value in summary.items():
        summary_lines.append(f"| {md_escape(key)} | {md_escape(value)} |")

    return f"""# TITAN Distribution Readiness Decision

## 1. Decision Header

| Field | Value |
|---|---|
| Created At | {record.get("created_at")} |
| Target | {record.get("target")} |
| Strict Mode | {record.get("strict_mode")} |
| Distribution Decision | {record.get("distribution_decision")} |
| Decision SHA-256 | `{record.get("distribution_readiness_decision_sha256")}` |
| Manifest SHA-256 | `{record.get("manifest_sha256")}` |

**Decision reasons**

```json
{json.dumps(record.get("decision_reasons", []), indent=2, ensure_ascii=False)}
```

**Recommended action**

```text
{record.get("recommended_action")}
```

---

## 2. Status Snapshot

{chr(10).join(snapshot_lines)}

---

## 3. Summary

{chr(10).join(summary_lines)}

---

## 4. Blocker Register

{blockers_md(record.get("blockers", []))}

---

## 5. Condition Register

{conditions_md(record.get("conditions", []))}

---

## 6. Release Index Preview

{release_index_md(record.get("release_index", []))}

---

## 7. Governance Rule

```text
This gatekeeper does not send files.
This gatekeeper does not upload files.
This gatekeeper does not modify original source documents.
External distribution requires authorized sign-off.
Decision record is an operational gate, not legal approval.
Audit precedes decision.
Gatekeeping precedes external release.
```
"""


def print_summary(record: dict[str, Any], paths: GatePaths) -> None:
    summary = record.get("summary", {}) if isinstance(record.get("summary"), dict) else {}
    print("=" * 100)
    print("TITAN DISTRIBUTION READINESS GATEKEEPER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Target:                   {record.get('target')}")
    print(f"Decision:                 {record.get('distribution_decision')}")
    print(f"Blockers:                 {summary.get('blocker_count')}")
    print(f"Critical blockers:        {summary.get('critical_blockers')}")
    print(f"Conditions:               {summary.get('condition_count')}")
    print(f"Release eligible:         {summary.get('release_eligible_count')}")
    print("-" * 100)
    print(f"Decision Markdown:        {paths.decision_md}")
    print(f"Decision JSON:            {paths.decision_json}")
    print(f"Blockers CSV:             {paths.blockers_csv}")
    print(f"Conditions CSV:           {paths.conditions_csv}")
    print(f"Release Index CSV:        {paths.release_index_csv}")
    print(f"Manifest JSON:            {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 28 — distribution readiness gatekeeper.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory.")
    parser.add_argument("--target", default="EBRD", choices=["EBRD", "EIB", "IFC", "BOARD", "INVESTOR", "INTERNAL"], help="Distribution target profile.")
    parser.add_argument("--strict", action="store_true", help="Strict mode treats warning statuses as blockers.")
    parser.add_argument("--print", action="store_true", help="Print Markdown decision to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, args.output_dir)

    try:
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        paths.output_dir.mkdir(parents=True, exist_ok=True)

        reports = load_reports(base_dir)
        source_manifest = build_source_manifest(base_dir)
        blockers, conditions = evaluate_readiness(reports, target=args.target, strict=bool(args.strict))
        release_index = build_release_index(reports)
        manifest = build_manifest(paths, reports, source_manifest, release_index)
        decision_record = build_decision_record(
            paths=paths,
            target=args.target,
            strict=bool(args.strict),
            reports=reports,
            blockers=blockers,
            conditions=conditions,
            release_index=release_index,
            manifest=manifest,
        )
        markdown = decision_to_markdown(decision_record)

        write_json(paths.manifest_json, manifest)
        write_json(paths.decision_json, decision_record)
        write_text(paths.decision_md, markdown)
        write_blockers_csv(paths.blockers_csv, blockers)
        write_conditions_csv(paths.conditions_csv, conditions)
        write_release_index_csv(paths.release_index_csv, release_index)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "DISTRIBUTION_READINESS_DECISION_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "target": args.target,
            "strict": bool(args.strict),
            "distribution_decision": decision_record.get("distribution_decision"),
            "decision_sha256": decision_record.get("distribution_readiness_decision_sha256"),
            "manifest_sha256": manifest.get("distribution_readiness_manifest_sha256"),
            "summary": decision_record.get("summary"),
            "outputs": decision_record.get("outputs"),
        })

        print_summary(decision_record, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "DISTRIBUTION_READINESS_GATEKEEPER_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "target": args.target,
            "strict": bool(args.strict),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN DISTRIBUTION READINESS GATEKEEPER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
