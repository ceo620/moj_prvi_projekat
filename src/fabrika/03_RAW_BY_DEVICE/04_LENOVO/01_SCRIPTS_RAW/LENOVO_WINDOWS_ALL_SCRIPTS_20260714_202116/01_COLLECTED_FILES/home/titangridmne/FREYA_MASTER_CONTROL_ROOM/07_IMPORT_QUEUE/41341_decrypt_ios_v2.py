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
print("🛡️ APPLE AES-256 DEŠIFROVANJE - SEKVENCA 2")
print("=" * 50)

try:
    print("\n⏳ Inicijalizujem dekripcijski modul...")
    # Popravljen parametar: backup_directory
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="Marel888")
    print("✅ Enkripcija probijena! Pristup Manifestu odobren.\n")

    # Tačne putanje unutar Apple fajl sistema
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

    print("\n💎 OPERACIJA ZAVRŠENA.")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ SISTEMSKA GREŠKA: {e}")
