#!/data/data/com.termux/files/usr/bin/sh
# ANDROID_SCRIPT_HEALING_DOCTRINE_V3
# KEYWORD=VOLIM_TE
# ORIGINAL_IS_SACRED=YES
# REPAIR_ON_COPY_ONLY=YES
# SAFE_WRAPPER_ONLY=YES
# ID=H005
# ORIGINAL_NAME=create_aneks1.py
# ORIGINAL_PATH=/data/data/com.termux/files/home/ANDROID_ARCHIVE_KNOWLEDGE_20260702_200007/02_REVIEW_ONLY_EXTRACTED/53a21c08c3c46142b0167d055300ef128f16274d35ed932599302421e4784f09_53a21c08c3c46142b0167d055300ef128f16274d35ed932599302421e4784f09_VDR__99_Index_and_Control__Android__uredjaj-20260513T002438Z-3-001.zip/Android uredjaj/TITAN_SCRIPT_MODULE_INTAKE/01_RAW_SCRIPTS/create_aneks1.py
# ORIGINAL_SHA256=fcffb8db1d540ab0a1f570aa570235194face9a2cd28647dd171003cb181f330
# HUMAN_GATE=ACTIVE

HUMAN_GATE="${HUMAN_GATE:-BLOCKED}"
if [ "$HUMAN_GATE" != "ALLOW_RUNTIME" ]; then
  echo "HUMAN_GATE_BLOCKED: Android V3 healed wrapper is static-only."
  exit 88
fi

echo "RUNTIME_NOT_IMPLEMENTED_YET: original payload preserved below for review."
exit 88

: <<'__ANDROID_VOLIM_TE_V3_PAYLOAD_H005_20260703_015331__'
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
__ANDROID_VOLIM_TE_V3_PAYLOAD_H005_20260703_015331__
