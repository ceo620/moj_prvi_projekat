#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_DB_SNAPSHOT_ENGINE.py
TITAN 11 - Database Snapshot Engine v1.1 HARDENED
Phase: DATABASE_SNAPSHOT (Step 6.5)
Zavisnost: Step 6 (03_v29_queue_consumer_v1_EXPORT.py)
Opis: Kreira verifikovani snapshot SQLite baze PRIJE signal extraction
"""

import argparse
import hashlib
import json
import logging
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "TITAN_DB_SNAPSHOT_ENGINE.py"
SCRIPT_VERSION = "1.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")
DEFAULT_SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "GRID/SNAPSHOTS")
DEFAULT_RETENTION = int(os.getenv("SNAPSHOT_RETENTION", "10"))

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"snapshot_step6.5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== SNAPSHOT LOGIC ======================
def create_snapshot(root: Path, db_path: Path, snapshot_dir: Path, retention: int):
    # 1. WAL checkpoint
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA wal_checkpoint(FULL);")
    conn.close()
    logging.info("WAL checkpoint (FULL) izvršen")

    # 2. Kreiranje snapshot-a
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"titan_snapshot_6.5_{timestamp}.db"
    snapshot_path = snapshot_dir / snapshot_name

    shutil.copy2(str(db_path), str(snapshot_path))
    logging.info(f"Snapshot kopiran: {snapshot_path} ({snapshot_path.stat().st_size / (1024*1024):.2f} MB)")

    # 3. Kreiranje manifest.json
    manifest = {
        "snapshot_version": "1.1",
        "created_at": datetime.now().isoformat(),
        "step": "6.5",
        "phase": "DATABASE_SNAPSHOT",
        "description": "Snapshot kreiran ODMAH nakon Queue Consumption (Step 6)",
        "original_db": str(db_path),
        "snapshot_path": str(snapshot_path),
        "snapshot_size_mb": round(snapshot_path.stat().st_size / (1024*1024), 2),
        "titan_version": os.getenv("TITAN_VERSION", "unknown"),
        "integrity_status": "PENDING"
    }

    # Integrity check
    try:
        check_conn = sqlite3.connect(str(snapshot_path))
        cursor = check_conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        manifest["integrity_status"] = "OK" if integrity == "ok" else f"ERROR: {integrity}"
        
        cursor.execute("PRAGMA quick_check")
        manifest["quick_check"] = cursor.fetchone()[0]
        
        # Row counts
        tables = ["documents", "queue_items", "signals", "forensic_findings", "reconciliation_log"]
        row_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_counts[table] = cursor.fetchone()[0]
            except:
                row_counts[table] = 0
        manifest["row_counts"] = row_counts

        # BLAKE2b hash
        with open(snapshot_path, "rb") as f:
            h = hashlib.blake2b(digest_size=32)
            for chunk in iter(lambda: f.read(8*1024*1024), b""):
                h.update(chunk)
            manifest["snapshot_blake2b"] = h.hexdigest()

        check_conn.close()
    except Exception as e:
        manifest["integrity_status"] = f"FAILED: {e}"
        logging.error(f"Integrity check failed: {e}")

    # Sačuvaj manifest
    manifest_path = snapshot_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info(f"Manifest kreiran: {manifest_path}")

    # 4. Rotirajuće čišćenje (zadržavamo poslednjih N)
    snapshots = sorted(snapshot_dir.glob("titan_snapshot_*.db"), key=lambda x: x.stat().st_ctime)
    to_delete = len(snapshots) - retention
    if to_delete > 0:
        for old in snapshots[:to_delete]:
            old.unlink(missing_ok=True)
            old.with_suffix(".manifest.json").unlink(missing_ok=True)
            logging.info(f"Old snapshot obrisan (retention): {old.name}")

    return snapshot_path, manifest

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Database Snapshot Engine v1.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root folder")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--snapshot-dir", default=DEFAULT_SNAPSHOT_DIR, help="Snapshot output directory")
    parser.add_argument("--retention", type=int, default=DEFAULT_RETENTION, help="Number of snapshots to keep")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path
    snapshot_dir = root / args.snapshot_dir

    if not root.exists():
        print(f"❌ Root folder {root} ne postoji!")
        sys.exit(1)
    if not db_path.exists():
        print(f"❌ Baza {db_path} ne postoji! Pokreni Step 3-6 prvo.")
        sys.exit(1)

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(root)
    logging.info(f"Snapshot dir: {snapshot_dir}")

    snapshot_path, manifest = create_snapshot(root, db_path, snapshot_dir, args.retention)

    logging.info("=== Step 6.5 DATABASE SNAPSHOT USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*80)
    print("✅ TITAN_DB_SNAPSHOT_ENGINE v1.1 HARDENED - ZAVRŠENO")
    print("="*80)
    print(f"Snapshot kreiran     : {snapshot_path.name}")
    print(f"Manifest             : {snapshot_path.with_suffix('.manifest.json').name}")
    print(f"Integritet           : {manifest['integrity_status']}")
    print(f"Ukupno redova        : {sum(manifest.get('row_counts', {}).values())}")
    print(f"Zadržano snapshot-ova: {args.retention}")
    print("\nSljedeći korak: Step 7 → 14_check_document_signals_v1_EXPORT.py")
    print("Pokreni ga komandom:")
    print("   python 14_check_document_signals_v1_EXPORT.py")
    print("="*80)

if __name__ == "__main__":
    main()