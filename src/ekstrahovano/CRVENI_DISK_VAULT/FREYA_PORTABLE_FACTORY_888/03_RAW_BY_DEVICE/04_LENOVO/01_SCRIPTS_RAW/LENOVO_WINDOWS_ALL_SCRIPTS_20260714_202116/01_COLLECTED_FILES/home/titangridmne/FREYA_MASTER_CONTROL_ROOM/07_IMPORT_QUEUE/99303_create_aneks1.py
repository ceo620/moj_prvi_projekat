from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime

today = datetime.date.today().strftime("%Y-%m-%d")
out = Path("/storage/emulated/0/Download/TITAN_ECOSYSTEM/TITAN1_SYSTEM/03_ANNEXES")

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

p("ANEKS 1", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("Revizija kapitalnih izdataka za projekat TITAN 1", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 12)

p("1. Osnovne informacije", True, 12)
p("Naziv projekta: TITAN 1 – Fabrika transformatorskih kazana (tankova)")
p("Investitor: Ars Metal Industries D.O.O. Podgorica")
p("Lokacija: Industrijska zona Tuzi / KAP")
p("Know-how partner: dasmetal.com.tr")

p("2. Revizija CAPEX-a", True, 12)
p("Prethodna vrijednost u Elaboratu: [stara vrijednost iz Elaborata]")
p("Nova ažurirana vrijednost: 18,2 miliona EUR")
p("Razlog revizije: Ažurirane inženjerske procjene, optimizacija proizvodnog procesa i nove ponude u lancu snabdijevanja.")

p("3. Zaključak", True, 12)
p("Nakon revizije, CAPEX za TITAN 1 iznosi 18,2 miliona EUR. Aneks 1 postaje sastavni dio originalnog Elaborata.")

p("Sa poštovanjem,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"ANEKS_1_REVIZIJA_CAPEX_TITAN1_{today}.docx")
print(f"✅ Aneks 1 kreiran: ANEKS_1_REVIZIJA_CAPEX_TITAN1_{today}.docx")
