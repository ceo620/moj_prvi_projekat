from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from datetime import datetime

doc = Document()

# === PAGE SETUP ===
section = doc.sections[0]
section.left_margin = Inches(1)
section.right_margin = Inches(1)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
section.header_distance = Inches(0.5)
section.footer_distance = Inches(0.5)

# === HEADER ===
header = section.header
h_table = header.add_table(rows=1, cols=3, width=Inches(8))
h_table.autofit = False
h_table.columns[0].width = Inches(2.5)
h_table.columns[1].width = Inches(3)
h_table.columns[2].width = Inches(2.5)

# ARS Logo (lijevo)
cell = h_table.cell(0, 0)
p = cell.paragraphs[0]
p.add_run().add_picture("ARS_Logo.png", width=Inches(2.2))  # stavi logo u folder

# Naslov u sredini
cell = h_table.cell(0, 1)
p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("TITAN GRID")
run.font.size = Pt(16)
run.font.bold = True
run.font.color.rgb = RGBColor(10, 37, 64)
p.add_run("\nARS METAL INDUSTRIES D.O.O. MONTENEGRO").font.size = Pt(9)

# === FOOTER ===
footer = section.footer
f_table = footer.add_table(rows=1, cols=1, width=Inches(8))
f_table.autofit = False
cell = f_table.cell(0, 0)
p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

run = p.add_run("CONFIDENTIAL – Titan Grid V25 | For Authorized Investors Only")
run.font.size = Pt(8)
run.font.color.rgb = RGBColor(100, 100, 100)
p.add_run("   |   ").font.size = Pt(8)
p.add_run(f"Page ").font.size = Pt(8)
p.add_run()._element.append(docx.oxml.OxmlElement('w:fldSimple'))
p.add_run(f" | {datetime.now().strftime('%d.%m.%Y.')}").font.size = Pt(8)

# === DANIJELIN SIGNATURE BLOCK (kao template placeholder) ===
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
run = p.add_run("Danijela Đurović Keskin")
run.font.size = Pt(14)
run.font.bold = True
run.font.color.rgb = RGBColor(10, 37, 64)

doc.add_paragraph("Executive Director\nARS METAL INDUSTRIES D.O.O. MONTENEGRO\nProject Manager & CFO – Titan Grid\nAuthorized Signatory", style="Normal")

p = doc.add_paragraph()
p.add_run("────────────────────────────────────────────────────────────").font.size = Pt(11)
p.add_run("\nPotpis / Signature").font.size = Pt(9)
p.add_run("                                   Date: ________________________").font.size = Pt(9)

# Sačuvaj kao template (.dotx)
doc.save("Titan_Grid_ARS_Master_Template.dotx")

print("✅ Savršeni brendirani Word template je kreiran!")
print("   Fajl: Titan_Grid_ARS_Master_Template.dotx")
print("   Spreman za 02_Executive_Teaser i sve ostale dokumente.")