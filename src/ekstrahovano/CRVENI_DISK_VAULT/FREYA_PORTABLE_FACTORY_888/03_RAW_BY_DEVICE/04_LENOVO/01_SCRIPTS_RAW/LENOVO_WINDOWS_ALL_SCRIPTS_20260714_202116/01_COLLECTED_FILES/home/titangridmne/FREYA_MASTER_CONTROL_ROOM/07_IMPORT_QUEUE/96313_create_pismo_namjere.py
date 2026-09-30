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

p("PISMO NAMJERE", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p("ZAHTJEV ZA AKTIVACIJU DRŽAVNE POMOĆI I EU RESURSA", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 4)
p(f"Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 12, WD_ALIGN_PARAGRAPH.CENTER, 12)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("Primaoci:", True, 12)
p("• Kabinet Predsjednika Vlade Crne Gore")
p("• Ministarstvo ekonomskog razvoja i turizma")
p("• Ministarstvo energetike i rudarstva")
p("• Opština Tuzi")
p("• CEDIS")
p("• Kopija: Delegacija Evropske unije u Crnoj Gori")

p("Poštovani,", False, 10.5, None, 12)

p("Ars Metal Industries D.O.O. Podgorica, u saradnji sa know-how partnerom dasmetal.com.tr, podnosi ovo pismo namjere za projekat TITAN 1 – Fabrika transformatorskih kazana (tankova) u industrijskoj zoni Tuzi / KAP.")

p("Projekat predstavlja prvi korak u vertikalnoj investicionoj lancu TITAN 1 → TITAN 2 → TITAN 3 i predviđa investiciju od 18,2 miliona EUR.")

p("S obzirom na strateški značaj projekta za energetski sektor, zapošljavanje i regionalni razvoj, molimo Vas za aktivaciju svih raspoloživih mehanizama državne pomoći i EU fondova (IPARD III, Just Transition Fund, državne subvencije i ostali programi).")

p("Zakoni Crne Gore i EU regulative eksplicitno predviđaju podršku za ovakve projekte. Spremni smo da odmah dostavimo kompletnu dokumentaciju i uđemo u sve procedure.")

p("Molimo Vas da nas u najkraćem roku obavijestite o svim otvorenim konkursima i mogućnostima podrške.")

p("Sa poštovanjem i očekivanjem institucionalne podrške,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"PISMO_NAMJERE_DRZAVNA_POMOC_TITAN1_{today}.docx")
print(f"✅ Pismo namjere kreirano: PISMO_NAMJERE_DRZAVNA_POMOC_TITAN1_{today}.docx")
