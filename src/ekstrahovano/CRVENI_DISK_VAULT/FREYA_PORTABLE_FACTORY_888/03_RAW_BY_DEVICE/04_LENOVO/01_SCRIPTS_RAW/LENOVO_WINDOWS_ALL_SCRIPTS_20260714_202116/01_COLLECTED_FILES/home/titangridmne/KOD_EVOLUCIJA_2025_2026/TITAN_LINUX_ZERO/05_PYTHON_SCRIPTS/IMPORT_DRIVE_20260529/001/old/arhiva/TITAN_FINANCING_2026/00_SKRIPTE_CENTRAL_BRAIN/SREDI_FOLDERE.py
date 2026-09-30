import os
from pathlib import Path

# DEFINISANJE GLAVNE LOKACIJE NA DESKTOPU
DESKTOP = Path(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'))
MAIN_FOLDER = DESKTOP / "TITAN_GRID_FINANCING_PACKAGE_2026"

# STRUKTURA PO BANKARSKIM STANDARDIMA (EIB/EBRD Ready)
FOLDERS = [
    "00_MASTER_INDEX_CONTROL",         # Za Majku Titana V25 i Excel Tower
    "01_CORPORATE_LEGAL",              # Statut Marel i ugovor Hamza Yavuz
    "02_FINANCIAL_MODELS_CAPEX",       # Glavni CAPEX €19.92M i DSCR
    "03_TECHNICAL_DUE_DILIGENCE",      # SCADA, ABB i Fabrika Tuzi
    "04_ESG_GREEN_COMPLIANCE",         # CBAM i Solarna elektrana 1.4MWp
    "05_STRATEGY_MARKETING",           # Iron Clover i Poljska ekspanzija
    "06_RISK_MANAGEMENT",              # Matrica rizika i NDA ugovori
    "99_SYSTEM_PYTHON_SCRIPTS"         # Ovdje ćemo prebaciti svih 100+ Pitona
]

def build_fortress():
    print(f"🚀 Kreiram TITAN GRID strukturu na Desktopu...")
    
    if not MAIN_FOLDER.exists():
        MAIN_FOLDER.mkdir(parents=True)
        print(f"✅ Glavni folder kreiran: {MAIN_FOLDER.name}")

    for folder in FOLDERS:
        subfolder = MAIN_FOLDER / folder
        subfolder.mkdir(exist_ok=True)
        print(f"  ∟ Sektor spreman: {folder}")

    print("\n✨ DIGITALNA TVRĐAVA JE SPREMNA, ONUR!")
    os.startfile(MAIN_FOLDER) # Automatski otvara prozor pred tobom

if __name__ == "__main__":
    build_fortress()