import json, os
from datetime import datetime
from docx import Document
from docx.shared import Pt

# Učitaj registre
with open("00_MASTER_TOKEN_AUTHORITY/MASTER_TOKEN_REGISTER.json") as f:
    master = json.load(f)
with open("00_MASTER_TOKEN_AUTHORITY/DOCUMENT_SCOPE_POLICY.json") as f:
    policy = json.load(f)

print("🔒 CTOS — Controlled Generation (ANEKS 1)")
print(f"   Scope: {master['scope']}")
print(f"   Canonical CAPEX: {master['canonical_capex_label']}\n")

doc = Document()
doc.styles['Normal'].font.name = 'Calibri'
doc.styles['Normal'].font.size = Pt(11)

doc.add_heading('ANEKS 1', 0).alignment = 1
doc.add_heading('REVIZIJA CAPEX OKVIRA ZA PROJEKAT TITAN 1', 1).alignment = 1
doc.add_paragraph(f'Datum: 2026-05-10\n')

text = f"""Ovaj Aneks 1 odnosi se isključivo na projekat:

{master['canonical_project_name']}

Nosilac projekta:
{master['canonical_company']}

Lokacija projekta:
{master['canonical_location']}, Crna Gora

Ovaj Aneks ne odnosi se na projekte TITAN 2 i TITAN 3 niti predstavlja zahtjev ili dokumentaciju za njihove buduće faze razvoja.

3. AŽURIRANI CAPEX OKVIR

Ažurirani CAPEX okvir za TITAN 1:
{master['canonical_capex_label']}

4. STATUS DOKUMENTA

Ovaj Aneks predstavlja prateće objašnjenje uz postojeću projektnu dokumentaciju i koristi se isključivo za potrebe institucionalne komunikacije."""

for paragraph in text.split('\n'):
    if paragraph.strip():
        doc.add_paragraph(paragraph)

doc.add_paragraph('\nSa poštovanjem,')
doc.add_paragraph('DANIJELA KESKIN')
doc.add_paragraph('Director')
doc.add_paragraph('Ars Metal Industries D.O.O. Podgorica')

filename = "ANEKS_1_REVIZIJA_CAPEX_TITAN1_2026-05-10.docx"
doc.save(filename)

print(f"\n✅ ANEKS 1 generisan: {filename}")
print("   Generisan isključivo iz MASTER_TOKEN_REGISTER + DOCUMENT_SCOPE_POLICY")
print("   Spreman za manual review i human signoff.")
