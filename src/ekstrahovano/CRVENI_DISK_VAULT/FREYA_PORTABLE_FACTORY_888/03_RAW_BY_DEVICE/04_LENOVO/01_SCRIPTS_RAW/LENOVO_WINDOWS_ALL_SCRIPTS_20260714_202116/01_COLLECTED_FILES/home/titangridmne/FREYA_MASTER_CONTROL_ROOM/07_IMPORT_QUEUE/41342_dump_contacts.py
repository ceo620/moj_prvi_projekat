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
import string

db_path = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\APPLE_RAW_DB\Contacts_Decrypted.sqlite"
out_path = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TITAN_KONTAKTI_EKSTRAKCIJA.txt"

print("=" * 50)
print("📊 ČITANJE BAZE KONTAKATA U TOKU...")
print("=" * 50)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Apple iOS format za kontakte (tabela ABPerson i ABMultiValue)
    query = '''
    SELECT 
        IFNULL(ABPerson.First, ''), 
        IFNULL(ABPerson.Last, ''), 
        IFNULL(ABPerson.Organization, ''),
        IFNULL(ABMultiValue.value, '') 
    FROM ABPerson 
    LEFT JOIN ABMultiValue ON ABPerson.ROWID = ABMultiValue.record_id
    WHERE ABMultiValue.value IS NOT NULL
    '''
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("TITAN STRATEŠKI KONTAKTI - SIROVI DUMP\n")
        f.write("=" * 50 + "\n")
        for row in rows:
            first, last, org, value = row
            # Čišćenje brojeva telefona
            value = str(value).replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            line = f"Ime: {first} {last} | Firma: {org} | Kontakt: {value}\n"
            f.write(line)
            
    print(f"✅ USPEŠNO! {len(rows)} kontakata je izvučeno i sačuvano.")
    print(f"📁 Fajl se nalazi ovde: {out_path}")

except Exception as e:
    print(f"⚠️ Apple SQL šema se razlikuje. Pokrećem 'Raw String' ekstrakciju...")
    with open(db_path, "rb") as f, open(out_path, 'w', encoding='utf-8') as out:
        out.write("TITAN KONTAKTI - RAW STRING DUMP\n" + "="*50 + "\n")
        data = f.read().decode('utf-8', 'ignore')
        for line in data.split('\n'):
            if any(char.isdigit() for char in line) and len(line) > 5:
                clean_line = ''.join(filter(lambda x: x in string.printable, line))
                out.write(clean_line.strip() + "\n")
    print(f"✅ Fallback ekstrakcija završena. Proveri fajl: {out_path}")

print("=" * 50)
