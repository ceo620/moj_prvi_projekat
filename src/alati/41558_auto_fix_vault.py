import os
import re
import subprocess

# Lista najčešćih lokacija gde OneDrive i Windows kriju trezore
possible_paths = [
    "/mnt/c/Users/titangrid.info/OneDrive/Desktop/TITAN GRID",
    "/mnt/c/Users/titangrid.info/OneDrive/Documents/TITAN GRID",
    "/mnt/c/Users/titangrid.info/Desktop/TITAN GRID",
    "/mnt/c/Users/titangrid.info/Documents/TITAN GRID",
    "/mnt/c/Users/titangrid.info/OneDrive/TITAN GRID"
]

true_vault_path = None

# 1. Brza provera poznatih putanja
for path in possible_paths:
    if os.path.exists(os.path.join(path, ".obsidian")):
        true_vault_path = path
        break

# 2. Ako ne nađe, vrši brzu pretragu ključnih foldera
if not true_vault_path:
    print("[*] Duboka provera OneDrive i Desktop lokacija...")
    search_dirs = [
        "/mnt/c/Users/titangrid.info/OneDrive",
        "/mnt/c/Users/titangrid.info/Desktop",
        "/mnt/c/Users/titangrid.info/Documents"
    ]
    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            for root, dirs, files in os.walk(s_dir):
                if "TITAN GRID" in root and os.path.exists(os.path.join(root, ".obsidian")):
                    true_vault_path = root
                    break
            if true_vault_path:
                break

if true_vault_path:
    print(f"[✓] PRONAĐEN PRAVI OBSIDIAN TREZOR NA WINDOWSU: {true_vault_path}")
    
    # Prepisivanje obsidian_bridge.py sa ispravnom putanjom
    bridge_path = "obsidian_bridge.py"
    if os.path.exists(bridge_path):
        with open(bridge_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        # Hirurški menjamo liniju OBSIDIAN_VAULT = ...
        updated_code = re.sub(
            r'OBSIDIAN_VAULT = ".*?"', 
            f'OBSIDIAN_VAULT = "{true_vault_path}"', 
            code
        )
        
        with open(bridge_path, "w", encoding="utf-8") as f:
            f.write(updated_code)
        print("[✓] Most uspešno re-kalibrisan na novu putanju.")
        
        # Odmah pokrećemo sinhronizaciju
        print("[*] Pokrećem sinhronizaciju sa pravim trezorom...")
        subprocess.run(["python3", "obsidian_bridge.py"])
else:
    print("[!] Greška: Nisam uspeo automatski da nađem folder 'TITAN GRID' koji ima .obsidian podešavanja.")
