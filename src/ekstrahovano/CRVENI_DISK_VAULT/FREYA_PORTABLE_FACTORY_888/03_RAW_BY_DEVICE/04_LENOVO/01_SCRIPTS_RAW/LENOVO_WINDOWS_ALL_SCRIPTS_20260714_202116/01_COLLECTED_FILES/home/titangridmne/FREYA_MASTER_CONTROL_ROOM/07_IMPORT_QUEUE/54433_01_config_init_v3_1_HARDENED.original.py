#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_config_init_v3_1_HARDENED.py
TITAN 11 - Configuration Init v3.1 HARDENED
Phase: CONFIGURATION (Step 2)
Zavisnost: Step 1 (00_SETUP_STRUCTURE_v3_1_HARDENED.py)
Opis: Generiše .env, titan_config.json i schema snapshot
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "01_config_init_v3_1_HARDENED.py"
SCRIPT_VERSION = "3.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"config_init_step2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== .env GENERATION ======================
def create_or_update_env(root: Path):
    env_path = root / ".env"
    env_content = f"""# ====================== TITAN 11 CONFIG ======================
# Core paths
DB_PATH=titan_kernel.db
QUARANTINE_DIR=GRID/QUARANTINE
SNAPSHOT_DIR=GRID/SNAPSHOTS
DEDUPLICATION_REPORTS_DIR=KERNEL/05_FORENSIC_AUDIT/deduplication_reports

# Performance & Security
HASH_ALGO=blake2b
BATCH_SIZE=500
SNAPSHOT_RETENTION=10
LOG_LEVEL=INFO

# System info
TITAN_VERSION=11.2-HARDENED
TITAN_ROOT={root}
ENVIRONMENT=DESKTOP
CREATED_AT={datetime.now().isoformat()}

# Optional (for future live mode)
LIVE_MODE_ENABLED=false
DAEMON_INTERVAL_SECONDS=60
"""

    if not env_path.exists():
        env_path.write_text(env_content, encoding="utf-8")
        logging.info("✓ Kreiran novi .env fajl")
    else:
        # Dodaj samo missing ključeve
        existing = env_path.read_text(encoding="utf-8")
        with open(env_path, "a", encoding="utf-8") as f:
            if "SNAPSHOT_RETENTION" not in existing:
                f.write("\nSNAPSHOT_RETENTION=10\n")
            if "HASH_ALGO" not in existing:
                f.write("HASH_ALGO=blake2b\n")
        logging.info("✓ .env ažuriran (dodati missing ključevi)")

# ====================== TITAN_CONFIG.JSON ======================
def create_titan_config(root: Path):
    config_path = root / "titan_config.json"
    config = {
        "system_name": SYSTEM_NAME,
        "version": "11.2-HARDENED",
        "bootstrap_version": "v5.2",
        "created_at": datetime.now().isoformat(),
        "pipeline_steps": 19,
        "critical_steps": [0, 1, 2, 3, 4, 4.5, 5, 6, 6.5, 7, 8, 8.5, 9, 13, 14, 15, 16, 17, 18],
        "current_phase": "CONFIGURATION",
        "next_step": 3,
        "author": "Onur - TITAN Kernel",
        "environment": "DESKTOP",
        "description": "Full end-to-end financial decision intelligence platform"
    }

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("✓ Kreiran / ažuriran titan_config.json")

# ====================== SCHEMA SNAPSHOT ======================
def create_schema_snapshot(root: Path):
    snapshot_path = root / "schema_snapshot.json"
    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "step": 2,
        "description": "Initial schema template for titan_kernel.db",
        "tables": {
            "documents": [
                "id", "file_path", "file_name", "source_path", "file_size_bytes",
                "mime_type", "content_hash", "hash_algorithm", "data_quality_status",
                "duplicate_of_document_id", "quarantine_reason", "quarantine_path",
                "data_quality_checked_at", "processed_at"
            ],
            "queue_items": ["id", "document_id", "status", "added_at"],
            "signals": ["id", "document_id", "loan_amount", "dscr", "esg_score", "capex", "extracted_at"],
            "forensic_findings": ["id", "document_id", "confidence_score", "flags", "audit_notes"],
            "reconciliation_log": ["id", "document_id", "gaps", "reconciled_at"]
        },
        "note": "Ovo je template. Prava schema će biti kreirana u Step 3 (02_DATABASE_INIT_v2_1.py)"
    }

    snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("✓ Kreiran schema_snapshot.json")

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Configuration Init v3.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder (default: TITAN_KERNEL)")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji! Prvo pokreni Step 0 i Step 1.")
        sys.exit(1)

    setup_logging(root)
    logging.info(f"Root folder: {root}")

    create_or_update_env(root)
    create_titan_config(root)
    create_schema_snapshot(root)

    logging.info("=== Step 2 CONFIGURATION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*70)
    print("✅ TITAN CONFIGURATION INIT v3.1 HARDENED - ZAVRŠENO")
    print("="*70)
    print(f"Root lokacija : {root}")
    print("Kreirani fajlovi:")
    print("   • .env")
    print("   • titan_config.json")
    print("   • schema_snapshot.json")
    print("\nSljedeći korak: Step 3 → 02_DATABASE_INIT_v2_1.py")
    print("Pokreni ga komandom:")
    print("   python 02_DATABASE_INIT_v2_1.py")
    print("="*70)

if __name__ == "__main__":
    main()