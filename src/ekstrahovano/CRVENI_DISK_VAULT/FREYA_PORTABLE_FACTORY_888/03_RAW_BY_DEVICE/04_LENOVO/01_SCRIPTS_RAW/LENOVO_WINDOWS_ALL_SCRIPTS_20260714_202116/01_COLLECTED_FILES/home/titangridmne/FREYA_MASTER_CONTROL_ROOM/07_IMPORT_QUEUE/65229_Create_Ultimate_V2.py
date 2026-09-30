import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
import re

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
            
            # Kategorija
            if any(x in f_lower for x in ["zakon", "legal", "ugovor", "dozvola", "statut", "memorandum"]):
                kategorija = "Zakoni"
            elif any(x in f_lower for x in ["analiza", "izvještaj", "study", "analysis", "esg", "cbam"]):
                kategorija = "Analize"
            elif any(x in f_lower for x in ["kalkulacija", "budget", "capex", "opex", "financi", "model", "cash flow", "dscr"]):
                kategorija = "Kalkulacije"
            else:
                kategorija = "Aktivni podaci"
            
            # Status
            if any(x in f_lower for x in ["final", "zavrsen", "gotov", "komplet"]):
                status = "Završen"
            elif any(x in f_lower for x in ["hitno", "urgent", "prioritet"]):
                status = "Hitno"
            elif any(x in f_lower for x in ["rad", "draft", "priprema", "u radu"]):
                status = "U radu"
            else:
                status = "Aktivan"
            
            # Rok (pokušaj detekcije datuma)
            rok = "N/A"
            date_match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})|(\d{1,2}\.\d{1,2})', file + str(rel_folder))
            if date_match:
                rok = date_match.group(0)
            
            # Budžet (gruba detekcija)
            budget = "N/A"
            budget_match = re.search(r'(\d{5,})', file)
            if budget_match and any(b in f_lower for b in ["budzet", "budget", "euro", "k", "000"]):
                budget = budget_match.group(0) + " €"
            
            data.append({
                "File Name": file,
                "Extension": filepath.suffix.lower(),
                "Size (MB)": size_mb,
                "Date Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "Folder": str(rel_folder),
                "Kategorija": kategorija,
                "Status": status,
                "Rok": rok,
                "Budžet": budget,
                "Full Path": str(filepath)
            })
        except:
            pass

df = pd.DataFrame(data)
df = df.sort_values(by=["Kategorija", "Status", "Rok", "Folder", "File Name"])

excel_file = "01_Ultimate_Canon_Dashboard_V2.xlsx"

with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All_Files", index=False)
    df.groupby(["Kategorija", "Status"]).size().reset_index(name="Count").to_excel(writer, sheet_name="Kategorije", index=False)

# Profesionalno formatiranje
wb = load_workbook(excel_file)
ws = wb["All_Files"]

# AutoFilter
ws.auto_filter.ref = ws.dimensions

# Frozen panes
ws.freeze_panes = "A2"

# Bojenje Status
status_colors = {"Hitno": "FF0000", "U radu": "FFCC00", "Završen": "00FF00", "Aktivan": "00CCFF"}
for row in range(2, ws.max_row + 1):
    status_cell = ws.cell(row=row, column=7)
    color = status_colors.get(status_cell.value, "FFFFFF")
    status_cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    status_cell.font = Font(bold=True)

# DASHBOARD
ws_dash = wb.create_sheet("DASHBOARD", 0)
ws_dash["A1"] = "ULTIMATE CANON DASHBOARD V2"
ws_dash["A1"].font = Font(size=18, bold=True)

ws_dash["A3"] = "Ukupno fajlova:"
ws_dash["B3"] = len(df)
ws_dash["A4"] = "Last Updated:"
ws_dash["B4"] = datetime.now().strftime("%d.%m.%Y %H:%M")

# Sažetak
cat_summary = df["Kategorija"].value_counts()
row = 6
for cat, cnt in cat_summary.items():
    ws_dash[f"A{row}"] = cat
    ws_dash[f"B{row}"] = cnt
    row += 1

# Bar chart
chart1 = BarChart()
data_ref = Reference(ws_dash, min_col=2, min_row=6, max_row=row-1)
cats_ref = Reference(ws_dash, min_col=1, min_row=6, max_row=row-1)
chart1.add_data(data_ref, titles_from_data=True)
chart1.set_categories(cats_ref)
chart1.title = "Broj fajlova po kategoriji"
ws_dash.add_chart(chart1, "D3")

# Pie chart po Statusu
status_summary = df["Status"].value_counts()
row_s = row + 2
for st, cnt in status_summary.items():
    ws_dash[f"A{row_s}"] = st
    ws_dash[f"B{row_s}"] = cnt
    row_s += 1

chart2 = PieChart()
data_ref2 = Reference(ws_dash, min_col=2, min_row=row+2, max_row=row_s-1)
cats_ref2 = Reference(ws_dash, min_col=1, min_row=row+2, max_row=row_s-1)
chart2.add_data(data_ref2, titles_from_data=True)
chart2.set_categories(cats_ref2)
chart2.title = "Struktura po Statusu"
ws_dash.add_chart(chart2, "D15")

print("✅ ULTIMATE CANON DASHBOARD V2 GOTOV!")
print(f"   Ukupno fajlova: {len(df)}")
print("   Otvori 01_Ultimate_Canon_Dashboard_V2.xlsx")
print("   Prvi sheet je DASHBOARD sa 2 grafa, rokovima i budžetima!")
