import os
import pandas as pd
from datetime import datetime
from pathlib import Path

folder_path = r"C:\Users\Lenovo\Desktop\888. CANVA FINAL DOKUMNENTA"

print("🔍 Skeniram tvoj folder sa stotinama fajlova...")
print(f"Putanja: {folder_path}\n")

data = []
for root, dirs, files in os.walk(folder_path):
    for file in files:
        filepath = Path(root) / file
        try:
            stat = filepath.stat()
            size_mb = round(stat.st_size / (1024*1024), 3)
            data.append({
                "ID": len(data) + 1,
                "File Name": file,
                "Extension": filepath.suffix.lower(),
                "Size (MB)": size_mb,
                "Date Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "Folder": Path(root).relative_to(folder_path),
                "Full Path": str(filepath)
            })
        except:
            pass

df = pd.DataFrame(data)

summary = df.groupby("Extension").agg(
    Count=("File Name", "count"),
    Total_Size_MB=("Size (MB)", "sum")
).round(3).sort_values(by="Count", ascending=False)

print(f"✅ Pronađeno ukupno {len(df)} fajlova")
print("\n📊 SAŽETAK PO TIPOVIMA:")
print(summary)

excel_file = "01_Master_Inventory.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All_Files", index=False)
    summary.to_excel(writer, sheet_name="Summary_by_Type")

print(f"\n🎉 GOTOVO! Kreiran fajl: {excel_file}")
print("   Otvori ga i konačno vidiš šta je unutra!")
