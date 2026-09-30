import json, os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

with open("00_MASTER_TOKEN_AUTHORITY/MASTER_TOKEN_REGISTER_v4.0.json") as f:
    master = json.load(f)

print("🔒 CTOS — Professional & Institutional ANEKS 1 (final)")

doc = Document()
doc.sections[0].top_margin = Inches(1)
doc.sections[0].bottom_margin = Inches(1)
doc.sections[0].left_margin = Inches(1)
doc.sections[0].right_margin = Inches(1)

# Header (logo placeholder)
header = doc.sections[0].header
h = header.paragraphs[0]
h.text = "Ars Metal Industries D.O.O. Podgorica"
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
h.style.font.size = Pt(10)
h.style.font.color.rgb = RGBColor(0, 51, 153)

doc.add_paragraph("ANEKS 1", style='Heading 1').alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph("REVIZIJA CAPEX OKVIRA ZA PROJEKAT TITAN 1", style='Heading 2').alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph(f'Datum: 2026-05-10\n').alignment = WD_ALIGN_PARAGRAPH.CENTER

text = f"""Poštovani,

Ovaj Aneks 1 odnosi se isključivo na projekat **TITAN 1 – Fabrika transformatorskih kazana (tankova)**, koji predstavlja aktivni investicioni prioritet kompanije Ars Metal Industries D.O.O. Podgorica.

Svrha ovog aneksa je da se nadležnim institucijama i partnerima pruži ažurirano i precizno objašnjenje CAPEX okvira projekta TITAN 1, nastalo nakon detaljne interne revizije tehničkih, inženjerskih i troškovnih procjena.

Originalni Elaborat je izrađen u ranijoj fazi razvoja projekta i sadržavao je preliminarne procjene koje su bile podložne daljoj optimizaciji. Nakon preciznijeg definisanja proizvodnog procesa, ažuriranja tehničkih parametara, novih ponuda dobavljača i optimizacije troškovnog modela specifičnog za proizvodnju transformatorskih kazana, CAPEX okvir za TITAN 1 je revidiran na **{master['canonical_capex']['label']}**.

Ova revizija omogućava preciznije planiranje, bolje usklađivanje projektne dokumentacije sa trenutno raspoloživim podacima i najnovijim internim procjenama, te predstavlja osnovu za dalju institucionalnu komunikaciju i proceduralno usklađivanje.

Ovaj Aneks služi isključivo kao prateće objašnjenje uz postojeću projektnu dokumentaciju i koristi se u svrhu institucionalne komunikacije, preliminarnog usklađivanja i daljih procedura vezanih za projekat TITAN 1.

Uvažavajući Vašu ulogu u procesu, molimo Vas da razmotrite ovaj dokument u okviru dalje saradnje i proceduralnog usklađivanja.

Sa poštovanjem,"""

for paragraph in text.split('\n'):
    if paragraph.strip():
        doc.add_paragraph(paragraph)

doc.add_paragraph('DANIJELA KESKIN')
doc.add_paragraph('Director')
doc.add_paragraph('Ars Metal Industries D.O.O. Podgorica')

filename = "ANEKS_1_REVIZIJA_CAPEX_TITAN1_PROFESSIONAL_FINAL_2026-05-10.docx"
doc.save(filename)

print(f"\n✅ PROFESIONALNA VERZIJA ANEKS 1 generisana: {filename}")
print("   • Poboljšan institucionalni ton")
print("   • Dodate sve potrebne informacije o investiciji")
print("   • Spreman za tablet i slanje institucijama")
