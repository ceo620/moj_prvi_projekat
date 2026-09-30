#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_RECONCILIATION_ENGINE.py
TITAN 11 - Reconciliation Engine v1.1 HARDENED
Phase: RECONCILIATION (Step 8.5)
Zavisnost: Step 8 (TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py)
Opis: Upoređuje raw signale iz Step 7 sa forenzičkim nalazima i detektuje gapove/konflikte
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
SCRIPT_NAME = "TITAN_RECONCILIATION_ENGINE.py"
SCRIPT_VERSION = "1.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"reconciliation_step8.5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== RECONCILIATION LOGIKA ======================
def run_reconciliation(root: Path, db_path: Path, batch_size: int = 300):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    logging.info("Počinjem reconciliation – upoređivanje raw signala i forenzike...")

    cursor.execute("""
        SELECT 
            d.id AS document_id,
            d.file_name,
            s.loan_amount AS raw_loan,
            s.dscr AS raw_dscr,
            s.esg_score AS raw_esg,
            s.capex AS raw_capex,
            f.confidence_score,
            f.flags
        FROM documents d
        JOIN signals s ON d.id = s.document_id
        LEFT JOIN forensic_findings f ON d.id = f.document_id
        WHERE d.data_quality_status = 'VALID'
          AND d.duplicate_of_document_id IS NULL
        ORDER BY d.id
    """)

    processed = 0
    issues = 0
    batch = []

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        for row in rows:
            doc_id = row[0]
            file_name = row[1]
            raw_loan = row[2]
            raw_dscr = row[3]
            raw_esg = row[4]
            raw_capex = row[5]
            confidence = row[6] or 0.0
            forensic_flags = json.loads(row[7]) if row[7] else []

            gaps = []
            notes = []

            # Loan mismatch
            if raw_loan and confidence < 0.7:
                gaps.append("LOAN_CONFIDENCE_LOW")
                notes.append(f"Low confidence on loan ({confidence})")

            # DSCR mismatch / low value
            if raw_dscr and raw_dscr < 1.2:
                gaps.append("LOW_DSCR")
                notes.append(f"DSCR is critically low: {raw_dscr}")

            # ESG low
            if raw_esg and raw_esg < 60:
                gaps.append("LOW_ESG")
                notes.append(f"ESG score below threshold: {raw_esg}")

            # General low confidence
            if confidence < 0.85:
                gaps.append("LOW_OVERALL_CONFIDENCE")

            if gaps:
                issues += 1
                batch.append((
                    doc_id,
                    json.dumps(gaps),
                    "\n".join(notes),
                    "FLAGGED",
                    datetime.now().isoformat()
                ))

            processed += 1

        if batch:
            cursor.executemany("""
                INSERT OR REPLACE INTO reconciliation_log 
                (document_id, gaps, audit_notes, status, reconciled_at)
                VALUES (?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            logging.info(f"Reconciliation batch → {processed} dokumenata | {issues} issues")
            batch = []

    conn.close()
    logging.info(f"Reconciliation završena. Ukupno: {processed} | Issues/gapova: {issues}")

    return processed, issues

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Reconciliation Engine v1.1 HARDENED")
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
    logging.info(f"Reconciliation na bazi: {db_path}")

    total, issues = run_reconciliation(root, db_path)

    logging.info("=== Step 8.5 RECONCILIATION USPJEŠNO ZAVRŠEN ===")
    print("\n" + "="*85)
    print("✅ TITAN_RECONCILIATION_ENGINE v1.1 HARDENED - ZAVRŠENO")
    print("="*85)
    print(f"Ukupno procesirano dokumenata : {total}")
    print(f"Pronađeno gapova / konflikata : {issues}")
    print(f"Database ažuriran              : {db_path}")
    print("\nSljedeći korak: Step 9 → 05_kernel_decision_engine_v1_EXPORT.py")
    print("Pokreni ga komandom:")
    print("   python 05_kernel_decision_engine_v1_EXPORT.py")
    print("="*85)

if __name__ == "__main__":
    main()