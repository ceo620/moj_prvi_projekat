#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
23_master_orchestrator.py

TITAN GRID / TITAN 11
MASTER REASONING ORCHESTRATOR

Runs engines 16-22 over C:\\DANIJELA and creates one master report.

Pipeline:
    16_document_coverage_engine.py
    17_semantic_role_engine.py
    18_entity_extraction_engine.py
    19_relation_mapping_engine.py
    20_importance_engine.py
    21_logic_integrity_engine.py
    22_logic_model_reconstructor.py

Outputs:
    C:\\DANIJELA\\_TITAN_MASTER_REASONING_REPORT
        - MASTER_REASONING_REPORT.json
        - MASTER_REASONING_REPORT.txt
        - master_orchestrator.log
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "1.0.0-TITAN-MASTER-REASONING-ORCHESTRATOR-LOCKED"

DEFAULT_ROOT = Path(r"C:\DANIJELA")
DEFAULT_OUTPUT_DIR = Path(r"C:\DANIJELA\_TITAN_MASTER_REASONING_REPORT")


PIPELINE = [
    {
        "id": "16",
        "name": "Document Coverage Engine",
        "script": "16_document_coverage_engine.py",
        "expected_output": r"_TITAN_COVERAGE_AUDIT\coverage_summary.json",
    },
    {
        "id": "17",
        "name": "Semantic Role Engine",
        "script": "17_semantic_role_engine.py",
        "expected_output": r"_TITAN_SEMANTIC_AUDIT\semantic_roles_manifest.json",
    },
    {
        "id": "18",
        "name": "Entity Extraction Engine",
        "script": "18_entity_extraction_engine.py",
        "expected_output": r"_TITAN_ENTITY_AUDIT\entity_manifest.json",
    },
    {
        "id": "19",
        "name": "Relation Mapping Engine",
        "script": "19_relation_mapping_engine.py",
        "expected_output": r"_TITAN_RELATION_AUDIT\relation_manifest.json",
    },
    {
        "id": "20",
        "name": "Importance Engine",
        "script": "20_importance_engine.py",
        "expected_output": r"_TITAN_IMPORTANCE_AUDIT\importance_manifest.json",
    },
    {
        "id": "21",
        "name": "Logic Integrity Engine",
        "script": "21_logic_integrity_engine.py",
        "expected_output": r"_TITAN_LOGIC_INTEGRITY_AUDIT\logic_integrity_manifest.json",
    },
    {
        "id": "22",
        "name": "Logic Model Reconstructor",
        "script": "22_logic_model_reconstructor.py",
        "expected_output": r"_TITAN_LOGIC_MODEL\LOGIC_MODEL.json",
    },
]


@dataclass(frozen=True)
class StepResult:
    step_id: str
    step_name: str
    script_path: str
    exit_code: int
    duration_seconds: float
    status: str
    expected_output: str
    expected_output_exists: bool
    stdout_tail: str
    stderr_tail: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def tail_text(text: str, max_chars: int = 3000) -> str:
    return text[-max_chars:] if text else ""


class TitanMasterReasoningOrchestrator:
    def __init__(
        self,
        root: Path,
        kernel_dir: Path,
        output_dir: Path,
        stop_on_error: bool = True,
        verbose: bool = False,
    ) -> None:
        self.root = root.resolve()
        self.kernel_dir = kernel_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.stop_on_error = stop_on_error
        self.verbose = verbose
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.output_dir / "master_orchestrator.log"
        self.results: list[StepResult] = []

    def log(self, message: str) -> None:
        line = f"{utc_now()} | {message}"
        print(line)
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")

    def run_step(self, step: dict[str, str]) -> StepResult:
        script_path = self.kernel_dir / step["script"]
        expected_output = self.root / step["expected_output"]

        if not script_path.exists():
            result = StepResult(
                step_id=step["id"],
                step_name=step["name"],
                script_path=str(script_path),
                exit_code=127,
                duration_seconds=0.0,
                status="SCRIPT_MISSING",
                expected_output=str(expected_output),
                expected_output_exists=expected_output.exists(),
                stdout_tail="",
                stderr_tail=f"Missing script: {script_path}",
            )
            self.results.append(result)
            self.log(f"FAIL | {step['id']} | missing script | {script_path}")
            return result

        cmd = [sys.executable, str(script_path), "--root", str(self.root)]

        self.log(f"START | {step['id']} | {step['name']}")
        start = time.time()

        completed = subprocess.run(
            cmd,
            cwd=str(self.kernel_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        duration = round(time.time() - start, 3)
        output_exists = expected_output.exists()

        if completed.returncode == 0 and output_exists:
            status = "PASS"
        elif completed.returncode == 0 and not output_exists:
            status = "PASS_OUTPUT_MISSING"
        else:
            status = "FAIL"

        result = StepResult(
            step_id=step["id"],
            step_name=step["name"],
            script_path=str(script_path),
            exit_code=completed.returncode,
            duration_seconds=duration,
            status=status,
            expected_output=str(expected_output),
            expected_output_exists=output_exists,
            stdout_tail=tail_text(completed.stdout),
            stderr_tail=tail_text(completed.stderr),
        )

        self.results.append(result)
        self.log(f"{status} | {step['id']} | exit={completed.returncode} | duration={duration}s | output={output_exists}")

        return result

    def collect_summary_layers(self) -> dict[str, Any]:
        coverage = read_json(self.root / r"_TITAN_COVERAGE_AUDIT\coverage_summary.json")
        logic_model = read_json(self.root / r"_TITAN_LOGIC_MODEL\LOGIC_MODEL.json")
        return {
            "coverage_summary": coverage,
            "logic_model_available": bool(logic_model),
            "logic_model_path": str(self.root / r"_TITAN_LOGIC_MODEL\LOGIC_MODEL.json"),
        }

    def final_status(self) -> str:
        if any(r.status in {"FAIL", "SCRIPT_MISSING"} for r in self.results):
            return "FAIL"
        if any(r.status == "PASS_OUTPUT_MISSING" for r in self.results):
            return "PASS_WITH_OUTPUT_WARNINGS"
        return "PASS"

    def write_reports(self) -> dict[str, Path]:
        final_status = self.final_status()
        summary_layers = self.collect_summary_layers()

        report = {
            "engine": "23_master_orchestrator.py",
            "version": VERSION,
            "generated_utc": utc_now(),
            "root": str(self.root),
            "kernel_dir": str(self.kernel_dir),
            "status": final_status,
            "steps_total": len(self.results),
            "steps_passed": sum(1 for r in self.results if r.status == "PASS"),
            "steps_failed": sum(1 for r in self.results if r.status in {"FAIL", "SCRIPT_MISSING"}),
            "steps_warnings": sum(1 for r in self.results if r.status == "PASS_OUTPUT_MISSING"),
            "results": [asdict(r) for r in self.results],
            "summary_layers": summary_layers,
        }
        report["master_report_hash"] = sha256_text(json.dumps(report, ensure_ascii=False, sort_keys=True))

        json_path = self.output_dir / "MASTER_REASONING_REPORT.json"
        txt_path = self.output_dir / "MASTER_REASONING_REPORT.txt"

        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            "=" * 100,
            "TITAN MASTER REASONING ORCHESTRATOR REPORT",
            "=" * 100,
            f"VERSION: {VERSION}",
            f"STATUS: {final_status}",
            f"ROOT: {self.root}",
            f"STEPS TOTAL: {report['steps_total']}",
            f"PASSED: {report['steps_passed']}",
            f"FAILED: {report['steps_failed']}",
            f"WARNINGS: {report['steps_warnings']}",
            f"HASH: {report['master_report_hash']}",
            "-" * 100,
        ]

        for result in self.results:
            lines.append(
                f"{result.step_id} | {result.status} | {result.step_name} | "
                f"exit={result.exit_code} | {result.duration_seconds}s | output={result.expected_output_exists}"
            )

        lines.extend(["-" * 100, f"LOGIC MODEL: {summary_layers.get('logic_model_path')}", "=" * 100])
        txt_path.write_text("\n".join(lines), encoding="utf-8")

        return {"json": json_path, "txt": txt_path}

    def run(self) -> int:
        if not self.root.exists():
            raise FileNotFoundError(f"Root not found: {self.root}")

        self.log(f"MASTER_START | version={VERSION} | root={self.root} | kernel_dir={self.kernel_dir}")

        for step in PIPELINE:
            result = self.run_step(step)
            if self.stop_on_error and result.status in {"FAIL", "SCRIPT_MISSING"}:
                self.log(f"STOP_ON_ERROR | step={result.step_id}")
                break

        outputs = self.write_reports()

        print("=" * 100)
        print("TITAN MASTER REASONING ORCHESTRATOR COMPLETE")
        print("=" * 100)
        print("VERSION:", VERSION)
        print("STATUS:", self.final_status())
        print("ROOT:", self.root)
        print("REPORT JSON:", outputs["json"])
        print("REPORT TXT:", outputs["txt"])
        print("LOG:", self.log_path)
        print("=" * 100)

        return 0 if self.final_status() in {"PASS", "PASS_WITH_OUTPUT_WARNINGS"} else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TITAN reasoning engines 16-22 as one orchestrated pipeline.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--kernel-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    orchestrator = TitanMasterReasoningOrchestrator(
        root=args.root,
        kernel_dir=args.kernel_dir,
        output_dir=args.output_dir,
        stop_on_error=not args.continue_on_error,
        verbose=args.verbose,
    )
    return orchestrator.run()


if __name__ == "__main__":
    raise SystemExit(main())
