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

input_file = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TITAN_KONTAKTI_EKSTRAKCIJA.txt"
memory_file = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\DELTA_MEMORY_CORE.txt"

# Proširena lista ključnih institucija i partnera za TITAN 1
keywords = ["CEDIS", "ECO", "TRANSFORMER", "TUZI", "MIA", "VLADA", "MINISTARSTVO", "OPSTINA", "AGENCIJA", "BANKA", "EBRD", "EIB", "ARS", "METAL"]

print("=" * 50)
print("🧠 DELTA INGESTION: KREIRANJE MEMORIJSKOG JEZGRA")
print("=" * 50)

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    memory_data = []
    for line in lines:
        if any(keyword in line.upper() for keyword in keywords):
            memory_data.append(line.strip())

    with open(memory_file, 'w', encoding='utf-8') as out:
        out.write("--- DELTA STRATEGIC MEMORY CORE ---\n")
        out.write("PROJEKAT: TITAN 1 / ARS METAL INDUSTRIES\n")
        out.write("SADRŽAJ: VERIFIKOVANI STEJKHOLDERI (IZVOR: IPHONE BACKUP)\n")
        out.write("=" * 50 + "\n\n")
        for data in memory_data:
            out.write(data + "\n")
            
    print(f"✅ Memorijsko jezgro komprimirano! Spremno za upload u DELTU.")
    print(f"📁 Otvori fajl: {memory_file}")
    print("=" * 50)

except Exception as e:
    print(f"❌ GREŠKA PRI KREIRANJU MEMORIJE: {e}")
