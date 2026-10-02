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

# KORISTIMO POTVRĐENU ŠIFRU
confirmed_pwd = "nasla"

print("=" * 60)
print(f"☢️ POKREĆEM 'THE VOID' V2 - KORISTIM KLJUČ: {confirmed_pwd}")
print("=" * 60)

try:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=confirmed_pwd)
    
    scanned = 0
    saved = 0
    
    for root, dirs, files in os.walk(backup_dir):
        for file_hash in files:
            if len(file_hash) == 40:
                scanned += 1
                try:
                    # Pokušaj dešifrovanja sa 'nasla'
                    decrypted_data = backup.decrypt_inner_file(file_hash)
                    
                    # Identifikacija SQLite baze
                    if decrypted_data[:15] == b'SQLite format 3':
                        dest = os.path.join(out_dir, f"DB_{file_hash}.sqlite")
                        with open(dest, 'wb') as f: f.write(decrypted_data)
                        saved += 1
                    
                    # Identifikacija Apple Plist dokumenata
                    elif decrypted_data[:6] == b'bplist' or decrypted_data[:6] == b'<?xml ':
                        dest = os.path.join(out_dir, f"DOC_{file_hash}.plist")
                        with open(dest, 'wb') as f: f.write(decrypted_data)
                        saved += 1
                        
                except:
                    pass # Fajl nije za ovu šifru ili je sistemski zaštićen
                
                if scanned % 2000 == 0:
                    print(f"🌀 Progres: {scanned} | Pronađeno: {saved}")

    print("=" * 60)
    print(f"✅ OPERACIJA ZAVRŠENA!")
    print(f"💎 UKUPNO IZVUČENO DOKAZA: {saved}")
    print("=" * 60)

except Exception as e:
    print(f"❌ GREŠKA: {e}")
