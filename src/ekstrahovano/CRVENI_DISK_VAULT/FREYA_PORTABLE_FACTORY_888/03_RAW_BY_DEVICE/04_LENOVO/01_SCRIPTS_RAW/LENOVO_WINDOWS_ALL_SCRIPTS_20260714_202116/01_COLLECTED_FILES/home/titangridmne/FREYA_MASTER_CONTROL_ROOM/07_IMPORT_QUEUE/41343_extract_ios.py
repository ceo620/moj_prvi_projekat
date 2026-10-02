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

﻿import sqlite3
import os
import shutil

# Putanje
vdr_path = r'C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO'
backup_dir = r'C:\Users\titangrid.info\Apple\MobileSync\Backup\00008150-001564A40C40401C'
raw_db_path = os.path.join(vdr_path, r'09_iPhone_Strategic_Mine\DELTA_COMMAND\APPLE_RAW_DB')
manifest_path = os.path.join(raw_db_path, 'Manifest.db')

# Povezivanje na krunski ključ
conn = sqlite3.connect(manifest_path)
cursor = conn.cursor()

# Mete koje tražimo u bazi (SQL LIKE sintaksa)
targets = {
    'Notes': '%NoteStore.sqlite%',
    'Contacts': '%AddressBook.sqlitedb%',
    'Viber': '%viber.sqlite%',
    'WhatsApp': '%ChatStorage.sqlite%'
}

print('\n🔍 PRETRAŽUJEM APPLE MANIFEST ZA STRATEŠKIM METAMA...')
print('-' * 50)

for name, pattern in targets.items():
    cursor.execute('SELECT fileID, relativePath FROM Files WHERE relativePath LIKE ?', (pattern,))
    results = cursor.fetchall()

    if results:
        for file_id, rel_path in results:
            # U Apple backup-u, fajl je u folderu koji nosi ime prva 2 karaktera hash-a
            folder_prefix = file_id[:2]
            source_file = os.path.join(backup_dir, folder_prefix, file_id)
            
            # Pravimo bezbedno i čitljivo ime za naš VDR
            safe_name = f"{name}_{os.path.basename(rel_path)}"
            dest_file = os.path.join(raw_db_path, safe_name)

            if os.path.exists(source_file):
                shutil.copy2(source_file, dest_file)
                print(f'✅ {name} LOCIRAN I IZVUČEN: {safe_name}')
            else:
                print(f'⚠️ Fajl za {name} je u manifestu, ali nije preuzet (možda cloud-only).')
    else:
        print(f'❌ {name} nije lociran u lokalnom Manifestu.')

conn.close()
print('-' * 50)
print('💎 AUTOMATSKA EKSTRAKCIJA ZAVRŠENA.')
