import os; from docx import Document
D = 'C:/TITAN_KONACNO'

doc = Document()
doc.add_heading('TITAN GRID - TEHNIČKA SPECIFIKACIJA OPREME I RADOVA', 0)

# Stubovi sa konkretnim tehničkim opisima iz tvog Dashboard-a
tech_data = {
    "ELEKTRO & AUTOMATIZACIJA (ABB / Elkom)": [
        "Sistem: SCADA integracija za real-time monitoring proizvodnje.",
        "Komponente: ABB zaštitni ormari i napredni kontroleri za automatizaciju procesa.",
        "Infrastruktura: Namjensko kabliranje za digitalni prenos podataka (Elkom)."
    ],
    "MAŠINSKA OPREMA & VENTILACIJA (MechServ / EkoTerm)": [
        "Sistem: Novi ventilacioni sistem sa optimizovanim tipovima ventilatora za industrijske hale.",
        "Mehaničke komponente: Prilagođeni mehanički sklopovi za rad u visokim temperaturnim zonama."
    ],
    "GRAĐEVINSKA KONSTRUKCIJA (MetAlCon / Beton Mont)": [
        "Čelična struktura: Zadebljani profili za povećanu statičku stabilnost postrojenja.",
        "Civil Works: Ojačana armatura i dodatni temeljni blokovi za tešku mašinsku opremu.",
        "Arhitektura: Namjenski enterijer prilagođen Smart Factory standardima."
    ]
}

for title, points in tech_data.items():
    doc.add_heading(title, 1)
    for point in points:
        doc.add_paragraph(point, style='List Bullet')

doc.add_paragraph("\nStatus: TEHNIČKI VERIFIKOVANO ZA 23. APRIL 2026.")
doc.save('C:\TITAN_KONACNO\MASTER_RAW_MATRIX_v2.docx')
print("🚀 TEHNIČKI OPISI SU INTEGRISANI U MASTER MATRIX!")
