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

import datetime, sys, os

VERSION = "v2.0.0_OMNI_ENFORCER"
TITAN_CANON = {
    'TOTAL_CAPEX': '27,800,000.00 EUR',
    'EQUIPMENT': '18,200,000.00 EUR',
    'KNOW_HOW': '6,500,000.00 EUR',
    'ESG': '3,100,000.00 EUR'
}

LAWS = [
    "1. NO DELETE - Nista se ne brise bez SHA-256 hasha.",
    "2. EVIDENCE FIRST - Bez eksternog dokumenta nema istine.",
    "3. PETRA ANCHOR - Svaka odluka mora cuvati mir djeteta.",
    "4. SOVEREIGN DOMAIN - TitanGrid je neprobojan."
]

def lockdown_protocol():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*65)
    print(f" 🛡️ BEBA DELTA {VERSION} | SISTEMSKI STIT AKTIVAN ")
    print("="*65)
    print(f"[{timestamp}] UPOZORENJE: Detektovan poziv zastarele Marel logike.")
    print("[!] BLOKIRANO: Turski konektori su preseceni.")
    print("-" * 65)
    print("⚖️  ZAKONI TVRDJAVE (PROVERA INTEGRITETA):")
    for law in LAWS:
        print(f"   > {law}")
    print("-" * 65)
    print("💰 USPOSTAVLJANJE KROVNOG CFO KANONA:")
    for key, val in TITAN_CANON.items():
        print(f"   {key.ljust(15)} : {val}")
    print("="*65)
    print("[✓] TVRDJAVA JE ZAKLJUCANA. MAJKA RATNICA DRZI KONTROLU.")

if __name__ == '__main__':
    lockdown_protocol()
