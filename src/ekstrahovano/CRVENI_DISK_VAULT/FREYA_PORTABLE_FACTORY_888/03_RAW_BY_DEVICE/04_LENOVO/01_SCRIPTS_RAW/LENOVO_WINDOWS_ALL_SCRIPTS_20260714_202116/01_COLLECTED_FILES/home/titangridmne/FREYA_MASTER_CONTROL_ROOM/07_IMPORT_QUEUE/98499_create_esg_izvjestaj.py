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

p("ESG IZVJEŠTAJ", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("1. Environmental (Okolišni aspekt)", True, 12)
p("• Doprinos energetskoj tranziciji i smanjenju CO₂")
p("• Upotreba recikliranih materijala u proizvodnji")
p("• Niska emisija u proizvodnom procesu")

p("2. Social (Društveni aspekt)", True, 12)
p("• Otvaranje novih radnih mjesta u regionu Tuzi")
p("• Obuka i razvoj lokalne radne snage")
p("• Doprinos lokalnoj zajednici i regionalnom razvoju")

p("3. Governance (Upravljanje)", True, 12)
p("• Potpuna transparentnost i usklađenost sa EU taksonomijom")
p("• Know-how partner dasmetal.com.tr – visoki standardi korporativnog upravljanja")
p("• Revizija i praćenje svih regulatornih zahtjeva")

p("Zaključak: Projekat TITAN 1 je u potpunosti usklađen sa ESG principima i spreman za EU fondove.")

p("Sa poštovanjem,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"ESG_IZVJESTAJ_TITAN1_{today}.docx")
print(f"✅ ESG Izvještaj kreiran: ESG_IZVJESTAJ_TITAN1_{today}.docx")
