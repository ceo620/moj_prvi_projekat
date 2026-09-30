from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime

today = datetime.date.today().strftime("%Y-%m-%d")
out = Path("/storage/emulated/0/Download/TITAN_ECOSYSTEM/TITAN1_SYSTEM/01_ACTIVE")

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.65)
sec.bottom_margin = Inches(0.65)
sec.left_margin = Inches(0.8)
sec.right_margin = Inches(0.8)

def p(text="", bold=False, size=10.5, align=None, after=6):
    par = doc.add_paragraph()
    if align:
        par.alignment = align
    par.paragraph_format.space_after = Pt(after)
    r = par.add_run(text)
    r.bold = bold
    r.font.name = "Arial"
    r.font.size = Pt(size)
    return par

p("ZAHTJEV ZA PODRŠKU", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("PROGRAM IPARD III", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 12, WD_ALIGN_PARAGRAPH.CENTER, 12)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("Primaoci:", True, 12)
p("• IPARD Agencija / Ministarstvo poljoprivrede, šumarstva i vodoprivrede")
p("• Ministarstvo ekonomskog razvoja i turizma")
p("• Kabinet Predsjednika Vlade Crne Gore")
p("• Kopija: Opština Tuzi, CEDIS, Delegacija EU")

p("Poštovani,", False, 10.5, None, 12)

p("Ars Metal Industries D.O.O. Podgorica, u saradnji sa know-how partnerom dasmetal.com.tr, podnosi formalni zahtjev za podršku u okviru programa **IPARD III** za projekat TITAN 1 – Fabrika transformatorskih kazana (tankova) u industrijskoj zoni Tuzi / KAP.")

p("Projekat predstavlja prvi korak u vertikalnoj investicionoj lancu TITAN 1 → TITAN 2 → TITAN 3 i predviđa investiciju od 18,2 miliona EUR.")

p("Tražimo podršku za realizaciju strateškog industrijskog projekta koji doprinosi energetskoj tranziciji, zapošljavanju i razvoju ruralnog područja Opštine Tuzi.")

p("Spremni smo da dostavimo kompletnu dokumentaciju, finansijski model, ESG izvještaj i ostale tražene obrasce.")

p("Molimo Vas da nas u najkraćem roku obavijestite o proceduri, rokovima i raspoloživim sredstvima za ovaj projekat.")

p("Sa poštovanjem i očekivanjem podrške po programu IPARD III,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"ZAHTJEV_IPARD_III_TITAN1_{today}.docx")
print(f"✅ Zahtjev za IPARD III kreiran: ZAHTJEV_IPARD_III_TITAN1_{today}.docx")
