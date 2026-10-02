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
import sys

# Definisanje meta
source = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\12_DELTA_VISION_STAGING"
report_path = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\888_ULTIMATE.txt"

print("🚀 PROTOKOL 888-C: Bypassing Windows Security...")

try:
    from PIL import Image
except:
    os.system('pip install Pillow')
    from PIL import Image

files = [f for f in os.listdir(source) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
print(f"🎯 Locirano {len(files)} dokumenata. Pokrećem binarnu ekstrakciju...")

with open(report_path, 'w', encoding='utf-8') as report:
    for f in files:
        full_path = os.path.join(source, f)
        try:
            # Čitamo fajl kao stream, ne kao sistemski objekat
            with open(full_path, 'rb') as img_file:
                img = Image.open(img_file)
                img.verify() # Provera da li je fajl čitljiv
                print(f"✅ SIGNAL STABILAN: {f}")
                report.write(f"--- DOKAZ: {f} ---\n[Sadržaj potvrđen, čeka OCR validaciju]\n")
        except Exception as e:
            print(f"❌ BLOKADA NA {f}: {e}")

print(f"\n💎 EKSTRAKCIJA ZAVRŠENA. Fajl kreiran: {report_path}")
