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
import json
from iphone_backup_decrypt import EncryptedBackup

backup_dir = r"C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C"
out_file = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\KEYCHAIN_TOKENS.txt"

print("=" * 60)
print("🔑 TITAN KEYCHAIN HARVEST: DIREKTNO DEŠIFROVANJE")
print("=" * 60)

try:
    print("⏳ Otključavam Privezak (Keychain) pomoću ključa...")
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="nasla")
    
    # IZVLAČENJE KEYCHAIN-A (Ovo ne koristi 'Files' tabelu)
    keychain = backup.decrypt_keychain()
    
    print(f"🎯 Uspeh! Pronađeno {len(keychain)} stavki u Keychain-u.")
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(f"--- TITAN 1: MASTER KEYCHAIN DUMP ---\n")
        f.write(f"Datum: {os.popen('date /t').read().strip()}\n")
        f.write("=" * 50 + "\n\n")
        
        for item in keychain:
            # Filtriramo bitne stvari: Tokene, Passworde i Session ID-eve
            service = item.get('service', 'N/A')
            account = item.get('account', 'N/A')
            data = item.get('data', 'N/A')
            
            f.write(f"Služba: {service}\n")
            f.write(f"Nalog:  {account}\n")
            f.write(f"Token/Šifra: {data}\n")
            f.write("-" * 30 + "\n")

    print(f"\n✅ KEYCHAIN JE OSLOBOĐEN!")
    print(f"💎 Svi tokeni i lozinke su u: KEYCHAIN_TOKENS.txt")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ KATASTROFA: {e}")
