# TITAN_NEW_FORENSIC_CHECK_888.py
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# MODE: READ_ONLY | REPORT_ONLY | ZERO_TRUST | NO_NETWORK | NO_EXECUTION_OF_TARGETS

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SYSTEM_STATUS = "SYSTEM RED — STEP102 LOCKED — NO FINAL USE"

SCRIPT_EXTENSIONS = {".py", ".ps1", ".sh", ".bat", ".cmd", ".js", ".mjs", ".vbs"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".ps1", ".py", ".js", ".mjs", ".sh", ".bat", ".cmd", ".vbs"}

UNSAFE_WORDING = [
    "lender-ready", "bankable", "approved", "confirmed", "validated",
    "fully aligned", "eligible asset", "grant secured", "financing secured",
    "ready-to-go", "guaranteed", "final", "no risk", "step102 accepted",
    "creditor-ready", "sovereign authority confirmed", "43.5m eur validated",
    "final_use_allowed yes",
]

RISK_PATTERNS = {
    "destructive_delete": [
        r"\bRemove-Item\b", r"\brm\s+", r"\bdel\s+", r"\bunlink\s*\(",
        r"\bshutil\.rmtree\s*\(", r"\bos\.remove\s*\(", r"\bos\.unlink\s*\(",
    ],
    "move_or_rename": [
        r"\bMove-Item\b", r"\bRename-Item\b", r"\bmv\s+", r"\bos\.rename\s*\(",
        r"\bshutil\.move\s*\(", r"\bos\.replace\s*\(",
    ],
    "network_or_upload": [
        r"\bInvoke-WebRequest\b", r"\bInvoke-RestMethod\b", r"\bcurl\b", r"\bwget\b",
        r"\brequests\.", r"\burllib\.", r"\bhttpx\.", r"\bftp\b", r"\bscp\b",
        r"\bupload\b", r"\bsubmit\b",
    ],
    "telegram_or_bot": [
        r"telegram", r"bot_token", r"chat_id", r"sendMessage", r"api\.telegram\.org",
    ],
    "credential_risk": [
        r"token", r"secret", r"password", r"passwd", r"credential", r"private[_-]?key",
        r"api[_-]?key", r"client_secret",
    ],
    "office_macro_or_com": [
        r"win32com", r"Dispatch\(", r"\.xlsm\b", r"VBProject", r"macro",
    ],
    "shell_execution": [
        r"subprocess\.", r"os\.system\s*\(", r"Start-Process", r"ShellExecute",
        r"child_process", r"exec\s*\(", r"eval\s*\(",
    ],
    "scheduled_or_registry": [
        r"Register-ScheduledTask", r"schtasks", r"New-ItemProperty", r"Set-ItemProperty",
        r"HKCU:", r"HKLM:",
    ],
    "v888_gold_sovereign_contamination": [
        r"\bV888\b", r"\bGOLD\b", r"\bSOVEREIGN\b", r"ARS_METAL_GOLDEN_VAULT",
        r"OPERACIJA_REGISTRATOR",
    ],
}


@dataclass
class FileRecord:
    file_path: str
    relative_path: str
    extension: str
    size_bytes: int
    sha256: str
    is_script: str
    unsafe_wording_flag: str
    risk_categories: str
    safe_to_execute_now: str
    final_use_allowed: str
    classification: str


@dataclass
class Finding:
    file_path: str
    line_number: int
    category: str
    snippet: str
    severity: str
    final_use_allowed: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "UNVERIFIED_NO_ACCESS"


def safe_read_lines(path: Path, max_bytes: int = 2_000_000) -> list[str]:
    try:
        if path.stat().st_size > max_bytes:
            return []
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def classify_script(risk_categories: set[str]) -> str:
    if not risk_categories:
        return "SAFE_READONLY_CANDIDATE"
    if "destructive_delete" in risk_categories or "move_or_rename" in risk_categories:
        return "DO_NOT_EXECUTE_DESTRUCTIVE_RISK"
    if "network_or_upload" in risk_categories or "telegram_or_bot" in risk_categories:
        return "DO_NOT_EXECUTE_NETWORK_OR_UPLOAD_RISK"
    if "credential_risk" in risk_categories:
        return "DO_NOT_EXECUTE_CREDENTIAL_RISK"
    if "v888_gold_sovereign_contamination" in risk_categories:
        return "DO_NOT_EXECUTE_QUARANTINE_RISK"
    return "NEEDS_HUMAN_REVIEW_BEFORE_EXECUTION"


def scan_file(path: Path, root: Path) -> tuple[FileRecord, list[Finding]]:
    rel = str(path.relative_to(root))
    ext = path.suffix.lower()
    size = path.stat().st_size
    digest = sha256_file(path)
    is_script = "YES" if ext in SCRIPT_EXTENSIONS else "NO"

    findings: list[Finding] = []
    risk_categories: set[str] = set()
    unsafe_flag = "NO"

    if ext in TEXT_EXTENSIONS:
        lines = safe_read_lines(path)
        for idx, line in enumerate(lines, start=1):
            low = line.lower()

            for word in UNSAFE_WORDING:
                if word in low:
                    unsafe_flag = "YES"
                    findings.append(Finding(str(path), idx, "unsafe_wording", line.strip()[:240], "REVIEW_REQUIRED", "NO"))

            for category, patterns in RISK_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, line, flags=re.IGNORECASE):
                        risk_categories.add(category)
                        findings.append(Finding(str(path), idx, category, line.strip()[:240], "REVIEW_REQUIRED", "NO"))
                        break

    classification = classify_script(risk_categories) if is_script == "YES" else (
        "DO_NOT_USE_QUARANTINE" if unsafe_flag == "YES" else "SAFE_TO_KEEP_REPORT_ONLY"
    )

    record = FileRecord(
        file_path=str(path),
        relative_path=rel,
        extension=ext,
        size_bytes=size,
        sha256=digest,
        is_script=is_script,
        unsafe_wording_flag=unsafe_flag,
        risk_categories="|".join(sorted(risk_categories)) if risk_categories else "NONE",
        safe_to_execute_now="NO",
        final_use_allowed="NO",
        classification=classification,
    )

    return record, findings


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python TITAN_NEW_FORENSIC_CHECK_888.py <ROOT_TO_SCAN>")
        return 2

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"ERROR: root not found: {root}")
        return 2

    out = root / "TITAN_NEW_FORENSIC_CHECK_888_OUTPUT"
    out.mkdir(parents=True, exist_ok=True)

    records: list[FileRecord] = []
    findings: list[Finding] = []
    errors: list[dict] = []

    for path in root.rglob("*"):
        try:
            if not path.is_file():
                continue
            if out in path.parents:
                continue
            record, file_findings = scan_file(path, root)
            records.append(record)
            findings.extend(file_findings)
        except Exception as exc:
            errors.append({"path": str(path), "error": repr(exc), "final_use_allowed": "NO"})

    script_records = [r for r in records if r.is_script == "YES"]
    do_not_execute = [r for r in script_records if r.classification.startswith("DO_NOT_EXECUTE")]
    review_scripts = [r for r in script_records if r.classification == "NEEDS_HUMAN_REVIEW_BEFORE_EXECUTION"]

    write_csv(out / "TITAN_NEW_FORENSIC_FILE_REGISTER.csv", [asdict(r) for r in records], list(FileRecord.__dataclass_fields__.keys()))
    write_csv(out / "TITAN_NEW_FORENSIC_FINDINGS.csv", [asdict(f) for f in findings], list(Finding.__dataclass_fields__.keys()))
    write_csv(out / "TITAN_NEW_FORENSIC_SCRIPT_DO_NOT_EXECUTE.csv", [asdict(r) for r in do_not_execute], list(FileRecord.__dataclass_fields__.keys()))
    write_csv(out / "TITAN_NEW_FORENSIC_SCRIPT_REVIEW_REQUIRED.csv", [asdict(r) for r in review_scripts], list(FileRecord.__dataclass_fields__.keys()))
    write_csv(out / "TITAN_NEW_FORENSIC_ERROR_LOG.csv", errors, ["path", "error", "final_use_allowed"])

    summary = {
        "scanner": "TITAN_NEW_FORENSIC_CHECK_888",
        "created_utc": utc_now(),
        "root": str(root),
        "system_status": SYSTEM_STATUS,
        "mode": "READ_ONLY_REPORT_ONLY_ZERO_TRUST",
        "source_files_modified": "NO",
        "files_moved_deleted_renamed": "NO",
        "network_used": "NO",
        "telegram_send": "NO",
        "safe_to_execute_now_count": 0,
        "final_use_allowed_yes_count": 0,
        "total_files": len(records),
        "total_scripts": len(script_records),
        "scripts_do_not_execute": len(do_not_execute),
        "scripts_need_review": len(review_scripts),
        "total_findings": len(findings),
        "unsafe_wording_files": sum(1 for r in records if r.unsafe_wording_flag == "YES"),
        "error_count": len(errors),
        "final_verdict": "TITAN_NEW_FORENSIC_CHECK_888_REVIEW_REQUIRED",
        "final_status": SYSTEM_STATUS,
    }

    (out / "TITAN_NEW_FORENSIC_SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest_path = out / "TITAN_NEW_FORENSIC_HASH_MANIFEST.txt"
    lines = [
        "# TITAN NEW FORENSIC CHECK 888 HASH MANIFEST",
        f"# CREATED_UTC: {summary['created_utc']}",
        f"# STATUS: {SYSTEM_STATUS}",
        "",
    ]
    for f in sorted(out.iterdir()):
        if f.is_file() and f.name != manifest_path.name:
            lines.append(f"{sha256_file(f)} | {f.name}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nOutput: {out}")
    print(SYSTEM_STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
