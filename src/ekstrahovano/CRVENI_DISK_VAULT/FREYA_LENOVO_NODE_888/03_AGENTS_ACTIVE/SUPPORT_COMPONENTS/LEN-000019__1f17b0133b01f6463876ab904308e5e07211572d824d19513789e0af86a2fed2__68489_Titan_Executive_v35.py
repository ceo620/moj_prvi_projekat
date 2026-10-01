import pandas as pd
import os, warnings
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

warnings.filterwarnings('ignore')

# PUTANJE - TVOJA TVRĐAVA
IN_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '02_MAJKA_TITANA_NEURAL_v33_FINAL.xlsx')
OUT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '04_TITAN_EXECUTIVE_DASHBOARD_v35.xlsx')

def analyze_executive_impact(df):
    """CFO Analitika: Pretvara podatke u odluke"""
    total_neto = df.get('IZNOS_NETO', pd.Series([0])).sum()
    total_vat = df.get('PDV_21', pd.Series([0])).sum()
    
    # Računamo stratešku težinu
    high_value_count = len(df[df.get('IZNOS_NETO', 0) > 50000])
    l5_security_count = len(df[df.get('NDA', '').str.contains('LEVEL 5', na=False)])
    
    return total_neto, total_vat, high_value_count, l5_security_count

if __name__ == '__main__':
    print("🚀 LANSIRANJE POSLEDNJEG KODA: TITAN EXECUTIVE v35...")
    
    if os.path.exists(IN_FILE):
        xl = pd.ExcelFile(IN_FILE)
        summary_data = []
        
        with pd.ExcelWriter(OUT_FILE, engine='openpyxl') as writer:
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                if df.empty: continue
                
                # CFO Analitika za svaki Pilar
                net, vat, high, l5 = analyze_executive_impact(df)
                summary_data.append({
                    'SEGMENT': sheet,
                    'TOTAL_NETO_EUR': net,
                    'POVRAT_PDV_21': vat,
                    'KRITIČNI_DOKUMENTI': high,
                    'NDA_L5_ZAŠTITA': l5
                })
                
                # Dodavanje podataka u finalni Excel
                df.to_excel(writer, sheet_name=sheet, index=False, startrow=2)
                
                # Stilovi (Onur Navy & Gold)
                ws = writer.sheets[sheet]
                ws['A1'] = f"TITAN GRID - COMMANDER VIEW - {sheet}"
                ws['A1'].font = Font(size=18, bold=True, color='000080')
                
            # KREIRANJE EXECUTIVE DASHBOARD TABA
            dash_df = pd.DataFrame(summary_data)
            dash_df.to_excel(writer, sheet_name='EXECUTIVE_DASHBOARD', index=False, startrow=4)
            
            dw = writer.sheets['EXECUTIVE_DASHBOARD']
            dw['A1'] = "MAJKA TITANA - EXECUTIVE SUMMARY (VLASNIK: ONUR)"
            dw['A1'].font = Font(size=22, bold=True, color='000080')
            dw['A2'] = f"DATUM IZVJEŠTAJA: 2026-04-04 | STATUS: AUDIT-READY"
            dw['A2'].font = Font(size=12, italic=True)
            
            # Ukupna suma carstva
            total_inv = dash_df['TOTAL_NETO_EUR'].sum()
            dw['A3'] = f"UKUPNA VRIJEDNOST IDENTIFIKOVANOG ASSET-A: {total_inv:,.2f} EUR"
            dw['A3'].font = Font(size=14, bold=True, color='FF0000')

        print(f"💎 TRIJUMF KOMANDE! v35 Dashboard je na Desktopu.")
        os.startfile(OUT_FILE)
