import os, re, pandas as pd, warnings
from datetime import datetime
try:
    from docx import Document
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("❌ Instaliraj biblioteke: pip install pandas openpyxl python-docx pdf2image pytesseract")

warnings.filterwarnings('ignore')

# 🏛️ PUTANJE TVOG CARSTVA
RAW = r'C:\Users\Lenovo\Desktop\CTITAN_CENTRAL_BRAINRaw_Data'
OUT_DIR = r'C:\Users\Lenovo\Desktop\CTITAN_CENTRAL_BRAINRaw_Data'
OUT = os.path.join(OUT_DIR, '00_CENTRALNI_MOZAK_MAJKA_TITANA_v26_HARMONY.xlsx')

def get_pilar(text):
    """Neuralna kategorizacija iz v24.1"""
    t = text.upper()
    if any(k in t for k in ["EUR", "CAPEX", "BUDGET", "COST", "INVESTIC"]): return "01_FINANCE_MASTER"
    if any(k in t for k in ["SCADA", "ABB", "TECHNICAL", "SMART", "INZENJER"]): return "02_TECHNICAL_DNA"
    if any(k in t for k in ["HAMZA", "STRATEGY", "INVESTOR", "VISION"]): return "03_STRATEGY_HUB"
    if any(k in t for k in ["RIZIK", "DELAY", "PENAL", "KASNIDBA", "PROBLEM"]): return "04_RISK_SENTINEL"
    if any(k in t for k in ["ESG", "CBAM", "GREEN", "ZELENO", "EKOLOG"]): return "05_ESG_COMPLIANCE"
    return "06_GENERAL_DATA"

def process_v26(fpath):
    """Sinteza znanja i ekstrakcija podataka"""
    name = os.path.basename(fpath)
    if name.startswith('~$'): return None
    ext = os.path.splitext(fpath)[1].lower()
    content = ""
    try:
        if ext == '.docx':
            doc = Document(fpath)
            content = ' '.join([p.text for p in doc.paragraphs])
        else:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
    except: return None
    
    if len(content) < 5: return None
    
    # Ekstrakcija finansija (Master Finansija)
    vals = [float(a.replace('.', '').replace(',', '.')) for a in re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', content)]
    net_val = sum(vals)
    
    # Skalabilnost (Industrijski Inzenjeri)
    scalability = '95% (MODULAR)' if any(k in content.upper() for k in ['SCADA', 'SMART', 'ABB', 'INDUSTRY 4.0']) else '65% (STANDARD)'
    
    return {
        'PILAR': get_pilar(content),
        'DOKUMENT': name,
        'NETO_EUR': round(net_val, 2),
        'PDV_21_EUR': round(net_val * 0.21, 2),
        'BRUTO_TOTAL': round(net_val * 1.21, 2),
        'STRATESKI_AKTERI': ', '.join([n for n in ['HAMZA YAVUZ', 'DARKO DJUROVIC', 'ABB', 'MAREL', 'ARS METAL'] if n in content.upper()]),
        'SKALABILNOST': scalability,
        'SIROVA_MATERIJA_TEXT': content[:3500].strip().replace('\n', ' '),
        'CFO_AUDIT_FLAG': '🚨 HITNO' if net_val > 50000 or any(k in content.upper() for k in ['DELAY', 'PENAL', 'KASNIDBA']) else 'OK',
        'VLASNIK': 'ONUR (100% MAREL ENGINEERING)',
        'PROJEKAT': 'TITAN GRID - TUZI',
        'DATUM': '2026-04-04'
    }

if __name__ == '__main__':
    if not os.path.exists(OUT_DIR): os.makedirs(OUT_DIR, exist_ok=True)
    paths = [os.path.join(r, f) for r, d, files in os.walk(RAW) for f in files if not f.startswith('~$')]
    
    print(f"🚀 HARMONIZACIJA U TOKU: Analiziram {len(paths)} dokumenata...")
    results = [r for r in [process_v26(p) for p in paths] if r]
    
    if results:
        df = pd.DataFrame(results)
        with pd.ExcelWriter(OUT, engine='openpyxl') as writer:
            for pilar in sorted(df['PILAR'].unique()):
                sheet_name = pilar[:31]
                df[df['PILAR'] == pilar].to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)
                
                ws = writer.sheets[sheet_name]
                
                # 🎨 DIZAJN: Harmonizacija Boja (Navy & White)
                navy_fill = PatternFill(start_color='000080', end_color='000080', fill_type='solid')
                white_font = Font(color='FFFFFF', bold=True)
                
                # Zaglavlje (Red 2)
                for cell in ws[2]:
                    cell.fill = navy_fill
                    cell.font = white_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # BRENDIRANJE: Onur-ov pecat (Red 1)
                ws.merge_cells(f'A1:{get_column_letter(ws.max_column)}1')
                ws['A1'] = f"TITAN HARMONY v26 - CENTRALNI MOZAK - PROPERTY OF ONUR (CFO)"
                ws['A1'].font = Font(bold=True, size=18, color='000080')
                ws['A1'].alignment = Alignment(horizontal='center')
                
                # Auto-fit kolona i Freeze Panes
                for col in ws.columns:
                    max_length = 0
                    column = col[1].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
                        except: pass
                    ws.column_dimensions[column].width = min((max_length + 3), 60)
                
                ws.freeze_panes = "A3"
                ws.auto_filter.ref = f"A2:{get_column_letter(ws.max_column)}{ws.max_row}"

        print(f"💎 TRIJUMF! TITAN HARMONY v26 JE RODJEN I FORMULISAN!")
        os.startfile(OUT)
    else:
        print("⚠ Greska: Nema podataka u Raw_Data folderu!")
