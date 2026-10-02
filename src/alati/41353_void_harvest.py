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
from iphone_backup_decrypt import EncryptedBackup

backup_dir = r"C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C"
out_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\THE_VOID"
os.makedirs(out_dir, exist_ok=True)

print("=" * 60)
print("☢️ POKREĆEM 'THE VOID' - TOTALNA EKSTRAKCIJA BEZ MANIFESTA")
print("=" * 60)

try:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="2312")
    
    scanned = 0
    saved = 0
    
    # Prolazimo kroz sve podfoldere (00, 01, ..., ff)
    for root, dirs, files in os.walk(backup_dir):
        for file_hash in files:
            if len(file_hash) == 40: # Provera da li je legitimni Apple hash
                scanned += 1
                try:
                    # Pokušavamo "slepu" dešifraciju
                    decrypted_data = backup.decrypt_inner_file(file_hash)
                    
                    # Provera zaglavlja: SQLite baze
                    if decrypted_data[:15] == b'SQLite format 3':
                        dest = os.path.join(out_dir, f"DATABASE_{file_hash}.sqlite")
                        with open(dest, 'wb') as f:
                            f.write(decrypted_data)
                        saved += 1
                    
                    # Provera zaglavlja: Apple Plist (konfiguracije i dokumenti)
                    elif decrypted_data[:6] == b'bplist':
                        dest = os.path.join(out_dir, f"DOC_{file_hash}.plist")
                        with open(dest, 'wb') as f:
                            f.write(decrypted_data)
                        saved += 1
                        
                except:
                    # Fajl nije šifrovan ovom šifrom ili nije podržan - preskoči
                    pass
                
                if scanned % 1000 == 0:
                    print(f"🌀 Skenirano: {scanned} | Izvučeno dijamanata: {saved}")

    print("=" * 60)
    print(f"✅ OPERACIJA ZAVRŠENA!")
    print(f"📊 Skenirano fajlova: {scanned}")
    print(f"💎 Ukupno spašeno čistih dokaza: {saved}")
    print(f"📍 Putanja: {out_dir}")
    print("=" * 60)

except Exception as e:
    print(f"❌ KATASTROFALNA GREŠKA: {e}")
