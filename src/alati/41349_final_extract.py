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
output_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\APPLE_RAW_DB"

print("=" * 50)
print("🔓 TREZOR JE OTVOREN | FINALNA EKSTRAKCIJA")
print("=" * 50)

passphrase = input("🔑 Unesi tačnu šifru koju smo upravo pronašli: ")

try:
    print("\n⏳ Otključavam Apple Manifest...")
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)

    # Tačne putanje za mete
    targets = [
        ("Library/AddressBook/AddressBook.sqlitedb", "Contacts_Decrypted.sqlite"),
        ("Library/Notes/NoteStore.sqlite", "Notes_Decrypted.sqlite")
    ]

    for rel_path, out_name in targets:
        out_path = os.path.join(output_dir, out_name)
        try:
            backup.extract_file(relative_path=rel_path, output_filename=out_path)
            print(f"✅ USPEŠNO DEŠIFROVANO I IZVUČENO: {out_name}")
        except Exception as e:
            print(f"⚠️ Nije uspelo za {out_name}. Razlog: {e}")

    print("\n💎 SVI STRATEŠKI DOKAZI SU SADA U TVOM VDR-u!")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ GREŠKA PRI EKSTRAKCIJI: {e}")
