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
print("💬 LOV NA WHATSAPP TREZOR POKRENUT")
print("=" * 50)

try:
    print("\n⏳ Pristupam trezoru...")
    # Šifra 2312 je sada ugrađena
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="2312")

    # Standardna iOS putanja za WhatsApp bazu
    wa_path = "AppDomainGroup-group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
    out_path = os.path.join(output_dir, "WhatsApp_Decrypted.sqlite")

    try:
        backup.extract_file(relative_path=wa_path, output_filename=out_path)
        print(f"✅ BINGO! WHATSAPP BAZA JE IZVUČENA: {out_path}")
    except Exception as e:
        print(f"⚠️ Nije uspelo. Razlog: {e}")

    print("=" * 50)

except Exception as e:
    print(f"\n❌ GREŠKA: {e}")
