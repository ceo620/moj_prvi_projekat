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
print("👁️ DELTA VISION: DEEP EXTRACTION POKRENUT")
print("=" * 50)

try:
    print("⏳ Pristupam Keybag-u i otključavam trezor...")
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="2312")
    
    # Pristupamo čistom Manifestu koji je biblioteka otključala u pozadini
    temp_manifest = backup._temp_decrypted_manifest_db_path
    conn = sqlite3.connect(temp_manifest)
    cursor = conn.cursor()
    
    print("🔍 Skeniram bazu za vizuelnim dokazima (Screenshots, PNG, JPG)...")
    # Screenshot-ovi na iPhone-u su uvek PNG. Kamere su JPG.
    cursor.execute("SELECT relativePath FROM Files WHERE relativePath LIKE '%.png' OR relativePath LIKE '%.jpg' OR relativePath LIKE '%.jpeg'")
    rows = cursor.fetchall()
    
    # Filtriramo samo one iz Camera Roll-a ili Attachments-a (gde su slike, a ne ikonice aplikacija)
    targets = [row[0] for row in rows if 'DCIM' in row[0] or 'Attachments' in row[0] or 'Media' in row[0]]
    
    if not targets:
        targets = [row[0] for row in rows] # Fallback ako su putanje drugačije
        
    print(f"🎯 Locirano {len(targets)} meta. Započinjem ekstrakciju prvih 500 (Signal Harvest limit)...")
    
    extracted_count = 0
    for rel_path in targets[:500]:
        # Pravimo bezbedno ime fajla da se ne preklapaju
        safe_name = rel_path.split('/')[-1]
        if not safe_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            safe_name += '.png'
            
        out_file = os.path.join(output_dir, f"{extracted_count:03d}_{safe_name}")
        
        try:
            backup.extract_file(relative_path=rel_path, output_filename=out_file)
            extracted_count += 1
            if extracted_count % 50 == 0:
                print(f"   ⏳ Usisano {extracted_count} slika...")
        except Exception:
            pass

    print(f"\n✅ VIZUELNA EKSTRAKCIJA ZAVRŠENA!")
    print(f"📁 Ukupno izvučeno slika: {extracted_count}")
    print(f"📍 Spremno u: {output_dir}")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ GREŠKA PRI UDUBLJIVANJU U TREZOR: {e}")
