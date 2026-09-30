#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_TITAN_ELITE_RECONSTRUCTOR.py
TITAN 11 - Elite File Reconstructor v2.1 HARDENED
Phase: RECONSTRUCTION (Step 4)
Zavisnost: Step 3 (02_DATABASE_INIT_v2_1.py)
Opis: Skener svih fajlova (~33k), indexiranje i inicijalno punjenje documents tabele
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "01_TITAN_ELITE_RECONSTRUCTOR.py"
SCRIPT_VERSION = "2.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# Folders to skip during scan
SKIP_FOLDERS = {"QUARANTINE", "SNAPSHOTS", "ARCHIVES", "BACKUP", ".git", "__pycache__", "VENV"}

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"reconstructor_step4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== SCAN & INSERT ======================
def scan_and_reconstruct(root: Path, db_path: Path, batch_size: int = 500, limit: int = None):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    logging.info(f"Počinjem skeniranje foldera: {root}")
    files_found = 0
    inserted = 0
    skipped = 0
    batch = []

    for file_path in root.rglob("*"):
        if file_path.is_file():
            # Skip unwanted folders
            if any(skip in file_path.parts for skip in SKIP_FOLDERS):
                skipped += 1
                continue

            files_found += 1
            rel_path = file_path.relative_to(root.parent if root.name == "TITAN_KERNEL" else root)
            
            batch.append((
                str(file_path),                    # file_path
                file_path.name,                    # file_name
                str(rel_path),                     # source_path
                file_path.stat().st_size,          # file_size_bytes
                datetime.now().isoformat()         # processed_at
            ))

            if len(batch) >= batch_size:
                cursor.executemany("""
                    INSERT OR IGNORE INTO documents 
                    (file_path, file_name, source_path, file_size_bytes, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                inserted += len(batch)
                logging.info(f"Processed batch → {inserted} fajlova")
                batch = []

            if limit and files_found >= limit:
                break

    # Last batch
    if batch:
        cursor.executemany("""
            INSERT OR IGNORE INTO documents 
            (file_path, file_name, source_path, file_size_bytes, processed_at)
            VALUES (?, ?, ?, ?, ?)
        """, batch)
        conn.commit()
        inserted += len(batch)

    conn.close()

    logging.info(f"Ukupno pronađeno: {files_found} | Ubaceno: {inserted} | Preskočeno: {skipped}")
    return files_found, inserted

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Elite Reconstructor v2.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--limit", type=int, default=None, help="Limit for testing (e.g. 1000)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji! Pokreni Step 0-3 prvo.")
        sys.exit(1)
    if not db_path.exists():
        print(f"❌ Baza {db_path} ne postoji! Pokreni Step 3 prvo.")
        sys.exit(1)

    setup_logging(root)
    logging.info(f"Root: {root} | DB: {db_path}")

    files_found, inserted = scan_and_reconstruct(
        root, db_path, args.batch_size, args.limit
    )

    logging.info("=== Step 4 RECONSTRUCTION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*80)
    print("✅ TITAN ELITE RECONSTRUCTOR v2.1 HARDENED - ZAVRŠENO")
    print("="*80)
    print(f"Pronađeno fajlova : {files_found}")
    print(f"Ubaceno u bazu   : {inserted}")
    print(f"Database path    : {db_path}")
    print("\nSljedeći korak: Step 4.5 → TITAN_DEDUPLICATION_CLEANER_v1_2_HARDENED.py")
    print("Pokreni ga komandom:")
    print("   python TITAN_DEDUPLICATION_CLEANER_v1_2_HARDENED.py --verbose")
    print("="*80)

if __name__ == "__main__":
    main()