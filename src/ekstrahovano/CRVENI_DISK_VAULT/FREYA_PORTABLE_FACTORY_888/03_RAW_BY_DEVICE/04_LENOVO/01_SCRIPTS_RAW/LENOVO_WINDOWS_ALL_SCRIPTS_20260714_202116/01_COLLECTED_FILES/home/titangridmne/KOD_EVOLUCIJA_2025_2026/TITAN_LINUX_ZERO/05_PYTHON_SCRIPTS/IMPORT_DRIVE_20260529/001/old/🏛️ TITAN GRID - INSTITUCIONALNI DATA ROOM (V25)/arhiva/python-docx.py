import qrcode
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_invisible_table_borders(table):
    """Uklanja sve vertikalne i unutrašnje linije za 'Big4' čist izgled tabela."""
    for row in table.rows:
        for cell in row.cells:
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'nil')
                tcBorders.append(border)
            cell._tc.get_or_add_tcPr().append(tcBorders)

def add_banking_table_lines(table):
    """Dodaje samo debelu liniju na vrh i dno tabele (Standard u finansijama)."""
    # Gornja linija prvog reda
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        top = OxmlElement('w:top')
        top.set(qn('w:val'), 'single')
        top.set(qn('w:sz'), '12') # Debljina
        top.set(qn('w:space'), '0')
        top.set(qn('w:color'), '0A192F') # Midnight Blue
        tcBorders.append(top)
        tcPr.append(tcBorders)
    
    # Donja linija poslednjeg reda
    for cell in table.rows[-1].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '12')
        bottom.set(qn('w:space'), '0')
        bottom.set(qn('w:color'), '0A192F')
        tcBorders.append(bottom)
        tcPr.append(tcBorders)

# ====================== INICIJALIZACIJA ======================
doc = Document()

# Boje: Ultra-premium paleta
MIDNIGHT_BLUE = RGBColor(10, 25, 47)
CHARCOAL = RGBColor(51, 51, 51)
LIGHT_TEXT = RGBColor(100, 100, 100)

# ====================== STILOVI ======================
# Glavni naslovi (Manji, ali boldirani, mnogo prostora)
h1_style = doc.styles['Heading 1']
h1_font = h1_style.font
h1_font.name = 'Arial'
h1_font.size = Pt(12)
h1_font.color.rgb = MIDNIGHT_BLUE
h1_font.bold = True
h1_style.paragraph_format.space_before = Pt(30)
h1_style.paragraph_format.space_after = Pt(15)

# Normal tekst (Savršen prored, Justified)
normal_style = doc.styles['Normal']
normal_font = normal_style.font
normal_font.name = 'Arial' # Ili 'Garamond' ako želiš klasičan M&A izgled
normal_font.size = Pt(10)
normal_font.color.rgb = CHARCOAL
normal_style.paragraph_format.space_after = Pt(12)
normal_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
normal_style.paragraph_format.line_spacing = 1.3
normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Margine (1.5 inča svuda za luksuzan "vazduh" oko teksta)
section = doc.sections[0]
for margin in ['left_margin', 'right_margin', 'top_margin', 'bottom_margin']:
    setattr(section, margin, Inches(1.5))

# ====================== NASLOVNA STRANA ======================
doc.add_paragraph("\n\n\n\n\n\n")

p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT # Levo poravnanje je modernije
run_title = p_title.add_run("TITAN GRID")
run_title.font.size = Pt(42)
run_title.font.bold = True
run_title.font.color.rgb = MIDNIGHT_BLUE

p_sub = doc.add_paragraph()
run_sub = p_sub.add_run("PROJECT FINANCE MEMORANDUM")
run_sub.font.size = Pt(14)
run_sub.font.color.rgb = LIGHT_TEXT
run_sub.font.bold = True
p_sub.paragraph_format.space_after = Pt(40)

p_comp = doc.add_paragraph("ARS Metal Industries d.o.o. Montenegro")
p_comp.runs[0].font.size = Pt(10)
p_comp.runs[0].font.color.rgb = CHARCOAL

p_date = doc.add_paragraph(f"Strictly Confidential  |  Version V25  |  {datetime.now().strftime('%B %Y')}")
p_date.runs[0].font.size = Pt(9)
p_date.runs[0].font.color.rgb = LIGHT_TEXT

doc.add_page_break()

# ====================== TEKST I TABELE ======================
doc.add_paragraph("1. EXECUTIVE SUMMARY", style="Heading 1")
doc.add_paragraph("ARS Metal Industries D.O.O. is initiating the development of TITAN GRID, a state-of-the-art, greenfield manufacturing facility located in Tuzi, Montenegro. Designed to meet the stringent quality standards of the European Union, the project leverages Industry 4.0 automation and an optimized cost structure to disrupt the regional supply chain for high-voltage energy infrastructure.", style="Normal")

doc.add_paragraph("2. KEY FINANCIAL METRICS", style="Heading 1")

# Minimalistička finansijska tabela
fin_table = doc.add_table(rows=6, cols=2)
fin_table.autofit = True
add_invisible_table_borders(fin_table)
add_banking_table_lines(fin_table)

fin_data = [
    ("Estimated Total CAPEX", "€ 35.5 Million"),
    ("Target Internal Rate of Return (IRR)", "18.4%"),
    ("Stabilized EBITDA Margin", "22.5%"),
    ("Payback Period", "4.2 Years"),
    ("Debt Service Coverage Ratio (DSCR)", "Min 1.45x"),
    ("EU Taxonomy Status", "Fully Compliant")
]

for i, (k, v) in enumerate(fin_data):
    row_cells = fin_table.rows[i].cells
    
    # Dodajemo padding unutar ćelija
    for cell in row_cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m, val in [('top', 80), ('bottom', 80)]:
            node = OxmlElement(f'w:{m}')
            node.set(qn('w:w'), str(val)); node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    row_cells[0].text = k
    row_cells[0].paragraphs[0].runs[0].font.size = Pt(9)
    row_cells[0].paragraphs[0].runs[0].font.color.rgb = LIGHT_TEXT
    
    row_cells[1].text = v
    row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    row_cells[1].paragraphs[0].runs[0].font.bold = True
    row_cells[1].paragraphs[0].runs[0].font.size = Pt(10)
    row_cells[1].paragraphs[0].runs[0].font.color.rgb = MIDNIGHT_BLUE

doc.save("Titan_Grid_Investment_Bank_Style.docx")
print("✅ ULTRA-MINIMALIST DOKUMENT JE GENERISAN.")