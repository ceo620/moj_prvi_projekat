import os; import pandas as pd; from docx import Document
DIR = 'C:/TITAN_KONACNO'; RAW = 'C:/TITAN_CENTRAL_BRAIN/Raw_Data'
EXCEL = os.path.join(RAW, 'TITAN_Master_Key_Facts_v2.0_DUBLJE.xlsx - STRATEŠKI.csv')

# Čitamo tvoje sirove podatke
facts_text = ""
if os.path.exists(EXCEL):
    df = pd.read_csv(EXCEL); facts = {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows()}
    facts_text = "\n".join([f"- {k}: {v}" for k, v in list(facts.items())[:20]])

doc = Document()
doc.add_heading('01_Executive_Summary - DEEP ANALYSIS', 0)
doc.add_paragraph("PROJEKAT TITAN GRID - ANALIZA SIROVIH PODATAKA")
doc.add_paragraph(f"Lokacija: Tuzi, Montenegro. Vlasnik: Onur (Marel Engineering).")
doc.add_paragraph("\nDETALJNI PODACI IZ RAW_DATA FOLDERA:\n")
doc.add_paragraph(facts_text if facts_text else "Učitavanje sirovih podataka iz Excela... Proveri putanju.")
doc.add_paragraph("\nStatus: SPREMNO ZA INVESTITORA (April 2026)")
doc.save(os.path.join(DIR, "01_Executive_Summary.docx"))
print("🚀 PODACI SU USISANI IZ RAW_DATA U WORD!")
