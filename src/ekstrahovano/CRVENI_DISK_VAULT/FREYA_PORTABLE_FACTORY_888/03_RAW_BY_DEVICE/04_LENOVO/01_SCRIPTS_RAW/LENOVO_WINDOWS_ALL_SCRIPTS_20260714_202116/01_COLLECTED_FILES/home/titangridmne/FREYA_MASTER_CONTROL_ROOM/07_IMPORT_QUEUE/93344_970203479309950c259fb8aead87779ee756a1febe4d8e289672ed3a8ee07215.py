#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_v29_queue_consumer_v1_EXPORT.py
TITAN 11 - Queue Consumer v2.9 HARDENED
Phase: QUEUE_CONSUMPTION (Step 6)
Zavisnost: Step 5 (03_v31_producer_v1_EXPORT.py)
Opis: Čita queue.jsonl i puni SQLite (documents + queue_items)
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
SCRIPT_NAME = "03_v29_queue_consumer_v1_EXPORT.py"
SCRIPT_VERSION = "2.9-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")
DEFAULT_QUEUE_FILE = os.getenv("QUEUE_FILE", "queue.jsonl")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"consumer_step6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== MAIN CONSUMER ======================
def consume_queue(root: Path, db_path: Path, queue_file: Path, batch_size: int = 500):
    queue_path = root / queue_file
    if not queue_path.exists():
        logging.error(f"Queue fajl {queue_path} ne postoji! Pokreni Step 5 prvo.")
        return 0

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    logging.info(f"Čitam queue fajl: {queue_path}")

    processed = 0
    batch = []
    line_count = 0

    with queue_path.open("r", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            try:
                item = json.loads(line.strip())
                document_id = item.get("document_id")
                file_path = item.get("file_path")

                if not document_id:
                    continue

                # Update documents table
                batch.append((
                    "CONSUMED",                    # data_quality_status
                    datetime.now().isoformat(),    # processed_at
                    document_id
                ))

                # Insert into queue_items
                cursor.execute("""
                    INSERT OR IGNORE INTO queue_items 
                    (document_id, status, added_at, processed_at)
                    VALUES (?, 'CONSUMED', ?, ?)
                """, (document_id, item.get("added_at", datetime.now().isoformat()), datetime.now().isoformat()))

                if len(batch) >= batch_size:
                    cursor.executemany("""
                        UPDATE documents 
                        SET data_quality_status = ?, processed_at = ?
                        WHERE id = ?
                    """, batch)
                    conn.commit()
                    processed += len(batch)
                    logging.info(f"Processed batch → {processed} stavki")
                    batch = []

            except json.JSONDecodeError:
                logging.warning(f"Neispravan JSON u redu {line_count}")
                continue
            except Exception as e:
                logging.error(f"Greška u redu {line_count}: {e}")
                continue

    # Last batch
    if batch:
        cursor.executemany("""
            UPDATE documents 
            SET data_quality_status = ?, processed_at = ?
            WHERE id = ?
        """, batch)
        conn.commit()
        processed += len(batch)

    conn.close()
    logging.info(f"Ukupno procesirano: {processed} stavki (od {line_count} redova u queue.jsonl)")

    return processed

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Queue Consumer v2.9 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--queue-file", default=DEFAULT_QUEUE_FILE, help="Input queue file")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path
    queue_file = Path(args.queue_file)

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji!")
        sys.exit(1)
    if not db_path.exists():
        print(f"❌ Baza {db_path} ne postoji!")
        sys.exit(1)

    setup_logging(root)
    logging.info(f"Počinjem konzumaciju queue fajla: {queue_file}")

    total = consume_queue(root, db_path, queue_file)

    logging.info("=== Step 6 QUEUE CONSUMPTION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*75)
    print("✅ TITAN QUEUE CONSUMER v2.9 HARDENED - ZAVRŠENO")
    print("="*75)
    print(f"Ukupno procesirano stavki : {total}")
    print(f"Queue fajl               : {queue_file}")
    print(f"Database ažuriran        : {db_path}")
    print("\nSljedeći korak: Step 6.5 → TITAN_DB_SNAPSHOT_ENGINE.py")
    print("Pokreni ga komandom:")
    print("   python TITAN_DB_SNAPSHOT_ENGINE.py")
    print("="*75)

if __name__ == "__main__":
    main()