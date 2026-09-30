#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_v31_producer_v1_EXPORT.py
TITAN 11 - Queue Producer v3.1 HARDENED
Phase: QUEUE_PRODUCTION (Step 5)
Zavisnost: Step 4.5 (TITAN_DEDUPLICATION_CLEANER_v1_2_HARDENED.py)
Opis: Generiše queue.jsonl SAMO od VALID i ne-duplikat fajlova
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
SCRIPT_NAME = "03_v31_producer_v1_EXPORT.py"
SCRIPT_VERSION = "3.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")
DEFAULT_QUEUE_FILE = os.getenv("QUEUE_FILE", "queue.jsonl")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"producer_step5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== MAIN PRODUCER ======================
def create_queue(root: Path, db_path: Path, queue_file: Path, batch_size: int = 1000):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logging.info("Čitam VALID i ne-duplikat fajlove iz baze...")

    cursor.execute("""
        SELECT 
            id AS document_id,
            file_path,
            file_name,
            source_path,
            file_size_bytes,
            content_hash,
            data_quality_status
        FROM documents
        WHERE data_quality_status = 'VALID'
          AND duplicate_of_document_id IS NULL
        ORDER BY id
    """)

    queue_path = root / queue_file
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with queue_path.open("w", encoding="utf-8") as f:
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                item = {
                    "document_id": row["document_id"],
                    "file_path": row["file_path"],
                    "file_name": row["file_name"],
                    "source_path": row["source_path"],
                    "file_size_bytes": row["file_size_bytes"],
                    "content_hash": row["content_hash"],
                    "status": "PENDING",
                    "added_at": datetime.now().isoformat()
                }
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1

    conn.close()
    logging.info(f"Generisano {count} stavki u queue.jsonl")

    return count, str(queue_path)

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Queue Producer v3.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--queue-file", default=DEFAULT_QUEUE_FILE, help="Output queue file")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path
    queue_file = Path(args.queue_file)

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji!")
        sys.exit(1)
    if not db_path.exists():
        print(f"❌ Baza {db_path} ne postoji! Pokreni Step 3 i 4 prvo.")
        sys.exit(1)

    setup_logging(root)
    logging.info(f"Generišem queue iz baze: {db_path}")

    total, queue_path = create_queue(root, db_path, queue_file)

    logging.info("=== Step 5 QUEUE PRODUCTION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*75)
    print("✅ TITAN QUEUE PRODUCER v3.1 HARDENED - ZAVRŠENO")
    print("="*75)
    print(f"Ukupno stavki u queue.jsonl : {total}")
    print(f"Queue fajl                 : {queue_path}")
    print("\nSljedeći korak: Step 6 → 03_v29_queue_consumer_v1_EXPORT.py")
    print("Pokreni ga komandom:")
    print("   python 03_v29_queue_consumer_v1_EXPORT.py")
    print("="*75)

if __name__ == "__main__":
    main()