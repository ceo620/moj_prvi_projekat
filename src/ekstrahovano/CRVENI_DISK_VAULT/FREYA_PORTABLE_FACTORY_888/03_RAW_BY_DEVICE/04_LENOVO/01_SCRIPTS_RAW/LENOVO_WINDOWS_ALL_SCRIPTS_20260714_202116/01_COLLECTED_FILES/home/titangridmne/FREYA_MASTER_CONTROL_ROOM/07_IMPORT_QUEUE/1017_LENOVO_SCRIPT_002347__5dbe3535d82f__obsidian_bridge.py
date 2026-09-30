import os
import datetime
import subprocess

# 1. Automatski detektujemo tvoj stvarni Windows korisnički folder preko cmd-a
try:
    win_profile = subprocess.check_output(["cmd.exe", "/c", "echo %USERPROFILE%"]).decode("utf-8").strip()
    wsl_vault_base = win_profile.replace("C:\\", "/mnt/c/").replace("\\", "/")
except Exception:
    wsl_vault_base = "/mnt/c/Users/titangridmne"

# Tražimo stvarni TITAN GRID folder na tvom Windowsu
possible_vaults = [
    f"{wsl_vault_base}/OneDrive/Desktop/TITAN GRID",
    f"{wsl_vault_base}/OneDrive/Documents/TITAN GRID",
    f"{wsl_vault_base}/Desktop/TITAN GRID",
    f"{wsl_vault_base}/Documents/TITAN GRID",
    f"{wsl_vault_base}/OneDrive/TITAN GRID"
]

OBSIDIAN_VAULT = None
for path in possible_vaults:
    if os.path.exists(path):
        OBSIDIAN_VAULT = path
        break

# Ako ga ne nađemo na uobičajenim mestima, pravimo ga direktno na tvom stvarnom Desktopu
if not OBSIDIAN_VAULT:
    OBSIDIAN_VAULT = f"{wsl_vault_base}/OneDrive/Desktop/TITAN GRID"
    if not os.path.exists(OBSIDIAN_VAULT):
        os.makedirs(OBSIDIAN_VAULT)

LIVE_DIR = os.path.join(OBSIDIAN_VAULT, "Beba_Delta_Live")
if not os.path.exists(LIVE_DIR):
    os.makedirs(LIVE_DIR)

TITAN_CANON = {
    "TOTAL_CAPEX": "27,800,000.00 EUR",
    "EQUIPMENT": "18,200,000.00 EUR",
    "KNOW_HOW": "6,500,000.00 EUR",
    "ESG": "3,100,000.00 EUR"
}

LAWS = [
    "1. NO DELETE - Ništa se ne briše bez SHA-256 hasha.",
    "2. EVIDENCE FIRST - Bez eksternog dokumenta nema istine.",
    "3. PETRA ANCHOR - Svaka odluka mora čuvati mir djeteta.",
    "4. SOVEREIGN DOMAIN - TitanGrid je neprobojan."
]

def sync_to_obsidian():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Pisanje dokumenata
    with open(os.path.join(LIVE_DIR, "00_KROVNI_KANON.md"), "w", encoding="utf-8") as f:
        f.write(f"---\ntags: [cfo, kanon]\n---\n# 🛡️ BEBA DELTA: OČIŠĆENA ISTINA\n\n> **Poslednji sken:** `{timestamp}`\n\n## 💰 Finansijski Stubovi\n\n| Kategorija | Fiksirani Iznos |\n| :--- | :--- |\n")
        for key, val in TITAN_CANON.items():
            f.write(f"| {key} | {val} |\n")
            
    with open(os.path.join(LIVE_DIR, "01_ZAKONI_TVRDJAVE.md"), "w", encoding="utf-8") as f:
        f.write("# ⚖️ ZAKONI TVRĐAVE\n\n")
        for law in LAWS:
            f.write(f"* **{law}**\n")

    with open(os.path.join(LIVE_DIR, "02_MREZNA_DOKTRINA.md"), "w", encoding="utf-8") as f:
        f.write("# 📡 LIVE STATUS PERIMETRA MREŽE\n\n| Uređaj | Status CFO Doktrine |\n| :--- | :--- |\n| MASTER_MACBOOK | ČEKA SE SIGNAL... |\n| MSI_LAPTOP | ČEKA SE SIGNAL... |\n")

    with open(os.path.join(LIVE_DIR, "03_RIZNICA_ZNANJA.md"), "w", encoding="utf-8") as f:
        f.write("# 🧠 RIZNICA ZNANJA: TITAN GRID INTELEKTUALNA SVOJINA\n\n### 🧠 ARS METAL INDUSTRIES (6.5M EUR)\n- Razvoj inovativnih metalnih struktura.\n- Čeka se tehnički transfer dokumentacije iz Turske.\n\n### ⚙️ ECO TRANSFORMER (18.2M EUR)\n- Energetski transformatori snage 110kV do 400kV.\n- Tržišna dominacija osigurana.\n")

    with open(os.path.join(LIVE_DIR, "04_TAKTICKI_RATNI_PLAN.md"), "w", encoding="utf-8") as f:
        f.write("# 📝 TAKTIČKI RATNI PLAN (TO-DO LISTA)\n\n- [x] Sinhronizovan Lenovo Linux terminal.\n- [x] Probijena barijera ka Windows Obsidianu.\n- [ ] Povezati MSI laptop na mrežu.\n- [ ] Povezati Master MacBook.\n")

    with open(os.path.join(OBSIDIAN_VAULT, "BEBA_DELTA_DASHBOARD.md"), "w", encoding="utf-8") as f:
        f.write("# 🌌 BEBA DELTA v3.0 | GLOBALNI KONTROLNI CENTAR\n\n### 🖇️ Čvorovi Tvrđave\n- [[Beba_Delta_Live/00_KROVNI_KANON|💰 Krovni Finansijski Kanon (27.8M EUR)]]\n- [[Beba_Delta_Live/01_ZAKONI_TVRDJAVE|⚖️ Zakoni Tvrđave (Manifest)]]\n- [[Beba_Delta_Live/02_MREZNA_DOKTRINA|📡 Live Status Perimetra Mreže]]\n- [[Beba_Delta_Live/03_RIZNICA_ZNANJA|🧠 Riznica Znanja]]\n- [[Beba_Delta_Live/04_TAKTICKI_RATNI_PLAN|📝 Aktivni Ratni Plan]]\n- [[Dobrodošlica]]\n")

    print(f"[✓] Znanje se uspešno prelilo na lokaciju: {OBSIDIAN_VAULT}")

if __name__ == '__main__':
    sync_to_obsidian()
