import pandas as pd
from pathlib import Path
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font

# --- CONFIG ---
TXT_FOLDER = Path("txt_documents")
EXCEL_OUTPUT = "Master_Sheet.xlsx"

# --- Funkcija za čitanje txt fajlova ---
def extract_data(txt_path):
    text = txt_path.read_text(encoding="utf-8")
    project = [line.replace("Project ","") for line in text.splitlines() if "Project" in line][0]
    capex = [float(line.replace("CAPEX €","").strip()) for line in text.splitlines() if "CAPEX" in line][0]
    cod = [int(line.strip()) for line in text.splitlines() if line.strip().isdigit()][0]
    return {"Project":project, "CAPEX (€)":capex, "COD":cod}

# --- Učitavanje podataka ---
all_data = []
for txt_file in TXT_FOLDER.glob("*.txt"):
    info = extract_data(txt_file)
    all_data.append(info)

df = pd.DataFrame(all_data)

# --- Kreiranje Excel-a ---
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Master"

for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
    for c_idx, value in enumerate(row, 1):
        cell = ws.cell(row=r_idx, column=c_idx, value=value)
        if r_idx==1:
            cell.font = Font(bold=True)

wb.save(EXCEL_OUTPUT)
print(f"Master sheet kreiran: {EXCEL_OUTPUT}")