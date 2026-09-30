#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
21_executive_report_pack_builder.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 21 — Executive Report Pack Builder
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Build an executive / lender / board review pack from the already-produced
TITAN RAG outputs.

This script does NOT scan source documents.
This script does NOT modify source documents.
This script does NOT generate unsupported conclusions.
It consolidates existing audit-grade reports into a structured executive pack.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Inputs
------
05_reports/TITAN_RAG_CONTROL_TOWER.xlsx
05_reports/rag_control_tower_export_summary.json
05_reports/night_run_summary.json
05_reports/morning_briefing.json
05_reports/latest_audit_record.json
05_reports/citation_verification_report.json
05_reports/conflict_report.json
05_reports/ssot_candidates_report.json
05_reports/financial_signals_report.json
05_reports/risk_signals_report.json
05_reports/document_priority_rank.json
05_reports/evidence_pack_report.json
05_reports/latest_rag_answer.json
05_reports/latest_evidence_pack.json

Outputs
-------
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.md
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK.json
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK_INDEX.csv
05_reports/executive_pack/TITAN_RAG_EXECUTIVE_PACK_MANIFEST.json
06_logs/executive_pack_builder_audit.jsonl
06_logs/executive_pack_builder_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\21_executive_report_pack_builder.py" --print

Custom pack folder
------------------
python ".\\08_scripts\\21_executive_report_pack_builder.py" --output-dir ".\\05_reports\\executive_pack"
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "21_executive_report_pack_builder.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")

DEFAULT_OUTPUT_DIR = Path("05_reports") / "executive_pack"

OUTPUT_PACK_MD = "TITAN_RAG_EXECUTIVE_PACK.md"
OUTPUT_PACK_JSON = "TITAN_RAG_EXECUTIVE_PACK.json"
OUTPUT_PACK_INDEX_CSV = "TITAN_RAG_EXECUTIVE_PACK_INDEX.csv"
OUTPUT_PACK_MANIFEST_JSON = "TITAN_RAG_EXECUTIVE_PACK_MANIFEST.json"

AUDIT_LOG = Path("06_logs") / "executive_pack_builder_audit.jsonl"
ERROR_LOG = Path("06_logs") / "executive_pack_builder_errors.jsonl"

PACK_STATUS_READY = "EXECUTIVE_PACK_READY"
PACK_STATUS_REVIEW_REQUIRED = "EXECUTIVE_PACK_REVIEW_REQUIRED"
PACK_STATUS_BLOCKED = "EXECUTIVE_PACK_BLOCKED"
PACK_STATUS_INCOMPLETE = "EXECUTIVE_PACK_INCOMPLETE"

SOURCE_FILES = {
    "control_tower_xlsx": Path("05_reports") / "TITAN_RAG_CONTROL_TOWER.xlsx",
    "control_tower_summary": Path("05_reports") / "rag_control_tower_export_summary.json",
    "night_run_summary": Path("05_reports") / "night_run_summary.json",
    "morning_briefing": Path("05_reports") / "morning_briefing.json",
    "latest_audit_record": Path("05_reports") / "latest_audit_record.json",
    "citation_verification": Path("05_reports") / "citation_verification_report.json",
    "conflict_report": Path("05_reports") / "conflict_report.json",
    "ssot_candidates": Path("05_reports") / "ssot_candidates_report.json",
    "financial_signals": Path("05_reports") / "financial_signals_report.json",
    "risk_signals": Path("05_reports") / "risk_signals_report.json",
    "document_priority": Path("05_reports") / "document_priority_rank.json",
    "evidence_report": Path("05_reports") / "evidence_pack_report.json",
    "latest_answer": Path("05_reports") / "latest_rag_answer.json",
    "latest_evidence_pack": Path("05_reports") / "latest_evidence_pack.json",
}

OPTIONAL_COPY_FILES = {
    "control_tower_xlsx": Path("05_reports") / "TITAN_RAG_CONTROL_TOWER.xlsx",
    "document_priority_csv": Path("05_reports") / "document_priority_rank.csv",
    "risk_signals_csv": Path("05_reports") / "risk_signals.csv",
    "financial_signals_csv": Path("05_reports") / "financial_signals.csv",
    "ssot_candidates_csv": Path("05_reports") / "ssot_candidates.csv",
    "conflict_report_csv": Path("05_reports") / "conflict_report.csv",
    "citation_report_csv": Path("05_reports") / "citation_verification_report.csv",
    "evidence_pack_report_csv": Path("05_reports") / "evidence_pack_report.csv",
    "morning_tasks_csv": Path("05_reports") / "morning_briefing_tasks.csv",
    "night_steps_csv": Path("05_reports") / "night_run_steps.csv",
}


@dataclass(frozen=True)
class PackPaths:
    base_dir: Path
    output_dir: Path
    pack_md: Path
    pack_json: Path
    index_csv: Path
    manifest_json: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def short_text(value: Any, max_chars: int = 1400) -> str:
    text = str(value or "")
    text = text.replace("\x00", "")
    if len(text) > max_chars:
        return text[:max_chars] + " ...[TRUNCATED]"
    return text


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


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
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def resolve_paths(base_dir: Path, output_dir_arg: str | None) -> PackPaths:
    output_dir = Path(output_dir_arg) if output_dir_arg else base_dir / DEFAULT_OUTPUT_DIR
    return PackPaths(
        base_dir=base_dir,
        output_dir=output_dir,
        pack_md=output_dir / OUTPUT_PACK_MD,
        pack_json=output_dir / OUTPUT_PACK_JSON,
        index_csv=output_dir / OUTPUT_PACK_INDEX_CSV,
        manifest_json=output_dir / OUTPUT_PACK_MANIFEST_JSON,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def load_sources(base_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        name: load_json_if_exists(base_dir / rel_path)
        for name, rel_path in SOURCE_FILES.items()
        if rel_path.suffix.lower() == ".json"
    }


def file_manifest_rows(base_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for name, rel_path in {**SOURCE_FILES, **OPTIONAL_COPY_FILES}.items():
        source_path = base_dir / rel_path
        rows.append({
            "Name": name,
            "Source_Path": str(source_path),
            "Exists": source_path.exists(),
            "File_Size_Bytes": source_path.stat().st_size if source_path.exists() and source_path.is_file() else None,
            "Modified_Time_UTC": datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if source_path.exists() and source_path.is_file() else None,
            "SHA256": sha256_file(source_path),
            "Pack_Copy_Path": str(output_dir / "source_exports" / source_path.name) if source_path.exists() else None,
        })

    return rows


def copy_selected_files(base_dir: Path, output_dir: Path, copy_files: bool) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    target_dir = output_dir / "source_exports"
    target_dir.mkdir(parents=True, exist_ok=True)

    for name, rel_path in OPTIONAL_COPY_FILES.items():
        source = base_dir / rel_path
        if not source.exists() or not source.is_file():
            copied.append({
                "name": name,
                "source": str(source),
                "copied": False,
                "reason": "missing",
                "target": None,
                "sha256": None,
            })
            continue

        target = target_dir / source.name

        if copy_files:
            shutil.copy2(source, target)
            copied.append({
                "name": name,
                "source": str(source),
                "copied": True,
                "reason": "copied",
                "target": str(target),
                "sha256": sha256_file(target),
            })
        else:
            copied.append({
                "name": name,
                "source": str(source),
                "copied": False,
                "reason": "copy_disabled",
                "target": str(target),
                "sha256": sha256_file(source),
            })

    return copied


def write_index_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Name",
        "Source_Path",
        "Exists",
        "File_Size_Bytes",
        "Modified_Time_UTC",
        "SHA256",
        "Pack_Copy_Path",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summary_value(report: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if not isinstance(report, dict):
        return default
    if key in report:
        return report.get(key)
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return summary.get(key, default)


def determine_pack_status(reports: dict[str, dict[str, Any] | None]) -> tuple[str, list[str]]:
    reasons: list[str] = []

    required = [
        "latest_audit_record",
        "citation_verification",
        "conflict_report",
        "risk_signals",
        "financial_signals",
        "document_priority",
        "latest_evidence_pack",
    ]

    missing = [name for name in required if not reports.get(name)]
    if missing:
        reasons.append("Missing required reports: " + ", ".join(missing))
        return PACK_STATUS_INCOMPLETE, reasons

    audit_status = summary_value(reports.get("latest_audit_record"), "audit_status")
    citation_status = summary_value(reports.get("citation_verification"), "verification_status")
    conflict_status = summary_value(reports.get("conflict_report"), "institutional_status")
    risk_status = summary_value(reports.get("risk_signals"), "institutional_status")
    risk_critical = safe_int(summary_value(reports.get("risk_signals"), "critical_count"), 0)
    doc_p0 = safe_int(summary_value(reports.get("document_priority"), "p0_count"), 0)

    if audit_status in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE"}:
        reasons.append(f"Latest audit blocks institutional use: {audit_status}")

    if citation_status in {"CITATION_VERIFICATION_FAIL", "NO_EVIDENCE_NO_CITATION"}:
        reasons.append(f"Citation verification blocks use: {citation_status}")

    if conflict_status in {"HIGH_CONFLICT_RISK_MANUAL_REVIEW", "CONFLICTS_DETECTED_REVIEW_REQUIRED"}:
        reasons.append(f"Conflict report requires review: {conflict_status}")

    if risk_critical > 0 or risk_status == "CRITICAL_RISK_REVIEW_REQUIRED":
        reasons.append(f"Critical risks detected: {risk_critical}")

    if doc_p0 > 0:
        reasons.append(f"P0 documents require immediate review: {doc_p0}")

    if reasons:
        return PACK_STATUS_BLOCKED, reasons

    if audit_status != "AUDIT_PASS" or citation_status != "CITATION_VERIFICATION_PASS":
        reasons.append("Audit or citation status is not clean PASS.")
        return PACK_STATUS_REVIEW_REQUIRED, reasons

    reasons.append("Core audit/citation/risk/conflict gates are clean or non-blocking.")
    return PACK_STATUS_READY, reasons


def build_dashboard(reports: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    return [
        {
            "Metric": "Latest Audit Status",
            "Value": summary_value(reports.get("latest_audit_record"), "audit_status"),
            "Decision_Impact": "Must be AUDIT_PASS before institutional use.",
        },
        {
            "Metric": "Citation Verification",
            "Value": summary_value(reports.get("citation_verification"), "verification_status"),
            "Decision_Impact": "Must be CITATION_VERIFICATION_PASS for clean source traceability.",
        },
        {
            "Metric": "Conflict Status",
            "Value": summary_value(reports.get("conflict_report"), "institutional_status"),
            "Decision_Impact": "Conflicts require manual SSOT review.",
        },
        {
            "Metric": "Risk Status",
            "Value": summary_value(reports.get("risk_signals"), "institutional_status"),
            "Decision_Impact": "Critical/high risks drive executive review.",
        },
        {
            "Metric": "Critical Risks",
            "Value": summary_value(reports.get("risk_signals"), "critical_count", 0),
            "Decision_Impact": "Critical risk blocks institutional reliance.",
        },
        {
            "Metric": "High Risks",
            "Value": summary_value(reports.get("risk_signals"), "high_count", 0),
            "Decision_Impact": "High risk requires manual review.",
        },
        {
            "Metric": "Financial Signals",
            "Value": summary_value(reports.get("financial_signals"), "total_signals", 0),
            "Decision_Impact": "Universe of possible model/lender signals.",
        },
        {
            "Metric": "SSOT Candidates",
            "Value": summary_value(reports.get("ssot_candidates"), "total_candidates", 0),
            "Decision_Impact": "Candidates only; not locked truth.",
        },
        {
            "Metric": "P0 Documents",
            "Value": summary_value(reports.get("document_priority"), "p0_count", 0),
            "Decision_Impact": "Immediate document review queue.",
        },
        {
            "Metric": "P1 Documents",
            "Value": summary_value(reports.get("document_priority"), "p1_count", 0),
            "Decision_Impact": "High-priority review queue.",
        },
        {
            "Metric": "Evidence Count",
            "Value": summary_value(reports.get("latest_evidence_pack"), "evidence_count", 0),
            "Decision_Impact": "Current evidence base size for the query.",
        },
    ]


def top_items(report: dict[str, Any] | None, collection_key: str, count: int) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        return []
    rows = report.get(collection_key, [])
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)][:count]


def build_pack(reports: dict[str, dict[str, Any] | None], manifest_rows: list[dict[str, Any]], copied_files: list[dict[str, Any]], strict: bool) -> dict[str, Any]:
    status, reasons = determine_pack_status(reports)
    dashboard = build_dashboard(reports)

    latest_answer = reports.get("latest_answer") or {}
    answer_confidence = latest_answer.get("confidence") if isinstance(latest_answer.get("confidence"), dict) else {}

    pack = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "EXECUTIVE_REPORT_PACK_AUDIT_LOCKED",
        "strict_mode": strict,
        "pack_status": status,
        "pack_status_reasons": reasons,
        "query": summary_value(reports.get("latest_evidence_pack"), "query") or latest_answer.get("query"),
        "dashboard": dashboard,
        "executive_summary": {
            "direct_answer_snapshot": short_text(latest_answer.get("direct_answer"), 1800),
            "answer_institutional_status": latest_answer.get("institutional_status"),
            "answer_confidence_score": answer_confidence.get("confidence_score"),
            "answer_confidence_label": answer_confidence.get("confidence_label"),
            "risk_if_skipped": latest_answer.get("risk_if_skipped"),
            "next_action": latest_answer.get("next_action"),
        },
        "key_counts": {
            "evidence_count": summary_value(reports.get("latest_evidence_pack"), "evidence_count", 0),
            "source_file_count": summary_value(reports.get("latest_evidence_pack"), "source_file_count", 0),
            "risk_total": summary_value(reports.get("risk_signals"), "total_risks", 0),
            "risk_critical": summary_value(reports.get("risk_signals"), "critical_count", 0),
            "risk_high": summary_value(reports.get("risk_signals"), "high_count", 0),
            "financial_signals": summary_value(reports.get("financial_signals"), "total_signals", 0),
            "ssot_candidates": summary_value(reports.get("ssot_candidates"), "total_candidates", 0),
            "conflicts": summary_value(reports.get("conflict_report"), "total_conflicts", 0),
            "ranked_documents": summary_value(reports.get("document_priority"), "ranked_documents", 0),
            "p0_documents": summary_value(reports.get("document_priority"), "p0_count", 0),
            "p1_documents": summary_value(reports.get("document_priority"), "p1_count", 0),
        },
        "top_risks": top_items(reports.get("risk_signals"), "signals", 20),
        "top_financial_signals": top_items(reports.get("financial_signals"), "signals", 20),
        "top_ssot_candidates": top_items(reports.get("ssot_candidates"), "candidates", 20),
        "top_conflicts": top_items(reports.get("conflict_report"), "conflicts", 20),
        "top_documents": top_items(reports.get("document_priority"), "documents", 30),
        "manifest": manifest_rows,
        "copied_files": copied_files,
        "source_report_hashes": {
            name: sha256_json(payload) if isinstance(payload, dict) else None
            for name, payload in reports.items()
        },
        "governance_rule": {
            "executive_pack_consolidates_existing_reports_only": True,
            "no_new_unsupported_claims": True,
            "source_documents_not_modified": True,
            "pack_status_blocked_requires_manual_review": True,
            "json_reports_and_original_sources_remain_authoritative": True,
            "audit_precedes_decision": True,
        },
    }

    pack["executive_pack_sha256"] = sha256_json(pack)
    return pack


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def dashboard_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Metric | Value | Decision Impact |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Metric'))} | {md_escape(row.get('Value'))} | {md_escape(row.get('Decision_Impact'))} |"
        )
    return "\n".join(lines)


def risks_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No risk rows available."

    lines = [
        "| Severity | Status | Type | Confidence | Source | Chunk | Action |",
        "|---|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Risk_Status'))} | "
            f"{md_escape(row.get('Risk_Type'))} | "
            f"{row.get('Confidence_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` | "
            f"`{md_escape(row.get('Chunk_ID'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def documents_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No document priority rows available."

    lines = [
        "| Rank | Class | Score | Status | File | Action |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('Priority_Rank')} | "
            f"{md_escape(row.get('Priority_Class'))} | "
            f"{row.get('Priority_Score')} | "
            f"{md_escape(row.get('Review_Status'))} | "
            f"`{md_escape(row.get('Document_Path'))}` | "
            f"{md_escape(row.get('Recommended_Action'))} |"
        )
    return "\n".join(lines)


def financial_md(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No financial signal rows available."

    lines = [
        "| Severity | Status | Category | Type | Value | Confidence | Source |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Severity'))} | "
            f"{md_escape(row.get('Financial_Status'))} | "
            f"{md_escape(row.get('Signal_Category'))} | "
            f"{md_escape(row.get('Value_Type'))} | "
            f"{md_escape(row.get('Canonical_Value'))} | "
            f"{row.get('Confidence_Score')} | "
            f"`{md_escape(row.get('Source_Path'))}` |"
        )
    return "\n".join(lines)


def manifest_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Name | Exists | Size | SHA256 | Source |",
        "|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_escape(row.get('Name'))} | "
            f"{row.get('Exists')} | "
            f"{row.get('File_Size_Bytes')} | "
            f"`{md_escape(row.get('SHA256'))}` | "
            f"`{md_escape(row.get('Source_Path'))}` |"
        )
    return "\n".join(lines)


def pack_to_markdown(pack: dict[str, Any]) -> str:
    executive = pack.get("executive_summary", {}) if isinstance(pack.get("executive_summary"), dict) else {}
    counts = pack.get("key_counts", {}) if isinstance(pack.get("key_counts"), dict) else {}

    return f"""# TITAN RAG Executive Report Pack

## 1. Pack Identity

| Field | Value |
|---|---|
| Created At | {pack.get("created_at")} |
| Pack Status | {pack.get("pack_status")} |
| Query | {md_escape(pack.get("query"))} |
| Strict Mode | {pack.get("strict_mode")} |
| Executive Pack SHA-256 | `{pack.get("executive_pack_sha256")}` |

**Pack status reasons**

```json
{json.dumps(pack.get("pack_status_reasons", []), indent=2, ensure_ascii=False)}
```

---

## 2. Executive Snapshot

| Field | Value |
|---|---|
| Answer Institutional Status | {executive.get("answer_institutional_status")} |
| Answer Confidence Score | {executive.get("answer_confidence_score")} |
| Answer Confidence Label | {executive.get("answer_confidence_label")} |
| Evidence Count | {counts.get("evidence_count")} |
| Source File Count | {counts.get("source_file_count")} |
| Critical Risks | {counts.get("risk_critical")} |
| High Risks | {counts.get("risk_high")} |
| Conflicts | {counts.get("conflicts")} |
| Financial Signals | {counts.get("financial_signals")} |
| SSOT Candidates | {counts.get("ssot_candidates")} |
| P0 Documents | {counts.get("p0_documents")} |
| P1 Documents | {counts.get("p1_documents")} |

**Direct answer snapshot**

```text
{executive.get("direct_answer_snapshot") or ""}
```

**Risk if skipped**

```text
{executive.get("risk_if_skipped") or ""}
```

**Next action**

```text
{executive.get("next_action") or ""}
```

---

## 3. Dashboard

{dashboard_md(pack.get("dashboard", []))}

---

## 4. Top Risks

{risks_md(pack.get("top_risks", []))}

---

## 5. Top Financial Signals

{financial_md(pack.get("top_financial_signals", []))}

---

## 6. Top Documents for Review

{documents_md(pack.get("top_documents", []))}

---

## 7. Top Conflicts

```json
{json.dumps(pack.get("top_conflicts", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 8. Top SSOT Candidates

```json
{json.dumps(pack.get("top_ssot_candidates", []), indent=2, ensure_ascii=False)[:12000]}
```

---

## 9. Source Manifest

{manifest_md(pack.get("manifest", []))}

---

## 10. Governance Rule

```text
Executive pack consolidates existing reports only.
It does not create new unsupported claims.
It does not modify source documents.
If pack status is BLOCKED or REVIEW_REQUIRED, manual review is mandatory.
JSON reports and original source files remain authoritative.
Audit precedes decision.
```
"""


def build_manifest_json(pack: dict[str, Any], paths: PackPaths) -> dict[str, Any]:
    manifest = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "output_dir": str(paths.output_dir),
        "pack_markdown": str(paths.pack_md),
        "pack_json": str(paths.pack_json),
        "pack_index_csv": str(paths.index_csv),
        "pack_status": pack.get("pack_status"),
        "executive_pack_sha256": pack.get("executive_pack_sha256"),
        "files": pack.get("manifest", []),
        "copied_files": pack.get("copied_files", []),
        "governance_rule": pack.get("governance_rule", {}),
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    return manifest


def print_summary(pack: dict[str, Any], paths: PackPaths) -> None:
    counts = pack.get("key_counts", {}) if isinstance(pack.get("key_counts"), dict) else {}
    print("=" * 100)
    print("TITAN RAG EXECUTIVE REPORT PACK BUILDER v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Pack status:              {pack.get('pack_status')}")
    print(f"Query:                    {pack.get('query')}")
    print(f"Critical risks:            {counts.get('risk_critical')}")
    print(f"High risks:                {counts.get('risk_high')}")
    print(f"Conflicts:                 {counts.get('conflicts')}")
    print(f"P0 documents:              {counts.get('p0_documents')}")
    print("-" * 100)
    print(f"Pack Markdown:             {paths.pack_md}")
    print(f"Pack JSON:                 {paths.pack_json}")
    print(f"Pack Index CSV:            {paths.index_csv}")
    print(f"Pack Manifest JSON:        {paths.manifest_json}")
    print("=" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 21 — executive report pack builder.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--output-dir", default=None, help="Optional executive pack output directory.")
    parser.add_argument("--no-copy-files", action="store_true", help="Do not copy CSV/XLSX exports into executive_pack/source_exports.")
    parser.add_argument("--strict", action="store_true", help="Strict metadata flag for pack governance.")
    parser.add_argument("--print", action="store_true", help="Print Markdown executive pack to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir, args.output_dir)

    try:
        if not base_dir.exists():
            raise FileNotFoundError(f"Base directory does not exist: {base_dir}")

        paths.output_dir.mkdir(parents=True, exist_ok=True)

        reports = load_sources(base_dir)
        manifest_rows = file_manifest_rows(base_dir, paths.output_dir)
        copied_files = copy_selected_files(
            base_dir=base_dir,
            output_dir=paths.output_dir,
            copy_files=not bool(args.no_copy_files),
        )

        pack = build_pack(
            reports=reports,
            manifest_rows=manifest_rows,
            copied_files=copied_files,
            strict=bool(args.strict),
        )
        markdown = pack_to_markdown(pack)
        manifest = build_manifest_json(pack, paths)

        write_json(paths.pack_json, pack)
        write_text(paths.pack_md, markdown)
        write_index_csv(paths.index_csv, manifest_rows)
        write_json(paths.manifest_json, manifest)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "EXECUTIVE_REPORT_PACK_CREATED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "pack_status": pack.get("pack_status"),
            "pack_sha256": pack.get("executive_pack_sha256"),
            "manifest_sha256": manifest.get("manifest_sha256"),
            "outputs": {
                "pack_md": str(paths.pack_md),
                "pack_json": str(paths.pack_json),
                "index_csv": str(paths.index_csv),
                "manifest_json": str(paths.manifest_json),
            },
        })

        print_summary(pack, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "EXECUTIVE_REPORT_PACK_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "output_dir": str(paths.output_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG EXECUTIVE REPORT PACK BUILDER FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
