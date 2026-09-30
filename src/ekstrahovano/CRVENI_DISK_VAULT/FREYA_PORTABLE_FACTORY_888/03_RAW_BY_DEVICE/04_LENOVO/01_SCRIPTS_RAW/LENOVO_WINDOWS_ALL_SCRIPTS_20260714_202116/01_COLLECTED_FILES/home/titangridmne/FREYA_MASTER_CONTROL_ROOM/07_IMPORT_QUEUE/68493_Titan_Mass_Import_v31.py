import os, re, pandas as pd, warnings
from datetime import datetime
try:
    from docx import Document
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
except:
    pass

warnings.filterwarnings('ignore')

# PUTANJE - TVOJ DESKTOP I TVOJA MOĆ
RAW_DIR = r'C:\Users\Lenovo\Desktop\CTITAN_CENTRAL_BRAINRaw_Data'
OUTPUT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '01_MAJKA_TITANA_50K_MASTER.xlsx')

def extract_financials(text):
    """CFO Mozak: Izvlači cifre i računa PDV"""
    numbers = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', text)
    amounts = [float(n.replace('.', '').replace(',', '.')) for n in numbers]
    total = sum(amounts)
    return total, total * 0.21, total * 1.21

def detect_pilar(text):
    """Neuralna klasifikacija znanja"""
    t = text.upper()
    if any(k in t for k in ["EUR", "CAPEX", "BUDGET", "FINANS", "PDV"]): return "01_FINANCE"
    if any(k in t for k in ["SCADA", "ABB", "TEHNIK", "INZENJER", "ROBOT"]): return "02_TECHNICAL"
    if any(k in t for k in ["HAMZA", "VIZIJA", "STRATEGIJA", "MARKET", "POLJSKA"]): return "03_STRATEGY"
    if any(k in t for k in ["RIZIK", "PENAL", "OSIGURANJE", "SUD", "ZASTITA"]): return "04_RISK"
    if any(k in t for k in ["ESG", "CBAM", "ZELENO", "SOLAR", "EKOLOG"]): return "05_ESG"
    return "06_GENERAL_KNOWLEDGE"

def process_file(file_path):
    fname = os.path.basename(file_path)
    if fname.startswith('~$') or fname.startswith('.'): return None
    
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    try:
        if ext == '.docx':
            doc = Document(file_path)
            content = '\n'.join([p.text for p in doc.paragraphs])
        elif ext in ['.txt', '.csv', '.log']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            return None # Ignorišemo binarne fajlove koji kvare sliku
    except:
        return None

    if len(content) < 5: return None
    
    neto, pdv, bruto = extract_financials(content)
    pilar = detect_pilar(content)
    
    # Određivanje Sentinela i Tajnosti
    sentinel = "Onur (CFO)" if pilar in ["01_FINANCE", "03_STRATEGY"] else "Darko D. (Tech)"
    nda = "LEVEL 5 (Samo Onur)" if neto > 100000 or "UGOVOR" in content.upper() else "LEVEL 3 (Interno)"

    return {
        'PILAR': pilar,
        'DOKUMENT_NAZIV': fname,
        'IZNOS_NETO': round(neto, 2),
        'PDV_21': round(pdv, 2),
        'BRUTO_TOTAL': round(bruto, 2),
        'DNA_FORMULA': content[:200].replace('\n', ' ') + "...",
        'STATUS': 'Uvezeno u Central Brain',
        'NDA': nda,
        'SENTINEL': sentinel,
        'EU_VEZA': 'Identifikovano' if any(k in content.upper() for k in ["EU", "GRANT", "EBRD"]) else 'N/A',
        'ROK': '23.04.2026',
        'ROI_UTICAJ': 'VISOK' if neto > 50000 else 'OPERATIVNI'
    }

if __name__ == '__main__':
    print("🚀 POKRETANJE TITAN MASS IMPORT v31...")
    print(f"📂 Skeniram: {RAW_DIR}")
    
    all_files = []
    for root, dirs, files in os.walk(RAW_DIR):
        for file in files:
            all_files.append(os.path.join(root, file))
    
    print(f"📊 Pronađeno {len(all_files)} fajlova. Počinjem atomske reviziju...")
    
    results = []
    for f in all_files:
        res = process_file(f)
        if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results)
        # Sortiranje da bi tvojih 150 stubova uvek bilo na vrhu
        df = df.sort_values(by=['PILAR', 'IZNOS_NETO'], ascending=[True, False])
        
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            for pilar_name in df['PILAR'].unique():
                # Čišćenje imena taba za Excel (max 31 char)
                sheet_n = pilar_name[:30]
                df[df['PILAR'] == pilar_name].to_excel(writer, sheet_name=sheet_n, index=False, startrow=1)
                
                ws = writer.sheets[sheet_n]
                # Stil Onur - Navy Blue i White
                navy = PatternFill(start_color='000080', end_color='000080', fill_type='solid')
                white_bold = Font(color='FFFFFF', bold=True)
                
                for cell in ws[2]:
                    cell.fill = navy
                    cell.font = white_bold
                    cell.alignment = Alignment(horizontal='center')
                
                ws['A1'] = f"TITAN GRID - CENTRALNI MOZAK v31 - VLASNIK: ONUR (100% MAREL)"
                ws['A1'].font = Font(size=14, bold=True, color='000080')
        
        print(f"💎 TRIJUMF! {len(results)} dokumenata je harmonizovano.")
        print(f"📂 Fajl: {OUTPUT_FILE}")
        os.startfile(OUTPUT_FILE)
    else:
        print("❌ Nije pronađen nijedan validan dokument za import.")
