import os
import pandas as pd

# 1. DEFINISANJE GLAVNOG RADNOG PROSTORA
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
glavni_folder = os.path.join(desktop, "TITAN_GRID_CENTRAL_BRAIN") # Pojednostavljeno ime foldera bez emotikona da izbjegnemo greške

# 2. STRUKTURA FOLDERA
folderi = [
    "01_Data_Core",          
    "02_Python_Engine",      
    "03_Assets_Vault",       
    "04_Export_Terminal"     
]

print("🚀 Pokrećem inicijalizaciju sistema...")
if not os.path.exists(glavni_folder):
    os.makedirs(glavni_folder)

for folder in folderi:
    putanja = os.path.join(glavni_folder, folder)
    if not os.path.exists(putanja):
        os.makedirs(putanja)
        print(f"📁 Kreiran sektor: {folder}")

# 3. KREIRANJE MASTER MATRIX EXCELA
putanja_excela = os.path.join(glavni_folder, "01_Data_Core", "Titan_Grid_Master_Matrix.xlsx")

kolone = [
    "ID_Dokumenta", 
    "Ime_Institucije", 
    "Tip_Institucije", 
    "Trazeni_Iznos", 
    "Ciljani_IRR", 
    "DSCR_Target",
    "Fokus_Elaborata", 
    "Ime_Donosioca_Odluke"
]

test_podaci = [
    ["001", "European Investment Bank (EIB)", "Razvojna banka", "€ 11.85M", "41.2%", "3.8x", "ESG & Climate", "Mr. Werner Hoyer"],
    ["002", "Erste Bank Podgorica", "Komercijalna banka", "€ 5.00M", "35.0%", "2.5x", "Risk & Collateral", "G. Aleksa Lukić"],
    ["003", "Siemens Energy", "Tier-1 Kupac", "N/A", "N/A", "N/A", "Technical Specs & Supply Chain", "Mr. Christian Bruch"]
]

df = pd.DataFrame(test_podaci, columns=kolone)
df.to_excel(putanja_excela, index=False)

print("\n" + "="*50)
print(f"✅ CENTRALNI MOZAK JE POSTAVLJEN!")
print(f"📄 Tvoj radni prostor je na Desktopu: TITAN_GRID_CENTRAL_BRAIN")
print("="*50)

# Otvaranje foldera da ga odmah vidiš
os.startfile(glavni_folder)