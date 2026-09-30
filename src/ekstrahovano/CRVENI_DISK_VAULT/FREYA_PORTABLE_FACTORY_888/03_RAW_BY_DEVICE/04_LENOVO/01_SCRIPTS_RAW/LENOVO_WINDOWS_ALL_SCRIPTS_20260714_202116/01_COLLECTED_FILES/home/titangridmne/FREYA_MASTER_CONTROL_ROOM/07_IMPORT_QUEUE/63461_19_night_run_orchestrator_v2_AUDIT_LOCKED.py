#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
19_night_run_orchestrator.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 19 — Night Run Orchestrator
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Run the TITAN RAG pipeline in a controlled, auditable night cycle.

This script does NOT modify source documents.
This script does NOT invent answers.
This script does NOT bypass safety.
It executes approved pipeline scripts in sequence, captures their results,
classifies failures, and writes a night-run control record.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Default pipeline
----------------
01 Discover
02 Safety Filter
09 Incremental Refresh
03 Extract Text          # incremental mode by default
04 Chunk Text
05 Build Embeddings
06 Search RAG            # default query
07 Generate Answer
08 Final Audit
12 Evidence Pack Reporter
13 Citation Verifier
14 Conflict Detector
15 SSOT Candidate Extractor
16 Financial Signal Extractor
17 Risk Signal Extractor
18 Document Priority Ranker
10 Morning Briefing

Outputs
-------
05_reports/night_run_summary.json
05_reports/night_run_summary.md
05_reports/night_run_steps.csv
06_logs/night_run_orchestrator_audit.jsonl
06_logs/night_run_orchestrator_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\19_night_run_orchestrator.py"

Sa prikazom izvještaja:
-----------------------
python ".\\08_scripts\\19_night_run_orchestrator.py" --print

Full rebuild:
-------------
python ".\\08_scripts\\19_night_run_orchestrator.py" --full-rebuild

Skip discovery/safety:
----------------------
python ".\\08_scripts\\19_night_run_orchestrator.py" --skip-discovery

Custom query:
-------------
python ".\\08_scripts\\19_night_run_orchestrator.py" --query "EIB EBRD CAPEX DSCR WACC loan risk SSOT audit"

Continue even after non-critical failures:
-----------------------------------------
Default behavior already continues after non-critical steps and stops on critical steps.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "19_night_run_orchestrator.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
SCRIPTS_DIR = Path("08_scripts")

OUTPUT_SUMMARY_JSON = Path("05_reports") / "night_run_summary.json"
OUTPUT_SUMMARY_MD = Path("05_reports") / "night_run_summary.md"
OUTPUT_STEPS_CSV = Path("05_reports") / "night_run_steps.csv"

AUDIT_LOG = Path("06_logs") / "night_run_orchestrator_audit.jsonl"
ERROR_LOG = Path("06_logs") / "night_run_orchestrator_errors.jsonl"

DEFAULT_QUERY = (
    "EIB EBRD CAPEX OPEX DSCR WACC IRR NPV loan equity grant "
    "financial model business plan risk conflict missing unsigned permit "
    "SSOT audit lender bankability"
)

DEFAULT_TIMEOUT_SECONDS = None

STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"
STATUS_SKIPPED = "SKIPPED"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_MISSING_SCRIPT = "MISSING_SCRIPT"
STATUS_ERROR = "ERROR"

FINAL_SUCCESS = "SUCCESS"
FINAL_SUCCESS_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"
FINAL_FAILED_CRITICAL_STEP = "FAILED_CRITICAL_STEP"
FINAL_FAILED_CONFIGURATION = "FAILED_CONFIGURATION"

CRITICAL_STEPS = {
    "01_DISCOVER_FILES",
    "02_SAFETY_FILTER",
    "03_EXTRACT_TEXT",
    "04_CHUNK_TEXT",
    "05_BUILD_EMBEDDINGS",
    "06_SEARCH_RAG",
    "07_GENERATE_ANSWER",
    "08_WRITE_AUDIT_LOG",
}

STEP_DEFINITIONS = [
    {
        "step_id": "01_DISCOVER_FILES",
        "script": "01_discover_files.py",
        "critical": True,
        "category": "INDEX",
        "description": "Discover files and create file_index.jsonl.",
    },
    {
        "step_id": "02_SAFETY_FILTER",
        "script": "02_safety_filter.py",
        "critical": True,
        "category": "SAFETY",
        "description": "Filter sensitive/unsafe files before extraction.",
    },
    {
        "step_id": "09_INCREMENTAL_REFRESH",
        "script": "09_incremental_refresh.py",
        "critical": False,
        "category": "INCREMENTAL",
        "description": "Create incremental worklists and snapshot.",
    },
    {
        "step_id": "03_EXTRACT_TEXT",
        "script": "03_extract_text.py",
        "critical": True,
        "category": "EXTRACTION",
        "description": "Extract text from safe files.",
    },
    {
        "step_id": "04_CHUNK_TEXT",
        "script": "04_chunk_text.py",
        "critical": True,
        "category": "CHUNKING",
        "description": "Create evidence chunks.",
    },
    {
        "step_id": "05_BUILD_EMBEDDINGS",
        "script": "05_build_embeddings.py",
        "critical": True,
        "category": "VECTOR",
        "description": "Build/update local vector index.",
    },
    {
        "step_id": "06_SEARCH_RAG",
        "script": "06_search_rag.py",
        "critical": True,
        "category": "RETRIEVAL",
        "description": "Retrieve evidence pack for the night query.",
    },
    {
        "step_id": "07_GENERATE_ANSWER",
        "script": "07_generate_answer.py",
        "critical": True,
        "category": "ANSWER",
        "description": "Generate evidence-bound answer.",
    },
    {
        "step_id": "08_WRITE_AUDIT_LOG",
        "script": "08_write_audit_log.py",
        "critical": True,
        "category": "AUDIT",
        "description": "Create final audit record.",
    },
    {
        "step_id": "12_EVIDENCE_PACK_REPORTER",
        "script": "12_evidence_pack_reporter.py",
        "critical": False,
        "category": "REPORT",
        "description": "Create evidence pack review report.",
    },
    {
        "step_id": "13_SOURCE_CITATION_VERIFIER",
        "script": "13_source_citation_verifier.py",
        "critical": False,
        "category": "CITATION",
        "description": "Verify source citation integrity.",
    },
    {
        "step_id": "14_CONFLICT_DETECTOR",
        "script": "14_conflict_detector.py",
        "critical": False,
        "category": "CONFLICT",
        "description": "Detect value/status/date conflicts.",
    },
    {
        "step_id": "15_SSOT_CANDIDATE_EXTRACTOR",
        "script": "15_ssot_candidate_extractor.py",
        "critical": False,
        "category": "SSOT",
        "description": "Extract SSOT candidates.",
    },
    {
        "step_id": "16_FINANCIAL_SIGNAL_EXTRACTOR",
        "script": "16_financial_signal_extractor.py",
        "critical": False,
        "category": "FINANCIAL",
        "description": "Extract financial signals.",
    },
    {
        "step_id": "17_RISK_SIGNAL_EXTRACTOR",
        "script": "17_risk_signal_extractor.py",
        "critical": False,
        "category": "RISK",
        "description": "Extract risk signals.",
    },
    {
        "step_id": "18_DOCUMENT_PRIORITY_RANKER",
        "script": "18_document_priority_ranker.py",
        "critical": False,
        "category": "PRIORITY",
        "description": "Rank documents for review.",
    },
    {
        "step_id": "10_MORNING_BRIEFING",
        "script": "10_morning_briefing.py",
        "critical": False,
        "category": "BRIEFING",
        "description": "Create morning briefing.",
    },
]


@dataclass(frozen=True)
class OrchestratorPaths:
    base_dir: Path
    scripts_dir: Path
    summary_json: Path
    summary_md: Path
    steps_csv: Path
    audit_log: Path
    error_log: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


def seconds_between(start: datetime, end: datetime) -> float:
    return round((end - start).total_seconds(), 3)


def normalize_inline(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def tail_text(text: Any, max_chars: int = 8000) -> str:
    value = str(text or "")
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def resolve_paths(base_dir: Path) -> OrchestratorPaths:
    return OrchestratorPaths(
        base_dir=base_dir,
        scripts_dir=base_dir / SCRIPTS_DIR,
        summary_json=base_dir / OUTPUT_SUMMARY_JSON,
        summary_md=base_dir / OUTPUT_SUMMARY_MD,
        steps_csv=base_dir / OUTPUT_STEPS_CSV,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def build_step_command(
    paths: OrchestratorPaths,
    step: dict[str, Any],
    args: argparse.Namespace,
) -> list[str]:
    script_path = paths.scripts_dir / str(step["script"])
    cmd = [sys.executable, str(script_path)]

    step_id = str(step["step_id"])

    if step_id == "09_INCREMENTAL_REFRESH":
        if args.force_all:
            cmd.append("--force-all")
        if args.no_snapshot_update:
            cmd.append("--no-snapshot-update")

    elif step_id == "03_EXTRACT_TEXT":
        if args.full_rebuild:
            # Default full run reads safe_file_index.jsonl.
            pass
        else:
            incremental_safe = paths.base_dir / "01_index" / "incremental_safe_file_index.jsonl"
            if incremental_safe.exists():
                cmd.extend(["--input", str(incremental_safe)])
        if args.extract_overwrite:
            cmd.append("--overwrite")

    elif step_id == "05_BUILD_EMBEDDINGS":
        if args.full_rebuild or args.reset_vectors:
            cmd.append("--reset")
        if args.embedding_batch_size:
            cmd.extend(["--batch-size", str(args.embedding_batch_size)])

    elif step_id == "06_SEARCH_RAG":
        cmd.extend(["--query", args.query])
        cmd.extend(["--top-k-raw", str(args.top_k_raw)])
        cmd.extend(["--top-k-final", str(args.top_k_final)])
        if args.min_search_score is not None:
            cmd.extend(["--min-score", str(args.min_search_score)])

    elif step_id == "07_GENERATE_ANSWER":
        if args.min_answer_score is not None:
            cmd.extend(["--min-score", str(args.min_answer_score)])

    elif step_id == "08_WRITE_AUDIT_LOG":
        if args.strict_audit:
            cmd.append("--strict")

    elif step_id in {
        "13_SOURCE_CITATION_VERIFIER",
        "14_CONFLICT_DETECTOR",
        "15_SSOT_CANDIDATE_EXTRACTOR",
        "16_FINANCIAL_SIGNAL_EXTRACTOR",
        "17_RISK_SIGNAL_EXTRACTOR",
        "18_DOCUMENT_PRIORITY_RANKER",
    }:
        if args.strict_downstream:
            cmd.append("--strict")

    return cmd


def should_skip_step(step: dict[str, Any], args: argparse.Namespace) -> tuple[bool, str | None]:
    step_id = str(step["step_id"])

    if args.skip_discovery and step_id in {"01_DISCOVER_FILES", "02_SAFETY_FILTER", "09_INCREMENTAL_REFRESH"}:
        return True, "Skipped by --skip-discovery"

    if args.search_only and step_id in {
        "01_DISCOVER_FILES", "02_SAFETY_FILTER", "09_INCREMENTAL_REFRESH",
        "03_EXTRACT_TEXT", "04_CHUNK_TEXT", "05_BUILD_EMBEDDINGS",
    }:
        return True, "Skipped by --search-only"

    if args.no_downstream and step_id in {
        "12_EVIDENCE_PACK_REPORTER",
        "13_SOURCE_CITATION_VERIFIER",
        "14_CONFLICT_DETECTOR",
        "15_SSOT_CANDIDATE_EXTRACTOR",
        "16_FINANCIAL_SIGNAL_EXTRACTOR",
        "17_RISK_SIGNAL_EXTRACTOR",
        "18_DOCUMENT_PRIORITY_RANKER",
        "10_MORNING_BRIEFING",
    }:
        return True, "Skipped by --no-downstream"

    if args.steps:
        allowed = {x.strip().upper() for x in args.steps.split(",") if x.strip()}
        if step_id not in allowed and str(step["script"]).upper() not in allowed:
            return True, "Skipped because not listed in --steps"

    return False, None


def run_step(
    paths: OrchestratorPaths,
    step: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    started_dt = now_dt()
    started_at = started_dt.isoformat(timespec="seconds")

    skip, skip_reason = should_skip_step(step, args)
    script_path = paths.scripts_dir / str(step["script"])

    base_record = {
        "step_id": step["step_id"],
        "script": step["script"],
        "category": step["category"],
        "critical": bool(step["critical"]),
        "description": step["description"],
        "started_at": started_at,
        "ended_at": None,
        "duration_seconds": 0.0,
        "status": None,
        "exit_code": None,
        "command": None,
        "skip_reason": skip_reason,
        "stdout_tail": "",
        "stderr_tail": "",
        "error": None,
    }

    if skip:
        ended_dt = now_dt()
        base_record.update({
            "ended_at": ended_dt.isoformat(timespec="seconds"),
            "duration_seconds": seconds_between(started_dt, ended_dt),
            "status": STATUS_SKIPPED,
        })
        return base_record

    if not script_path.exists():
        ended_dt = now_dt()
        base_record.update({
            "ended_at": ended_dt.isoformat(timespec="seconds"),
            "duration_seconds": seconds_between(started_dt, ended_dt),
            "status": STATUS_MISSING_SCRIPT,
            "error": f"Missing script: {script_path}",
        })
        return base_record

    cmd = build_step_command(paths, step, args)
    base_record["command"] = cmd

    try:
        result = subprocess.run(
            cmd,
            cwd=str(paths.base_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout_seconds,
        )

        ended_dt = now_dt()
        status = STATUS_SUCCESS if result.returncode == 0 else STATUS_FAILED

        base_record.update({
            "ended_at": ended_dt.isoformat(timespec="seconds"),
            "duration_seconds": seconds_between(started_dt, ended_dt),
            "status": status,
            "exit_code": result.returncode,
            "stdout_tail": tail_text(result.stdout, args.tail_chars),
            "stderr_tail": tail_text(result.stderr, args.tail_chars),
        })

        return base_record

    except subprocess.TimeoutExpired as exc:
        ended_dt = now_dt()
        base_record.update({
            "ended_at": ended_dt.isoformat(timespec="seconds"),
            "duration_seconds": seconds_between(started_dt, ended_dt),
            "status": STATUS_TIMEOUT,
            "stdout_tail": tail_text(exc.stdout or "", args.tail_chars),
            "stderr_tail": tail_text(exc.stderr or "", args.tail_chars),
            "error": f"Timeout after {args.timeout_seconds} seconds",
        })
        return base_record

    except Exception as exc:
        ended_dt = now_dt()
        base_record.update({
            "ended_at": ended_dt.isoformat(timespec="seconds"),
            "duration_seconds": seconds_between(started_dt, ended_dt),
            "status": STATUS_ERROR,
            "error": str(exc),
            "stderr_tail": traceback.format_exc()[-args.tail_chars:],
        })
        return base_record


def write_steps_csv(path: Path, steps: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "step_id",
        "script",
        "category",
        "critical",
        "status",
        "exit_code",
        "duration_seconds",
        "started_at",
        "ended_at",
        "skip_reason",
        "error",
        "command",
        "description",
        "stdout_tail",
        "stderr_tail",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for step in steps:
            row = dict(step)
            row["command"] = " ".join(str(x) for x in row.get("command") or [])
            row["stdout_tail"] = normalize_inline(row.get("stdout_tail"))[:2000]
            row["stderr_tail"] = normalize_inline(row.get("stderr_tail"))[:2000]
            writer.writerow(row)


def final_status_from_steps(steps: list[dict[str, Any]]) -> str:
    critical_failures = [
        s for s in steps
        if bool(s.get("critical")) and s.get("status") not in {STATUS_SUCCESS, STATUS_SKIPPED}
    ]
    if critical_failures:
        return FINAL_FAILED_CRITICAL_STEP

    noncritical_failures = [
        s for s in steps
        if not bool(s.get("critical")) and s.get("status") not in {STATUS_SUCCESS, STATUS_SKIPPED}
    ]
    if noncritical_failures:
        return FINAL_SUCCESS_WITH_WARNINGS

    return FINAL_SUCCESS


def collect_key_report_snapshots(base_dir: Path) -> dict[str, Any]:
    report_paths = {
        "incremental_refresh_summary": base_dir / "05_reports" / "incremental_refresh_summary.json",
        "embedding_summary": base_dir / "05_reports" / "embedding_summary.json",
        "latest_audit_record": base_dir / "05_reports" / "latest_audit_record.json",
        "citation_verification_report": base_dir / "05_reports" / "citation_verification_report.json",
        "conflict_report": base_dir / "05_reports" / "conflict_report.json",
        "ssot_candidates_report": base_dir / "05_reports" / "ssot_candidates_report.json",
        "financial_signals_report": base_dir / "05_reports" / "financial_signals_report.json",
        "risk_signals_report": base_dir / "05_reports" / "risk_signals_report.json",
        "document_priority_rank": base_dir / "05_reports" / "document_priority_rank.json",
        "morning_briefing": base_dir / "05_reports" / "morning_briefing.json",
    }

    snapshots: dict[str, Any] = {}

    for name, path in report_paths.items():
        payload = load_json_if_exists(path)
        if payload is None:
            snapshots[name] = {"available": False}
            continue

        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        snapshots[name] = {
            "available": True,
            "path": str(path),
            "status": (
                payload.get("status")
                or payload.get("audit_status")
                or payload.get("verification_status")
                or payload.get("overall_status")
                or summary.get("institutional_status")
                or summary.get("report_status")
            ),
            "summary": summary,
        }

    return snapshots


def build_summary(
    paths: OrchestratorPaths,
    started_at: str,
    ended_at: str,
    steps: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    critical_failures = [
        s for s in steps
        if bool(s.get("critical")) and s.get("status") not in {STATUS_SUCCESS, STATUS_SKIPPED}
    ]
    noncritical_failures = [
        s for s in steps
        if not bool(s.get("critical")) and s.get("status") not in {STATUS_SUCCESS, STATUS_SKIPPED}
    ]

    status_counts: dict[str, int] = {}
    duration_total = 0.0

    for step in steps:
        status = str(step.get("status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        duration_total += float(step.get("duration_seconds") or 0.0)

    summary = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "NIGHT_RUN_ORCHESTRATION_AUDIT_LOCKED",
        "base_dir": str(paths.base_dir),
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": round(duration_total, 3),
        "final_status": final_status_from_steps(steps),
        "query": args.query,
        "full_rebuild": bool(args.full_rebuild),
        "search_only": bool(args.search_only),
        "skip_discovery": bool(args.skip_discovery),
        "no_downstream": bool(args.no_downstream),
        "strict_audit": bool(args.strict_audit),
        "strict_downstream": bool(args.strict_downstream),
        "step_count": len(steps),
        "critical_failure_count": len(critical_failures),
        "noncritical_failure_count": len(noncritical_failures),
        "status_counts": dict(sorted(status_counts.items())),
        "critical_failures": summarize_failures(critical_failures),
        "noncritical_failures": summarize_failures(noncritical_failures),
        "steps": steps,
        "report_snapshots": collect_key_report_snapshots(paths.base_dir),
        "outputs": {
            "summary_json": str(paths.summary_json),
            "summary_md": str(paths.summary_md),
            "steps_csv": str(paths.steps_csv),
            "audit_log": str(paths.audit_log),
            "error_log": str(paths.error_log),
        },
        "governance_rule": {
            "orchestrator_runs_scripts_only": True,
            "source_documents_not_modified": True,
            "critical_step_failure_stops_pipeline": True,
            "noncritical_failure_allows_summary": True,
            "audit_precedes_decision": True,
        },
    }

    summary["night_run_summary_sha256"] = sha256_json(summary)
    return summary


def summarize_failures(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for failure in failures:
        rows.append({
            "step_id": failure.get("step_id"),
            "script": failure.get("script"),
            "status": failure.get("status"),
            "exit_code": failure.get("exit_code"),
            "error": failure.get("error"),
            "stderr_tail": tail_text(failure.get("stderr_tail"), 1200),
        })
    return rows


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def steps_table_md(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "No steps."

    lines = [
        "| # | Step | Critical | Status | Exit | Seconds | Script |",
        "|---:|---|---:|---|---:|---:|---|",
    ]

    for idx, step in enumerate(steps, start=1):
        lines.append(
            f"| {idx} | "
            f"{md_escape(step.get('step_id'))} | "
            f"{step.get('critical')} | "
            f"{md_escape(step.get('status'))} | "
            f"{step.get('exit_code')} | "
            f"{step.get('duration_seconds')} | "
            f"`{md_escape(step.get('script'))}` |"
        )
    return "\n".join(lines)


def failures_md(title: str, failures: list[dict[str, Any]]) -> str:
    if not failures:
        return f"## {title}\n\nNo failures."

    blocks = [f"## {title}\n"]
    for f in failures:
        blocks.append(
            f"### {f.get('step_id')} — {f.get('status')}\n\n"
            f"- Script: `{f.get('script')}`\n"
            f"- Exit code: {f.get('exit_code')}\n"
            f"- Error: {f.get('error')}\n\n"
            f"```text\n{f.get('stderr_tail') or ''}\n```\n"
        )
    return "\n".join(blocks)


def snapshots_md(snapshots: dict[str, Any]) -> str:
    if not snapshots:
        return "No report snapshots."

    lines = [
        "| Report | Available | Status | Key Summary |",
        "|---|---:|---|---|",
    ]

    for name, snap in snapshots.items():
        summary = snap.get("summary") if isinstance(snap, dict) else {}
        key_summary = ""
        if isinstance(summary, dict):
            keep = {}
            for key in [
                "institutional_status", "total_risks", "critical_count", "high_count",
                "total_signals", "total_conflicts", "total_candidates",
                "ranked_documents", "p0_count", "p1_count",
                "incremental_records", "incremental_safe_records",
            ]:
                if key in summary:
                    keep[key] = summary[key]
            key_summary = json.dumps(keep, ensure_ascii=False)
        lines.append(
            f"| {md_escape(name)} | "
            f"{snap.get('available') if isinstance(snap, dict) else False} | "
            f"{md_escape(snap.get('status') if isinstance(snap, dict) else '')} | "
            f"{md_escape(key_summary)} |"
        )
    return "\n".join(lines)


def summary_to_markdown(summary: dict[str, Any]) -> str:
    return f"""# TITAN RAG Night Run Summary

## 1. Executive Status

| Field | Value |
|---|---|
| Created At | {summary.get("created_at")} |
| Final Status | {summary.get("final_status")} |
| Started At | {summary.get("started_at")} |
| Ended At | {summary.get("ended_at")} |
| Duration Seconds | {summary.get("duration_seconds")} |
| Query | {md_escape(summary.get("query"))} |
| Step Count | {summary.get("step_count")} |
| Critical Failures | {summary.get("critical_failure_count")} |
| Noncritical Failures | {summary.get("noncritical_failure_count")} |
| Summary SHA-256 | `{summary.get("night_run_summary_sha256")}` |

---

## 2. Status Counts

```json
{json.dumps(summary.get("status_counts", {}), indent=2, ensure_ascii=False)}
```

---

## 3. Step Execution Table

{steps_table_md(summary.get("steps", []))}

---

{failures_md("4. Critical Failures", summary.get("critical_failures", []))}

---

{failures_md("5. Noncritical Failures", summary.get("noncritical_failures", []))}

---

## 6. Report Snapshots

{snapshots_md(summary.get("report_snapshots", {}))}

---

## 7. Governance Rule

```text
Orchestrator runs scripts only.
Source documents are not modified.
Critical step failure stops pipeline.
Non-critical failure allows summary and morning briefing.
Audit precedes decision.
```
"""


def print_summary(summary: dict[str, Any], paths: OrchestratorPaths) -> None:
    print("=" * 100)
    print("TITAN RAG NIGHT RUN ORCHESTRATOR v2.0 AUDIT LOCKED")
    print("=" * 100)
    print(f"Final status:              {summary.get('final_status')}")
    print(f"Duration seconds:          {summary.get('duration_seconds')}")
    print(f"Step count:                {summary.get('step_count')}")
    print(f"Critical failures:         {summary.get('critical_failure_count')}")
    print(f"Noncritical failures:      {summary.get('noncritical_failure_count')}")
    print(f"Query:                     {summary.get('query')}")
    print("-" * 100)
    print(f"Summary JSON:              {paths.summary_json}")
    print(f"Summary Markdown:          {paths.summary_md}")
    print(f"Steps CSV:                 {paths.steps_csv}")
    print("=" * 100)


def run_night_pipeline(paths: OrchestratorPaths, args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now_iso()
    steps: list[dict[str, Any]] = []

    for step in STEP_DEFINITIONS:
        record = run_step(paths, step, args)
        steps.append(record)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "NIGHT_RUN_STEP_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "step": record,
        })

        print(f"[{record.get('status')}] {record.get('step_id')} ({record.get('duration_seconds')}s)")

        failed = record.get("status") not in {STATUS_SUCCESS, STATUS_SKIPPED}
        critical = bool(record.get("critical"))

        if failed and critical:
            append_jsonl(paths.error_log, {
                "timestamp": utc_now_iso(),
                "event": "CRITICAL_STEP_FAILED_PIPELINE_STOPPED",
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "step": record,
            })
            break

    ended_at = utc_now_iso()

    summary = build_summary(
        paths=paths,
        started_at=started_at,
        ended_at=ended_at,
        steps=steps,
        args=args,
    )

    return summary


def validate_base(paths: OrchestratorPaths) -> None:
    if not paths.base_dir.exists():
        raise FileNotFoundError(f"Base directory does not exist: {paths.base_dir}")
    if not paths.scripts_dir.exists():
        raise FileNotFoundError(f"Scripts directory does not exist: {paths.scripts_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN RAG Step 19 — night run orchestrator.")

    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base TITAN_FULL_RAG directory.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Default query used in Step 06.")
    parser.add_argument("--top-k-raw", type=int, default=80, help="Step 06 raw retrieval count.")
    parser.add_argument("--top-k-final", type=int, default=20, help="Step 06 final evidence count.")
    parser.add_argument("--min-search-score", type=float, default=None, help="Optional Step 06 score threshold.")
    parser.add_argument("--min-answer-score", type=float, default=None, help="Optional Step 07 evidence score threshold.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Optional timeout per step.")
    parser.add_argument("--tail-chars", type=int, default=8000, help="Captured stdout/stderr tail per step.")

    parser.add_argument("--full-rebuild", action="store_true", help="Run extraction full and reset embeddings.")
    parser.add_argument("--reset-vectors", action="store_true", help="Reset vectors in Step 05.")
    parser.add_argument("--force-all", action="store_true", help="Pass --force-all to Step 09.")
    parser.add_argument("--no-snapshot-update", action="store_true", help="Pass --no-snapshot-update to Step 09.")
    parser.add_argument("--extract-overwrite", action="store_true", help="Pass --overwrite to Step 03.")
    parser.add_argument("--embedding-batch-size", type=int, default=None, help="Optional Step 05 batch size.")

    parser.add_argument("--skip-discovery", action="store_true", help="Skip Steps 01, 02 and 09.")
    parser.add_argument("--search-only", action="store_true", help="Skip indexing/extraction/vector build; run search/answer/audit/downstream.")
    parser.add_argument("--no-downstream", action="store_true", help="Stop after Step 08.")
    parser.add_argument("--steps", default=None, help="Comma-separated step IDs or script names to run only selected steps.")

    parser.add_argument("--strict-audit", action="store_true", help="Pass --strict to Step 08.")
    parser.add_argument("--strict-downstream", action="store_true", help="Pass --strict to Steps 13-18.")

    parser.add_argument("--print", action="store_true", help="Print Markdown summary to console.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = resolve_paths(Path(args.base_dir))

    try:
        validate_base(paths)

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "NIGHT_RUN_STARTED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(paths.base_dir),
            "query": args.query,
            "args": vars(args),
        })

        summary = run_night_pipeline(paths, args)
        markdown = summary_to_markdown(summary)

        write_json(paths.summary_json, summary)
        write_text(paths.summary_md, markdown)
        write_steps_csv(paths.steps_csv, summary.get("steps", []))

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "NIGHT_RUN_COMPLETED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "final_status": summary.get("final_status"),
            "summary_sha256": summary.get("night_run_summary_sha256"),
            "summary": {
                "duration_seconds": summary.get("duration_seconds"),
                "step_count": summary.get("step_count"),
                "critical_failure_count": summary.get("critical_failure_count"),
                "noncritical_failure_count": summary.get("noncritical_failure_count"),
                "status_counts": summary.get("status_counts"),
            },
            "outputs": summary.get("outputs"),
        })

        print_summary(summary, paths)

        if args.print:
            print("\n" + markdown)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "NIGHT_RUN_ORCHESTRATOR_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(paths.base_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG NIGHT RUN ORCHESTRATOR FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
