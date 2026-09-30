import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- FUNKCIJA ZA BOJANJE ĆELIJA U TABLICI ---
def set_cell_background(cell, fill_color):
    """Postavlja pozadinsku boju ćelije (hex format)."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), fill_color)
    tcPr.append(shd)

def kreiraj_onepager():
    print("Pokrećem generiranje dokumenta...")
    
    # 1. Inicijalizacija
    doc = Document()

    # 2. Postavke A4 stranice (One-Pager, uske margine)
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)

    # 3. Tipografija (Calibri, EU standard)
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(10)

    h1_font = doc.styles['Heading 1'].font
    h1_font.name = 'Calibri'
    h1_font.size = Pt(16)
    h1_font.bold = True
    h1_font.color.rgb = RGBColor(0, 51, 102) # EU tamno plava

    h2_font = doc.styles['Heading 2'].font
    h2_font.name = 'Calibri'
    h2_font.size = Pt(12)
    h2_font.bold = True
    h2_font.color.rgb = RGBColor(0, 51, 102)

    # --- ZAGLAVLJE ---
    naslov = doc.add_heading('TITAN GRID - 03_Key_Metrics_OnePager', level=1)
    naslov.alignment = WD_ALIGN_PARAGRAPH.CENTER

    podnaslov = doc.add_paragraph()
    podnaslov.add_run('Izvještaj o statusu znanstvenog projekta\n').bold = True
    info = podnaslov.add_run('EU Grant ID: 1010XXXXX | Horizon Europe | Period: M1 - M12')
    info.font.color.rgb = RGBColor(89, 89, 89)
    podnaslov.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph('_' * 85).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- 1. SAŽETAK ---
    doc.add_heading('1. Sažetak statusa (Executive Summary)', level=2)
    doc.add_paragraph(
        "Projekt Titan Grid napreduje prema definiranom planu (ON TRACK). Sve ključne isporuke "
        "za prvu godinu (M1-M12) su uspješno završene. Arhitektura sustava je validirana prema "
        "najvišim SCI standardima, a prvi set znanstvenih publikacija zadovoljava Open Access zahtjeve. "
        "Iskorištenost budžeta je optimalna."
    )

    # --- 2. KLJUČNI INDIKATORI (KPI) ---
    doc.add_heading('2. Ključni indikatori (Top-Level KPIs)', level=2)
    
    kpi_tablica = doc.add_table(rows=2, cols=3)
    kpi_tablica.style = 'Table Grid'
    
    zaglavlja_kpi = ['Znanstvene publikacije', 'Iskorištenost budžeta', 'Ostvarene prekretnice']
    vrijednosti_kpi = ['12 / 15', '65.00 %', '5 / 8']
    
    for i in range(3):
        # Naslovi kartica
        celija_naslov = kpi_tablica.cell(0, i)
        celija_naslov.text = zaglavlja_kpi[i]
        set_cell_background(celija_naslov, '003366')
        celija_naslov.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        celija_naslov.paragraphs[0].runs[0].bold = True
        celija_naslov.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Brojke
        celija_broj = kpi_tablica.cell(1, i)
        celija_broj.text = vrijednosti_kpi[i]
        set_cell_background(celija_broj, 'F2F2F2')
        celija_broj.paragraphs[0].runs[0].font.size = Pt(14)
        celija_broj.paragraphs[0].runs[0].bold = True
        celija_broj.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() 

    # --- 3. RADNI PAKETI (Work Packages) ---
    doc.add_heading('3. Status radnih paketa (Work Packages)', level=2)
    
    wp_tablica = doc.add_table(rows=1, cols=4)
    wp_tablica.style = 'Table Grid'
    
    wp_zaglavlja = ['Radni paket (WP)', 'Naziv', 'Dovršenost', 'Status']
    for i, tekst in enumerate(wp_zaglavlja):
        celija = wp_tablica.rows[0].cells[i]
        celija.text = tekst
        set_cell_background(celija, 'D9E2F3')
        celija.paragraphs[0].runs[0].bold = True

    wp_podaci = [
        ('WP1', 'Upravljanje projektom i koordinacija', '100%', 'Završeno'),
        ('WP2', 'Arhitektura Titan Grid sustava', '85%', 'U tijeku'),
        ('WP3', 'Razvoj i integracija SCI modela', '40%', 'U tijeku'),
        ('WP4', 'Diseminacija i komunikacija', '25%', 'Započeto')
    ]

    for wp in wp_podaci:
        red = wp_tablica.add_row().cells
        for i in range(4):
            red[i].text = wp[i]
        red[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        red[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # --- 4. PREKRETNICE (Milestones) ---
    doc.add_heading('4. Znanstvene prekretnice (Milestones)', level=2)
    
    ms_tablica = doc.add_table(rows=1, cols=3)
    ms_tablica.style = 'Table Grid'
    
    ms_zaglavlja = ['ID', 'Opis prekretnice', 'Datum isporuke']
    for i, tekst in enumerate(ms_zaglavlja):
        celija = ms_tablica.rows[0].cells[i]
        celija.text = tekst
        set_cell_background(celija, 'D9E2F3')
        celija.paragraphs[0].runs[0].bold = True

    ms_podaci = [
        ('MS1', 'Inicijalni dizajn grid mreže definiran', 'M3 (Ostvareno)'),
        ('MS2', 'Prototip validiran u lab okruženju (SCI standard)', 'M9 (Ostvareno)'),
        ('MS3', 'Predaja prve publikacije u Q1 časopis', 'M14 (Na čekanju)')
    ]

    for ms in ms_podaci:
        red = ms_tablica.add_row().cells
        for i in range(3):
            red[i].text = ms[i]

    # --- SPREMANJE ---
    ime_datoteke = 'Titan_Grid_03_Key_Metrics_OnePager.docx'
    puna_putanja = os.path.abspath(ime_datoteke)
    
    doc.save(ime_datoteke)
    print("\n" + "="*60)
    print("USPJESNO GENERIRANO!")
    print(f"Tvoj Word dokument spremljen je točno ovdje:\n-> {puna_putanja}")
    print("="*60 + "\n")

if __name__ == "__main__":
    kreiraj_onepager()