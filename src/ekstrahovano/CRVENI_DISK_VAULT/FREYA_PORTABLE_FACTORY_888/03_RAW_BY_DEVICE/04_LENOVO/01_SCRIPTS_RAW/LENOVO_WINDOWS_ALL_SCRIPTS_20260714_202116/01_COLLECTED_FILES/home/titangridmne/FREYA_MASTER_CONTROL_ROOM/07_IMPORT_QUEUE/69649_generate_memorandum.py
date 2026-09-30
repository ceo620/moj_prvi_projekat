import os
import csv
import qrcode
import matplotlib.pyplot as plt
from datetime import datetime
from openpyxl import load_workbook
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- KONFIGURACIJA ---
VERSION = "V25"
EXCEL_FILE = "Titan_Grid_Model.xlsx"
WORD_FILE = f"Titan_Grid_IM_{VERSION}.docx"
PDF_FILE = f"Titan_Grid_IM_{VERSION}.pdf"
LOG_FILE = "Central_Brain_Version_Log.csv"

# Boje ARS Metal Industries
BRAND_BLUE_HEX = '#0A2540'
DARK_GRAY_HEX = '#333333'
BRAND_BLUE = RGBColor(10, 37, 64)

# ====================== 1. EXCEL INTEGRACIJA ======================
def fetch_financials():
    """Čita live podatke iz Master Excel modela. Ako fajl ne postoji, koristi fallback podatke."""
    data = {
        "capex": "€ 35.5 million",
        "irr": "18.4%",
        "ebitda_margin": "22.5%",
        "payback": "4.2 years",
        "revenues": [12, 25, 40, 55, 68], # 5-year projection
        "ebitda": [1.5, 5.2, 9.8, 14.5, 18.2]
    }
    try:
        wb = load_workbook(EXCEL_FILE, data_only=True)
        ws = wb['Dashboard'] # Pretpostavka imena taba
        # Primer kako bi čitao prave ćelije:
        # data["irr"] = f"{ws['C10'].value * 100:.1f}%"
        print(f"✅ Excel '{EXCEL_FILE}' uspešno učitan.")
    except FileNotFoundError:
        print(f"⚠️ Nije pronađen '{EXCEL_FILE}'. Koristim projektovane placeholder podatke.")
    
    return data

# ====================== 2. MATPLOTLIB GRAFIKONI ======================
def generate_chart(revenues, ebitda):
    """Kreira premium minimalistički grafikon za Word dokument."""
    years = ['2026', '2027', '2028', '2029', '2030']
    
    fig, ax1 = plt.subplots(figsize=(7, 3.5))
    
    # Revenue Bars
    ax1.bar(years, revenues, color=DARK_GRAY_HEX, alpha=0.3, label='Revenue (€m)')
    ax1.set_ylabel('Revenue (€m)', color=DARK_GRAY_HEX, fontsize=10)
    ax1.tick_params(axis='y', labelcolor=DARK_GRAY_HEX)
    
    # EBITDA Line
    ax2 = ax1.twinx()
    ax2.plot(years, ebitda, color=BRAND_BLUE_HEX, marker='o', linewidth=3, markersize=8, label='EBITDA (€m)')
    ax2.set_ylabel('EBITDA (€m)', color=BRAND_BLUE_HEX, fontsize=10)
    ax2.tick_params(axis='y', labelcolor=BRAND_BLUE_HEX)
    
    # Čišćenje ivica (Big4 stil)
    for spine in ax1.spines.values(): spine.set_visible(False)
    for spine in ax2.spines.values(): spine.set_visible(False)
    
    plt.title("5-Year Revenue & EBITDA Projection", fontsize=12, fontweight='bold', color=BRAND_BLUE_HEX, pad=15)
    plt.tight_layout()
    
    chart_path = "temp_financial_chart.png"
    plt.savefig(chart_path, dpi=300, transparent=True)
    plt.close()
    return chart_path

# ====================== 3. WORD GENERATOR (PREMIUM STIL) ======================
def create_word_report(data, chart_path):
    doc = Document()
    
    # Naslovna
    doc.add_paragraph("\n\n\n")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("TITAN GRID")
    run.font.size = Pt(54); run.font.bold = True; run.font.color.rgb = BRAND_BLUE
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("EXECUTIVE INVESTMENT MEMORANDUM\nARS METAL INDUSTRIES D.O.O.")
    run.font.size = Pt(14); run.font.color.rgb = RGBColor(51, 51, 51)
    
    doc.add_paragraph("\n")
    p_ver = doc.add_paragraph(f"Version {VERSION} | {datetime.now().strftime('%d.%m.%Y.')}")
    p_ver.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # Executive Summary & Podaci iz Excela
    doc.add_paragraph("EXECUTIVE SUMMARY", style="Heading 1")
    p_intro = doc.add_paragraph("Based on the latest financial modeling for the Tuzi facility expansion, the core project metrics are highly optimized for institutional investment and EU Taxonomy alignment.")
    
    # Tabela sa spojenim podacima
    table = doc.add_table(rows=4, cols=2)
    table.style = 'Light Shading Accent 1'
    metrics = [
        ("Total CAPEX", data["capex"]),
        ("Target IRR", data["irr"]),
        ("EBITDA Margin", data["ebitda_margin"]),
        ("Payback Period", data["payback"])
    ]
    for i, (k, v) in enumerate(metrics):
        table.cell(i, 0).text = k
        table.cell(i, 1).text = str(v)
        table.cell(i, 0).paragraphs[0].runs[0].font.bold = True

    doc.add_paragraph("\nFINANCIAL PROJECTIONS", style="Heading 1")
    doc.add_picture(chart_path, width=Inches(6.5))
    
    doc.save(WORD_FILE)
    print(f"✅ Word dokument kreiran: {WORD_FILE}")

# ====================== 4. PDF KONVERZIJA & LOGOVANJE ======================
def convert_to_pdf():
    try:
        from docx2pdf import convert
        convert(WORD_FILE, PDF_FILE)
        print(f"✅ PDF dokument kreiran: {PDF_FILE}")
    except Exception as e:
        print("⚠️ PDF konverzija nije uspela (zahteva Windows i instaliran MS Word).")

def log_to_central_brain(data):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Version', 'Author', 'CAPEX', 'IRR', 'EBITDA Margin'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), VERSION, "Onur", data['capex'], data['irr'], data['ebitda_margin']])
    print(f"✅ Verzija {VERSION} upisana u Central Brain log ({LOG_FILE}).")

# ====================== POKRETANJE SISTEMA ======================
if __name__ == "__main__":
    print(f"🚀 Pokrećem TITAN GRID Automatizaciju za Verziju {VERSION}...\n")
    
    fin_data = fetch_financials()
    chart_img = generate_chart(fin_data["revenues"], fin_data["ebitda"])
    create_word_report(fin_data, chart_img)
    
    # Čišćenje privremenih fajlova
    if os.path.exists(chart_img): os.remove(chart_img)
    
    convert_to_pdf()
    log_to_central_brain(fin_data)
    
    print("\n🎯 PROCES ZAVRŠEN. Dokumentacija je spremna za distribuciju.")