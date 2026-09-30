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

p("IZJAVA O STRATEŠKOM PROJEKTU OD NACIONALNOG INTERESA", True, 18, WD_ALIGN_PARAGRAPH.CENTER, 8)
p(f"Projekat TITAN 1 – Fabrika transformatorskih kazana (tankova)", True, 14, WD_ALIGN_PARAGRAPH.CENTER, 12)
p(f"Datum: {today}", False, 10.5, WD_ALIGN_PARAGRAPH.CENTER, 20)

p("Primaoci:", True, 12)
p("• Kabinet Predsjednika Vlade Crne Gore")
p("• Ministarstvo ekonomskog razvoja i turizma")
p("• Ministarstvo energetike i rudarstva")
p("• Opština Tuzi")

p("Poštovani,", False, 10.5, None, 12)

p("Ars Metal Industries D.O.O. Podgorica, u saradnji sa know-how partnerom dasmetal.com.tr, podnosi ovu izjavu da je projekat TITAN 1 – Fabrika transformatorskih kazana (tankova) u industrijskoj zoni Tuzi / KAP **strateški projekat od nacionalnog interesa** za Crnu Goru.")

p("Projekat je dio vertikalne investicione lance TITAN 1 → TITAN 2 → TITAN 3 i direktno doprinosi:")
p("• Energetskoj tranziciji i zelenoj industriji")
p("• Povećanju zaposlenosti u sjevernom i centralnom regionu")
p("• Razvoju domaće metaloprerađivačke industrije")
p("• Smanjenju zavisnosti od uvoza energetske opreme")

p("S obzirom na strateški značaj, molimo da se projektu TITAN 1 dodijeli status strateškog projekta od nacionalnog interesa i da se aktiviraju svi raspoloživi mehanizmi državne i EU podrške.")

p("Spremni smo da odmah dostavimo kompletnu dokumentaciju i uđemo u sve procedure.")

p("Sa poštovanjem,", False, 10.5, None, 14)
p("DANIJELA KESKIN", True, 10.5, None, 0)
p("Director", False, 10.5, None, 0)
p("Ars Metal Industries D.O.O. Podgorica", False, 10.5, None, 0)
p("+382 68 323 339 | d.djurovic@adsmetal.com.tr", False, 10.5, None, 0)

doc.save(out / f"IZJAVA_STRATESKI_PROJEKAT_NACIONALNI_INTERES_TITAN1_{today}.docx")
print(f"✅ Izjava o strateškom projektu kreirana: IZJAVA_STRATESKI_PROJEKAT_NACIONALNI_INTERES_TITAN1_{today}.docx")
