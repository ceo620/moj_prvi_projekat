#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_SETUP_STRUCTURE_v3_1_HARDENED.py
TITAN 11 - Python Bootstrap v3.1 HARDENED
Phase: BOOTSTRAP (Step 1)
Zavisnost: Step 0 (00_CREATE_TITAN_DESKTOP_STRUCTURE_v5_2_HARDENED.ps1)
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "00_SETUP_STRUCTURE_v3_1_HARDENED.py"
SCRIPT_VERSION = "3.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")

# ====================== LOGGING ======================
def setup_logging():
    log_dir = Path(DEFAULT_ROOT) / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"bootstrap_step1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== FOLDER STRUCTURE ======================
FOLDERS_TO_CREATE = [
    "SCRIPTS/PRE_PROCESSING",
    "SCRIPTS/QUEUE",
    "SCRIPTS/DATABASE",
    "SCRIPTS/SIGNAL_EXTRACTION",
    "SCRIPTS/FORENSIC",
    "SCRIPTS/RECONCILIATION",
    "SCRIPTS/DECISION",
    "SCRIPTS/CONTROL_TOWER",
    "SCRIPTS/STRATEGIC_DOCUMENTS",
    "SCRIPTS/ARCHIVE",
    "GRID/QUARANTINE",
    "GRID/SNAPSHOTS",
    "GRID/ARCHIVES",
    "KERNEL/05_FORENSIC_AUDIT/deduplication_reports",
    "LOGS",
    "BACKUP",
    "VENV",                    # Python virtual environment
]

def create_folders(root: Path):
    logging.info("Kreiram enterprise Python folder strukturu...")
    created = 0
    for folder in FOLDERS_TO_CREATE:
        full_path = root / folder
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"✓ Kreiran: {folder}")
            created += 1
        else:
            logging.info(f"✓ Već postoji: {folder}")
    logging.info(f"Folders created/verified: {created} new")

# ====================== REQUIREMENTS.TXT ======================
def create_requirements(root: Path):
    req_path = root / "requirements.txt"
    if not req_path.exists():
        content = """# TITAN 11 - Core dependencies
python-dotenv>=1.0.0
sqlite3
psutil
tqdm
pandas
openpyxl
python-dateutil
"""
        req_path.write_text(content, encoding="utf-8")
        logging.info("✓ Kreiran requirements.txt")
    else:
        logging.info("✓ requirements.txt već postoji")

# ====================== VIRTUAL ENVIRONMENT ======================
def setup_virtualenv(root: Path):
    venv_path = root / "VENV"
    if not venv_path.exists():
        logging.info("Kreiram Python virtual environment...")
        os.system(f"{sys.executable} -m venv \"{venv_path}\"")
        logging.info("✓ Virtual environment kreiran (VENV)")
        logging.info("   Aktiviraj sa: VENV\\Scripts\\Activate.ps1 (PowerShell)")
    else:
        logging.info("✓ Virtual environment već postoji")

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Python Bootstrap v3.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder (default: TITAN_KERNEL)")
    parser.add_argument("--skip-venv", action="store_true", help="Preskoči kreiranje virtual environment-a")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    
    if not root.exists():
        logging.error(f"Root folder {root} ne postoji! Prvo pokreni Step 0.")
        sys.exit(1)

    setup_logging()
    logging.info(f"Root folder: {root}")

    create_folders(root)
    create_requirements(root)
    
    if not args.skip_venv:
        setup_virtualenv(root)
    else:
        logging.info("Virtual environment preskočen po zahtjevu.")

    logging.info("=== Step 1 BOOTSTRAP USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*60)
    print("✅ TITAN PYTHON BOOTSTRAP v3.1 HARDENED - ZAVRŠENO")
    print("="*60)
    print(f"Root lokacija: {root}")
    print("Sljedeći korak: Step 2 → 01_config_init_v3_1_HARDENED.py")
    print("Pokreni ga komandom:")
    print("   python 01_config_init_v3_1_HARDENED.py")
    print("="*60)

if __name__ == "__main__":
    main()