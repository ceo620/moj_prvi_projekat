#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_SETUP_STRUCTURE.py

TITAN 11 - Enterprise Folder Bootstrap v3.0
Purpose:
    Creates the canonical TITAN_11 project folder structure, starter files,
    manifest, audit log, and export directories.

Design principles:
    - Idempotent: safe to run multiple times.
    - Windows-friendly: supports C:\\Users\\... paths and relative paths.
    - Audit-grade: writes bootstrap_manifest.json and bootstrap_audit_log.jsonl.
    - SSOT-aligned: prepares folders for config, data, exports, logs, docs,
      tests, orchestration, kernel, VDR governance and investor outputs.

Usage:
    python 00_SETUP_STRUCTURE.py
    python 00_SETUP_STRUCTURE.py --base-dir "C:\\Users\\Lenovo\\Desktop\\TITAN_11"
    python 00_SETUP_STRUCTURE.py --base-dir ./TITAN_11 --force-starter-files
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


SCRIPT_NAME = "00_SETUP_STRUCTURE.py"
SCRIPT_VERSION = "3.0"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"
DEFAULT_ROOT = "TITAN_11"


CANONICAL_DIRECTORIES = [
    # Core source package
    "src",
    "src/titan11",
    "src/titan11/config",
    "src/titan11/core",
    "src/titan11/extractors",
    "src/titan11/intelligence",
    "src/titan11/engines",
    "src/titan11/exporters",
    "src/titan11/utils",

    # Scripts by phase
    "scripts",
    "scripts/00_bootstrap",
    "scripts/01_config",
    "scripts/02_database",
    "scripts/03_ingestion",
    "scripts/04_orchestration",
    "scripts/05_signals",
    "scripts/06_kernel",
    "scripts/07_ssot",
    "scripts/08_decision",
    "scripts/09_reporting",

    # Configuration
    "config",
    "config/env",
    "config/schemas",
    "config/rules",

    # Data lake
    "data",
    "data/00_raw",
    "data/01_inbox",
    "data/02_processed",
    "data/03_quarantine",
    "data/04_temp",
    "data/05_reference",

    # Database and runtime
    "database",
    "database/sqlite",
    "database/migrations",
    "runtime",
    "runtime/queue",
    "runtime/state",
    "runtime/locks",

    # Kernel and decision intelligence
    "kernel",
    "kernel/decision_reports",
    "kernel/document_signals",
    "kernel/status_monitor",
    "kernel/daily_radar",
    "kernel/logs",
    "kernel/runtime_state",

    # SSOT / governance
    "ssot",
    "ssot/master_index",
    "ssot/signal_registry",
    "ssot/conflict_resolution",
    "ssot/audit_trail",

    # VDR and lender package
    "vdr",
    "vdr/01_governance",
    "vdr/02_legal",
    "vdr/03_financial",
    "vdr/04_technical",
    "vdr/05_esg",
    "vdr/06_procurement",
    "vdr/07_risk",
    "vdr/08_investor_pack",

    # Exports
    "exports",
    "exports/excel",
    "exports/word",
    "exports/pdf",
    "exports/summary",
    "exports/json",
    "exports/csv",
    "exports/investor_book",
    "exports/eib_ebrd",

    # Logs, docs, tests
    "logs",
    "logs/audit",
    "logs/runtime",
    "logs/errors",
    "docs",
    "docs/architecture",
    "docs/operating_manual",
    "docs/compliance",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",

    # CI / packaging
    ".github",
    ".github/workflows",
]


STARTER_FILES: Dict[str, str] = {
    "README.md": """# TITAN 11 Enterprise Decision Intelligence Platform

## Purpose
TITAN 11 is a local-first, audit-grade document, SSOT and decision intelligence platform for institutional project finance, EIB/EBRD preparation and internal governance.

## Canonical pipeline
00_SETUP_STRUCTURE.py
01_config_init.py
02_DATABASE_INIT.py
03_ingestion / V31 producer
V29 queue consumer
signal extraction
forensic engine
kernel
SSOT / control tower
decision engine

## Operating principle
The system separates:
- raw evidence
- processed state
- SSOT truth layer
- decision intelligence
- investor/lender reporting

## Audit policy
Every production script should write logs, deterministic outputs and reproducible metadata.
""",

    ".env.example": """# TITAN 11 environment template
TITAN_ENV=development
TITAN_PROJECT_NAME=TITAN_11
TITAN_DB_PATH=./database/sqlite/titan_state.db
TITAN_LOG_LEVEL=INFO
TITAN_INPUT_DIR=./data/01_inbox
TITAN_EXPORT_DIR=./exports
TITAN_SSOT_DIR=./ssot
TITAN_KERNEL_DIR=./kernel
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.venv/
venv/
env/

# OS / editors
.DS_Store
Thumbs.db
.vscode/
.idea/

# Runtime / logs / databases
*.log
logs/runtime/*
logs/errors/*
runtime/queue/*
runtime/state/*
runtime/locks/*
*.db
*.sqlite
*.sqlite3
*.db-wal
*.db-shm

# Generated exports
exports/excel/*
exports/word/*
exports/pdf/*
exports/json/*
exports/csv/*
exports/summary/*
exports/investor_book/*
exports/eib_ebrd/*

# Keep folder placeholders
!.gitkeep
""",

    "pyproject.toml": """[project]
name = "titan11"
version = "0.1.0"
description = "TITAN 11 Enterprise Decision Intelligence Platform"
requires-python = ">=3.10"

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
""",

    "requirements.txt": """pandas>=2.0.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
""",

    "src/titan11/__init__.py": '"""TITAN 11 core package."""\n__version__ = "0.1.0"\n',

    "src/titan11/config/__init__.py": '"""Configuration layer."""\n',
    "src/titan11/core/__init__.py": '"""Core system layer."""\n',
    "src/titan11/extractors/__init__.py": '"""Document extraction layer."""\n',
    "src/titan11/intelligence/__init__.py": '"""Signal and intelligence layer."""\n',
    "src/titan11/engines/__init__.py": '"""Decision and forensic engines."""\n',
    "src/titan11/exporters/__init__.py": '"""Export layer."""\n',
    "src/titan11/utils/__init__.py": '"""Utility layer."""\n',

    "docs/architecture/TITAN_11_ARCHITECTURE.md": """# TITAN 11 Architecture

## Layers
1. Bootstrap
2. Configuration
3. Database
4. Ingestion
5. Queue orchestration
6. Signal extraction
7. Forensic validation
8. Kernel
9. SSOT
10. Decision intelligence
11. Investor / lender reporting
""",

    ".github/workflows/ci.yml": """name: TITAN 11 CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  basic-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Compile Python files
        run: python -m compileall .
""",
}


@dataclass
class BootstrapEvent:
    timestamp_utc: str
    event_type: str
    path: str
    status: str
    details: str


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def resolve_base_dir(base_dir: Optional[str]) -> Path:
    if base_dir:
        return Path(base_dir).expanduser().resolve()
    return Path.cwd().joinpath(DEFAULT_ROOT).resolve()


def write_text_file(path: Path, content: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return "skipped_existing"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created_or_overwritten"


def create_gitkeep_files(base_dir: Path) -> List[BootstrapEvent]:
    events: List[BootstrapEvent] = []
    for directory in CANONICAL_DIRECTORIES:
        dpath = base_dir / directory
        gitkeep = dpath / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
            status = "created"
        else:
            status = "exists"
        events.append(
            BootstrapEvent(
                timestamp_utc=utc_now(),
                event_type="gitkeep",
                path=str(gitkeep),
                status=status,
                details="Folder placeholder file.",
            )
        )
    return events


def create_directories(base_dir: Path) -> List[BootstrapEvent]:
    events: List[BootstrapEvent] = []
    base_dir.mkdir(parents=True, exist_ok=True)

    for directory in CANONICAL_DIRECTORIES:
        path = base_dir / directory
        existed = path.exists()
        path.mkdir(parents=True, exist_ok=True)

        events.append(
            BootstrapEvent(
                timestamp_utc=utc_now(),
                event_type="directory",
                path=str(path),
                status="exists" if existed else "created",
                details="Canonical TITAN directory.",
            )
        )

    return events


def create_starter_files(base_dir: Path, overwrite: bool) -> List[BootstrapEvent]:
    events: List[BootstrapEvent] = []

    for relative_path, content in STARTER_FILES.items():
        path = base_dir / relative_path
        status = write_text_file(path, content, overwrite=overwrite)
        events.append(
            BootstrapEvent(
                timestamp_utc=utc_now(),
                event_type="starter_file",
                path=str(path),
                status=status,
                details="Starter file generated by bootstrap.",
            )
        )

    return events


def build_manifest(base_dir: Path, events: List[BootstrapEvent]) -> Dict[str, object]:
    created_dirs = sum(1 for e in events if e.event_type == "directory" and e.status == "created")
    existing_dirs = sum(1 for e in events if e.event_type == "directory" and e.status == "exists")
    created_files = sum(
        1 for e in events
        if e.event_type in {"starter_file", "gitkeep"} and e.status in {"created", "created_or_overwritten"}
    )

    return {
        "system_name": SYSTEM_NAME,
        "script_name": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "schema": "TITAN_BOOTSTRAP_MANIFEST_v3",
        "generated_at_utc": utc_now(),
        "base_dir": str(base_dir),
        "python_version": sys.version,
        "platform": platform.platform(),
        "user": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown",
        "summary": {
            "canonical_directory_count": len(CANONICAL_DIRECTORIES),
            "starter_file_count": len(STARTER_FILES),
            "created_directories": created_dirs,
            "existing_directories": existing_dirs,
            "created_or_overwritten_files": created_files,
            "event_count": len(events),
        },
        "canonical_directories": CANONICAL_DIRECTORIES,
        "starter_files": sorted(STARTER_FILES.keys()),
        "next_scripts": [
            "01_config_init.py",
            "02_DATABASE_INIT.py",
            "TITAN_DECISION_ENGINE_v1.py",
        ],
    }


def write_audit_outputs(base_dir: Path, events: List[BootstrapEvent], manifest: Dict[str, object]) -> None:
    audit_dir = base_dir / "logs" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = base_dir / "bootstrap_manifest.json"
    audit_jsonl_path = audit_dir / "bootstrap_audit_log.jsonl"

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    with audit_jsonl_path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def bootstrap(base_dir: Path, force_starter_files: bool = False, no_gitkeep: bool = False) -> Dict[str, object]:
    logging.info("TITAN bootstrap started")
    logging.info("Base directory: %s", base_dir)

    events: List[BootstrapEvent] = []
    events.extend(create_directories(base_dir))
    events.extend(create_starter_files(base_dir, overwrite=force_starter_files))

    if not no_gitkeep:
        events.extend(create_gitkeep_files(base_dir))

    manifest = build_manifest(base_dir, events)
    write_audit_outputs(base_dir, events, manifest)

    logging.info("Bootstrap completed")
    logging.info("Manifest: %s", base_dir / "bootstrap_manifest.json")
    logging.info("Audit log: %s", base_dir / "logs" / "audit" / "bootstrap_audit_log.jsonl")

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN 11 enterprise folder structure bootstrap."
    )
    parser.add_argument(
        "--base-dir",
        default=None,
        help=f"Target base directory. Default: ./{DEFAULT_ROOT}",
    )
    parser.add_argument(
        "--force-starter-files",
        action="store_true",
        help="Overwrite starter files if they already exist.",
    )
    parser.add_argument(
        "--no-gitkeep",
        action="store_true",
        help="Do not create .gitkeep files in empty directories.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(verbose=args.verbose)

    try:
        base_dir = resolve_base_dir(args.base_dir)
        manifest = bootstrap(
            base_dir=base_dir,
            force_starter_files=args.force_starter_files,
            no_gitkeep=args.no_gitkeep,
        )
        print(json.dumps(manifest["summary"], indent=2, ensure_ascii=False))
        print(f"\nTITAN bootstrap exported successfully: {base_dir}")
        return 0
    except Exception as exc:
        logging.exception("Bootstrap failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
