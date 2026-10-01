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

﻿import os
import sqlite3
from iphone_backup_decrypt import EncryptedBackup

backup_dir = r"C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C"
out_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TOKEN_HARVEST"
os.makedirs(out_dir, exist_ok=True)

print("=" * 60)
print("🔑 TITAN TOKEN MINER: DUBINSKO RUDARENJE SESIJA")
print("=" * 60)

try:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="nasla")
    
    # Mete: Gde aplikacije kriju tokene
    token_targets = [
        "%.plist",
        "%.binarycookies",
        "%.sqlite",
        "%.db"
    ]
    
    # Kritični domeni (WhatsApp, Safari, Gmail, Teams...)
    domains = ["AppDomain-", "HomeDomain", "RootDomain"]
    
    print("⏳ Pristupam Manifestu i tražim potpisane tokene...")
    
    # Otvaramo Manifest da lociramo fajlove
    conn = sqlite3.connect(backup._temp_decrypted_manifest_db_path)
    cursor = conn.cursor()
    
    harvested_count = 0
    
    for target in token_targets:
        query = "SELECT relativePath, domain FROM Files WHERE relativePath LIKE ?"
        cursor.execute(query, (target,))
        rows = cursor.fetchall()
        
        for rel_path, domain in rows:
            # Filtriramo samo bitne foldere (Preferences, Cookies, Local Storage)
            if any(x in rel_path for x in ["Preferences", "Cookies", "LocalStorage", "Auth"]):
                try:
                    # Kreiramo bezbedno ime fajla
                    safe_name = f"{domain}_{rel_path.replace('/', '_')}"
                    dest = os.path.join(out_dir, safe_name)
                    
                    backup.extract_file(relative_path=rel_path, output_filename=dest)
                    harvested_count += 1
                    if harvested_count % 50 == 0:
                        print(f"   ✨ Iskopano {harvested_count} potencijalnih tokena...")
                except:
                    pass

    print("=" * 60)
    print(f"✅ HARVEST ZAVRŠEN! Ukupno izvučeno: {harvested_count} fajlova.")
    print(f"📍 Svi tokeni su u folderu: TOKEN_HARVEST")
    print("=" * 60)

except Exception as e:
    print(f"❌ GREŠKA: {e}")
