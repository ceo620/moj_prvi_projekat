import pandas as pd
from pdfminer.high_level import extract_text
import os
from datetime import datetime

# ✅ TVOJ FOLDER SA PDF
BASE = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\DATA_ROOM_FINAL_PDF"

OUTPUT = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT\EXTRACTION.xlsx"

rules = {
    "€": ("CAPEX","Amount","CRITICAL"),
    "cost": ("OPEX","Cost","HIGH"),
    "energy": ("OPEX","Energy","HIGH"),
    "akciz": ("TAX","Excise","HIGH"),
    "tax": ("TAX","Tax","HIGH"),
    "dscr": ("FINANCING","DSCR","CRITICAL"),
    "irr": ("FINANCING","IRR","CRITICAL"),
    "risk": ("RISK","Risk","HIGH")
}

rows = []
ID = 1

for root, dirs, files in os.walk(BASE):
    for file in files:
        if file.lower().endswith(".pdf"):

            path = os.path.join(root, file)
            print("▶ Processing:", file)

            try:
                text = extract_text(path)
            except:
                continue

            for line in text.split("\n"):
                clean = line.lower().strip()

                if len(clean) < 10:
                    continue

                for key, (pillar, sub, level) in rules.items():
                    if key in clean:

                        rows.append({
                            "ID": ID,
                            "Source": file,
                            "Value": line.strip(),
                            "Pillars": pillar,
                            "Sub": sub,
                            "Level": level,
                            "Date": datetime.today().strftime('%Y-%m-%d')
                        })

                        ID += 1
                        break

os.makedirs(r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT", exist_ok=True)

df = pd.DataFrame(rows)
df.to_excel(OUTPUT, index=False)

print("\n✅ DONE →", OUTPUT)