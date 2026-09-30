import os
import pandas as pd
from datetime import datetime
from pathlib import Path

folder = r"C:\Users\Lenovo\Desktop\888. CANVA FINAL DOKUMNENTA"

data = []
for root, dirs, files in os.walk(folder):
    for file in files:
        if file.startswith("~$") or file.startswith("."): continue
        filepath = Path(root) / file
        try:
            stat = filepath.stat()
            size_mb = round(stat.st_size / (1024*1024), 2)
            rel_folder = str(Path(root).relative_to(folder))
            data.append({
                "File Name": file,
                "Extension": filepath.suffix.lower(),
                "Size (MB)": size_mb,
                "Date Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "Folder": rel_folder,
                "Full Path": str(filepath)
            })
        except:
            pass

df = pd.DataFrame(data)

# Pametna kategorizacija na osnovu imena foldera i fajlova
def categorize(row):
    f = row["Folder"].lower() + " " + row["File Name"].lower()
    if any(x in f for x in ["zakon", "legal", "ugovor", "dozvola", "statut", "memorandum"]):
        return "Zakoni"
    elif any(x in f for x in ["analiza", "izvještaj", "study", "analysis", "esg", "cbam"]):
        return "Analize"
    elif any(x in f for x in ["kalkulacija", "budget", "capex", "opex", "financi", "model", "cash flow", "dscr"]):
        return "Kalkulacije"
    else:
        return "Aktivni podaci"

df["Kategorija"] = df.apply(categorize, axis=1)

# Sažetak
summary = df.groupby(["Kategorija", "Folder"]).size().reset_index(name="Count")

excel_file = "01_Master_Sheet.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All_Files", index=False)
    summary.to_excel(writer, sheet_name="Kategorije", index=False)

print(f"✅ GOTOVO! Kreiran pametni 01_Master_Sheet.xlsx")
print(f"   Ukupno fajlova: {len(df)}")
print("   Otvori ga i vidiš sve razvrstano po Zakoni / Analize / Kalkulacije / Aktivni podaci")
