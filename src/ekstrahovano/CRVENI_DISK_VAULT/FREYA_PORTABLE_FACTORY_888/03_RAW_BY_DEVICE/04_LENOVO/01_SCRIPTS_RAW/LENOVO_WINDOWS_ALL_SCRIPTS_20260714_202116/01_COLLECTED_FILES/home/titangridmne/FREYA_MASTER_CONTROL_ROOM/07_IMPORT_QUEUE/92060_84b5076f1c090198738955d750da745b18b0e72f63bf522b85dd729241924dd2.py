#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_kernel_decision_engine_v1_EXPORT.py
TITAN 11 - Kernel Decision Engine v1.1 HARDENED
Phase: KERNEL_DECISION (Step 9)
Zavisnost: Step 8.5 (TITAN_RECONCILIATION_ENGINE.py)
Opis: Operativna decision logika - računa bankability score, risk flags i operativne odluke
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
SCRIPT_NAME = "05_kernel_decision_engine_v1_EXPORT.py"
SCRIPT_VERSION = "1.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"kernel_decision_step9_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== DECISION LOGIKA ======================
def run_kernel_decision(root: Path, db_path: Path, batch_size: int = 250):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    logging.info("Pokrećem Kernel Decision Engine...")

    cursor.execute("""
        SELECT 
            d.id AS document_id,
            d.file_name,
            s.loan_amount,
            s.dscr,
            s.esg_score,
            s.capex,
            f.confidence_score,
            COALESCE(r.gaps, '[]') AS gaps
        FROM documents d
        JOIN signals s ON d.id = s.document_id
        LEFT JOIN forensic_findings f ON d.id = f.document_id
        LEFT JOIN reconciliation_log r ON d.id = r.document_id
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
            loan = row[2] or 0
            dscr = row[3] or 0
            esg = row[4] or 0
            capex = row[5] or 0
            confidence = row[6] or 0
            gaps = json.loads(row[7])

            # === KERNEL DECISION SCORE ===
            bankability_score = 0.0
            risk_flags = []
            decision = "HOLD"

            # Osnovni score
            if loan > 0:
                bankability_score += 25
            if dscr >= 1.35:
                bankability_score += 30
            elif dscr >= 1.1:
                bankability_score += 15
            else:
                risk_flags.append("CRITICAL_DSCR")

            if esg >= 75:
                bankability_score += 20
            elif esg >= 60:
                bankability_score += 10
            else:
                risk_flags.append("LOW_ESG")

            if confidence >= 0.85:
                bankability_score += 15
            elif confidence >= 0.7:
                bankability_score += 5
            else:
                risk_flags.append("LOW_CONFIDENCE")

            if gaps:
                bankability_score -= 10 * len(gaps)
                risk_flags.extend(gaps)

            # Finalna odluka
            bankability_score = max(0, min(100, bankability_score))

            if bankability_score >= 75 and not risk_flags:
                decision = "APPROVE"
            elif bankability_score >= 55:
                decision = "CONDITIONAL_APPROVE"
            else:
                decision = "REJECT"

            batch.append((
                doc_id,
                round(bankability_score, 2),
                decision,
                json.dumps(risk_flags),
                json.dumps({"loan": loan, "dscr": dscr, "esg": esg, "capex": capex}),
                datetime.now().isoformat()
            ))

            processed += 1

        if batch:
            cursor.executemany("""
                INSERT OR REPLACE INTO kernel_decisions 
                (document_id, bankability_score, decision, risk_flags, raw_metrics, decided_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            logging.info(f"Decision batch processed → {processed} dokumenata")
            batch = []

    conn.close()
    logging.info(f"Kernel Decision Engine završen. Ukupno: {processed} dokumenata")
    return processed

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Kernel Decision Engine v1.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path

    setup_logging(root)
    total = run_kernel_decision(root, db_path)

    print("\n" + "="*85)
    print("✅ 05_KERNEL_DECISION_ENGINE_v1_EXPORT - ZAVRŠENO")
    print("="*85)
    print(f"Ukupno obrađeno dokumenata : {total}")
    print(f"Database ažuriran           : {db_path}")
    print("\nSljedeći korak: Step 13 → 09_generate_document_register_v1_EXPORT.py")
    print("Pokreni ga komandom:")
    print("   python 09_generate_document_register_v1_EXPORT.py")
    print("="*85)

if __name__ == "__main__":
    main()