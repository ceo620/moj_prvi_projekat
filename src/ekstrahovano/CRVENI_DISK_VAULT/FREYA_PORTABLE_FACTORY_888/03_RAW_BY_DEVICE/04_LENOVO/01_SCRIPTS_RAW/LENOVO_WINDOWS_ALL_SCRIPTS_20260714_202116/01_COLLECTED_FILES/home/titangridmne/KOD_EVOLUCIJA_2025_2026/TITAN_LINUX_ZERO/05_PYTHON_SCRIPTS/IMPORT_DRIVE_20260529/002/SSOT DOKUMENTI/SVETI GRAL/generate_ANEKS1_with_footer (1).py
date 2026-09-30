import json, os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

with open("00_MASTER_TOKEN_AUTHORITY/MASTER_TOKEN_REGISTER.json") as f:
    master = json.load(f)

print("🔒 CTOS — ANEKS 1 with EU Footer")

doc = Document()
doc.styles['Normal'].font.name = 'Calibri'
doc.styles['Normal'].font.size = Pt(11)

# Naslov
doc.add_heading('ANEKS 1', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_heading('REVIZIJA CAPEX OKVIRA ZA PROJEKAT TITAN 1', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph(f'Datum: 2026-05-10\n').alignment = WD_ALIGN_PARAGRAPH.CENTER

text = f"""Ovaj Aneks 1 odnosi se isključivo na projekat TITAN 1.

Nosilac projekta:
{master['canonical_company']}

Lokacija projekta:
{master['canonical_location']}, Crna Gora

3. AŽURIRANI CAPEX OKVIR

Ažurirani CAPEX okvir za TITAN 1:
{master['canonical_capex_label']}

4. STATUS DOKUMENTA

Ovaj Aneks predstavlja prateće objašnjenje uz postojeću projektnu dokumentaciju i koristi se isključivo za potrebe institucionalne komunikacije i preliminarnog usklađivanja."""

for paragraph in text.split('\n'):
    if paragraph.strip():
        doc.add_paragraph(paragraph)

doc.add_paragraph('\nSa poštovanjem,')
doc.add_paragraph('DANIJELA KESKIN')
doc.add_paragraph('Director')
doc.add_paragraph('Ars Metal Industries D.O.O. Podgorica')

# === EU STYLE FOOTER ===
section = doc.sections[0]
footer = section.footer
p = footer.paragraphs[0]
p.text = ""
p.add_run("Ars Metal Industries D.O.O. Podgorica  |  TITAN 1").bold = True
p.alignment = WD_ALIGN_PARAGRAPH.LEFT

run = p.add_run("                                      Stranica ")
run.font.color.rgb = RGBColor(0, 51, 153)  # EU plava
run = p.add_run("X")
run.font.color.rgb = RGBColor(0, 51, 153)
p.add_run(" od Y")

p.add_run("                                      2026-05-10  |  CONFIDENTIAL – INTERNAL USE ONLY").font.color.rgb = RGBColor(0, 51, 153)

filename = "ANEKS_1_REVIZIJA_CAPEX_TITAN1_EU_FOOTER_2026-05-10.docx"
doc.save(filename)

print(f"\n✅ ANEKS 1 sa EU footerom generisan: {filename}")
print("   Footer: EU plava + broj stranice + povjerljivost")
print("   Spreman za tablet i institutionalni paket.")
