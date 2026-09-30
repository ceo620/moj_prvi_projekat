#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py
TITAN 11 - Forensic Validation Engine v3.4 HARDENED
Phase: FORENSIC_VALIDATION (Step 8)
Zavisnost: Step 7 (14_check_document_signals_v1_EXPORT.py)
Opis: Forenzička validacija signala + audit trail (confidence score, flags, notes)
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
SCRIPT_NAME = "TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py"
SCRIPT_VERSION = "3.4-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"forensic_step8_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== FORENSIC VALIDATION LOGIKA ======================
def run_forensic_validation(root: Path, db_path: Path, batch_size: int = 300):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    logging.info("Počinjem forenzičku validaciju signala...")

    cursor.execute("""
        SELECT d.id, d.file_name, s.loan_amount, s.dscr, s.esg_score, s.capex
        FROM documents d
        JOIN signals s ON d.id = s.document_id
        WHERE d.data_quality_status = 'VALID'
          AND d.duplicate_of_document_id IS NULL
        ORDER BY d.id
    """)

    processed = 0
    batch = []

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        for row in rows:
            doc_id = row[0]
            file_name = row[1]
            loan = row[2]
            dscr = row[3]
            esg = row[4]
            capex = row[5]

            # Forenzička pravila (hardened logika)
            confidence = 1.0
            flags = []
            notes = []

            if loan is None or loan <= 0:
                confidence -= 0.4
                flags.append("MISSING_LOAN")
                notes.append("Loan amount missing or invalid")

            if dscr is None or dscr < 1.0:
                confidence -= 0.3
                flags.append("LOW_DSCR")
                notes.append("DSCR is critically low")

            if esg is None or esg < 50:
                confidence -= 0.2
                flags.append("LOW_ESG")
                notes.append("ESG score below threshold")

            if capex is None or capex < 0:
                confidence -= 0.1
                flags.append("MISSING_CAPEX")

            # Minimalna confidence
            confidence = max(0.0, confidence)

            batch.append((
                doc_id,
                round(confidence, 3),
                json.dumps(flags),
                "\n".join(notes),
                datetime.now().isoformat()
            ))

            processed += 1

        if batch:
            cursor.executemany("""
                INSERT OR REPLACE INTO forensic_findings 
                (document_id, confidence_score, flags, audit_notes, forensic_at)
                VALUES (?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            logging.info(f"Forensic batch processed → {processed} dokumenata")
            batch = []

    conn.close()
    logging.info(f"Ukupno forenzički obrađeno: {processed} dokumenata")

    return processed

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Forensic Engine v3.4 HARDENED")
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
    logging.info(f"Forenzička validacija na bazi: {db_path}")

    total = run_forensic_validation(root, db_path)

    logging.info("=== Step 8 FORENSIC VALIDATION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*85)
    print("✅ TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED - ZAVRŠENO")
    print("="*85)
    print(f"Ukupno forenzički validirano dokumenata : {total}")
    print(f"Database ažuriran                         : {db_path}")
    print("\nSljedeći korak: Step 8.5 → TITAN_RECONCILIATION_ENGINE.py")
    print("Pokreni ga komandom:")
    print("   python TITAN_RECONCILIATION_ENGINE.py")
    print("="*85)

if __name__ == "__main__":
    main()