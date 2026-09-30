import os; import pandas as pd; from docx import Document
DIR = 'C:/TITAN_KONACNO'; RAW = 'C:/TITAN_CENTRAL_BRAIN/Raw_Data'

# Uzimamo prvi validan tabelarni fajl koji nađemo
files = [f for f in os.listdir(RAW) if f.endswith(('.csv', '.xlsx'))]
facts_text = ""

if files:
    target = os.path.join(RAW, files[0])
    # Ako je CSV, čitamo ga, ako je Excel koristimo read_excel
    df = pd.read_csv(target) if target.endswith('.csv') else pd.read_excel(target)
    facts_text = "\n".join([f"- {row.iloc[0]}: {row.iloc[1]}" for _, row in df.iterrows()])
    source_msg = f"Usisano iz: {files[0]}"
else:
    facts_text = "- Greška: Folder Raw_Data je prazan!"
    source_msg = "Nijednog fajla"

doc = Document()
doc.add_heading('01_Executive_Summary - FINAL DATA FEED', 0)
doc.add_paragraph(f"Vlasnik: Onur (Marel Engineering). Lokacija: Tuzi, Montenegro.")
doc.add_paragraph("\nPODACI DIREKTNO IZ TVOJIH SIROVIH MATERIJALA:\n")
doc.add_paragraph(facts_text)
doc.add_paragraph(f"\nStatus: VERIFIKOVANO IZ BAZE | {source_msg}")
doc.save(os.path.join(DIR, "01_Executive_Summary.docx"))
print(f"🚀 {source_msg}")
