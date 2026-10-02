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
try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("⏳ Instaliram potrebne 'vidne' senzore (Pillow)...")
    os.system('pip install Pillow')
    from PIL import Image

staging_dir = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\12_DELTA_VISION_STAGING"
output_file = r"C:\Users\titangrid.info\Desktop\ARS METAL INDUSTRIES DOO\09_iPhone_Strategic_Mine\DELTA_COMMAND\TITAN_SIGNAL_DUMP.txt"

print("=" * 50)
print("🧠 PYTHON VISION: DUBINSKO SKENIRANJE")
print("=" * 50)

files = [f for f in os.listdir(staging_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

with open(output_file, 'w', encoding='utf-8') as report:
    report.write("--- MASTER SIGNAL HARVEST: PYTHON OCR ---n")
    for f_name in files:
        full_path = os.path.join(staging_dir, f_name)
        print(f"🔍 Obrađujem: {f_name}")
        try:
            img = Image.open(full_path)
            # Ovde bi išao Tesseract poziv ako je instaliran
            # Ako nije, samo proveravamo integritet fajla
            print(f"✅ Fajl {f_name} je otvoren i validan.")
            report.write(f"\n[DOKAZ: {f_name}]\n(Sadržaj spreman za vizuelni pregled)\n")
        except Exception as e:
            print(f"❌ Greška na {f_name}: {e}")

print("=" * 50)
