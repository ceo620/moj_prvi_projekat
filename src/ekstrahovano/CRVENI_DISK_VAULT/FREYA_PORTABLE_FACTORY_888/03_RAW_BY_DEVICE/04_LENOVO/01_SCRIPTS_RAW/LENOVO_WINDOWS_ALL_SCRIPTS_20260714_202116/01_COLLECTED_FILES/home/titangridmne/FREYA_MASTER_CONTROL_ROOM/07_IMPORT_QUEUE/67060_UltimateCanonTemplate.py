import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font
import os

# Folder gdje se nalazi txt_documents
TXT_FOLDER = "txt_documents"
EXCEL_OUTPUT = "Ultimate_Canon_Template.xlsx"

# Primjer podataka za Master sheet
data = {
    "Source": ["Chat1", "Chat2", "File1"],
    "Project": ["TITAN", "ECO", "ARS"],
    "Scenario": ["Base", "Upside", "Downside"],
    "Phase": ["Construction", "Pre-Construction", "Operations"],
    "Type": ["CAPEX", "CAPEX", "OPEX"],
    "Amount (€)": [1000000, 500000, 200000],
    "COD": [2027, 2028, 2027],
    "Verified": [True, True, False]
}

df = pd.DataFrame(data)

# Kreiranje Excel fajla
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Master"

for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
    for c_idx, value in enumerate(row, 1):
        cell = ws.cell(row=r_idx, column=c_idx, value=value)
        if r_idx == 1:
            cell.font = Font(bold=True)

# Dodavanje primjera graf-a
chart = BarChart()
chart.type = "col"
chart.title = "Example CAPEX/OPEX by Project-Scenario"
chart.y_axis.title = "Amount (€)"
chart.x_axis.title = "Project-Scenario"
values = Reference(ws, min_col=6, min_row=2, max_row=4)
chart.add_data(values, titles_from_data=True)
cats = Reference(ws, min_col=2, min_row=2, max_row=4)
chart.set_categories(cats)
ws.add_chart(chart, "H2")

wb.save(EXCEL_OUTPUT)
print(f"Excel template kreiran: {EXCEL_OUTPUT}")