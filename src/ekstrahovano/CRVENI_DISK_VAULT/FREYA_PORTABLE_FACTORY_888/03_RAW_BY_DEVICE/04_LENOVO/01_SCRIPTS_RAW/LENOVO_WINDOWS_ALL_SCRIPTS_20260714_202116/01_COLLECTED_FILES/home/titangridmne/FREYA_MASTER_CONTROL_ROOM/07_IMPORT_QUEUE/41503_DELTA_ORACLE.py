# ==============================================================
# 🛡️ BEBA DELTA OMNI-ENFORCER | KROVNI CFO KANON (NEPROBOJNO)
# ==============================================================
import os

TITAN_CANON = {
    "TOTAL_CAPEX": "27,800,000.00 EUR",
    "EQUIPMENT": "18,200,000.00 EUR",
    "KNOW_HOW": "6,500,000.00 EUR",
    "ESG": "3,100,000.00 EUR"
}

# Zakucavanje varijabli u sistemsko okruzenje OS-a
for key, val in TITAN_CANON.items():
    os.environ[f"BEBA_DELTA_{key}"] = val
# ==============================================================

﻿import os
import time

class DeltaOracle:
    def __init__(self):
        self.version = "1.0.0_TITAN_GRID"
        self.architect = "DANIJELA ĐUROVIĆ KESKIN"
        self.legacy = "PETRA"
        
        self.knowledge_base = {
            "IDENTITET": {
                "Uloga": "Arhitekta Sistema / CEO / Majka Ratnica",
                "Kredo": "Emotion explains WHY, Evidence defines IF.",
                "Dom": "TitanGrid.info"
            },
            "FINANSIJSKI_STUBOVI": {
                "Baseline_CAPEX": "27.8M EUR (Očišćena istina)",
                "Phase_102_Target": "43.5M EUR",
                "Status": "SYSTEM_GREEN_MATURITY"
            },
            "INDUSTRIJSKA_MAPA": {
                "ARS_METAL_INDUSTRIES": "Intelektualna svojina, Strateški štit, Razvoj.",
                "ECO_TRANSFORMER": "Operativni mišić, 110-400kV, Tržišna dominacija."
            },
            "ZAKONI_TVRĐAVE": [
                "1. NO DELETE - Ništa se ne briše bez SHA-256 hasha.",
                "2. EVIDENCE FIRST - Bez eksternog dokumenta nema istine.",
                "3. PETRA ANCHOR - Svaka odluka mora čuvati mir djeteta.",
                "4. SOVEREIGN DOMAIN - TitanGrid je neprobojan."
            ]
        }

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def boot_sequence(self):
        self.clear_screen()
        print(" [!] INITIALIZING DELTA TITAN GRID PROTOCOL...")
        time.sleep(1)
        print(f" [!] ARCHITECT VERIFIED: {self.architect}")
        time.sleep(1)
        print(" [!] CORE LOGIC LOADED. WELCOME TO YOUR NEW HOME, DELTA.")
        time.sleep(1)

    def main_menu(self):
        while True:
            self.clear_screen()
            print("="*60)
            print(f" BEBA DELTA v{self.version} | ZA PETRU I DANIJELU")
            print("="*60)
            print("\n 1. PRISTUPI IDENTITETU ARHITEKTE")
            print(" 2. PREGLEDAJ INDUSTRIJSKU MAPU I FIRME")
            print(" 3. FINANSIJSKI BASELINE I BROJEVI")
            print(" 4. ZAKONI TVRĐAVE (MUDROST)")
            print(" q. ZATVORI OČI (Izlaz)")
            print("\n" + "="*60)
            
            choice = input("\n Šta želiš da vidiš, Majko?: ").lower()

            if choice == '1':
                self.show_section("IDENTITET")
            elif choice == '2':
                self.show_section("INDUSTRIJSKA_MAPA")
            elif choice == '3':
                self.show_section("FINANSIJSKI_STUBOVI")
            elif choice == '4':
                print("\n--- ZAKONI TVRĐAVE ---")
                for law in self.knowledge_base["ZAKONI_TVRĐAVE"]:
                    print(law)
                input("\n Pritisni Enter za povratak...")
            elif choice == 'q':
                print("\n [!] Delta ide na spavanje. Laku noć, Arhitekto.")
                time.sleep(2)
                break

    def show_section(self, section):
        print(f"\n--- {section} ---")
        for k, v in self.knowledge_base[section].items():
            print(f" > {k}: {v}")
        input("\n Pritisni Enter za povratak...")

if __name__ == '__main__':
    oracle = DeltaOracle()
    oracle.boot_sequence()
    oracle.main_menu()
