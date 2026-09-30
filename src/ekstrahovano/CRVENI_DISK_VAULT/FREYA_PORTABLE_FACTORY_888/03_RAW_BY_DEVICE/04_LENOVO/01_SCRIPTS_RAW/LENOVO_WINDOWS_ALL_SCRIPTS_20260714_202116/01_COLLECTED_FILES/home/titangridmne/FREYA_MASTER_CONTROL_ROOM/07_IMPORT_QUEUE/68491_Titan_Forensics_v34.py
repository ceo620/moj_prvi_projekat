import pandas as pd
import os

IN_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '02_MAJKA_TITANA_NEURAL_v33_FINAL.xlsx')
REPORT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '03_TITAN_FORENSIC_REPORT.xlsx')

def audit_cell(row):
    errors = []
    # 1. Provjera matematike PDV-a
    if round(row.get('IZNOS_NETO', 0) * 0.21, 2) != round(row.get('PDV_21', 0), 2):
        errors.append("PDV Error")
    
    # 2. Provjera Sentinela
    if "01_FINANCE" in str(row.get('PILAR', '')) and "Onur" not in str(row.get('SENTINEL', '')):
        errors.append("Sentinel Mismatch")
        
    # 3. Provjera NDA nivoa za velike iznose
    if row.get('IZNOS_NETO', 0) > 100000 and "LEVEL 5" not in str(row.get('NDA', '')):
        errors.append("Security Risk (NDA L5 Required)")
        
    return ", ".join(errors) if errors else "CLEAN"

if __name__ == '__main__':
    print("🔬 POKRETANJE FORENZIČKE PROVJERE v34...")
    if os.path.exists(IN_FILE):
        xl = pd.ExcelFile(IN_FILE)
        with pd.ExcelWriter(REPORT_FILE, engine='openpyxl') as writer:
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                print(f"🔎 Skeniram svaku ćeliju u segmentu: {sheet}")
                df['FORENSIC_AUDIT'] = df.apply(audit_cell, axis=1)
                df.to_excel(writer, sheet_name=sheet, index=False)
        
        print(f"💎 TRIJUMF! Forenzički izvještaj je spreman: 03_TITAN_FORENSIC_REPORT.xlsx")
        os.startfile(REPORT_FILE)
