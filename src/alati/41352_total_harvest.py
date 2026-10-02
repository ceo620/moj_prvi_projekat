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
out_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TOTAL_HARVEST"
os.makedirs(out_dir, exist_ok=True)

targets = {
    "WA_Chat": "AppDomainGroup-group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite",
    "SMS_DB": "HomeDomain/Library/SMS/sms.db",
    "Safari_Hist": "AppDomain-com.apple.mobilesafari/Library/Safari/History.db",
    "Calendar": "HomeDomain/Library/Calendar/Calendar.sqlitedb",
    "Photos_Meta": "CameraRollDomain/Media/PhotoData/Photos.sqlite",
    "Call_Hist": "HomeDomain/Library/CallHistoryDB/CallHistory.storedata",
    "Notes_DB": "AppDomain-com.apple.mobilenotes/Library/Notes/NoteStore.sqlite"
}

try:
    backup = EncryptedBackup(backup_directory=backup_dir, passphrase="2312")
    print("💎 RUDNIK JE OTVOREN. POČINJEM EKSTRAKCIJU DIJAMANATA...")
    
    for name, path in targets.items():
        try:
            dest = os.path.join(out_dir, f"{name}.sqlite")
            backup.extract_file(relative_path=path, output_filename=dest)
            print(f"✅ IZVUČENO: {name}")
        except:
            print(f"❌ NIJE PRONAĐENO: {name}")
            
    print("\n🏆 OPERACIJA ZAVRŠENA. SVE JE U TOTAL_HARVEST FOLDERU.")
except Exception as e:
    print(f"FATALNA GREŠKA: {e}")
