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
out_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TOKEN_FINAL"
os.makedirs(out_dir, exist_ok=True)

# Fiksni Apple Heševi za Tokene i Sesije
targets = {
    "Web_Cookies": "341f237f37803d15dae25184b25687796d38e217",
    "System_Accounts": "74b74542713f03b8e4e941f7e0ed3413925c4efd",
    "Keychain_Raw": "d1b54c2a4f475c441b05c93c4e334df56847a961",
    "WhatsApp_Index": "7c7fba66687396602377b21650b2984534164b38"
}

print("=" * 60)
print("🔑 TITAN SHA1 MINER: DIREKTNA EKSTRAKCIJA")
print("=" * 60)

try:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="nasla")
    
    for name, sha1 in targets.items():
        try:
            # Konstruisanje putanje na disku (prva dva slova heša su folder)
            folder = sha1[:2]
            dest = os.path.join(out_dir, f"{name}.decrypted")
            
            # Koristimo unutrašnju funkciju za dekripciju po hešu
            decrypted_data = backup.decrypt_inner_file(sha1)
            with open(dest, 'wb') as f:
                f.write(decrypted_data)
            print(f"✅ IZVUČENO: {name}")
        except Exception as e:
            print(f"❌ NEUSPEH ZA {name}: Fajl verovatno ne postoji u ovom backup-u.")

    print("=" * 60)
    print(f"🏁 HARVEST GOTOV. Rezultati u TOKEN_FINAL folderu.")
except Exception as e:
    print(f"❌ KRITIČNA GREŠKA: {e}")
