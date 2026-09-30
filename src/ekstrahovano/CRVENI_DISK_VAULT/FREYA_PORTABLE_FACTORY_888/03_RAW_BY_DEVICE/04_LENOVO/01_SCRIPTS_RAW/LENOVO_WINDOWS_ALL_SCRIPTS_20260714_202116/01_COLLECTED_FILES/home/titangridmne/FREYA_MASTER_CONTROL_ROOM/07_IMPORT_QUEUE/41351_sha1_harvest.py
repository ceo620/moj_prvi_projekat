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
import shutil
from iphone_backup_decrypt import EncryptedBackup

backup_dir = r"C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C"
out_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TOTAL_HARVEST"
os.makedirs(out_dir, exist_ok=True)

# Apple-ovi univerzalni heševi (Fiksni za sistemske baze)
diamonds = {
    "SMS_Message_Center": "3d0d7e5fb2ce288813306e4d4636395e047a3d28",
    "Call_History": "5a4935c78a5255723f707230a451d79c540d2741",
    "Safari_History": "ac40b170669894e77da441113b2e7c413c66f570",
    "Calendar_Events": "2b4c291c9bc88a5360980d24e5ec084931a3821a",
    "Location_Hinter": "12b144c0bd44122c4acc398c767832672e8f741c"
}

try:
    print("🔓 DEKRIPTOVANJE FIZIČKOG SLOJA...")
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="2312")

    for name, file_hash in diamonds.items():
        # Konstruisanje putanje: prvi 2 karaktera heša su ime foldera
        folder = file_hash[:2]
        source_path = os.path.join(backup_dir, folder, file_hash)
        dest_path = os.path.join(out_dir, f"{name}.sqlite")

        if os.path.exists(source_path):
            try:
                # Dekripcija direktno sa diska bez Manifesta
                backup.decrypt_inner_file(file_hash, dest_path)
                print(f"💎 DIJAMANT OSIGURAN: {name}")
            except Exception as e:
                print(f"⚠️ Greška pri brušenju {name}: {e}")
        else:
            print(f"❌ NIJE PRONAĐEN NA DISKU: {name}")

    print("\n🚀 SKENIRANJE WHATSAPP-A PO VELIČINI (Deep Scan)...")
    # WhatsApp nema fiksni heš, moramo ga naći pretragom
    # Tražimo SQLite fajlove veće od 5MB u backup-u
    count = 0
    for root, dirs, files in os.walk(backup_dir):
        for file in files:
            if len(file) == 40: # Provera da li je SHA1 format
                f_path = os.path.join(root, file)
                if os.path.getsize(f_path) > 5 * 1024 * 1024: # > 5MB
                    try:
                        dest = os.path.join(out_dir, f"POTENTIAL_WA_{count}.sqlite")
                        backup.decrypt_inner_file(file, dest)
                        print(f"📦 IZVUČENA MASIVNA BAZA ({count}) - Verovatno WhatsApp")
                        count += 1
                    except: pass

    print("\n🏁 OPERACIJA ZAVRŠENA. PROVERI TOTAL_HARVEST.")
except Exception as e:
    print(f"FATAL: {e}")
