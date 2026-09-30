#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_DATABASE_INIT_v2_1.py
TITAN 11 - Database Initialization v2.1 HARDENED
Phase: DATABASE (Step 3)
Zavisnost: Step 2 (01_config_init_v3_1_HARDENED.py)
Opis: Kreira / ažurira SQLite bazu sa WAL modom, kompletnom shemom i indeksima
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "02_DATABASE_INIT_v2_1.py"
SCRIPT_VERSION = "2.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"database_init_step3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== SQL SCHEMA ======================
SCHEMA_SQL = """
-- Main documents table (core of the system)
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_name TEXT,
    source_path TEXT,
    file_size_bytes INTEGER,
    mime_type TEXT,
    content_hash TEXT,
    hash_algorithm TEXT DEFAULT 'blake2b',
    data_quality_status TEXT DEFAULT 'PENDING',
    duplicate_of_document_id INTEGER,
    quarantine_reason TEXT,
    quarantine_path TEXT,
    data_quality_checked_at TEXT,
    file_size_checked_bytes INTEGER,
    fuzzy_name_group TEXT,
    processed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Queue for processing
CREATE TABLE IF NOT EXISTS queue_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    status TEXT DEFAULT 'PENDING',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Extracted signals (loan, ESG, DSCR, CAPEX...)
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    loan_amount REAL,
    dscr REAL,
    esg_score REAL,
    capex REAL,
    raw_loan_amount REAL,
    raw_dscr REAL,
    raw_esg_score REAL,
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Forensic validation findings
CREATE TABLE IF NOT EXISTS forensic_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    flags TEXT,                    -- JSON array of issues
    audit_notes TEXT,
    forensic_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Reconciliation log (gaps between raw signals and forensic)
CREATE TABLE IF NOT EXISTS reconciliation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    gaps TEXT,                     -- JSON array
    reconciled_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'FLAGGED',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Deduplication log (audit trail)
CREATE TABLE IF NOT EXISTS deduplication_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    action TEXT,
    reason TEXT,
    original_id INTEGER,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# ====================== INDEXES (14 indeksa) ======================
INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_dq_status ON documents(data_quality_status);
CREATE INDEX IF NOT EXISTS idx_documents_duplicate_of ON documents(duplicate_of_document_id);

CREATE INDEX IF NOT EXISTS idx_queue_document_id ON queue_items(document_id);
CREATE INDEX IF NOT EXISTS idx_queue_status ON queue_items(status);

CREATE INDEX IF NOT EXISTS idx_signals_document_id ON signals(document_id);
CREATE INDEX IF NOT EXISTS idx_signals_dscr ON signals(dscr);
CREATE INDEX IF NOT EXISTS idx_signals_esg ON signals(esg_score);

CREATE INDEX IF NOT EXISTS idx_forensic_document_id ON forensic_findings(document_id);
CREATE INDEX IF NOT EXISTS idx_forensic_confidence ON forensic_findings(confidence_score);

CREATE INDEX IF NOT EXISTS idx_reconciliation_document_id ON reconciliation_log(document_id);
CREATE INDEX IF NOT EXISTS idx_dedup_log_document_id ON deduplication_log(document_id);
"""

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Database Initialization v2.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji! Pokreni Step 0 i Step 1 prvo.")
        sys.exit(1)

    setup_logging(root)
    logging.info(f"Target database: {db_path}")

    # Connect and enable WAL
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    logging.info("WAL mode aktiviran")

    # Create schema
    conn.executescript(SCHEMA_SQL)
    logging.info("Core tables kreirane / ažurirane")

    # Create indexes
    conn.executescript(INDEXES_SQL)
    logging.info("14 indeksa kreirano")

    conn.commit()
    conn.close()

    logging.info("=== Step 3 DATABASE INIT USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*70)
    print("✅ TITAN DATABASE INITIALIZATION v2.1 HARDENED - ZAVRŠENO")
    print("="*70)
    print(f"Database path : {db_path}")
    print("Kreirano:")
    print("   • documents, queue_items, signals, forensic_findings, reconciliation_log")
    print("   • 14 indeksa")
    print("   • WAL mode + foreign keys")
    print("\nSljedeći korak: Step 4 → 01_TITAN_ELITE_RECONSTRUCTOR.py")
    print("Pokreni ga komandom:")
    print("   python 01_TITAN_ELITE_RECONSTRUCTOR.py")
    print("="*70)

if __name__ == "__main__":
    main()