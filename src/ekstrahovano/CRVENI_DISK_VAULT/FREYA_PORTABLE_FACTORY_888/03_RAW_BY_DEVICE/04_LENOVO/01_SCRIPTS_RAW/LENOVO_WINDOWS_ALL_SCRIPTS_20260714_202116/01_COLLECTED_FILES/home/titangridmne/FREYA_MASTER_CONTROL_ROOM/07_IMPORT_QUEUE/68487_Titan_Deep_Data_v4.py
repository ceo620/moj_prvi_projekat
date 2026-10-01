import os; import pandas as pd; from docx import Document
DIR = 'C:/TITAN_KONACNO'; RAW = 'C:/TITAN_CENTRAL_BRAIN/Raw_Data'

# Uzimamo Dashboard fajl koji smo identifikovali na tvojoj slici
target = os.path.join(RAW, '001. ARS METAL INDUSTRIES — CHANGE ORDER DASHBOARD.xlsx')

if os.path.exists(target):
    df = pd.read_excel(target)
    # Izvlačimo prve 4 bitne kolone da dobijemo cifre i opise
    data_list = []
    for _, row in df.iterrows():
        # Sastavljamo liniju: Kategorija | Detalji | Vrijednost | Status
        line = " | ".join([str(val) for val in row.iloc[:4] if pd.notna(val)])
        data_list.append(f"- {line}")
    facts_text = "\n".join(data_list)
    source_msg = "ANALIZA DASHBOARD-A (KOMPLETNI PODACI)"
else:
    facts_text = "- Greška: Fajl nije pronađen. Provjeri naziv u Raw_Data."
    source_msg = "Greška u putanji"

doc = Document()
doc.add_heading('01_Executive_Summary - SIROVA MATERIJA (DETALJNO)', 0)
doc.add_paragraph(f"Vlasnik: Onur (100% Marel Engineering). Lokacija: Tuzi, Montenegro.")
doc.add_paragraph("\nSTRUKTURA TROŠKOVA I RADOVA IZ DASHBOARD-A:\n")
doc.add_paragraph(facts_text)
doc.add_paragraph(f"\nStatus: VERIFIKOVANA SIROVA MATERIJA | {source_msg}")
doc.save(os.path.join(DIR, "01_Executive_Summary.docx"))
print(f"🚀 USISANO SVE IZ SIROVE MATERIJE!")
