#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
11_query_console.py

TITAN LOCAL EVIDENCE RAG ENGINE
Step 11 — Interactive Query Console
Version: v2.0_AUDIT_LOCKED

Purpose
-------
Provide a controlled local console for asking questions against the TITAN RAG
evidence base. This script orchestrates existing pipeline scripts:

06_search_rag.py
07_generate_answer.py
08_write_audit_log.py

This script does NOT invent facts.
This script does NOT bypass retrieval.
This script does NOT answer without evidence.
This script does NOT modify source documents.

Core doctrine
-------------
Evidence precedes intelligence.
Retrieval precedes generation.
Audit precedes decision.

Workflow
--------
User query -> Step 06 retrieval -> Step 07 evidence-bound answer -> Step 08 audit

Outputs
-------
05_reports/query_console_session.json
05_reports/query_console_session.md
06_logs/query_console_history.jsonl
06_logs/query_console_audit.jsonl
06_logs/query_console_errors.jsonl

Recommended command
-------------------
python ".\\08_scripts\\11_query_console.py"

Single query mode
-----------------
python ".\\08_scripts\\11_query_console.py" --query "Koji dokumenti pominju CAPEX?"

Strict audit
------------
python ".\\08_scripts\\11_query_console.py" --query "EIB EBRD CAPEX" --strict-audit

Higher recall
-------------
python ".\\08_scripts\\11_query_console.py" --query "DSCR WACC loan" --top-k-raw 80 --top-k-final 15
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_NAME = "11_query_console.py"
SCRIPT_VERSION = "v2.0_AUDIT_LOCKED"

DEFAULT_BASE_DIR = Path(r"C:\Users\Korisnik\Desktop\TITAN_FULL_RAG")
SCRIPTS_DIR = Path("08_scripts")

STEP_06 = "06_search_rag.py"
STEP_07 = "07_generate_answer.py"
STEP_08 = "08_write_audit_log.py"

LATEST_EVIDENCE_PACK = Path("05_reports") / "latest_evidence_pack.json"
LATEST_RAG_ANSWER = Path("05_reports") / "latest_rag_answer.json"
LATEST_AUDIT_RECORD = Path("05_reports") / "latest_audit_record.json"

SESSION_JSON = Path("05_reports") / "query_console_session.json"
SESSION_MD = Path("05_reports") / "query_console_session.md"

HISTORY_LOG = Path("06_logs") / "query_console_history.jsonl"
AUDIT_LOG = Path("06_logs") / "query_console_audit.jsonl"
ERROR_LOG = Path("06_logs") / "query_console_errors.jsonl"

DEFAULT_TOP_K_RAW = 50
DEFAULT_TOP_K_FINAL = 10
DEFAULT_TIMEOUT_SECONDS = None

EXIT_COMMANDS = {"exit", "quit", "q", ":q", "kraj"}
HELP_COMMANDS = {"help", "?", ":help"}
STATUS_COMMANDS = {"status", ":status"}
LAST_COMMANDS = {"last", ":last"}


@dataclass(frozen=True)
class ConsolePaths:
    base_dir: Path
    scripts_dir: Path
    evidence_pack: Path
    answer_json: Path
    audit_record: Path
    session_json: Path
    session_md: Path
    history_log: Path
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


def short_text(value: Any, max_chars: int = 800) -> str:
    text = str(value or "")
    if len(text) > max_chars:
        return text[:max_chars] + " ..."
    return text


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def resolve_paths(base_dir: Path) -> ConsolePaths:
    return ConsolePaths(
        base_dir=base_dir,
        scripts_dir=base_dir / SCRIPTS_DIR,
        evidence_pack=base_dir / LATEST_EVIDENCE_PACK,
        answer_json=base_dir / LATEST_RAG_ANSWER,
        audit_record=base_dir / LATEST_AUDIT_RECORD,
        session_json=base_dir / SESSION_JSON,
        session_md=base_dir / SESSION_MD,
        history_log=base_dir / HISTORY_LOG,
        audit_log=base_dir / AUDIT_LOG,
        error_log=base_dir / ERROR_LOG,
    )


def validate_scripts(paths: ConsolePaths) -> list[dict[str, Any]]:
    missing = []
    for script_name in [STEP_06, STEP_07, STEP_08]:
        script_path = paths.scripts_dir / script_name
        if not script_path.exists():
            missing.append({
                "script": script_name,
                "expected_path": str(script_path),
            })
    return missing


def run_subprocess(
    base_dir: Path,
    command: list[str],
    timeout_seconds: int | None,
) -> dict[str, Any]:
    started_at = utc_now_iso()

    try:
        result = subprocess.run(
            command,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )

        return {
            "started_at": started_at,
            "ended_at": utc_now_iso(),
            "command": command,
            "exit_code": result.returncode,
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "stdout_tail": tail_text(result.stdout, 8000),
            "stderr_tail": tail_text(result.stderr, 8000),
            "error": None,
        }

    except subprocess.TimeoutExpired as exc:
        return {
            "started_at": started_at,
            "ended_at": utc_now_iso(),
            "command": command,
            "exit_code": None,
            "status": "TIMEOUT",
            "stdout_tail": tail_text(exc.stdout or "", 8000),
            "stderr_tail": tail_text(exc.stderr or "", 8000),
            "error": f"Timeout after {timeout_seconds} seconds",
        }

    except Exception as exc:
        return {
            "started_at": started_at,
            "ended_at": utc_now_iso(),
            "command": command,
            "exit_code": None,
            "status": "ERROR",
            "stdout_tail": "",
            "stderr_tail": "",
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


def tail_text(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def build_step06_command(
    paths: ConsolePaths,
    query: str,
    top_k_raw: int,
    top_k_final: int,
    min_score: float | None,
    extension: list[str] | None,
    source_contains: list[str] | None,
    max_excerpt_chars: int | None,
) -> list[str]:
    cmd = [
        sys.executable,
        str(paths.scripts_dir / STEP_06),
        "--query",
        query,
        "--top-k-raw",
        str(top_k_raw),
        "--top-k-final",
        str(top_k_final),
    ]

    if min_score is not None:
        cmd.extend(["--min-score", str(min_score)])

    if max_excerpt_chars is not None:
        cmd.extend(["--max-excerpt-chars", str(max_excerpt_chars)])

    for ext in extension or []:
        cmd.extend(["--extension", ext])

    for marker in source_contains or []:
        cmd.extend(["--source-contains", marker])

    return cmd


def build_step07_command(paths: ConsolePaths, min_score: float | None, max_evidence_items: int | None) -> list[str]:
    cmd = [
        sys.executable,
        str(paths.scripts_dir / STEP_07),
    ]

    if min_score is not None:
        cmd.extend(["--min-score", str(min_score)])

    if max_evidence_items is not None:
        cmd.extend(["--max-evidence-items", str(max_evidence_items)])

    return cmd


def build_step08_command(paths: ConsolePaths, strict_audit: bool) -> list[str]:
    cmd = [
        sys.executable,
        str(paths.scripts_dir / STEP_08),
    ]

    if strict_audit:
        cmd.append("--strict")

    return cmd


def run_query_workflow(
    paths: ConsolePaths,
    query: str,
    top_k_raw: int,
    top_k_final: int,
    min_search_score: float | None,
    min_answer_score: float | None,
    max_evidence_items: int | None,
    extension: list[str] | None,
    source_contains: list[str] | None,
    max_excerpt_chars: int | None,
    strict_audit: bool,
    timeout_seconds: int | None,
    continue_on_audit_fail: bool,
) -> dict[str, Any]:
    workflow_started = utc_now_iso()
    query = normalize_inline(query)

    if len(query) < 2:
        raise ValueError("Query is too short.")

    steps: list[dict[str, Any]] = []

    step06_cmd = build_step06_command(
        paths=paths,
        query=query,
        top_k_raw=top_k_raw,
        top_k_final=top_k_final,
        min_score=min_search_score,
        extension=extension,
        source_contains=source_contains,
        max_excerpt_chars=max_excerpt_chars,
    )

    step06 = run_subprocess(paths.base_dir, step06_cmd, timeout_seconds)
    step06["step"] = "06_SEARCH_RAG"
    steps.append(step06)

    if step06["status"] != "SUCCESS":
        return finalize_workflow_result(
            paths=paths,
            query=query,
            workflow_started=workflow_started,
            steps=steps,
            final_status="FAILED_AT_RETRIEVAL",
        )

    step07_cmd = build_step07_command(
        paths=paths,
        min_score=min_answer_score,
        max_evidence_items=max_evidence_items,
    )

    step07 = run_subprocess(paths.base_dir, step07_cmd, timeout_seconds)
    step07["step"] = "07_GENERATE_ANSWER"
    steps.append(step07)

    if step07["status"] != "SUCCESS":
        return finalize_workflow_result(
            paths=paths,
            query=query,
            workflow_started=workflow_started,
            steps=steps,
            final_status="FAILED_AT_GENERATION",
        )

    step08_cmd = build_step08_command(paths=paths, strict_audit=strict_audit)

    step08 = run_subprocess(paths.base_dir, step08_cmd, timeout_seconds)
    step08["step"] = "08_WRITE_AUDIT_LOG"
    steps.append(step08)

    if step08["status"] != "SUCCESS" and not continue_on_audit_fail:
        return finalize_workflow_result(
            paths=paths,
            query=query,
            workflow_started=workflow_started,
            steps=steps,
            final_status="FAILED_AT_AUDIT",
        )

    evidence_pack = load_json_if_exists(paths.evidence_pack)
    answer = load_json_if_exists(paths.answer_json)
    audit = load_json_if_exists(paths.audit_record)

    final_status = derive_final_status(
        evidence_pack=evidence_pack,
        answer=answer,
        audit=audit,
        steps=steps,
    )

    return finalize_workflow_result(
        paths=paths,
        query=query,
        workflow_started=workflow_started,
        steps=steps,
        final_status=final_status,
        evidence_pack=evidence_pack,
        answer=answer,
        audit=audit,
    )


def derive_final_status(
    evidence_pack: dict[str, Any] | None,
    answer: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    steps: list[dict[str, Any]],
) -> str:
    if any(step.get("status") not in {"SUCCESS"} for step in steps):
        return "COMPLETED_WITH_STEP_WARNINGS"

    if not evidence_pack:
        return "NO_EVIDENCE_PACK"
    if not answer:
        return "NO_ANSWER"
    if not audit:
        return "NO_AUDIT_RECORD"

    audit_status = str(audit.get("audit_status") or "")
    institutional_status = str(answer.get("institutional_status") or "")

    if audit_status in {"AUDIT_FAIL", "AUDIT_NO_EVIDENCE"}:
        return "ANSWER_NOT_USABLE_AUDIT_FAIL"

    if audit_status in {"AUDIT_REVIEW_REQUIRED", "AUDIT_PASS_WITH_WARNINGS"}:
        return "ANSWER_DRAFT_REVIEW_REQUIRED"

    if "CONFLICT" in institutional_status or "REVIEW" in institutional_status:
        return "ANSWER_DRAFT_REVIEW_REQUIRED"

    if audit_status == "AUDIT_PASS":
        return "ANSWER_AUDIT_PASSED"

    return "ANSWER_CREATED_STATUS_UNKNOWN"


def finalize_workflow_result(
    paths: ConsolePaths,
    query: str,
    workflow_started: str,
    steps: list[dict[str, Any]],
    final_status: str,
    evidence_pack: dict[str, Any] | None = None,
    answer: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow = {
        "created_at": utc_now_iso(),
        "workflow_started_at": workflow_started,
        "workflow_ended_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "QUERY_CONSOLE_RETRIEVAL_GENERATION_AUDIT_CHAIN",
        "query": query,
        "final_status": final_status,
        "steps": steps,
        "summary": {
            "evidence_count": (evidence_pack or {}).get("evidence_count"),
            "source_file_count": (evidence_pack or {}).get("source_file_count"),
            "answer_institutional_status": (answer or {}).get("institutional_status"),
            "answer_confidence": (answer or {}).get("confidence"),
            "audit_status": (audit or {}).get("audit_status"),
            "audit_record_sha256": (audit or {}).get("audit_record_sha256"),
            "answer_sha256": (answer or {}).get("answer_sha256"),
            "evidence_pack_sha256": (evidence_pack or {}).get("evidence_pack_sha256"),
        },
        "outputs": {
            "latest_evidence_pack": str(paths.evidence_pack),
            "latest_rag_answer": str(paths.answer_json),
            "latest_audit_record": str(paths.audit_record),
        },
        "answer_snapshot": {
            "direct_answer": (answer or {}).get("direct_answer"),
            "risk_if_skipped": (answer or {}).get("risk_if_skipped"),
            "next_action": (answer or {}).get("next_action"),
            "source_files": (answer or {}).get("source_files"),
            "chunk_ids": (answer or {}).get("chunk_ids"),
        },
        "governance_rule": {
            "retrieval_precedes_generation": True,
            "audit_precedes_decision": True,
            "no_answer_without_evidence": True,
            "source_files_remain_authoritative": True,
            "console_is_orchestrator_not_truth_source": True,
        },
    }

    workflow["workflow_sha256"] = sha256_json(workflow)
    return workflow


def sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    import hashlib
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def append_session(paths: ConsolePaths, workflow: dict[str, Any]) -> dict[str, Any]:
    existing = load_json_if_exists(paths.session_json) or {
        "created_at": utc_now_iso(),
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "policy": "QUERY_CONSOLE_SESSION",
        "queries": [],
    }

    queries = existing.get("queries", [])
    if not isinstance(queries, list):
        queries = []

    queries.append(workflow)
    existing["queries"] = queries
    existing["updated_at"] = utc_now_iso()
    existing["query_count"] = len(queries)
    existing["last_status"] = workflow.get("final_status")
    existing["last_query"] = workflow.get("query")
    existing["session_sha256"] = sha256_json(existing)

    write_json(paths.session_json, existing)
    write_text(paths.session_md, session_to_markdown(existing))

    append_jsonl(paths.history_log, {
        "timestamp": utc_now_iso(),
        "event": "QUERY_WORKFLOW_COMPLETED",
        "query": workflow.get("query"),
        "final_status": workflow.get("final_status"),
        "workflow_sha256": workflow.get("workflow_sha256"),
        "summary": workflow.get("summary"),
    })

    append_jsonl(paths.audit_log, {
        "timestamp": utc_now_iso(),
        "event": "QUERY_CONSOLE_SESSION_UPDATED",
        "script": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "query_count": existing.get("query_count"),
        "last_status": existing.get("last_status"),
        "session_sha256": existing.get("session_sha256"),
    })

    return existing


def md_escape(value: Any) -> str:
    return normalize_inline(value).replace("|", "\\|")


def workflow_to_console_text(workflow: dict[str, Any]) -> str:
    summary = workflow.get("summary", {}) if isinstance(workflow.get("summary"), dict) else {}
    answer = workflow.get("answer_snapshot", {}) if isinstance(workflow.get("answer_snapshot"), dict) else {}

    lines = [
        "=" * 100,
        "TITAN RAG QUERY RESULT",
        "=" * 100,
        f"Query:          {workflow.get('query')}",
        f"Final status:   {workflow.get('final_status')}",
        f"Evidence count: {summary.get('evidence_count')}",
        f"Source files:   {summary.get('source_file_count')}",
        f"Answer status:  {summary.get('answer_institutional_status')}",
        f"Audit status:   {summary.get('audit_status')}",
        "-" * 100,
        "DIRECT ANSWER:",
        str(answer.get("direct_answer") or ""),
        "-" * 100,
        "RISK IF SKIPPED:",
        str(answer.get("risk_if_skipped") or ""),
        "-" * 100,
        "NEXT ACTION:",
        str(answer.get("next_action") or ""),
        "=" * 100,
    ]

    return "\n".join(lines)


def session_to_markdown(session: dict[str, Any]) -> str:
    queries = session.get("queries", [])
    if not isinstance(queries, list):
        queries = []

    rows = [
        "| # | Created | Status | Query | Evidence | Sources | Audit |",
        "|---:|---|---|---|---:|---:|---|",
    ]

    for idx, workflow in enumerate(queries, start=1):
        summary = workflow.get("summary", {}) if isinstance(workflow.get("summary"), dict) else {}
        rows.append(
            f"| {idx} | "
            f"{md_escape(workflow.get('created_at'))} | "
            f"{md_escape(workflow.get('final_status'))} | "
            f"{md_escape(workflow.get('query'))} | "
            f"{summary.get('evidence_count')} | "
            f"{summary.get('source_file_count')} | "
            f"{md_escape(summary.get('audit_status'))} |"
        )

    last = queries[-1] if queries else {}
    last_answer = last.get("answer_snapshot", {}) if isinstance(last.get("answer_snapshot"), dict) else {}

    return f"""# TITAN RAG Query Console Session

## 1. Session Identity

| Field | Value |
|---|---|
| Created At | {session.get("created_at")} |
| Updated At | {session.get("updated_at")} |
| Query Count | {session.get("query_count")} |
| Last Status | {session.get("last_status")} |
| Last Query | {md_escape(session.get("last_query"))} |
| Session SHA-256 | `{session.get("session_sha256")}` |

---

## 2. Query History

{chr(10).join(rows)}

---

## 3. Last Answer Snapshot

```text
{last_answer.get("direct_answer") or ""}
```

---

## 4. Last Risk If Skipped

```text
{last_answer.get("risk_if_skipped") or ""}
```

---

## 5. Last Next Action

```text
{last_answer.get("next_action") or ""}
```

---

## 6. Governance Rule

```text
Console orchestrates retrieval -> answer -> audit.
It is not a truth source.
Latest evidence pack, answer and audit record remain authoritative outputs.
```
"""


def print_help() -> None:
    print("""
Commands:
  help / ?        Show this help
  status          Show latest session/audit status
  last            Print latest answer snapshot
  exit / quit     Exit console

Normal usage:
  Type any question and press Enter.

Example:
  Koji dokumenti pominju CAPEX i EBRD?
  Gdje se nalazi DSCR?
  Koji su najveći rizici u dokazima?
""")


def print_status(paths: ConsolePaths) -> None:
    session = load_json_if_exists(paths.session_json) or {}
    answer = load_json_if_exists(paths.answer_json) or {}
    audit = load_json_if_exists(paths.audit_record) or {}
    evidence = load_json_if_exists(paths.evidence_pack) or {}

    print("=" * 100)
    print("TITAN RAG QUERY CONSOLE STATUS")
    print("=" * 100)
    print(f"Session query count:    {session.get('query_count')}")
    print(f"Last query:             {session.get('last_query')}")
    print(f"Last status:            {session.get('last_status')}")
    print(f"Evidence count:         {evidence.get('evidence_count')}")
    print(f"Answer status:          {answer.get('institutional_status')}")
    print(f"Audit status:           {audit.get('audit_status')}")
    print(f"Session file:           {paths.session_json}")
    print("=" * 100)


def print_last(paths: ConsolePaths) -> None:
    answer = load_json_if_exists(paths.answer_json) or {}
    print("=" * 100)
    print("LATEST TITAN RAG ANSWER")
    print("=" * 100)
    print(f"Query: {answer.get('query')}")
    print(f"Status: {answer.get('institutional_status')}")
    print("-" * 100)
    print(answer.get("direct_answer") or "No latest answer available.")
    print("-" * 100)
    print("Next action:")
    print(answer.get("next_action") or "")
    print("=" * 100)


def interactive_loop(args: argparse.Namespace, paths: ConsolePaths) -> None:
    print("=" * 100)
    print("TITAN RAG QUERY CONSOLE v2.0 AUDIT LOCKED")
    print("=" * 100)
    print("Type a question. Type 'help' for commands. Type 'exit' to quit.")
    print("=" * 100)

    while True:
        try:
            query = input("TITAN_RAG> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not query:
            continue

        lower = query.lower().strip()

        if lower in EXIT_COMMANDS:
            print("Exiting.")
            break

        if lower in HELP_COMMANDS:
            print_help()
            continue

        if lower in STATUS_COMMANDS:
            print_status(paths)
            continue

        if lower in LAST_COMMANDS:
            print_last(paths)
            continue

        try:
            workflow = run_query_workflow_from_args(args=args, paths=paths, query=query)
            append_session(paths, workflow)
            print(workflow_to_console_text(workflow))

        except Exception as exc:
            append_jsonl(paths.error_log, {
                "timestamp": utc_now_iso(),
                "event": "INTERACTIVE_QUERY_FAILED",
                "script": SCRIPT_NAME,
                "script_version": SCRIPT_VERSION,
                "query": query,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            })
            print(f"ERROR: {exc}")


def run_query_workflow_from_args(args: argparse.Namespace, paths: ConsolePaths, query: str) -> dict[str, Any]:
    return run_query_workflow(
        paths=paths,
        query=query,
        top_k_raw=int(args.top_k_raw),
        top_k_final=int(args.top_k_final),
        min_search_score=args.min_search_score,
        min_answer_score=args.min_answer_score,
        max_evidence_items=args.max_evidence_items,
        extension=args.extension,
        source_contains=args.source_contains,
        max_excerpt_chars=args.max_excerpt_chars,
        strict_audit=bool(args.strict_audit),
        timeout_seconds=args.timeout_seconds,
        continue_on_audit_fail=bool(args.continue_on_audit_fail),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN RAG Step 11 — interactive query console."
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base TITAN_FULL_RAG directory.",
    )

    parser.add_argument(
        "--query",
        default=None,
        help="Single query mode. If omitted, interactive console starts.",
    )

    parser.add_argument(
        "--top-k-raw",
        type=int,
        default=DEFAULT_TOP_K_RAW,
        help="Raw retrieval results for Step 06.",
    )

    parser.add_argument(
        "--top-k-final",
        type=int,
        default=DEFAULT_TOP_K_FINAL,
        help="Final evidence results for Step 06.",
    )

    parser.add_argument(
        "--min-search-score",
        type=float,
        default=None,
        help="Minimum final score in Step 06 search.",
    )

    parser.add_argument(
        "--min-answer-score",
        type=float,
        default=None,
        help="Minimum evidence score used by Step 07 answer.",
    )

    parser.add_argument(
        "--max-evidence-items",
        type=int,
        default=None,
        help="Maximum evidence items Step 07 may use.",
    )

    parser.add_argument(
        "--extension",
        action="append",
        default=None,
        help="Pass extension filter to Step 06. Can be repeated.",
    )

    parser.add_argument(
        "--source-contains",
        action="append",
        default=None,
        help="Pass source path marker filter to Step 06. Can be repeated.",
    )

    parser.add_argument(
        "--max-excerpt-chars",
        type=int,
        default=None,
        help="Maximum excerpt chars for Step 06 evidence pack.",
    )

    parser.add_argument(
        "--strict-audit",
        action="store_true",
        help="Run Step 08 in strict mode.",
    )

    parser.add_argument(
        "--continue-on-audit-fail",
        action="store_true",
        help="Keep workflow result even if Step 08 fails.",
    )

    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Optional timeout per sub-step.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print workflow result in single-query mode.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)
    paths = resolve_paths(base_dir)

    try:
        missing = validate_scripts(paths)
        if missing:
            raise FileNotFoundError(
                "Missing required pipeline scripts:\n"
                + "\n".join(item["expected_path"] for item in missing)
            )

        append_jsonl(paths.audit_log, {
            "timestamp": utc_now_iso(),
            "event": "QUERY_CONSOLE_STARTED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "single_query_mode": bool(args.query),
        })

        if args.query:
            workflow = run_query_workflow_from_args(args=args, paths=paths, query=args.query)
            session = append_session(paths, workflow)

            if args.print:
                print(workflow_to_console_text(workflow))
            else:
                print("=" * 100)
                print("TITAN RAG QUERY WORKFLOW COMPLETED")
                print("=" * 100)
                print(f"Final status:     {workflow.get('final_status')}")
                print(f"Query:            {workflow.get('query')}")
                print(f"Session JSON:     {paths.session_json}")
                print(f"Session MD:       {paths.session_md}")
                print("=" * 100)

        else:
            interactive_loop(args=args, paths=paths)

    except Exception as exc:
        append_jsonl(paths.error_log, {
            "timestamp": utc_now_iso(),
            "event": "QUERY_CONSOLE_FAILED",
            "script": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "base_dir": str(base_dir),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })

        print("=" * 100)
        print("TITAN RAG QUERY CONSOLE FAILED")
        print("=" * 100)
        print(f"Error: {exc}")
        print(f"Error log: {paths.error_log}")
        print("=" * 100)
        raise


if __name__ == "__main__":
    main()
