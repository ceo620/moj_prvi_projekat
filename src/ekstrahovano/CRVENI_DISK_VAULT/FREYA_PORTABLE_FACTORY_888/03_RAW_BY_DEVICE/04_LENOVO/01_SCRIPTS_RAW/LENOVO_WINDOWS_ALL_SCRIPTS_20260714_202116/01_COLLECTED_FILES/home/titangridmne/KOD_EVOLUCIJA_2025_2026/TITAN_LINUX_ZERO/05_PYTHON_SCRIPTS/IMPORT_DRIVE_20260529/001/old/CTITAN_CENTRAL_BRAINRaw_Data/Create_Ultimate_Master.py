import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.chart import BarChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows

folder = r"C:\Users\Lenovo\Desktop\888. CANVA FINAL DOKUMNENTA"

data = []
for root, dirs, files in os.walk(folder):
    for file in files:
        if file.startswith("~$") or file.startswith("."):
            continue
        filepath = Path(root) / file
        try:
            stat = filepath.stat()
            size_mb = round(stat.st_size / (1024*1024), 2)
            rel_folder = Path(root).relative_to(folder)
            
            f_lower = (str(rel_folder) + " " + file).lower()
            
            # Kategorija (isto kao prije)
            if any(x in f_lower for x in ["zakon", "legal", "ugovor", "dozvola", "statut", "memorandum"]):
                kategorija = "Zakoni"
            elif any(x in f_lower for x in ["analiza", "izvještaj", "study", "analysis", "esg", "cbam"]):
                kategorija = "Analize"
            elif any(x in f_lower for x in ["kalkulacija", "budget", "capex", "opex", "financi", "model", "cash flow", "dscr"]):
                kategorija = "Kalkulacije"
            else:
                kategorija = "Aktivni podaci"
            
            # Status (novo)
            if any(x in f_lower for x in ["final", "zavrsen", "gotov", "komplet"]):
                status = "Završen"
            elif any(x in f_lower for x in ["hitno", "urgent", "rok", "deadline", "prioritet"]):
                status = "Hitno"
            elif any(x in f_lower for x in ["rad", "draft", "priprema", "u radu"]):
                status = "U radu"
            else:
                status = "Aktivan"
            
            data.append({
                "File Name": file,
                "Extension": filepath.suffix.lower(),
                "Size (MB)": size_mb,
                "Date Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "Folder": str(rel_folder),
                "Kategorija": kategorija,
                "Status": status,
                "Full Path": str(filepath)
            })
        except:
            pass

df = pd.DataFrame(data)
df = df.sort_values(by=["Kategorija", "Status", "Folder", "File Name"])

# Sažetak
summary = df.groupby(["Kategorija", "Status"]).size().reset_index(name="Count")

excel_file = "01_Ultimate_Canon_Dashboard.xlsx"

with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All_Files", index=False)
    summary.to_excel(writer, sheet_name="Kategorije", index=False)

# Otvaramo workbook da dodamo boje i grafove
wb = load_workbook(excel_file)
ws_all = wb["All_Files"]
ws_cat = wb["Kategorije"]

# Bojenje Status kolone
status_colors = {
    "Hitno": "FF0000",      # crveno
    "U radu": "FFCC00",     # žuto
    "Završen": "00FF00",    # zeleno
    "Aktivan": "00CCFF"     # plavo
}
for row in range(2, ws_all.max_row + 1):
    status_cell = ws_all.cell(row=row, column=7)  # kolona Status
    color = status_colors.get(status_cell.value, "FFFFFF")
    status_cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    status_cell.font = Font(color="000000", bold=True)

# Dashboard sheet
ws_dash = wb.create_sheet("DASHBOARD", 0)
ws_dash["A1"] = "ULTIMATE CANON DASHBOARD"
ws_dash["A1"].font = Font(size=16, bold=True)

ws_dash["A3"] = "Ukupno fajlova:"
ws_dash["B3"] = len(df)

# Sažetak po kategoriji
cat_summary = df["Kategorija"].value_counts()
row = 5
for cat, cnt in cat_summary.items():
    ws_dash[f"A{row}"] = cat
    ws_dash[f"B{row}"] = cnt
    row += 1

# Bar chart po kategorijama
chart = BarChart()
data_ref = Reference(ws_dash, min_col=2, min_row=5, max_row=8, max_col=2)
cats_ref = Reference(ws_dash, min_col=1, min_row=5, max_row=8)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
chart.title = "Broj fajlova po kategoriji"
ws_dash.add_chart(chart, "D3")

print("✅ ULTIMATE CANON DASHBOARD GOTOV!")
print(f"   Ukupno fajlova: {len(df)}")
print("   Otvori 01_Ultimate_Canon_Dashboard.xlsx")
print("   Prvi sheet je DASHBOARD sa grafovima i bojama!")
