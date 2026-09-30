import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ====================== XML DESIGN FUNCTIONS ======================
def add_invisible_table_borders(table):
    for row in table.rows:
        for cell in row.cells:
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'nil')
                tcBorders.append(border)
            cell._tc.get_or_add_tcPr().append(tcBorders)

def add_banking_table_lines(table):
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        top = OxmlElement('w:top')
        top.set(qn('w:val'), 'single'); top.set(qn('w:sz'), '12'); top.set(qn('w:space'), '0'); top.set(qn('w:color'), '0A192F')
        tcBorders.append(top); tcPr.append(tcBorders)
    for cell in table.rows[-1].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single'); bottom.set(qn('w:sz'), '12'); bottom.set(qn('w:space'), '0'); bottom.set(qn('w:color'), '0A192F')
        tcBorders.append(bottom); tcPr.append(tcBorders)

def set_cell_margins(cell, top=80, bottom=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom)]:
        node = OxmlElement(f'w:{m}'); node.set(qn('w:w'), str(val)); node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

# ====================== INITIALIZATION & STYLING ======================
doc = Document()
MIDNIGHT_BLUE = RGBColor(10, 25, 47)
CHARCOAL = RGBColor(51, 51, 51)
LIGHT_TEXT = RGBColor(100, 100, 100)

section = doc.sections[0]
for margin in ['left_margin', 'right_margin', 'top_margin', 'bottom_margin']:
    setattr(section, margin, Inches(1.2))

for style_name in ['Normal', 'Heading 1', 'List Bullet']:
    if style_name in doc.styles: doc.styles[style_name].font.name = 'Arial'

h1_style = doc.styles['Heading 1']
h1_style.font.size = Pt(12); h1_style.font.color.rgb = MIDNIGHT_BLUE; h1_style.font.bold = True
h1_style.paragraph_format.space_before = Pt(24); h1_style.paragraph_format.space_after = Pt(10)

normal_style = doc.styles['Normal']
normal_style.font.size = Pt(10); normal_style.font.color.rgb = CHARCOAL
normal_style.paragraph_format.space_after = Pt(10)
normal_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
normal_style.paragraph_format.line_spacing = 1.2
normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ====================== COVER HEADER ======================
doc.add_paragraph("\n")
p_title = doc.add_paragraph()
run_title = p_title.add_run("TITAN GRID 1")
run_title.font.size = Pt(36); run_title.font.bold = True; run_title.font.color.rgb = MIDNIGHT_BLUE

p_sub = doc.add_paragraph("EXECUTIVE INVESTMENT TEASER")
p_sub.runs[0].font.size = Pt(12); p_sub.runs[0].font.bold = True; p_sub.runs[0].font.color.rgb = LIGHT_TEXT
p_sub.paragraph_format.space_after = Pt(20)

p_meta = doc.add_paragraph(f"ARS Metal Industries d.o.o. Montenegro  |  Strictly Confidential  |  {datetime.now().strftime('%B %Y')}")
p_meta.runs[0].font.size = Pt(9); p_meta.runs[0].font.color.rgb = CHARCOAL
p_meta.paragraph_format.space_after = Pt(30)

# ====================== DOCUMENT BODY ======================
doc.add_paragraph("1. PROJECT OVERVIEW & THE MACRO OPPORTUNITY", style="Heading 1")
doc.add_paragraph("ARS Metal Industries d.o.o. (a ring-fenced SPV controlled by ADS Metal Group) is initiating the establishment of TITAN GRID 1, a high-tech greenfield facility for the production of power transformer tanks (10–400 MVA) in Tuzi, Montenegro.", style="Normal")
doc.add_paragraph("The European Union is projecting approximately €584 billion in power grid investments by 2030. However, the execution of this cycle is severely constrained by a structural deficit in critical components and extended lead times (2–5 years for large units).", style="Normal")
doc.add_paragraph("TITAN GRID 1 directly resolves this bottleneck. Utilizing a nearshoring model and Industry 4.0 automation, the project compresses lead times from over 100 days (Asian suppliers) to just 3–5 days for key EU markets. This speed is monetized through premium pricing (15–25%), while freeing up working capital for buyers, positioning TITAN GRID 1 as a strategic infrastructure partner.", style="Normal")

doc.add_paragraph("2. STRATEGIC LOCATION & LOGISTICAL MOAT", style="Heading 1")
doc.add_paragraph("The project is strategically positioned in the Tuzi industrial zone on 22,742 m² of unencumbered land (100% SPV owned).", style="Normal")
def add_bullet(text_bold, text_normal):
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(text_bold).font.bold = True
    p.add_run(text_normal)

add_bullet("Logistical Compression: ", "Proximity to the airport (15 km), Corridor X, and the Port of Bar enables multimodal transport and delivery within 24 hours to Central Europe.")
add_bullet("Operational Infrastructure: ", "A newly constructed 10,573 m² (P+2) facility designed to EIB/IPARD standards (epoxy reinforced floors, NZEB standards, ZLD preparation).")
add_bullet("Sponsor Track Record: ", "Execution risk is heavily mitigated through 15 years of operational expertise from ADS Metal Group, and a management team with 20 years of experience scaling metal fabrication for energy infrastructure.")

doc.add_paragraph("3. TECHNICAL EXCELLENCE & ESG ALIGNMENT (EIB CLIMATE STANDARDS)", style="Heading 1")
doc.add_paragraph("TITAN GRID 1 is designed as a 'Dark Green' project, fully aligned with the EU Taxonomy and CBAM regulations.", style="Normal")
add_bullet("Industry 4.0: ", "Annual capacity of 10,000 tons (~1,200 transformer tanks) utilizing 30kW CNC fiber-lasers, robotic tandem welding lines with vision systems, and a Digital Twin platform (OEE > 85%, scrap rate < 3%).")
add_bullet("Energy Autonomy: ", "An integrated 1.4 MWp rooftop solar PV plant covers 15–20% of energy consumption, acting as an active hedge against energy price volatility.")
add_bullet("Zero Liquid Discharge (ZLD): ", "Closed-loop technical water recirculation system and CBAM-compliant steel procurement from EU/Turkey sources.")

doc.add_paragraph("4. REVENUE VISIBILITY & RISK MITIGATION", style="Heading 1")
doc.add_paragraph("Market and operational risks are systematically eliminated through a robust contractual structure, ensuring EBITDA margin protection across all scenarios:", style="Normal")
add_bullet("Contracted Demand: ", "Secured captive offtake of 30–40% and a validated LOI pipeline of €45–60 million with Tier-1 OEM buyers (Siemens Energy, Hitachi Energy, GE Vernova).")
add_bullet("Margin Protection: ", "Steel price pass-through clauses (60–70%) directly transfer raw material volatility to the end buyer.")
add_bullet("Working Capital Optimization: ", "Advance payments (30–40%) and milestone billing result in a negative Cash Conversion Cycle by Year 3, safeguarding liquidity.")

doc.add_page_break()
doc.add_paragraph("5. FINANCIAL HIGHLIGHTS & CAPITAL STRUCTURE", style="Heading 1")
doc.add_paragraph("The financial model demonstrates a rare balance of infrastructure-grade security and industrial returns. At stabilized operations, the project generates ~€34.5 million in annual revenue with an EBITDA margin of 28–32%.", style="Normal")

fin_table = doc.add_table(rows=8, cols=2)
fin_table.autofit = True
add_invisible_table_borders(fin_table)
add_banking_table_lines(fin_table)

fin_data = [
    ("Estimated Total CAPEX", "€ 17.48 Million"),
    ("Senior Debt (EIB / Commercial Bank)", "€ 11.85 Million (67.8%)"),
    ("EU Grants (EBRD SME Go Green / WBIF)", "Up to € 5.45 Million"),
    ("Sponsor Equity (incl. €1.08M Sunk Equity)", "€ 5.63 Million (32.2%)"),
    ("Target Levered IRR", "41.2%"),
    ("NPV (WACC 7.5%)", "€ 16.9 Million"),
    ("Payback Period", "3.4 Years"),
    ("Debt Service Coverage Ratio (DSCR)", "Min 3.8x")
]

for i, (k, v) in enumerate(fin_data):
    row_cells = fin_table.rows[i].cells
    set_cell_margins(row_cells[0], 60, 60); set_cell_margins(row_cells[1], 60, 60)
    row_cells[0].text = k
    row_cells[0].paragraphs[0].runs[0].font.size = Pt(9); row_cells[0].paragraphs[0].runs[0].font.color.rgb = CHARCOAL
    row_cells[1].text = v
    row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    row_cells[1].paragraphs[0].runs[0].font.bold = True; row_cells[1].paragraphs[0].runs[0].font.size = Pt(10); row_cells[1].paragraphs[0].runs[0].font.color.rgb = MIDNIGHT_BLUE

doc.add_paragraph("\n")
doc.add_paragraph("6. THE ASK & NEXT STEPS", style="Heading 1")
doc.add_paragraph("ARS Metal Industries d.o.o. is seeking institutional financing of €11.85 million (Senior Debt) to achieve financial close and commence facility deployment.", style="Normal")
doc.add_paragraph("Funds will be drawn on a Pari-Passu basis with remaining sponsor equity, specifically allocated for:", style="Normal")

for step in [
    "Finalization of civil works at the Tuzi facility.",
    "Procurement and installation of highly automated, grant-eligible Industry 4.0 equipment.",
    "Working capital allocation for the initial operational ramp-up phase."
]:
    doc.add_paragraph(step, style='List Number')

doc.add_paragraph("\nThe project is 'lender-ready'. Access to the comprehensive TITAN GRID 1 Data Room—including the Master Financial Model, land ownership proofs, technical blueprints, and LOI contracts—will be granted following the execution of an NDA.", style="Normal")

# ====================== ZAVRŠETAK I AUTOMATSKO OTVARANJE ======================
putanja_foldera = r"C:\Users\Lenovo\Desktop\🏛️ TITAN GRID - INSTITUCIONALNI DATA ROOM (V25)"

if not os.path.exists(putanja_foldera):
    os.makedirs(putanja_foldera)

puna_putanja = os.path.join(putanja_foldera, "02_Executive_Teaser_EIB_Standard.docx")
doc.save(puna_putanja)

print(f"✅ DOKUMENT JE KREIRAN: {puna_putanja}")

try:
    os.startfile(puna_putanja) 
except Exception as e:
    print(f"Fajl je sačuvan, ali automatsko otvaranje nije uspjelo: {e}")