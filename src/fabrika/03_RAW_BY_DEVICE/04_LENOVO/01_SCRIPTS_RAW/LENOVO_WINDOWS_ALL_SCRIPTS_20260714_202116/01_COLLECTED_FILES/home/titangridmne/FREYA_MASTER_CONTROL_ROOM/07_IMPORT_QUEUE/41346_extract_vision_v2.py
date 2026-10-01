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
output_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\APPLE_VISION_RAW"
os.makedirs(output_dir, exist_ok=True)

print("=" * 50)
print("👁️ DELTA VISION: DEEP EXTRACTION V2")
print("=" * 50)

backup = None
conn = None

try:
    print("⏳ Otključavam trezor i pristupam bazi...")
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="2312")
    
    temp_manifest = backup._temp_decrypted_manifest_db_path
    conn = sqlite3.connect(temp_manifest)
    cursor = conn.cursor()
    
    # Sistemski bypass: Čitamo arhitekturu baze direktno
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    
    targets = []
    if 'Files' in tables:
        print("🔍 Manifest lociran. Usisavam mape i instrukcije...")
        cursor.execute("SELECT relativePath FROM Files WHERE relativePath LIKE '%.png' OR relativePath LIKE '%.jpg' OR relativePath LIKE '%.jpeg'")
        targets = [row[0] for row in cursor.fetchall() if row[0]]
    else:
        print(f"⚠️ Apple je sakrio 'Files'. Trenutne tabele u trezoru: {tables}")
        
    # Filtriramo da izvučemo isključivo slike ekrana i kamere (ne ikonice)
    valid_targets = [t for t in targets if 'DCIM' in t or 'Media' in t or 'Attachments' in t]
    if not valid_targets and targets:
        valid_targets = targets # Fallback ako je arhitektura drugačija
        
    print(f"🎯 Locirano {len(valid_targets)} vizuelnih meta. Pokrećem harvesting (limit 500)...")
    
    extracted = 0
    for rel_path in valid_targets[:500]:
        # Čistimo ime fajla da Windows ne pravi problem
        safe_name = rel_path.replace('/', '_')
        out_file = os.path.join(output_dir, f"{extracted:04d}_{safe_name}")
        
        try:
            backup.extract_file(relative_path=rel_path, output_filename=out_file)
            extracted += 1
            if extracted % 50 == 0:
                print(f"   ⏳ Usisano {extracted} slika...")
        except:
            pass
            
    print(f"\n✅ VIZUELNA EKSTRAKCIJA ZAVRŠENA! Iščupano slika: {extracted}")
    print(f"📁 Lokacija: {output_dir}")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ GREŠKA: {e}")

finally:
    # OVO SPREČAVA WINDOWS BLOKADU (WinError 32)
    if conn:
        conn.close()
    if backup:
        try:
            backup._cleanup()
        except:
            pass
