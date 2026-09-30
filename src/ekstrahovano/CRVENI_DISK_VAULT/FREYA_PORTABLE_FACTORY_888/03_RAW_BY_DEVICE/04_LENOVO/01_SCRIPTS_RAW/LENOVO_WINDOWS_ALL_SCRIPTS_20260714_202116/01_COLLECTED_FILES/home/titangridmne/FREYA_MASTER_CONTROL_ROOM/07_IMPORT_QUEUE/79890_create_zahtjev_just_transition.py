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
p("JUST TRANSITION FUND", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 12, WD_ALIGN_PARAGRAPH.CENTER, 12)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("Primaoci:", True, 12)
p("• Ministarstvo energetike i rudarstva")
p("• Kabinet Predsjednika Vlade Crne Gore")
p("• Delegacija Evropske unije u Crnoj Gori")
p("• Kopija: Opština Tuzi, CEDIS")

p("Poštovani,", False, 10.5, None, 12)

p("Ars Metal Industries D.O.O. Podgorica, u saradnji sa know-how partnerom dasmetal.com.tr, podnosi formalni zahtjev za podršku iz Just Transition Fund-a za projekat TITAN 1 – Fabrika transformatorskih kazana (tankova) u industrijskoj zoni Tuzi / KAP.")

p("Projekat predstavlja prvi korak u vertikalnoj investicionoj lancu TITAN 1 → TITAN 2 → TITAN 3 i predviđa investiciju od 18,2 miliona EUR.")

p("TITAN 1 direktno doprinosi energetskoj tranziciji, smanjenju zavisnosti od fosilnih goriva i razvoju zelene industrije u Crnoj Gori.")

p("Molimo Vas da razmotrite naš projekat u okviru Just Transition Fund-a i obavijestite nas o proceduri, rokovima i raspoloživim sredstvima.")

p("Spremni smo da odmah dostavimo kompletnu dokumentaciju, finansijski model i ESG izvještaj.")

p("Sa poštovanjem i očekivanjem podrške iz Just Transition Fund-a,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"ZAHTJEV_JUST_TRANSITION_FUND_TITAN1_{today}.docx")
print(f"✅ Zahtjev za Just Transition Fund kreiran: ZAHTJEV_JUST_TRANSITION_FUND_TITAN1_{today}.docx")
