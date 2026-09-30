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
print("🔍 LOV NA BELEŠKE (NOTES) POKRENUT")
print("=" * 50)
passphrase = input("🔑 Unesi tvoju tačnu šifru ponovo: ")

try:
    print("\n⏳ Pristupam trezoru...")
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase=passphrase)

    # Moderne iOS putanje gde Apple krije NoteStore.sqlite
    potential_paths = [
        "AppDomainGroup-group.com.apple.notes/NoteStore.sqlite",
        "AppDomain-com.apple.mobilenotes/Library/Notes/NoteStore.sqlite",
        "HomeDomain/Library/Notes/NoteStore.sqlite"
    ]

    success = False
    for path in potential_paths:
        try:
            out_path = os.path.join(output_dir, "Notes_Decrypted.sqlite")
            backup.extract_file(relative_path=path, output_filename=out_path)
            print(f"✅ BINGO! Beleške su locirane i izvučene sa putanje:\n{path}")
            success = True
            break
        except Exception:
            pass

    if not success:
        print("⚠️ Beleške nisu pronađene ni na jednoj od 3 moderne putanje.")
    
    print("=" * 50)

except Exception as e:
    print(f"\n❌ GREŠKA: {e}")
