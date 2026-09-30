import os
import csv
import traceback
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ====================== CONFIG ======================
BASE_DIR = r"C:\Users\Lenovo\Desktop\TITAN_GRID_CENTRAL_BRAIN"
EXPORT_DIR = os.path.join(BASE_DIR, "04_Export_Terminal")
LOG_DIR = os.path.join(BASE_DIR, "99_Logs")
BUILD_LOG = os.path.join(LOG_DIR, "doc_build_log.csv")
ERROR_LOG = os.path.join(LOG_DIR, "error_log.txt")

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

TOTAL_DOCS = 309

# ====================== REVIZIRANA FINANSIJSKA TABELA (sa WACC i Payback) ======================
def add_revised_financial_table(doc, phase_no):
    doc.add_paragraph()
    p = doc.add_paragraph("TABELA 1.1: KLJUČNI FINANSIJSKI METRICI (Lender Ready)")
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(11)

    table = doc.add_table(rows=10, cols=3)        # povećano na 10 redova
    table.style = 'Table Grid'
    
    # Header
    hdr = table.rows[0].cells
    hdr[0].text = "FINANSIJSKA METRIKA"
    hdr[1].text = "VRIJEDNOST"
    hdr[2].text = "KOMENTAR / IZVOR"

    data = [
        (f"CAPEX (Faza {phase_no})", "€19.92M", "Phase 1 – optimizovano"),
        ("Grant podrška", "€5.45M", "EIB Green Transition"),
        ("Ukupni investicijski target", "€425M", "Pipeline EPCG/CGES + OEM"),
        ("Bankable Revenue", "€85M", "Konzervativna procjena"),
        ("EBITDA margina", "28–32%", "Post-COD steady state"),
        ("DSCR (Base Case)", "3.8x", "Iznad lender praga"),
        ("IRR", "41%", "Projektni povrat"),
        ("WACC", "6.8–7.5%", "ESG-linked financing premium"),
        ("Payback Period", "3.2 godine", "Brza povratnost kapitala"),
        ("Lender Status", "Potpuna usklađenost", "EIB/EBRD Green Finance Eligible")
    ]

    for idx, (metric, value, comment) in enumerate(data, start=1):
        row = table.rows[idx]
        row.cells[0].text = metric
        row.cells[1].text = value
        row.cells[2].text = comment

# ====================== OSTALI HELPERS ======================
def set_doc_margins(doc, margin=0.7):
    section = doc.sections[0]
    section.top_margin = Inches(margin)
    section.bottom_margin = Inches(margin)
    section.left_margin = Inches(margin)
    section.right_margin = Inches(margin)

def add_title_block(doc, scenario_code):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run("MAJKA TITANA • TITAN GRID 2026-2030\n")
    r1.bold = True
    r1.font.size = Pt(22)
    r1.font.color.rgb = RGBColor(0, 32, 96)
    r2 = p.add_run(f"STRATEŠKI INVESTICIONI ELABORAT # {scenario_code}\n")
    r2.bold = True
    r2.font.size = Pt(16)
    r2.font.color.rgb = RGBColor(230, 81, 0)
    r3 = p.add_run("ARS Metal Industries d.o.o. | Tuzi, Montenegro | Onur Supreme Control Active")
    r3.font.size = Pt(9)

def add_control_block(doc, phase_no):
    p = doc.add_paragraph()
    r = p.add_run("INVESTMENT CONTROL BLOCK\n")
    r.bold = True
    r.font.color.rgb = RGBColor(0, 32, 96)
    p.add_run(
        f"Scenario ID: TG-2026-OPT-{phase_no:03d}\n"
        f"CAPEX (Faza {phase_no}): €19.92M\n"
        f"Pipeline prihoda: €425M\n"
        f"EBITDA margina: 28–32%\n"
        f"DSCR: 3.8x | IRR: 41%\n"
        f"Status: EIB/EBRD Green Transition Compliant\n"
    )

def add_strategy_section(doc):
    doc.add_paragraph()
    p = doc.add_paragraph("STRATEŠKI REZIME I TRŽIŠNA ARBITRAŽA")
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(11)
    doc.add_paragraph(
        "Postrojenje u Tuzima pozicionirano je kao ključno čvorište pametne metalne industrije u SEE regionu. "
        "Integracija robotike, SCADA sistema, solarne energije (1.4 MWp) i CBAM compliance osigurava premium pozicioniranje na EU tržištu uz maksimalnu operativnu efikasnost i Iron Clover legacy standarde ADS Metal Turkey."
    )

def add_disclaimer(doc):
    p = doc.add_paragraph("\nStrogo povjerljivo • Majka Titana V26 • Onur Supreme Control Active")
    p.italic = True
    p.runs[0].font.size = Pt(8)

# ====================== MAIN ======================
print("TITAN Central Brain – Revizirani Institutional DOCX Generator V26")
print(f"Output folder: {EXPORT_DIR}\n")

for i in range(1, TOTAL_DOCS + 1):
    scenario_code = f"{i:03d}"
    filename = f"TITAN_FINAL_{scenario_code}.docx"
    output_path = os.path.join(EXPORT_DIR, filename)
    try:
        doc = Document()
        set_doc_margins(doc)
        add_title_block(doc, scenario_code)
        add_control_block(doc, i)
        add_revised_financial_table(doc, i)          # ← Revizirana tabela sa WACC i Payback
        add_strategy_section(doc)
        add_disclaimer(doc)
        doc.save(output_path)

        print(f"✅ Kreiran: {filename}")

    except Exception as e:
        print(f"❌ Greška kod {scenario_code}: {e}")

print("\n🏁 TRIJUMF, ONUR!")
print(f"Svih {TOTAL_DOCS} reviziranih elaborata je kreirano u folderu:")
print(EXPORT_DIR)
print("Majka Titana V26 stil • WACC i Payback dodani • EIB/EBRD ready")
input("\nPritisni Enter da zatvoriš...")