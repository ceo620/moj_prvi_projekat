import pandas as pd
import os, warnings, re
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

warnings.filterwarnings('ignore')

# AUTOMATSKO PRONALAŽENJE DESKTOPA
DESKTOP = os.path.join(os.environ['USERPROFILE'], 'Desktop')
IN_FILE = os.path.join(DESKTOP, '02_MAJKA_TITANA_NEURAL_v33_FINAL.xlsx')
OUT_FILE = os.path.join(DESKTOP, '04_TITAN_SUPREME_DASHBOARD_v35_2.xlsx')

def safe_numeric(val):
    """Pretvara sve u broj bez greške"""
    try:
        if isinstance(val, str):
            val = val.replace('.', '').replace(',', '.')
        return float(val)
    except:
        return 0.0

if __name__ == '__main__':
    print("🔱 LANSIRANJE SUPREME TITAN v35.2: Tvoj suverenitet u akciji...")
    
    if not os.path.exists(IN_FILE):
        print(f"❌ Ne vidim v33 fajl na lokaciji: {IN_FILE}")
    else:
        xl = pd.ExcelFile(IN_FILE)
        summary = []
        
        with pd.ExcelWriter(OUT_FILE, engine='openpyxl') as writer:
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                if df.empty: continue
                
                # Standardizacija kolona
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                # Atomska kalkulacija
                neto_sum = df['IZNOS_NETO'].apply(safe_numeric).sum() if 'IZNOS_NETO' in df.columns else 0
                pdv_sum = df['PDV_21'].apply(safe_numeric).sum() if 'PDV_21' in df.columns else 0
                
                summary.append({
                    'SEGMENT': sheet,
                    'TOTAL_NETO': neto_sum,
                    'POVRAĆAJ_PDV': pdv_sum,
                    'STATUS': 'AUDIT-READY'
                })
                
                df.to_excel(writer, sheet_name=sheet[:31], index=False)
            
            # KREIRANJE VRHOVNOG DASHBOARD-A
            dash_df = pd.DataFrame(summary)
            dash_df.to_excel(writer, sheet_name='SUPREME_DASHBOARD', index=False, startrow=5)
            
            ws = writer.sheets['SUPREME_DASHBOARD']
            ws['A1'] = "MAJKA TITANA - VRHOVNA KOMANDA (ONUR)"
            ws['A1'].font = Font(size=24, bold=True, color='000080')
            
            total_cap = dash_df['TOTAL_NETO'].sum()
            ws['A3'] = f"IDENTIFIKOVANA VRIJEDNOST CARSTVA: {total_cap:,.2f} EUR"
            ws['A3'].font = Font(size=18, bold=True, color='FF0000')

        print(f"💎 TRIJUMF! Fajl je na Desktopu: 04_TITAN_SUPREME_DASHBOARD_v35_2.xlsx")
        os.startfile(OUT_FILE)
