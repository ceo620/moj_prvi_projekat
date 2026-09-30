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

﻿from iphone_backup_decrypt import EncryptedBackup

backup_dir = r"C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C"

print("=" * 50)
print("🛡️ DELTA KEY-CRACKER POKRENUT")
print("=" * 50)

# Unos više šifri, odvojenih zarezom
passwords_input = input("🔑 Unesi moguće šifre (odvojene zarezom): ")
passwords = [p.strip() for p in passwords_input.split(',')]

success = False
for pwd in passwords:
    try:
        print(f"⏳ Testiram šifru: '{pwd}'...")
        backup = EncryptedBackup(backup_directory=backup_dir, passphrase=pwd)
        # Pokušavamo da izvučemo mali fajl čisto kao test
        backup.extract_file(relative_path="Library/AddressBook/AddressBook.sqlitedb", output_filename="test.sqlite")
        print(f"✅ BINGO! PRAVA ŠIFRA JE: {pwd}")
        success = True
        break
    except Exception:
        print(f"❌ Netačno.")

if not success:
    print("\n⚠️ Nijedna od unetih šifri nije otključala trezor.")
