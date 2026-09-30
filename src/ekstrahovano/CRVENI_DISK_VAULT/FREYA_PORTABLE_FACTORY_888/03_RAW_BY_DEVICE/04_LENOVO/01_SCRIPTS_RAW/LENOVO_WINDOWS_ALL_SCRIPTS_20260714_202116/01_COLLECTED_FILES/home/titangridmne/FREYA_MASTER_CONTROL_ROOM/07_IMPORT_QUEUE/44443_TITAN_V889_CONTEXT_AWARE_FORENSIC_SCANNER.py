#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_V889_CONTEXT_AWARE_FORENSIC_SCANNER.py
Context-aware forensic static scanner for TITAN_FULL_RAG / 08_scripts.

Read-only. No execution of scanned scripts. No file mutation outside output directory.

Core upgrades over keyword scanning:
- distinguishes comments/docstrings/policy text from executable code
- classifies atomic temp writes separately from destructive source operations
- separates external policy validation from real email/Telegram/upload calls
- scores risk using context, behavior, externality, and evidence impact
- emits CSV, JSON, TXT executive report, and evidence index

Usage:
    python TITAN_V889_CONTEXT_AWARE_FORENSIC_SCANNER.py --root "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts"
    python TITAN_V889_CONTEXT_AWARE_FORENSIC_SCANNER.py --root ./08_scripts --output ./V889_AUDIT_OUTPUT --strict
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import sys
import tokenize
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

VERSION = "V889_CONTEXT_AWARE_FORENSIC_SCANNER"

SCRIPT_EXTENSIONS = {".py", ".ps1", ".sh", ".bat", ".cmd"}
CRITICAL_NAMES = {
    "titan_hydra_discovery_router.py",
    "titan_hydra_rag_integrated_orchestrator_v1.py",
    "titan_hydra_integrated_rag_pipeline.py",
    "titan_full_rag_integrated_pipeline_v1_AUDIT_LOCKED.py",
}

KEYWORD_PATTERNS = {
    "external_upload_or_bid": re.compile(r"\b(upload|outreach|bid submission|external action|external use|procurement action|submit bid|approval action)\b", re.I),
    "email_or_telegram_send": re.compile(r"\b(telegram|bot_token|chat_id|send_message|sendmail|smtp|email|mailgun|ses|api_key|apikey|token|secret|credential|password|passwd)\b", re.I),
    "llm_or_embedding_activation": re.compile(r"\b(openai|anthropic|gemini|llm|embedding|embeddings|vectorize|api_key|model=|client\.chat|chat\.completions)\b", re.I),
    "shell_execution": re.compile(r"\b(subprocess|os\.system|popen|Start-Process|Invoke-Expression|iex|shell=True|powershell|cmd\.exe|bash)\b", re.I),
    "dynamic_code_execution": re.compile(r"\b(eval\(|exec\(|compile\(|execfile\(|Invoke-Expression|iex\b)\b", re.I),
    "dynamic_import": re.compile(r"\b(__import__\(|importlib\.import_module|SourceFileLoader|spec_from_file_location)\b", re.I),
    "destructive_delete": re.compile(r"\b(unlink\(|remove\(|rmdir\(|shutil\.rmtree|del\s+|Remove-Item|rm\s+-|os\.remove|Path\.unlink)\b", re.I),
    "move_or_replace": re.compile(r"\b(os\.replace|Path\.replace|shutil\.move|Move-Item|mv\s+|rename\(|os\.rename)\b", re.I),
    "writes_outputs": re.compile(r"\b(open\(.+['\"]w|write_text\(|write_bytes\(|csv\.writer|json\.dump|to_csv|to_excel|Export-Csv|Set-Content|Out-File)\b", re.I),
}

POLICY_NEGATION = re.compile(r"\b(no|not allowed|disabled|forbidden|blocked|deny|never|without|read-only|dry-run only|must not|cannot)\b", re.I)
TEMP_HINT = re.compile(r"\b(tmp|temp|temporary|\.tmp|_tmp|staging|atomic)\b", re.I)
SOURCE_HINT = re.compile(r"\b(source|raw|evidence|input|original|root|za_sortiranje|document|file_path|src)\b", re.I)
OUTPUT_HINT = re.compile(r"\b(output|report|audit|export|derived|index|manifest|result|target|dst|path)\b", re.I)
EXTERNAL_CALL_HINT = re.compile(r"\b(requests\.|urllib\.|httpx\.|smtp|sendmail|send_message|bot\.send|post\(|put\(|scp|ftp|s3|drive|upload)\b", re.I)

SEVERITY_ORDER = {"PASS": 0, "PASS_WITH_CONTROL": 1, "REVIEW_REQUIRED": 2, "MANUAL_BLOCK": 3, "EXECUTION_BLOCK": 4}

@dataclass
class Finding:
    file: str
    line: int
    category: str
    raw_priority: str
    revised_priority: str
    context_type: str
    behavior_type: str
    final_status: str
    score: int
    confidence: float
    evidence_impact: str
    externality: str
    snippet: str
    reason: str

@dataclass
class FileEvidence:
    file: str
    rel_path: str
    extension: str
    sha256: str
    size_bytes: int
    line_count: int
    ast_parse_status: str
    findings_count: int
    max_status: str
    max_score: int


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def decode_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1250", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def get_python_comment_docstring_lines(source: str) -> Tuple[Set[int], Set[int]]:
    comment_lines: Set[int] = set()
    doc_lines: Set[int] = set()
    try:
        tokens = tokenize.tokenize(BytesIO(source.encode("utf-8", errors="ignore")).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comment_lines.add(tok.start[0])
    except Exception:
        pass

    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr):
                    val = getattr(body[0], "value", None)
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        start = getattr(body[0], "lineno", 0)
                        end = getattr(body[0], "end_lineno", start)
                        doc_lines.update(range(start, end + 1))
    except Exception:
        pass
    return comment_lines, doc_lines


def ast_call_map(source: str) -> Dict[int, List[str]]:
    calls: Dict[int, List[str]] = defaultdict(list)
    try:
        tree = ast.parse(source)
    except Exception:
        return calls

    def call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = call_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node.func)
            if name:
                calls[getattr(node, "lineno", 0)].append(name)
    return calls


def classify_context(ext: str, line_no: int, line: str, comment_lines: Set[int], doc_lines: Set[int]) -> str:
    stripped = line.strip()
    if ext == ".py":
        if line_no in doc_lines:
            return "DOCSTRING_POLICY_TEXT" if POLICY_NEGATION.search(line) else "DOCSTRING"
        if line_no in comment_lines or stripped.startswith("#"):
            return "COMMENT_POLICY_TEXT" if POLICY_NEGATION.search(line) else "COMMENT"
    else:
        if stripped.startswith(("#", "//", "REM ", "::")):
            return "COMMENT_POLICY_TEXT" if POLICY_NEGATION.search(line) else "COMMENT"
    if POLICY_NEGATION.search(line) and any(p.search(line) for p in [KEYWORD_PATTERNS["external_upload_or_bid"], KEYWORD_PATTERNS["email_or_telegram_send"], KEYWORD_PATTERNS["llm_or_embedding_activation"]]):
        return "EXECUTABLE_POLICY_GUARD_OR_TEXT"
    return "EXECUTABLE_CODE"


def classify_behavior(category: str, line: str, calls: Sequence[str]) -> Tuple[str, str, str, float]:
    joined_calls = " ".join(calls)
    full = f"{line} {joined_calls}"

    if category == "destructive_delete":
        if TEMP_HINT.search(full):
            return "TEMP_CLEANUP", "DERIVED_OR_TEMP", "LOCAL", 0.86
        if SOURCE_HINT.search(full):
            return "SOURCE_EVIDENCE_DELETE", "SOURCE_EVIDENCE", "LOCAL", 0.84
        return "DELETE_REVIEW_REQUIRED", "UNKNOWN", "LOCAL", 0.62

    if category == "move_or_replace":
        if "replace" in full.lower() and TEMP_HINT.search(full) and OUTPUT_HINT.search(full):
            return "CONTROLLED_ATOMIC_WRITE", "DERIVED_OUTPUT", "LOCAL", 0.88
        if SOURCE_HINT.search(full) and not TEMP_HINT.search(full):
            return "SOURCE_EVIDENCE_MOVE_OR_REPLACE", "SOURCE_EVIDENCE", "LOCAL", 0.78
        return "MOVE_OR_REPLACE_REVIEW", "UNKNOWN", "LOCAL", 0.64

    if category == "shell_execution":
        if "subprocess.run" in full and "shell=True" not in full:
            return "SANDBOXABLE_SUBPROCESS", "DERIVED_OR_TEST", "LOCAL", 0.76
        if "shell=True" in full or re.search(r"Invoke-Expression|iex\b|os\.system", full, re.I):
            return "HIGH_RISK_SHELL_EXECUTION", "UNKNOWN", "LOCAL_OR_EXTERNAL", 0.90
        return "SHELL_REVIEW_REQUIRED", "UNKNOWN", "LOCAL", 0.66

    if category == "dynamic_code_execution":
        return "DYNAMIC_CODE_EXECUTION", "UNKNOWN", "LOCAL", 0.92

    if category == "dynamic_import":
        return "DYNAMIC_IMPORT", "UNKNOWN", "LOCAL", 0.72

    if category == "email_or_telegram_send":
        if EXTERNAL_CALL_HINT.search(full) or re.search(r"send_message|sendmail|SMTP|telegram\.Bot|bot\.send", full, re.I):
            return "EXTERNAL_SEND_OR_CREDENTIAL_USE", "UNKNOWN", "EXTERNAL", 0.90
        if re.search(r"policy|get\(|allow_|telegram_policy|token|secret|credential", full, re.I):
            return "EXTERNAL_POLICY_OR_SECRET_VALIDATION", "CONFIG_OR_POLICY", "POTENTIAL_EXTERNAL", 0.74
        return "EXTERNAL_KEYWORD_REVIEW", "UNKNOWN", "POTENTIAL_EXTERNAL", 0.58

    if category == "external_upload_or_bid":
        if EXTERNAL_CALL_HINT.search(full):
            return "EXTERNAL_UPLOAD_OR_ACTION", "UNKNOWN", "EXTERNAL", 0.92
        if POLICY_NEGATION.search(full):
            return "POLICY_TEXT_OR_GUARD", "CONFIG_OR_POLICY", "NONE", 0.80
        return "EXTERNAL_ACTION_KEYWORD_REVIEW", "UNKNOWN", "POTENTIAL_EXTERNAL", 0.55

    if category == "llm_or_embedding_activation":
        if re.search(r"client\.|\.create\(|chat\.completions|embeddings\.create|requests\.", full, re.I):
            return "ACTIVE_LLM_OR_EMBEDDING_CALL", "UNKNOWN", "EXTERNAL_OR_MODEL", 0.90
        if POLICY_NEGATION.search(full):
            return "POLICY_TEXT_OR_GUARD", "CONFIG_OR_POLICY", "NONE", 0.80
        return "LLM_OR_EMBEDDING_REFERENCE", "CONFIG_OR_POLICY", "POTENTIAL_EXTERNAL", 0.60

    if category == "writes_outputs":
        return "DERIVED_OUTPUT_WRITE", "DERIVED_OUTPUT", "LOCAL", 0.70

    return "GENERIC_REVIEW", "UNKNOWN", "UNKNOWN", 0.50


def score_and_status(category: str, context_type: str, behavior: str, evidence_impact: str, externality: str, confidence: float, critical_file: bool) -> Tuple[int, str, str]:
    base = {
        "dynamic_code_execution": 82,
        "shell_execution": 55,
        "email_or_telegram_send": 60,
        "external_upload_or_bid": 58,
        "llm_or_embedding_activation": 45,
        "destructive_delete": 50,
        "move_or_replace": 42,
        "dynamic_import": 35,
        "writes_outputs": 22,
    }.get(category, 20)

    if context_type.startswith("COMMENT") or context_type.startswith("DOCSTRING"):
        base = min(base, 18)
    elif context_type == "EXECUTABLE_POLICY_GUARD_OR_TEXT":
        base = min(base, 30)

    if behavior in {"SOURCE_EVIDENCE_DELETE", "SOURCE_EVIDENCE_MOVE_OR_REPLACE"}:
        base += 42
    if behavior in {"EXTERNAL_SEND_OR_CREDENTIAL_USE", "EXTERNAL_UPLOAD_OR_ACTION", "ACTIVE_LLM_OR_EMBEDDING_CALL"}:
        base += 35
    if behavior == "HIGH_RISK_SHELL_EXECUTION":
        base += 35
    if behavior in {"CONTROLLED_ATOMIC_WRITE", "TEMP_CLEANUP", "POLICY_TEXT_OR_GUARD"}:
        base -= 25
    if critical_file:
        base += 8

    score = max(0, min(100, int(base * confidence + base * (1 - confidence) * 0.75)))

    if score >= 90:
        return score, "P0", "EXECUTION_BLOCK"
    if score >= 75:
        return score, "P0", "MANUAL_BLOCK"
    if score >= 55:
        return score, "P1", "REVIEW_REQUIRED"
    if score >= 30:
        return score, "P2", "PASS_WITH_CONTROL"
    return score, "P3", "PASS"


def raw_priority(category: str) -> str:
    if category in {"dynamic_code_execution", "external_upload_or_bid", "email_or_telegram_send"}:
        return "P0"
    if category in {"shell_execution", "destructive_delete", "move_or_replace", "llm_or_embedding_activation"}:
        return "P1"
    if category == "dynamic_import":
        return "P2"
    return "P3"


def scan_file(path: Path, root: Path) -> Tuple[FileEvidence, List[Finding]]:
    data = safe_read_bytes(path)
    text = decode_text(data)
    rel = str(path.relative_to(root))
    ext = path.suffix.lower()
    lines = text.splitlines()
    comment_lines: Set[int] = set()
    doc_lines: Set[int] = set()
    call_map: Dict[int, List[str]] = {}
    ast_status = "N/A"
    if ext == ".py":
        try:
            ast.parse(text)
            ast_status = "OK"
        except SyntaxError as e:
            ast_status = f"SYNTAX_ERROR:{e.lineno}:{e.msg}"
        comment_lines, doc_lines = get_python_comment_docstring_lines(text)
        call_map = ast_call_map(text)

    findings: List[Finding] = []
    critical_file = path.name in CRITICAL_NAMES
    for i, line in enumerate(lines, start=1):
        for category, pattern in KEYWORD_PATTERNS.items():
            if not pattern.search(line):
                continue
            context = classify_context(ext, i, line, comment_lines, doc_lines)
            behavior, evidence_impact, externality, confidence = classify_behavior(category, line, call_map.get(i, []))
            score, revised, final_status = score_and_status(category, context, behavior, evidence_impact, externality, confidence, critical_file)
            rp = raw_priority(category)
            reason = f"{context}; {behavior}; evidence={evidence_impact}; externality={externality}"
            findings.append(Finding(
                file=rel,
                line=i,
                category=category,
                raw_priority=rp,
                revised_priority=revised,
                context_type=context,
                behavior_type=behavior,
                final_status=final_status,
                score=score,
                confidence=round(confidence, 2),
                evidence_impact=evidence_impact,
                externality=externality,
                snippet=line.strip()[:500],
                reason=reason,
            ))

    max_status = "PASS"
    max_score = 0
    for f in findings:
        if SEVERITY_ORDER[f.final_status] > SEVERITY_ORDER[max_status]:
            max_status = f.final_status
        max_score = max(max_score, f.score)

    evidence = FileEvidence(
        file=path.name,
        rel_path=rel,
        extension=ext,
        sha256=sha256_file(path),
        size_bytes=len(data),
        line_count=len(lines),
        ast_parse_status=ast_status,
        findings_count=len(findings),
        max_status=max_status,
        max_score=max_score,
    )
    return evidence, findings


def discover_scripts(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SCRIPT_EXTENSIONS)


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def build_summary(root: Path, files: List[FileEvidence], findings: List[Finding], created_utc: str) -> Dict[str, Any]:
    by_priority = Counter(f.revised_priority for f in findings)
    raw_by_priority = Counter(f.raw_priority for f in findings)
    by_status = Counter(f.final_status for f in findings)
    by_category = Counter(f.category for f in findings)
    by_context = Counter(f.context_type for f in findings)
    by_behavior = Counter(f.behavior_type for f in findings)
    py_files = [f for f in files if f.extension == ".py"]
    syntax_ok = sum(1 for f in py_files if f.ast_parse_status == "OK")
    blockers = [f for f in findings if f.final_status in {"MANUAL_BLOCK", "EXECUTION_BLOCK"}]
    package_hash_source = "".join(sorted(f.sha256 for f in files))
    package_fingerprint = hashlib.sha256(package_hash_source.encode()).hexdigest() if files else ""
    return {
        "scanner": VERSION,
        "created_utc": created_utc,
        "root": str(root),
        "scripts_scanned": len(files),
        "python_files": len(py_files),
        "python_ast_ok": syntax_ok,
        "python_ast_total": len(py_files),
        "total_findings": len(findings),
        "raw_priority_counts": dict(raw_by_priority),
        "revised_priority_counts": dict(by_priority),
        "final_status_counts": dict(by_status),
        "category_counts": dict(by_category),
        "context_counts": dict(by_context),
        "behavior_counts": dict(by_behavior),
        "blocker_count": len(blockers),
        "overall_status": "EXECUTION_BLOCK" if any(f.final_status == "EXECUTION_BLOCK" for f in findings) else ("MANUAL_BLOCK" if blockers else "PASS_WITH_CONTROL" if findings else "PASS"),
        "package_fingerprint_sha256": package_fingerprint,
    }


def write_txt_report(path: Path, summary: Dict[str, Any], findings: List[Finding]) -> None:
    blockers = [f for f in findings if f.final_status in {"MANUAL_BLOCK", "EXECUTION_BLOCK"}]
    top = sorted(findings, key=lambda f: (f.score, f.file, f.line), reverse=True)[:40]
    lines = []
    lines.append(f"{VERSION} REPORT")
    lines.append("=" * 72)
    lines.append(f"Created UTC: {summary['created_utc']}")
    lines.append(f"Root: {summary['root']}")
    lines.append(f"Scripts scanned: {summary['scripts_scanned']} (.py {summary['python_files']})")
    lines.append(f"Python AST parse: {summary['python_ast_ok']}/{summary['python_ast_total']} OK")
    lines.append(f"Overall status: {summary['overall_status']}")
    lines.append(f"Total findings: {summary['total_findings']}")
    lines.append(f"Blockers: {summary['blocker_count']}")
    lines.append("")
    lines.append("Revised priority counts: " + json.dumps(summary["revised_priority_counts"], ensure_ascii=False))
    lines.append("Final status counts: " + json.dumps(summary["final_status_counts"], ensure_ascii=False))
    lines.append("Context counts: " + json.dumps(summary["context_counts"], ensure_ascii=False))
    lines.append("Behavior counts: " + json.dumps(summary["behavior_counts"], ensure_ascii=False))
    lines.append("")
    lines.append("TOP BLOCKERS / HIGH-RISK FINDINGS")
    lines.append("-" * 72)
    if not blockers:
        lines.append("No MANUAL_BLOCK or EXECUTION_BLOCK findings detected.")
    else:
        for f in sorted(blockers, key=lambda x: (-x.score, x.file, x.line))[:50]:
            lines.append(f"{f.final_status} {f.revised_priority} score={f.score} {f.file}:{f.line} {f.category} {f.behavior_type}")
            lines.append(f"  {f.snippet}")
            lines.append(f"  reason: {f.reason}")
    lines.append("")
    lines.append("TOP 40 SCORED FINDINGS")
    lines.append("-" * 72)
    for f in top:
        lines.append(f"{f.final_status} {f.revised_priority} score={f.score} {f.file}:{f.line} {f.category} {f.context_type} {f.behavior_type}")
    lines.append("")
    lines.append("CFO CONTROL DECISION")
    lines.append("-" * 72)
    if summary["overall_status"] in {"EXECUTION_BLOCK", "MANUAL_BLOCK"}:
        lines.append("Execution remains blocked until blocker findings are manually reviewed or remediated.")
    else:
        lines.append("No execution blockers detected by V889; controlled dry-run execution may be considered.")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="TITAN V889 context-aware forensic scanner")
    parser.add_argument("--root", required=True, help="Root folder to scan, e.g. TITAN_FULL_RAG/08_scripts")
    parser.add_argument("--output", default=None, help="Output directory. Default: <root>/TITAN_V889_AUDIT_OUTPUT")
    parser.add_argument("--strict", action="store_true", help="Exit code 2 if MANUAL_BLOCK or EXECUTION_BLOCK findings exist")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: root does not exist or is not a directory: {root}", file=sys.stderr)
        return 1
    out = Path(args.output).expanduser().resolve() if args.output else root / "TITAN_V889_AUDIT_OUTPUT"
    out.mkdir(parents=True, exist_ok=True)

    created_utc = datetime.now(timezone.utc).isoformat()
    scripts = discover_scripts(root)
    files: List[FileEvidence] = []
    findings: List[Finding] = []
    for script in scripts:
        ev, fs = scan_file(script, root)
        files.append(ev)
        findings.extend(fs)

    summary = build_summary(root, files, findings, created_utc)

    findings_rows = [asdict(f) for f in findings]
    evidence_rows = [asdict(f) for f in files]

    write_csv(out / "TITAN_V889_FINDINGS.csv", findings_rows, list(Finding.__dataclass_fields__.keys()))
    write_csv(out / "TITAN_V889_EVIDENCE_INDEX.csv", evidence_rows, list(FileEvidence.__dataclass_fields__.keys()))
    (out / "TITAN_V889_REPORT.json").write_text(json.dumps({"summary": summary, "files": evidence_rows, "findings": findings_rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_txt_report(out / "TITAN_V889_EXECUTIVE_REPORT.txt", summary, findings)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nOutput: {out}")

    if args.strict and summary["overall_status"] in {"EXECUTION_BLOCK", "MANUAL_BLOCK"}:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
