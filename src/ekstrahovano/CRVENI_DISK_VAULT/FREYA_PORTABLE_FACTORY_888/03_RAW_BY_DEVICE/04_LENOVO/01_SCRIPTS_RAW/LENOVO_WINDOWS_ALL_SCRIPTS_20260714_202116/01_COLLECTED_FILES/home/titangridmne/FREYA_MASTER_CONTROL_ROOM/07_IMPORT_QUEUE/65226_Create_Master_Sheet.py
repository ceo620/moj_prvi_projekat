import os
import pandas as pd
from datetime import datetime
from pathlib import Path

folder = r"C:\Users\Lenovo\Desktop\888. CANVA FINAL DOKUMNENTA"

data = []
for root, dirs, files in os.walk(folder):
    for file in files:
        if file.startswith("~$") or file.startswith("."):  # preskače temp fajlove
            continue
        filepath = Path(root) / file
        try:
            stat = filepath.stat()
            size_mb = round(stat.st_size / (1024*1024), 2)
            rel_folder = Path(root).relative_to(folder)
            data.append({
                "File Name": file,
                "Extension": filepath.suffix.lower(),
                "Size (MB)": size_mb,
                "Date Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "Folder": str(rel_folder),
                "Full Path": str(filepath)
            })
        except:
            pass

df = pd.DataFrame(data)
df = df.sort_values(by=["Folder", "File Name"])

summary = df.groupby(["Folder", "Extension"]).size().reset_index(name="Count")

excel_file = "01_Master_Sheet.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All_Files", index=False)
    summary.to_excel(writer, sheet_name="Summary", index=False)

print(f"✅ GOTOVO! Kreiran 01_Master_Sheet.xlsx")
print(f"   Ukupno fajlova: {len(df)}")
print("   Otvori ga i vidiš sve na jednom mjestu!")
