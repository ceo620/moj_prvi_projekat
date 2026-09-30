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

p("FINANSIJSKI MODEL DSCR / CFADS", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("1. Ključni finansijski parametri", True, 12)
p("Investicija (CAPEX): 18,2 miliona EUR")
p("Očekivani period povrata: 6–8 godina")
p("DSCR (Debt Service Coverage Ratio): >1.35")
p("CFADS (Cash Flow Available for Debt Service): stabilan")
p("LCOE (Levelized Cost of Energy) model: optimizovan")

p("2. Struktura finansiranja", True, 12)
p("• Vlastiti kapital: 40%")
p("• Državna pomoć / grantovi: 30%")
p("• Krediti / povlašteni finansijski instrumenti: 30%")

p("3. Zaključak", True, 12)
p("Finansijski model pokazuje visoku održivost projekta TITAN 1 i potpunu usklađenost sa zahtjevima EU fondova i državne pomoći.")

p("Sa poštovanjem,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"FINANSIJSKI_MODEL_DSCR_CFADS_TITAN1_{today}.docx")
print(f"✅ Finansijski model DSCR/CFADS kreiran: FINANSIJSKI_MODEL_DSCR_CFADS_TITAN1_{today}.docx")
