import pandas as pd
from pdfminer.high_level import extract_text
from datetime import date

# INPUT PDF (promijeni putanju ako treba)
INPUT = r"C:\Users\Lenovo\Desktop\Zakon-o-akcizama-1 (1).pdf"

# OUTPUT Excel
OUTPUT = r"C:\Users\Lenovo\Desktop\TITAN_PILLARS.xlsx"

print("▶ Pokrećem ekstrakciju...")

text = extract_text(INPUT)

keywords = [
    "energ", "električ", "akciz", "gorivo",
    "skladi", "proizvod", "uvoz",
    "transport", "odloženo", "carina"
]

rows = []
i = 1

for line in text.split("\n"):
    if any(k in line.lower() for k in keywords):
        rows.append({
            "ID": i,
            "Source": "Zakon o akcizama",
            "Truth": "YES",
            "Value": line.strip(),
            "IC_DOC": "IC_REG_01",
            "Doc_Name": "Excise Law",
            "Pillars": "AUTO",
            "Sub": "Extracted",
            "DNA": "TITAN_CORE",
            "Level": "HIGH",
            "Owner": "CFO",
            "Date": str(date.today()),
            "Priority": "HIGH",
            "Notes": "",
            "Project_Phase": "ALL",
            "Sensitivity_Flag": "MEDIUM"
        })
        i += 1

df = pd.DataFrame(rows)

df.to_excel(OUTPUT, index=False)

print("✅ GOTOVO → Excel na Desktopu")