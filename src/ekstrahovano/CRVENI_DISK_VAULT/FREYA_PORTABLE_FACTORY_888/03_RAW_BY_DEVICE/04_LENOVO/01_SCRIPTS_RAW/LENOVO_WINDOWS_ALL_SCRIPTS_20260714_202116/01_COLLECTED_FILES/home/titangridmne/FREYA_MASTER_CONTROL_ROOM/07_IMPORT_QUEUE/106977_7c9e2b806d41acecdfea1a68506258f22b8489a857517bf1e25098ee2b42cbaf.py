#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_config_init.py

TITAN 11 - Configuration Initializer v3.0 EXPORT
Purpose:
    Initializes the TITAN 11 configuration layer after folder bootstrap.

Creates / updates:
    - .env
    - .env.example if missing
    - config/titan_config.json
    - config/schemas/titan_config_schema_snapshot.json
    - src/titan11/config.py
    - logs/audit/config_init_audit_log.jsonl
    - config/config_init_manifest.json

Design principles:
    - Idempotent: safe to run multiple times.
    - Conservative: does not overwrite existing .env unless --force-env is used.
    - SSOT-aligned: titan_config.json is treated as the primary configuration truth.
    - Audit-grade: deterministic outputs, manifest and JSONL audit trail.

Usage:
    python 01_config_init.py
    python 01_config_init.py --base-dir "C:\\Users\\Lenovo\\Desktop\\TITAN_11"
    python 01_config_init.py --base-dir ./TITAN_11 --force-env --force-config
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
from typing import Any, Dict, List, Optional


SCRIPT_NAME = "01_config_init.py"
SCRIPT_VERSION = "3.0"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"
CONFIG_SCHEMA_VERSION = "TITAN_CONFIG_SCHEMA_v3"
DEFAULT_ROOT = "TITAN_11"


PIPELINE_PHASES = [
    {
        "order": 0,
        "script": "00_SETUP_STRUCTURE.py",
        "phase": "BOOTSTRAP",
        "purpose": "Create canonical folder system and starter files.",
        "criticality": "CRITICAL",
        "status": "EXPECTED_COMPLETED",
    },
    {
        "order": 1,
        "script": "01_config_init.py",
        "phase": "CONFIGURATION",
        "purpose": "Create environment variables, JSON config and runtime settings module.",
        "criticality": "CRITICAL",
        "status": "CURRENT",
    },
    {
        "order": 2,
        "script": "02_DATABASE_INIT.py",
        "phase": "DATABASE",
        "purpose": "Initialize SQLite database, schema, indices and metadata.",
        "criticality": "CRITICAL",
        "status": "NEXT",
    },
    {
        "order": 3,
        "script": "01_TITAN_ELITE_RECONSTRUCTOR.py",
        "phase": "RECONSTRUCTION",
        "purpose": "Scan source documents and prepare normalized document index.",
        "criticality": "HIGH",
        "status": "PLANNED",
    },
    {
        "order": 4,
        "script": "03_v31_producer.py",
        "phase": "QUEUE_PRODUCTION",
        "purpose": "Produce queue.jsonl for controlled ingestion.",
        "criticality": "HIGH",
        "status": "PLANNED",
    },
    {
        "order": 5,
        "script": "03_v29_queue_consumer.py",
        "phase": "QUEUE_CONSUMPTION",
        "purpose": "Consume queue and persist document state to SQLite.",
        "criticality": "HIGH",
        "status": "PLANNED",
    },
    {
        "order": 6,
        "script": "14_check_document_signals.py",
        "phase": "SIGNAL_EXTRACTION",
        "purpose": "Extract document-level intelligence signals.",
        "criticality": "HIGH",
        "status": "PLANNED",
    },
    {
        "order": 7,
        "script": "TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py",
        "phase": "FORENSIC_VALIDATION",
        "purpose": "Validate, classify and audit critical project evidence.",
        "criticality": "HIGH",
        "status": "PLANNED",
    },
    {
        "order": 8,
        "script": "05_kernel_decision_engine.py",
        "phase": "KERNEL_DECISION",
        "purpose": "Apply operational kernel decision rules.",
        "criticality": "HIGH",
        "status": "PLANNED",
    },
    {
        "order": 9,
        "script": "08_sync_sqlite_to_existing_control_tower.py",
        "phase": "CONTROL_TOWER_SYNC",
        "purpose": "Sync SQLite state into Control Tower Excel.",
        "criticality": "MEDIUM",
        "status": "PLANNED",
    },
    {
        "order": 10,
        "script": "10_control_tower_refresh_v1.py",
        "phase": "CONTROL_TOWER_REFRESH",
        "purpose": "Refresh formulas and reporting workbook.",
        "criticality": "MEDIUM",
        "status": "PLANNED",
    },
    {
        "order": 11,
        "script": "TITAN_DECISION_ENGINE_v1.py",
        "phase": "STRATEGIC_DECISION_INTELLIGENCE",
        "purpose": "Convert SSOT signals into decision table, risk layer, gap analysis and bankability score.",
        "criticality": "CRITICAL",
        "status": "PLANNED",
    },
]


DEFAULT_ENV_LINES = [
    ("TITAN_ENV", "development"),
    ("TITAN_PROJECT_NAME", "TITAN_11"),
    ("TITAN_SYSTEM_NAME", SYSTEM_NAME),
    ("TITAN_CONFIG_SCHEMA_VERSION", CONFIG_SCHEMA_VERSION),
    ("TITAN_DB_PATH", "./database/sqlite/titan_state.db"),
    ("TITAN_LOG_LEVEL", "INFO"),
    ("TITAN_INPUT_DIR", "./data/01_inbox"),
    ("TITAN_RAW_DIR", "./data/00_raw"),
    ("TITAN_PROCESSED_DIR", "./data/02_processed"),
    ("TITAN_QUARANTINE_DIR", "./data/03_quarantine"),
    ("TITAN_EXPORT_DIR", "./exports"),
    ("TITAN_SSOT_DIR", "./ssot"),
    ("TITAN_KERNEL_DIR", "./kernel"),
    ("TITAN_RUNTIME_DIR", "./runtime"),
    ("TITAN_QUEUE_PATH", "./runtime/queue/queue.jsonl"),
    ("TITAN_AUDIT_LOG_DIR", "./logs/audit"),
    ("TITAN_CONTROL_TOWER_PATH", "./exports/excel/Control_Tower.xlsx"),
    ("TITAN_DOCUMENT_REGISTER_PATH", "./ssot/master_index/Document_Register.xlsx"),
    ("TITAN_DEFAULT_CURRENCY", "EUR"),
    ("TITAN_DEFAULT_COUNTRY", "Montenegro"),
    ("TITAN_DEPLOYMENT_MODEL", "Local + Docker + Enterprise API"),
    ("TITAN_AUDIT_LEVEL", "audit-grade"),
]


@dataclass
class ConfigEvent:
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
    candidate = Path.cwd().resolve()
    if candidate.name == DEFAULT_ROOT:
        return candidate
    if (candidate / DEFAULT_ROOT).exists():
        return (candidate / DEFAULT_ROOT).resolve()
    return candidate / DEFAULT_ROOT


def env_content() -> str:
    lines = [
        "# TITAN 11 environment file",
        f"# Generated by {SCRIPT_NAME} v{SCRIPT_VERSION}",
        f"# Generated at UTC: {utc_now()}",
        "",
    ]
    for key, value in DEFAULT_ENV_LINES:
        lines.append(f"{key}={value}")
    lines.append("")
    return "\n".join(lines)


def env_example_content() -> str:
    lines = [
        "# TITAN 11 environment template",
        "# Copy to .env and adjust paths if needed.",
        "",
    ]
    for key, value in DEFAULT_ENV_LINES:
        lines.append(f"{key}={value}")
    lines.append("")
    return "\n".join(lines)


def build_titan_config(base_dir: Path) -> Dict[str, Any]:
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "system": {
            "name": SYSTEM_NAME,
            "short_name": "TITAN_11",
            "status": "CONFIG_INITIALIZED",
            "generated_at_utc": utc_now(),
            "base_dir": str(base_dir),
            "deployment_model": "Local + Docker + Enterprise API",
            "audit_level": "audit-grade",
            "ssot_role": "Authoritative Truth Layer",
        },
        "project": {
            "project_name": "TITAN_11",
            "default_currency": "EUR",
            "default_country": "Montenegro",
            "institutional_targets": ["EIB", "EBRD", "IFC-style ESG", "Board reporting"],
            "governance_mode": "legal-by-design",
            "risk_policy": "conservative",
        },
        "paths": {
            "db_path": "./database/sqlite/titan_state.db",
            "input_dir": "./data/01_inbox",
            "raw_dir": "./data/00_raw",
            "processed_dir": "./data/02_processed",
            "quarantine_dir": "./data/03_quarantine",
            "export_dir": "./exports",
            "ssot_dir": "./ssot",
            "kernel_dir": "./kernel",
            "runtime_dir": "./runtime",
            "queue_path": "./runtime/queue/queue.jsonl",
            "audit_log_dir": "./logs/audit",
            "control_tower_path": "./exports/excel/Control_Tower.xlsx",
            "document_register_path": "./ssot/master_index/Document_Register.xlsx",
            "decision_engine_output": "./exports/excel/TITAN_Decision_Engine_v1_Output.xlsx",
        },
        "database": {
            "engine": "sqlite",
            "wal_enabled": True,
            "foreign_keys": True,
            "synchronous": "NORMAL",
            "temp_store": "MEMORY",
            "schema_expected": "TITAN_DB_SCHEMA_v2_1_or_later",
        },
        "pipeline": {
            "strict_phase_order": True,
            "phase_count": len(PIPELINE_PHASES),
            "phases": PIPELINE_PHASES,
        },
        "ssot": {
            "required_signal_columns": [
                "Signal_ID",
                "Entity_Category",
                "Canonical_Value",
                "Confidence_Score (POA)",
                "Nearby_Keywords",
                "SSOT_Status",
                "Strategic_Impact",
            ],
            "status_values": ["LOCKED", "DRAFT"],
            "confidence_policy": {
                "official_document": 1.0,
                "internal_estimate": 0.8,
                "unverified_or_partial": 0.5,
            },
            "deduplication_key": ["Entity_Category", "Canonical_Value"],
        },
        "decision_engine": {
            "latest_script": "TITAN_DECISION_ENGINE_v1.py",
            "outputs": [
                "01_DECISION_TABLE",
                "02_RISK_LAYER",
                "03_GAP_ANALYSIS",
                "04_EXECUTIVE_SUMMARY",
                "05_AUDIT_LOG",
            ],
            "risk_levels": ["LOW", "MEDIUM", "HIGH"],
            "bankability_classes": [
                "BANKABLE_WITH_STANDARD_REVIEW",
                "CONDITIONALLY_BANKABLE",
                "PRE_BANKABLE_REMEDIATION_REQUIRED",
                "NOT_BANKABLE_YET",
            ],
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s | %(levelname)s | %(message)s",
            "audit_jsonl": True,
        },
    }


def build_schema_snapshot() -> Dict[str, Any]:
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "required_top_level_keys": [
            "schema_version",
            "system",
            "project",
            "paths",
            "database",
            "pipeline",
            "ssot",
            "decision_engine",
            "logging",
        ],
        "path_keys": [
            "db_path",
            "input_dir",
            "raw_dir",
            "processed_dir",
            "quarantine_dir",
            "export_dir",
            "ssot_dir",
            "kernel_dir",
            "runtime_dir",
            "queue_path",
            "audit_log_dir",
            "control_tower_path",
            "document_register_path",
            "decision_engine_output",
        ],
        "pipeline_phase_schema": {
            "order": "integer",
            "script": "string",
            "phase": "string",
            "purpose": "string",
            "criticality": "CRITICAL | HIGH | MEDIUM | LOW",
            "status": "EXPECTED_COMPLETED | CURRENT | NEXT | PLANNED | COMPLETED",
        },
    }


def pydantic_config_module_content() -> str:
    return 