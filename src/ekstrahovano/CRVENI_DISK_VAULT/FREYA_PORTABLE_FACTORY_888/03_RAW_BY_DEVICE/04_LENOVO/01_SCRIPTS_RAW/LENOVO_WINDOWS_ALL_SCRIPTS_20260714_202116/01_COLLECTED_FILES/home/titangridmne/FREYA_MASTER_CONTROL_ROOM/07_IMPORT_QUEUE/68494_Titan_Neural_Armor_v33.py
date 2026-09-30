import pandas as pd
import os, warnings

warnings.filterwarnings('ignore')

# PUTANJE
IN_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '01_MAJKA_TITANA_50K_MASTER.xlsx')
OUT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', '02_MAJKA_TITANA_NEURAL_v33_FINAL.xlsx')

def assign_logic_safe(row):
    """Oklopna logika: Radi čak i ako podaci nedostaju"""
    try:
        # Tražimo pilar bez obzira na mala/velika slova
        pilar = str(row.get('PILAR', '06_GENERAL')).upper()
        neto = row.get('IZNOS_NETO', 0)
        
        if "01_FINANCE" in pilar:
            return f"exec_cfo_hedge(val={neto}, tax=0.21)"
        elif "02_TECHNICAL" in pilar:
            return "monitor_abb_robotics(uptime_target=0.95)"
        elif "03_STRATEGY" in pilar:
            return "expansion_cloning_sim(market='EU')"
        elif "04_RISK" in pilar:
            return "activate_risk_sentinel(penalty=True)"
        elif "05_ESG" in pilar:
            return "verify_green_compliance(norm='CBAM')"
        return "log_general_knowledge()"
    except:
        return "logic_error_bypass()"

if __name__ == '__main__':
    print("🛡️ POKRETANJE NEURALNOG OKLOPA v33...")
    
    if not os.path.exists(IN_FILE):
        print(f"❌ Greška: Ne vidim fajl na Desktopu: {IN_FILE}")
    else:
        xl = pd.ExcelFile(IN_FILE)
        processed_sheets = 0
        
        with pd.ExcelWriter(OUT_FILE, engine='openpyxl') as writer:
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                
                if df.empty: continue
                
                print(f"⚙️ Procesiram segment: {sheet}")
                # Dodajemo logiku koristeći safe funkciju
                df['PYTHON_LOGIC'] = df.apply(assign_logic_safe, axis=1)
                
                df.to_excel(writer, sheet_name=sheet, index=False)
                processed_sheets += 1
        
        if processed_sheets > 0:
            print(f"💎 TRIJUMF! Neuralni oklop je instaliran na {processed_sheets} tabova.")
            os.startfile(OUT_FILE)
        else:
            print("❌ Nema podataka za obradu u fajlu.")
