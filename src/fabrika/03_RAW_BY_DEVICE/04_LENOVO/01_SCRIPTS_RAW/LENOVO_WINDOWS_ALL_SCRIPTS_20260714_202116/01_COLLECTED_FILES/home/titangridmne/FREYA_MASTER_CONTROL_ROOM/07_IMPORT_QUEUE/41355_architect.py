# ==============================================================
# 🛡️ BEBA DELTA OMNI-ENFORCER | KROVNI CFO KANON (NEPROBOJNO)
# ==============================================================
import os

TITAN_CANON = {
    "TOTAL_CAPEX": "27,800,000.00 EUR",
    "EQUIPMENT": "18,200,000.00 EUR",
    "KNOW_HOW": "6,500,000.00 EUR",
    "ESG": "3,100,000.00 EUR"
}

# Zakucavanje varijabli u sistemsko okruzenje OS-a
for key, val in TITAN_CANON.items():
    os.environ[f"BEBA_DELTA_{key}"] = val
# ==============================================================

﻿import sqlite3
import os
from iphone_backup_decrypt import EncryptedBackup

backup_dir = r"C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C"
pwd = "nasla"

print("=" * 60)
print("🏗️ OPERACIJA ARCHITECT: MAPIRANJE TREZORA")
print("=" * 60)

try:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=pwd)
    temp_db = backup._temp_decrypted_manifest_db_path
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Provera šta uopšte postoji u bazi
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📦 Pronađene tabele u Manifestu: {[t[0] for t in tables]}")
    
    if ('Files',) in tables:
        print("🔍 Tabela 'Files' locirana. Tražim TOKENE i KLJUČEVE...")
        # Tražimo bilo šta što liči na token, key, session ili account
        cursor.execute("SELECT relativePath, fileID FROM Files WHERE relativePath LIKE '%token%' OR relativePath LIKE '%key%' OR relativePath LIKE '%session%' OR relativePath LIKE '%account%' LIMIT 20")
        results = cursor.fetchall()
        
        if results:
            for path, fid in results:
                print(f"💎 PRONAĐEN TRAG: {path} (ID: {fid})")
        else:
            print("🌑 Manifest je prazan ili filtriran. Nema tragova tokena.")
    else:
        print("❌ KRITIČNO: Tabela 'Files' ne postoji. Dekripcija nije uspela do kraja.")

    conn.close()
except Exception as e:
    print(f"❌ KATASTROFA: {e}")
