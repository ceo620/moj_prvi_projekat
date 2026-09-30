import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- POMOĆNA FUNKCIJA: Bojanje pozadine ćelije u tablici ---
def set_cell_background(cell, fill_color):
    """Postavlja hex boju pozadine za Word ćeliju (npr. 'D9D9D9')."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), fill_color)
    tcPr.append(shd)

def create_titan_grid_onepager():
    # 1. Inicijalizacija dokumenta
    doc = Document()

    # 2. Podešavanje stranice (A4 format, uske margine za One-Pager)
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)

    # 3. Podešavanje zadanih stilova (Tipografija)
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(10)

    style_h1 = doc.styles['Heading 1']
    font_h1 = style_h1.font
    font_h1.name = 'Calibri'
    font_h1.size = Pt(16)
    font_h1.bold = True
    font_h1.color.rgb = RGBColor(0, 51, 102) # Tamno plava (EU stil)

    style_h2 = doc.styles['Heading 2']
    font_h2 = style_h2.font
    font_h2.name = 'Calibri'
    font_h2.size = Pt(12)
    font_h2.bold = True
    font_h2.color.rgb = RGBColor(0, 51, 102)

    # --- ZAGLAVLJE ---
    title = doc.add_heading('TITAN GRID - 03_Key_Metrics_OnePager', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph()
    runner = subtitle.add_run('Izvještaj o statusu znanstvenog projekta\n')
    runner.bold = True
    runner.font.size = Pt(12)
    runner2 = subtitle.add_run('EU Grant ID: 1010XXXXX | Period: M1 - M12 | Status: ON TRACK')
    runner2.font.color.rgb = RGBColor(89, 89, 89)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph('_' * 80).alignment = WD_ALIGN_PARAGRAPH.CENTER # Vizualna linija

    # --- EXECUTIVE SUMMARY ---
    doc.add_heading('1. Sažetak statusa (Executive Summary)', level=2)
    summary_text = (
        "Projekt Titan Grid napreduje prema planu. Većina isporuka za prvu godinu (M1-M12) "
        "je uspješno završena. Arhitektura sustava je validirana, a prvi set znanstvenih "
        "publikacija je poslan na recenziju. Nema kritičnih odstupanja u budžetu."
    )
    doc.add_paragraph(summary_text)

    # --- KLJUČNI INDIKATORI (KPI) ---
    doc.add_heading('2. Ključni indikatori (Top-Level KPIs)', level=2)
    
    # Koristimo tablicu s 3 stupca kako bismo simulirali "Kartice"
    kpi_table = doc.add_table(rows=2, cols=3)
    kpi_table.style = 'Table Grid'
    
    # Headeri KPI kartica
    headers = ['Znanstvene publikacije', 'Iskorištenost budžeta', 'Ostvarene prekretnice']
    for i, text in enumerate(headers):
        cell = kpi_table.cell(0, i)
        cell.text = text
        set_cell_background(cell, 'EFEFEF') # Svijetlo siva pozadina
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Vrijednosti KPI kartica
    values = ['12 / 15 (Cilj)', '65.00 %', '5 / 8 (Dovršeno)']
    for i, text in enumerate(values):
        cell = kpi_table.cell(1, i)
        cell.text = text
        cell.paragraphs[0].runs[0].font.size = Pt(14)
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() # Razmak

    # --- STATUS RADNIH PAKETA (Work Packages) ---
    doc.add_heading('3. Status radnih paketa (Work Packages)', level=2)
    
    wp_table = doc.add_table(rows=1, cols=4)
    wp_table.style = 'Table Grid'
    
    # Header tablice
    wp_headers = wp_table.rows[0].cells
    wp_headers_text = ['Radni paket (WP)', 'Naziv', 'Dovršenost', 'Status']
    for i, text in enumerate(wp_headers_text):
        wp_headers[i].text = text
        set_cell_background(wp_headers[i], 'D9E2F3') # Plavkasta EU pozadina
        wp_headers[i].paragraphs[0].runs[0].bold = True

    # Podaci za radne pakete
    wp_data = [
        ('WP1', 'Upravljanje projektom i koordinacija', '100%', 'Završeno'),
        ('WP2', 'Arhitektura Titan Grid sustava', '85%', 'U tijeku'),
        ('WP3', 'Razvoj i integracija modela', '40%', 'U tijeku'),
        ('WP4', 'Diseminacija i Open Access', '25%', 'Započeto')
    ]

    for wp in wp_data:
        row_cells = wp_table.add_row().cells
        row_cells[0].text = wp[0]
        row_cells[1].text = wp[1]
        row_cells[2].text = wp[2]
        row_cells[3].text = wp[3]
        
        # Centriranje postotka i statusa
        row_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        row_cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() # Razmak

    # --- PREKRETNICE (Milestones) ---
    doc.add_heading('4. Znanstvene prekretnice (Milestones)', level=2)
    
    ms_table = doc.add_table(rows=1, cols=3)
    ms_table.style = 'Light Shading Accent 1' # Ugrađeni Word stil
    
    ms_headers = ms_table.rows[0].cells
    ms_headers[0].text = 'ID'
    ms_headers[1].text = 'Opis prekretnice'
    ms_headers[2].text = 'Datum isporuke'

    ms_data = [
        ('MS1', 'Inicijalni dizajn grid mreže definiran', 'M3 (Ostvareno)'),
        ('MS2', 'Prototip validiran u lab okruženju', 'M9 (Ostvareno)'),
        ('MS3', 'Prva publikacija u Q1 časopisu', 'M14 (Na čekanju)')
    ]

    for ms in ms_data:
        row_cells = ms_table.add_row().cells
        row_cells[0].text = ms[0]
        row_cells[1].text = ms[1]
        row_cells[2].text = ms[2]

    # 4. Spremanje dokumenta
    filename = 'Titan_Grid_03_Key_Metrics_OnePager.docx'
    doc.save(filename)
    print(f"Uspjeh! Dokument '{filename}' je generiran u trenutnom direktoriju.")

if __name__ == "__main__":
    create_titan_grid_onepager()