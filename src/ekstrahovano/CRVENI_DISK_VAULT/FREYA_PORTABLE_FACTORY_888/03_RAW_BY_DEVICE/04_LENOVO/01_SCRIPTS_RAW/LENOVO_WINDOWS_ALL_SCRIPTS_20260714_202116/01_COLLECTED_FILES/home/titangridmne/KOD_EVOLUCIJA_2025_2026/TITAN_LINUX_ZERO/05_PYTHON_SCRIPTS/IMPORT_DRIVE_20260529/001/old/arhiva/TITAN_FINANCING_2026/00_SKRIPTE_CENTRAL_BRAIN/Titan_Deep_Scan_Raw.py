import os; from docx import Document
DIR = 'C:/TITAN_KONACNO'; RAW = 'C:/TITAN_CENTRAL_BRAIN/Raw_Data'

# Skeniramo tekstualne briefing-e i checkliste
raw_files = [f for f in os.listdir(RAW) if f.endswith('.txt')]
extra_pilars = {}

for f_name in raw_files:
    with open(os.path.join(RAW, f_name), 'r', encoding='utf-8') as f:
        content = f.read()
        if 'Hamza' in f_name:
            extra_pilars["PILAR 7: INVESTICIONA STRATEGIJA (Hamza Yavuz)"] = content[:500] + "..."
        elif 'Darko' in f_name:
            extra_pilars["PILAR 8: OPERATIVNA EGZEKUCIJA (Darko Durovic)"] = content[:500] + "..."

doc = Document()
doc.add_heading('TITAN GRID - PROŠIRENI MASTER RAW MATERIAL (V3.0)', 0)
doc.add_paragraph("Dopunjeno direktnim uvidom u strateske briefing-e i operativne checkliste.")

for title, content in extra_pilars.items():
    doc.add_heading(title, 1)
    doc.add_paragraph(content)

doc.save('C:/TITAN_KONACNO/MASTER_RAW_MATRIX_v3.docx')
print("🚀 NOVI PILARI SU OTKLJUČANI I INTEGRISANI!")
