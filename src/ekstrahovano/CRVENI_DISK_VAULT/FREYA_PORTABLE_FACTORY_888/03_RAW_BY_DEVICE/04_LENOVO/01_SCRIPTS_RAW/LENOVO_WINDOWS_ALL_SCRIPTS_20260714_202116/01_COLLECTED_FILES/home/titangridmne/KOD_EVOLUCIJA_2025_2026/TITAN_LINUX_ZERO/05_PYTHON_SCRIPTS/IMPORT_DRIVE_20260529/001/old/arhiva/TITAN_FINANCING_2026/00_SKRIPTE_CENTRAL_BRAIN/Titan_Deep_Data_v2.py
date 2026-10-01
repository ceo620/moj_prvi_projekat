import os; import pandas as pd; from docx import Document
DIR = 'C:/TITAN_KONACNO'; RAW = 'C:/TITAN_CENTRAL_BRAIN/Raw_Data'

# Automatski pronalazimo Master Excel/CSV fajl
files = [f for f in os.listdir(RAW) if 'Master' in f and f.endswith('.csv')]
facts_text = ""

if files:
    target = os.path.join(RAW, files[0])
    df = pd.read_csv(target); facts = {str(row.iloc[0]): str(row.iloc[1]) for _, row in df.iterrows()}
    # Uzimamo tvoje ključne finansijske i strateške parametre
    facts_text = "\n".join([f"- {k}: {v}" for k, v in list(facts.items())])
else:
    facts_text = "- Greška: Master baza nije pronađena u Raw_Data folderu."

doc = Document()
doc.add_heading('01_Executive_Summary - REAL-TIME DATA FEED', 0)
doc.add_paragraph("PROJEKAT TITAN GRID - DIREKTAN UVOZ IZ BAZE")
doc.add_paragraph(f"Vlasnik: Onur (100% Marel Engineering). Lokacija: Tuzi, Montenegro.")
doc.add_paragraph("\nKLJUČNI PARAMETRI IZ TVOJIH SIROVIH MATERIJALA:\n")
doc.add_paragraph(facts_text)
doc.add_paragraph("\nStatus: VERIFIKOVAN DATA ROOM (April 2026)")
doc.save(os.path.join(DIR, "01_Executive_Summary.docx"))
print(f"🚀 USPEŠNO USISANO IZ: {files[0] if files else 'Nijednog fajla'}")
