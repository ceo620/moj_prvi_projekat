# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

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

p("MEMORANDUM", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("Opštini Tuzi", False, 10.5, None, 0)
p("Kopija: CEDIS – Crnogorski elektrodistributivni sistem", False, 10.5, None, 8)

par = doc.add_paragraph()
par.paragraph_format.space_after = Pt(8)
r = par.add_run("Predmet: ")
r.bold = True
r.font.name = "Arial"
r.font.size = Pt(10.5)
r = par.add_run(f"Zahtjev za institucionalnu podršku – projekat TITAN 1 (Fabrika transformatorskih kazana) u zoni Tuzi/KAP – {today}")
r.font.name = "Arial"
r.font.size = Pt(10.5)

p("Poštovani,")
p("Ars Metal Industries D.O.O. Podgorica, u saradnji sa know-how partnerom dasmetal.com.tr, planira realizaciju projekta TITAN 1 – Fabrika transformatorskih kazana (tankova) u industrijskoj zoni Tuzi / KAP.")
p("Ovo je prvi projekat u vertikalnoj investicionoj lancu TITAN 1 → TITAN 2 → TITAN 3.")
p("Projekat predviđa investiciju od 18,2 miliona EUR i otvaranje novih radnih mjesta.")
p("CAPEX okvir iznosi 18,2 miliona EUR prema ažuriranim projektnim podacima. Elaborat iz ranije faze biće ažuriran Aneksom 1.")

p("Za potrebe planiranja i procjene izvodljivosti, neophodno je pisano izjašnjenje CEDIS-a o sljedećem:")

for item in [
    "trenutni status rekonstrukcije relevantne distributivne infrastrukture,",
    "očekivani rok završetka radova,",
    "raspoloživi kapacitet nakon rekonstrukcije,",
    "preliminarna izvodljivost priključenja snage od 12,5 MW uz faznu realizaciju."
]:
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Inches(0.25)
    par.paragraph_format.space_after = Pt(2)
    r = par.add_run("• " + item)
    r.font.name = "Arial"
    r.font.size = Pt(10.5)

p("Molimo Opštinu Tuzi da uputi formalni zahtjev CEDIS-u za izdavanje tehničkih uslova priključenja.", False, 10.5, None, 8)

p("Prilozi:", True, 10.5, None, 2)
for item in ["Elaborat projekta (sa Aneksom 1)", "Kopija Plana", "Rješenje", "Planerski dokumenti i preliminarni tehnički materijali"]:
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Inches(0.25)
    par.paragraph_format.space_after = Pt(1)
    r = par.add_run("• " + item)
    r.font.name = "Arial"
    r.font.size = Pt(10.5)

p("Unaprijed zahvaljujemo na saradnji.", False, 10.5, None, 8)
p("Sa poštovanjem,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / "MEMORANDUM_TITAN1_v3_2026-05-09.docx")
print("✅ Memorandum TITAN 1 v3 kreiran.")
