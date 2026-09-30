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

p("BUSINESS PLAN", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("ZA EU FONDOVE I DRŽAVNU POMOĆ", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 12, WD_ALIGN_PARAGRAPH.CENTER, 12)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("1. Osnovne informacije", True, 12)
p("Naziv projekta: TITAN 1")
p("Investitor: Ars Metal Industries D.O.O. Podgorica")
p("Know-how partner: dasmetal.com.tr")
p("Lokacija: Industrijska zona Tuzi / KAP")
p("Investicija: 18,2 miliona EUR")
p("Vertikalna investicija: TITAN 1 → TITAN 2 → TITAN 3")

p("2. Strateški značaj projekta", True, 12)
p("• Doprinos energetskoj tranziciji i zelenoj industriji")
p("• Povećanje zaposlenosti u regionu")
p("• Razvoj domaće metaloprerađivačke industrije")
p("• Smanjenje zavisnosti od uvoza energetske opreme")

p("3. Finansijski okvir", True, 12)
p("CAPEX: 18,2 miliona EUR")
p("Očekivani period povrata: [procjena]")
p("DSCR i CFADS modeli: dostupni u prilogu")

p("4. Zahtjev za podršku", True, 12)
p("Tražimo podršku iz programa:")
p("• IPARD III")
p("• Just Transition Fund")
p("• Državna pomoć")
p("• Horizon Europe / Innovation Fund")

p("Spremni smo za sve procedure i dostavljanje dodatne dokumentacije.")

p("Sa poštovanjem,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"BUSINESS_PLAN_TITAN1_EU_FONDOVI_{today}.docx")
print(f"✅ Business Plan za EU fondove kreiran: BUSINESS_PLAN_TITAN1_EU_FONDOVI_{today}.docx")
