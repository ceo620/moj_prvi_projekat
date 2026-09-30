import os, re, pandas as pd, warnings
from datetime import datetime
try:
    from docx import Document
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    print("❌ Instaliraj biblioteke: pip install pdf2image pytesseract pandas python-docx")

warnings.filterwarnings('ignore')

RAW = r'C:\Users\Lenovo\Desktop\CTITAN_CENTRAL_BRAINRaw_Data'
ROOM = r'C:\Users\Lenovo\Desktop\TITAN_GRID_Data_Room_FINAL_April2026'
OUT = os.path.join(ROOM, '00_MASTER', 'TITAN_NEURAL_FORMULA_v18.xlsx')

def process(fpath):
    name = os.path.basename(fpath)
    ext = os.path.splitext(fpath)[1].lower()
    content = ""
    try:
        if ext == '.docx':
            doc = Document(fpath)
            content = ' '.join([p.text for p in doc.paragraphs])
        elif ext == '.pdf':
            imgs = convert_from_path(fpath, dpi=150)
            content = ' '.join([pytesseract.image_to_string(i, lang='eng+srp') for i in imgs])
        elif ext in ['.txt', '.csv']:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
    except: return None
    
    if len(content) < 10: return None
    
    vals = [float(a.replace('.', '').replace(',', '.')) for a in re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', content)]
    net = sum(vals)
    
    return {
        'Data_ID': 'TITAN-DNA',
        'Source': name,
        'Net_Value_EUR': round(net, 2),
        'Key_Actors': ', '.join([n for n in ['HAMZA', 'DARKO', 'ABB', 'EBRD', 'MAREL'] if n in content.upper()]),
        'Text_Insight': content[:2000].strip().replace('\n', ' '),
        'Timestamp': '2026-04-04'
    }

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(OUT)): os.makedirs(os.path.dirname(OUT))
    paths = [os.path.join(r, f) for r, d, files in os.walk(RAW) for f in files]
    print(f"🚀 Analiziram {len(paths)} dokumenata...")
    results = [res for res in [process(p) for p in paths] if res]
    if results:
        pd.DataFrame(results).to_excel(OUT, index=False)
        print(f"💎 NEURALNA FORMULA JE ZIVA! Fajl kreiran na: {OUT}")
        os.startfile(os.path.dirname(OUT))
    else:
        print("⚠ Nema podataka. Proveri Raw_Data folder.")
