import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font

# --- CONFIG ---
TXT_FOLDER = Path("txt_documents")     # folder s txt fajlovima
EXCEL_FOLDER = Path(".")               # folder za izlazni Excel
EXCEL_OUTPUT = EXCEL_FOLDER / "Ultimate_Canon_Master.xlsx"

# --- Funkcija za parsiranje txt fajlova ---
def extract_txt_data(txt_path):
    text = txt_path.read_text(encoding="utf-8")
    project = [line.replace("Project ","") for line in text.splitlines() if "Project" in line][0]
    capex = [float(line.replace("CAPEX €","").strip()) for line in text.splitlines() if "CAPEX" in line][0]
    cod = [int(line.strip()) for line in text.splitlines() if line.strip().isdigit()][0]
    return {"Project":project, "CAPEX (€)":capex, "COD":cod, "Source":txt_path.name, "Verified":True}

# --- Opcionalno: čitanje starih Excel fajlova ---
def extract_excel_data(file_path):
    df = pd.read_excel(file_path)
    # Pretpostavimo da Excel ima kolone: Project, CAPEX (€), COD
    df["Source"] = file_path.name
    df["Verified"] = True
    return df

# --- Agregacija svih izvora ---
all_records = []

# Učitavanje txt fajlova
if TXT_FOLDER.exists():
    for txt_file in TXT_FOLDER.glob("*.txt"):
        all_records.append(extract_txt_data(txt_file))

# (Opcionalno) Učitavanje Excel fajlova iz istog foldera
for xls_file in EXCEL_FOLDER.glob("*.xlsx"):
    if xls_file.name != EXCEL_OUTPUT.name:
        all_records.append(extract_excel_data(xls_file))

# --- Kreiranje DataFrame ---
df_list = []
for rec in all_records:
    if isinstance(rec, dict):
        df_list.append(pd.DataFrame([rec]))
    else:
        df_list.append(rec)

df_master = pd.concat(df_list, ignore_index=True)

# --- Kreiranje Excel Master sheet-a ---
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Master"

for r_idx, row in enumerate(dataframe_to_rows(df_master, index=False, header=True),1):
    for c_idx, value in enumerate(row,1):
        cell = ws.cell(row=r_idx, column=c_idx, value=value)
        if r_idx==1:
            cell.font = Font(bold=True)

# --- Dodavanje Pivot-like Stacked Bar Chart ---
chart = BarChart()
chart.type = "col"
chart.style = 10
chart.title = "CAPEX by Project & COD"
chart.y_axis.title = "Amount (€)"
chart.x_axis.title = "Project-COD"

# Dodavanje serija (Phase ili CAPEX)
# Za jednostavnost koristimo Amount (€) kolonu
values = Reference(ws, min_col=df_master.columns.get_loc("CAPEX (€)")+1,
                   min_row=2, max_row=1+len(df_master))
chart.add_data(values, titles_from_data=False)

# X-axis: Project-COD kategorije
for i, row in enumerate(df_master.itertuples(), start=2):
    ws.cell(row=i, column=len(df_master.columns)+1, value=f"{row.Project}-{row.COD}")

cats = Reference(ws, min_col=len(df_master.columns)+1, min_row=2, max_row=1+len(df_master))
chart.set_categories(cats)
ws.add_chart(chart, "H2")

# --- Spremi Excel ---
wb.save(EXCEL_OUTPUT)
print(f"Ultimate Canon Master Excel kreiran: {EXCEL_OUTPUT}")