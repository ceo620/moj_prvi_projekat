#!/usr/bin/env python3
"""
TITAN 1 — 00 GUARDIAN V2
Sequential script orchestrator for TITAN_KERNEL.

Purpose:
- Run all numbered Python scripts in order from a single safe entrypoint.
- Capture stdout/stderr, return codes, durations, and SHA-256 script fingerprints.
- Write machine-readable JSON and human-readable LOG run reports.
- Set TITAN_KERNEL_ROOT for child scripts.
- Stop on first failure by default.

Usage:
    python 00_guardian_v2.py
    python 00_guardian_v2.py --scripts-dir /path/to/SCRIPTS --kernel-root /path/to/TITAN_KERNEL
    python 00_guardian_v2.py --dry-run
    python 00_guardian_v2.py --continue-on-failure
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


GUARDIAN_VERSION = "v2.0"
DEFAULT_SKIP_PATTERNS = (
    r"^00[_\s-]*guardian.*\.py$",
    r".*launcher.*\.py$",
    r".*test.*\.py$",
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()
    except Exception:
        return None


def natural_script_key(path: Path) -> Tuple[int, str]:
    """
    Sort scripts by leading number first, then name.
    Examples:
      00_guardian_v2.py -> 0
      21_vdr_index_engine.py -> 21
      alpha.py -> 999999
    """
    m = re.match(r"^\s*(\d+)", path.name)
    prefix = int(m.group(1)) if m else 999999
    return (prefix, path.name.lower())


def should_skip(path: Path, skip_regexes: Tuple[str, ...]) -> bool:
    lowered = path.name.lower()
    for pattern in skip_regexes:
        if re.match(pattern, lowered, flags=re.IGNORECASE):
            return True
    return False


def discover_scripts(scripts_dir: Path, skip_regexes: Tuple[str, ...]) -> List[Path]:
    scripts = []
    for path in scripts_dir.glob("*.py"):
        if path.is_file() and not should_skip(path, skip_regexes):
            scripts.append(path)
    return sorted(scripts, key=natural_script_key)


def run_child_script(script: Path, kernel_root: Path, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["TITAN_KERNEL_ROOT"] = str(kernel_root)
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [sys.executable, str(script)]
    result: Dict[str, Any] = {
        "script": script.name,
        "script_path": str(script),
        "sha256": sha256_file(script),
        "started_at": now_iso(),
        "command": cmd,
        "returncode": None,
        "duration_seconds": None,
        "stdout": "",
        "stderr": "",
        "status": "UNKNOWN",
    }

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(script.parent),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["status"] = "PASSED" if proc.returncode == 0 else "FAILED"
    except subprocess.TimeoutExpired as exc:
        result["returncode"] = None
        result["stdout"] = exc.stdout or ""
        result["stderr"] = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds} seconds"
        result["status"] = "TIMEOUT"
    except Exception as exc:
        result["returncode"] = None
        result["stderr"] = repr(exc)
        result["status"] = "ERROR"
    finally:
        result["duration_seconds"] = round(time.perf_counter() - started, 3)
        result["finished_at"] = now_iso()

    return result


def write_reports(report_dir: Path, report: Dict[str, Any]) -> Tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = report_dir / f"guardian_v2_run_{stamp}.json"
    log_path = report_dir / f"guardian_v2_run_{stamp}.log"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("=" * 88)
    lines.append(f"TITAN 1 — 00 GUARDIAN V2 RUN REPORT")
    lines.append(f"Generated: {report['run_metadata']['finished_at']}")
    lines.append(f"Overall status: {report['summary']['overall_status']}")
    lines.append(f"Scripts discovered: {report['summary']['scripts_discovered']}")
    lines.append(f"Scripts executed: {report['summary']['scripts_executed']}")
    lines.append(f"Passed: {report['summary']['passed']} | Failed: {report['summary']['failed']} | Skipped: {report['summary']['skipped']}")
    lines.append("=" * 88)
    lines.append("")
    for item in report["scripts"]:
        lines.append("-" * 88)
        lines.append(f"SCRIPT: {item['script']}")
        lines.append(f"STATUS: {item['status']} | RETURN CODE: {item.get('returncode')} | DURATION: {item.get('duration_seconds')}s")
        lines.append(f"SHA256: {item.get('sha256')}")
        if item.get("stdout"):
            lines.append("[STDOUT]")
            lines.append(item["stdout"].rstrip())
        if item.get("stderr"):
            lines.append("[STDERR]")
            lines.append(item["stderr"].rstrip())
    lines.append("")
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, log_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="TITAN 1 — 00 Guardian V2 script orchestrator")
    parser.add_argument("--scripts-dir", default=None, help="Directory containing numbered Python scripts. Defaults to this file's directory.")
    parser.add_argument("--kernel-root", default=None, help="TITAN_KERNEL_ROOT passed to child scripts. Defaults to parent/TITAN_KERNEL.")
    parser.add_argument("--report-dir", default=None, help="Directory for Guardian run reports. Defaults to kernel-root/REPORTS/GUARDIAN.")
    parser.add_argument("--continue-on-failure", action="store_true", help="Continue running remaining scripts after a failure.")
    parser.add_argument("--dry-run", action="store_true", help="Discover and report scripts without executing them.")
    parser.add_argument("--timeout-seconds", type=int, default=300, help="Per-script timeout in seconds.")
    args = parser.parse_args(argv)

    this_file = Path(__file__).resolve()
    scripts_dir = Path(args.scripts_dir).resolve() if args.scripts_dir else this_file.parent
    kernel_root = Path(args.kernel_root).resolve() if args.kernel_root else scripts_dir.parent / "TITAN_KERNEL"
    report_dir = Path(args.report_dir).resolve() if args.report_dir else kernel_root / "REPORTS" / "GUARDIAN"

    skip_regexes = DEFAULT_SKIP_PATTERNS
    scripts = discover_scripts(scripts_dir, skip_regexes)

    report: Dict[str, Any] = {
        "run_metadata": {
            "guardian_version": GUARDIAN_VERSION,
            "started_at": now_iso(),
            "scripts_dir": str(scripts_dir),
            "kernel_root": str(kernel_root),
            "report_dir": str(report_dir),
            "dry_run": args.dry_run,
            "continue_on_failure": args.continue_on_failure,
            "timeout_seconds": args.timeout_seconds,
            "python_executable": sys.executable,
        },
        "summary": {
            "overall_status": "UNKNOWN",
            "scripts_discovered": len(scripts),
            "scripts_executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        },
        "scripts": [],
    }

    print("=" * 88)
    print("TITAN 1 — 00 GUARDIAN V2")
    print("=" * 88)
    print(f"[i] scripts_dir     : {scripts_dir}")
    print(f"[i] kernel_root     : {kernel_root}")
    print(f"[i] scripts found   : {len(scripts)}")

    if args.dry_run:
        for script in scripts:
            report["scripts"].append({
                "script": script.name,
                "script_path": str(script),
                "sha256": sha256_file(script),
                "status": "DRY_RUN_ONLY",
            })
            print(f"[dry-run] {script.name}")
        report["summary"]["skipped"] = len(scripts)
        report["summary"]["overall_status"] = "DRY_RUN"
    else:
        kernel_root.mkdir(parents=True, exist_ok=True)
        for script in scripts:
            print(f"[→] running {script.name}")
            result = run_child_script(script, kernel_root, args.timeout_seconds)
            report["scripts"].append(result)
            report["summary"]["scripts_executed"] += 1

            if result["status"] == "PASSED":
                report["summary"]["passed"] += 1
                print(f"[✓] {script.name}")
            else:
                report["summary"]["failed"] += 1
                print(f"[x] {script.name} :: {result['status']}")
                if not args.continue_on_failure:
                    remaining = len(scripts) - report["summary"]["scripts_executed"]
                    report["summary"]["skipped"] += remaining
                    print(f"[!] stopping on first failure; skipped remaining scripts: {remaining}")
                    break

        report["summary"]["overall_status"] = "PASSED" if report["summary"]["failed"] == 0 else "FAILED"

    report["run_metadata"]["finished_at"] = now_iso()
    json_path, log_path = write_reports(report_dir, report)
    print("=" * 88)
    print(f"[✓] Guardian JSON report: {json_path}")
    print(f"[✓] Guardian LOG report : {log_path}")
    print(f"[★] Overall status      : {report['summary']['overall_status']}")
    print("=" * 88)

    return 0 if report["summary"]["overall_status"] in ("PASSED", "DRY_RUN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
