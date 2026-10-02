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
output_file = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\STRATESKE_METE.txt"

# Ključne reči koje tražimo u kontaktima
keywords = ["CEDIS", "ECO", "TRANSFORMER", "TUZI", "MIA", "VLADA", "MINISTARSTVO", "OPSTINA", "AGENCIJA"]

print("=" * 50)
print("🎯 LASERSKO SKENIRANJE STRATEŠKIH KONTAKATA")
print("=" * 50)

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    found_targets = []
    for line in lines:
        if any(keyword in line.upper() for keyword in keywords):
            found_targets.append(line.strip())

    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("TITAN 1 - STRATEŠKI KONTAKTI ZA V3 DOKUMENT\n")
        out.write("=" * 50 + "\n")
        if found_targets:
            for target in found_targets:
                out.write(target + "\n")
            print(f"✅ BINGO! Pronađeno {len(found_targets)} strateških meta.")
        else:
            print("⚠️ Nisu pronađeni kontakti sa zadatim ključnim rečima.")
            out.write("Nema poklapanja.\n")

    print(f"📁 Rezultati su sačuvani u: {output_file}")
    print("=" * 50)

except Exception as e:
    print(f"❌ GREŠKA: {e}")
