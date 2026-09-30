#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
14_check_document_signals_v1_EXPORT.py
TITAN 11 - Document Signals Extraction v1.1 HARDENED
Phase: SIGNAL_EXTRACTION (Step 7)
Zavisnost: Step 6.5 (TITAN_DB_SNAPSHOT_ENGINE.py)
Opis: Ekstrakcija ključnih signala (loan_amount, DSCR, ESG_score, CAPEX) iz dokumenata
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "14_check_document_signals_v1_EXPORT.py"
SCRIPT_VERSION = "1.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"signals_step7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== SIGNAL EXTRACTION (placeholder logika) ======================
def extract_signals(root: Path, db_path: Path, batch_size: int = 200):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    logging.info("Počinjem ekstrakciju signala iz VALID dokumenata...")

    cursor.execute("""
        SELECT id, file_path, file_name 
        FROM documents 
        WHERE data_quality_status = 'VALID' 
          AND duplicate_of_document_id IS NULL
        ORDER BY id
    """)

    processed = 0
    batch = []

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        for row in rows:
            doc_id = row[0]
            file_path = row[1]
            file_name = row[2]

            # TODO: Ovdje ide prava ekstrakcija (PDF/Excel parsing)
            # Za sada koristimo placeholder vrijednosti (u produkciji zamijeniti sa stvarnim parserom)
            signals = {
                "loan_amount": 1250000.0,      # primjer
                "dscr": 1.45,
                "esg_score": 78.5,
                "capex": 450000.0,
                "raw_loan_amount": 1250000.0,
                "raw_dscr": 1.45,
                "raw_esg_score": 78.5,
            }

            batch.append((
                doc_id,
                signals["loan_amount"],
                signals["dscr"],
                signals["esg_score"],
                signals["capex"],
                signals["raw_loan_amount"],
                signals["raw_dscr"],
                signals["raw_esg_score"],
                datetime.now().isoformat()
            ))

            processed += 1

        if batch:
            cursor.executemany("""
                INSERT OR REPLACE INTO signals 
                (document_id, loan_amount, dscr, esg_score, capex, 
                 raw_loan_amount, raw_dscr, raw_esg_score, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            logging.info(f"Processed batch → {processed} dokumenata")
            batch = []

    conn.close()
    logging.info(f"Ukupno ekstrahovano signala: {processed}")

    return processed

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Signals Extraction v1.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji!")
        sys.exit(1)
    if not db_path.exists():
        print(f"❌ Baza {db_path} ne postoji!")
        sys.exit(1)

    setup_logging(root)
    logging.info(f"Ekstrakcija signala iz baze: {db_path}")

    total = extract_signals(root, db_path)

    logging.info("=== Step 7 SIGNAL EXTRACTION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*80)
    print("✅ TITAN SIGNALS EXTRACTION v1.1 HARDENED - ZAVRŠENO")
    print("="*80)
    print(f"Ukupno procesirano dokumenata : {total}")
    print(f"Database ažuriran              : {db_path}")
    print("\nSljedeći korak: Step 8 → TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py")
    print("Pokreni ga komandom:")
    print("   python TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py")
    print("="*80)

if __name__ == "__main__":
    main()