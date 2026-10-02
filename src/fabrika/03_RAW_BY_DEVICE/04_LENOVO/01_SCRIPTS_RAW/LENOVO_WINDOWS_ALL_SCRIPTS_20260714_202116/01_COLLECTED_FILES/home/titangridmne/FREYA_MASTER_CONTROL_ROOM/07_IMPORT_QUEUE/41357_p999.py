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
out_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\P999_HARVEST"
os.makedirs(out_dir, exist_ok=True)

print("=" * 60)
print("☢️ PROTOKOL 999: BINARNO RUDARENJE BEZ MANIFESTA")
print("=" * 60)

try:
    # Inicijalizujemo backup - ako ovo prođe, Keybag je bar teoretski dostupan
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="nasla")
    
    count = 0
    success = 0
    
    # Prolazimo kroz fizičku strukturu (00, 01, 02... folderi)
    for root, dirs, files in os.walk(backup_dir):
        for f in files:
            if len(f) == 40: # Provera da li je Apple hash format
                count += 1
                try:
                    # Direktan pokušaj dekripcije fajla po njegovom hešu
                    decrypted = backup.decrypt_inner_file(f)
                    
                    # Provera: Da li je ovo baza ili token?
                    if decrypted.startswith(b'SQLite format 3') or decrypted.startswith(b'bplist'):
                        ext = ".sqlite" if decrypted.startswith(b'SQLite format 3') else ".plist"
                        with open(os.path.join(out_dir, f + ext), 'wb') as out_f:
                            out_f.write(decrypted)
                        success += 1
                except:
                    pass
                
                if count % 5000 == 0:
                    print(f"🌀 Skenirano: {count} | Iskopano tokena: {success}")

    print("=" * 60)
    print(f"✅ OPERACIJA ZAVRŠENA! Iskopano dijamanta: {success}")
    print("=" * 60)

except Exception as e:
    print(f"❌ KATASTROFA: {e}")
