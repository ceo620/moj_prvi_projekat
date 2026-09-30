import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ====================== VIZUELNI EFEKTI ======================
def set_cell_background(cell, fill_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=40, bottom=40):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom)]:
        node = OxmlElement(f'w:{m}'); node.set(qn('w:w'), str(val)); node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

# ====================== INICIJALIZACIJA & STILOVI ======================
doc = Document()

# Paleta boja (Moderna)
EIB_BLUE = RGBColor(0, 84, 154)     
DARK_NAVY = RGBColor(10, 25, 47)    
TEXT_GRAY = RGBColor(40, 40, 40)    
HIGHLIGHT_RED = RGBColor(200, 30, 30)

section = doc.sections[0]
for margin in ['left_margin', 'right_margin', 'top_margin', 'bottom_margin']:
    setattr(section, margin, Inches(1.0))

for style_name in ['Normal', 'Heading 1', 'List Bullet']:
    if style_name in doc.styles: doc.styles[style_name].font.name = 'Arial'

h1_style = doc.styles['Heading 1']
h1_style.font.size = Pt(12)
h1_style.font.color.rgb = EIB_BLUE
h1_style.font.bold = True
h1_style.paragraph_format.space_before = Pt(16)
h1_style.paragraph_format.space_after = Pt(6)

normal_style = doc.styles['Normal']
normal_style.font.size = Pt(9.5) 
normal_style.font.color.rgb = TEXT_GRAY
normal_style.paragraph_format.space_after = Pt(6) 
normal_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE 
normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ====================== NASLOVNA STRANA ======================
doc.add_paragraph("\n")
p_title = doc.add_paragraph()
run_title = p_title.add_run("TITAN GRID 1")
run_title.font.size = Pt(40); run_title.font.bold = True; run_title.font.color.rgb = DARK_NAVY

p_sub = doc.add_paragraph("EXECUTIVE INVESTMENT TEASER")
p_sub.runs[0].font.size = Pt(14); p_sub.runs[0].font.bold = True; p_sub.runs[0].font.color.rgb = EIB_BLUE

p_line = doc.add_paragraph()
p_line.add_run("________________________________________________________________").font.color.rgb = EIB_BLUE

p_meta = doc.add_paragraph(f"ARS Metal Industries d.o.o. Montenegro  |  Strictly Confidential  |  {datetime.now().strftime('%B %Y')}")
p_meta.runs[0].font.size = Pt(9); p_meta.runs[0].font.color.rgb = HIGHLIGHT_RED
p_meta.paragraph_format.space_after = Pt(20)

# ====================== SADRŽAJ (GUSTI TEKST & NOVE BROJKE) ======================
doc.add_paragraph("1. PROJECT OVERVIEW & THE MACRO OPPORTUNITY", style="Heading 1")
doc.add_paragraph("ARS Metal Industries d.o.o. (a ring-fenced SPV controlled by ADS Metal Group) is initiating the establishment of TITAN GRID 1, a high-tech greenfield facility for the production of power transformer tanks (10–400 MVA) in Tuzi, Montenegro. The European Union is projecting approximately €584 billion in power grid investments by 2030. However, the execution of this cycle is severely constrained by a structural deficit in critical components and extended lead times (2–5 years for large units).", style="Normal")
doc.add_paragraph("TITAN GRID 1 directly resolves this bottleneck. Utilizing a nearshoring model and Industry 4.0 automation, the project compresses lead times from over 100 days (Asian suppliers) to just 3–5 days for key EU markets. This speed is monetized through premium pricing (15–25%), while freeing up working capital for buyers, positioning TITAN GRID 1 as a strategic infrastructure partner.", style="Normal")

doc.add_paragraph("2. STRATEGIC LOCATION & ESG ALIGNMENT", style="Heading 1")
def add_bullet(text_bold, text_normal):
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(text_bold).font.bold = True
    p.add_run(text_normal)

add_bullet("Logistical Compression: ", "Proximity to the airport (15 km), Corridor X, and the Port of Bar enables multimodal transport and delivery within 24 hours to Central Europe.")
add_bullet("Industry 4.0 & Dark Green Project: ", "Capacity of 10,000 tons utilizing 30kW CNC fiber-lasers and robotic tandem welding. Fully aligned with EU Taxonomy. Integrated 1.4 MWp rooftop solar PV plant covers 15–20% of energy consumption.")
add_bullet("Revenue Visibility: ", "Secured captive offtake of 30–40% and a validated LOI pipeline of €45–60 million with Tier-1 OEM buyers. Steel price pass-through clauses (60–70%) directly transfer volatility.")

# ====================== ŠARENA I UPEČATLJIVA TABELA ======================
doc.add_paragraph("3. FINANCIAL HIGHLIGHTS & CAPITAL STRUCTURE", style="Heading 1")

fin_table = doc.add_table(rows=9, cols=2)
fin_table.style = 'Table Grid'

# Zaglavlje
hdr_cells = fin_table.rows[0].cells
hdr_cells[0].text, hdr_cells[1].text = "METRIC", "PROJECTED VALUE"
for cell in hdr_cells:
    set_cell_background(cell, "0A192F") 
    set_cell_margins(cell, 60, 60)
    run = cell.paragraphs[0].runs[0]
    run.font.bold = True; run.font.color.rgb = RGBColor(255, 255, 255)

# Tvoji pravi podaci
fin_data = [
    ("Estimated Total CAPEX", "€ 17.48 Million"),
    ("Senior Debt (EIB / Commercial Bank)", "€ 11.85 Million (67.8%)"),
    ("EU Grants (EBRD SME Go Green)", "Up to € 5.45 Million"),
    ("Sponsor Equity", "€ 5.63 Million (32.2%)"),
    ("Target Levered IRR", "41.2%"),
    ("NPV (WACC 7.5%)", "€ 16.9 Million"),
    ("Payback Period", "3.4 Years"),
    ("Debt Service Coverage Ratio (DSCR)", "Min 3.8x")
]

for i, (k, v) in enumerate(fin_data, start=1):
    row_cells = fin_table.rows[i].cells
    set_cell_margins(row_cells[0], 40, 40); set_cell_margins(row_cells[1], 40, 40)
    
    row_cells[0].text = k
    row_cells[0].paragraphs[0].runs[0].font.size = Pt(9.5)
    row_cells[0].paragraphs[0].runs[0].font.bold = True
    
    row_cells[1].text = v
    row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    row_cells[1].paragraphs[0].runs[0].font.bold = True
    row_cells[1].paragraphs[0].runs[0].font.size = Pt(10)
    
    if "IRR" in k or "DSCR" in k:
        row_cells[1].paragraphs[0].runs[0].font.color.rgb = EIB_BLUE

    if i % 2 == 0:
        set_cell_background(row_cells[0], "F0F4F8")
        set_cell_background(row_cells[1], "F0F4F8")

doc.add_paragraph("\n")
doc.add_paragraph("4. THE ASK & NEXT STEPS", style="Heading 1")
p_ask = doc.add_paragraph("ARS Metal Industries d.o.o. is seeking institutional financing of ", style="Normal")
p_ask.add_run("€11.85 million (Senior Debt)").font.bold = True
p_ask.add_run(" to achieve financial close and commence facility deployment. The project is 'lender-ready'. Access to the comprehensive TITAN GRID 1 Data Room—including the Master Financial Model, land ownership proofs, and LOI contracts—will be granted following the execution of an NDA.")

# ====================== ČUVANJE (U TRENUTNI FOLDER) ======================
trenutni_folder = os.getcwd() 
puna_putanja = os.path.join(trenutni_folder, "FINALNI_EIB_TEASER_V25.docx")

doc.save(puna_putanja)

print("\n" + "="*50)
print(f"✅ DOKUMENT JE USPJEŠNO KREIRAN!")
print(f"📄 POTRAŽI GA OVDJE: {puna_putanja}")
print("="*50 + "\n")

try:
    os.startfile(puna_putanja)
except:
    pass