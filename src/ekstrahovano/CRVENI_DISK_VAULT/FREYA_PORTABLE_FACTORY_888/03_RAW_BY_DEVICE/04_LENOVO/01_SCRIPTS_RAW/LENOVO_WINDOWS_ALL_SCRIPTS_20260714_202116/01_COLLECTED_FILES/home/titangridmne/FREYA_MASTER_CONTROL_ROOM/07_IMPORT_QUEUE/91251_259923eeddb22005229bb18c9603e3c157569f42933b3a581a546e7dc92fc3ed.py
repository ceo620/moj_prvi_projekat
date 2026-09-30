#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09_generate_document_register_v1_EXPORT.py
TITAN 11 - Document Register Generator v1.1 HARDENED
Phase: DOCUMENT_REGISTER (Step 13)
Zavisnost: Step 9 (05_kernel_decision_engine_v1_EXPORT.py)
Opis: Generiše glavni SSOT Document_Register.xlsx sa svim podacima
"""

import argparse
import logging
import sqlite3
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIG ====================
SCRIPT_NAME = "09_generate_document_register_v1_EXPORT.py"
SCRIPT_VERSION = "1.1-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"

load_dotenv()

DEFAULT_ROOT = os.getenv("TITAN_ROOT", "TITAN_KERNEL")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "titan_kernel.db")

# ====================== LOGGING ======================
def setup_logging(root: Path):
    log_dir = root / "LOGS"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"document_register_step13_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
    )
    logging.info(f"=== {SCRIPT_NAME} v{SCRIPT_VERSION} START ===")

# ====================== GENERATE REGISTER ======================
def generate_document_register(root: Path, db_path: Path):
    conn = sqlite3.connect(str(db_path))

    query = """
        SELECT 
            d.id AS document_id,
            d.file_name,
            d.file_path,
            d.source_path,
            d.file_size_bytes,
            d.data_quality_status,
            d.quarantine_reason,
            s.loan_amount,
            s.dscr,
            s.esg_score,
            s.capex,
            f.confidence_score,
            f.flags AS forensic_flags,
            r.gaps AS reconciliation_gaps,
            k.bankability_score,
            k.decision,
            k.risk_flags,
            d.processed_at,
            k.decided_at
        FROM documents d
        LEFT JOIN signals s ON d.id = s.document_id
        LEFT JOIN forensic_findings f ON d.id = f.document_id
        LEFT JOIN reconciliation_log r ON d.id = r.document_id
        LEFT JOIN kernel_decisions k ON d.id = k.document_id
        WHERE d.data_quality_status = 'VALID'
        ORDER BY d.id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Formatiranje
    df['forensic_flags'] = df['forensic_flags'].apply(lambda x: json.loads(x) if isinstance(x, str) and x != '[]' else x)
    df['reconciliation_gaps'] = df['reconciliation_gaps'].apply(lambda x: json.loads(x) if isinstance(x, str) and x != '[]' else x)
    df['risk_flags'] = df['risk_flags'].apply(lambda x: json.loads(x) if isinstance(x, str) and x != '[]' else x)

    # Sačuvaj Excel
    register_path = root / "KERNEL" / "Document_Register.xlsx"
    register_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(register_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Document_Register", index=False)
        
        # Dodaj summary sheet
        summary = pd.DataFrame({
            "Metric": ["Total Documents", "Valid Documents", "Avg Bankability Score", "Approve", "Conditional", "Reject"],
            "Value": [
                len(df),
                len(df[df['data_quality_status'] == 'VALID']),
                round(df['bankability_score'].mean(), 2) if not df.empty else 0,
                len(df[df['decision'] == 'APPROVE']),
                len(df[df['decision'] == 'CONDITIONAL_APPROVE']),
                len(df[df['decision'] == 'REJECT'])
            ]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)

    logging.info(f"SSOT Document_Register.xlsx kreiran: {register_path}")
    return len(df), str(register_path)

# ====================== MAIN ======================
def main():
    parser = argparse.ArgumentParser(description="TITAN Document Register Generator v1.1 HARDENED")
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = root / args.db_path

    setup_logging(root)
    total, register_path = generate_document_register(root, db_path)

    print("\n" + "="*90)
    print("✅ 09_generate_document_register_v1_EXPORT - ZAVRŠENO")
    print("="*90)
    print(f"Ukupno dokumenata u registru : {total}")
    print(f"SSOT fajl kreiran            : {register_path}")
    print("\nSljedeći korak: Step 14 → 08_sync_sqlite_to_existing_control_tower.py")
    print("Pokreni ga komandom:")
    print("   python 08_sync_sqlite_to_existing_control_tower.py")
    print("="*90)

if __name__ == "__main__":
    main()