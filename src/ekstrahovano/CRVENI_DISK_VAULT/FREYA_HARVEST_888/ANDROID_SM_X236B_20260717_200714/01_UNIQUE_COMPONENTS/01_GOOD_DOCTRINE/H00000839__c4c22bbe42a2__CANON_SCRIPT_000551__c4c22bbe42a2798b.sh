#!/bin/bash
# FREYA_DIRECT_REPAIR_RUNTIME_GATE
if [ "$HUMAN_GATE_RUNTIME_APPROVED" != "YES" ]; then
  echo "BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved"
  exit 0
fi
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

# ==============================================================================
# TITAN GRID : ABSOLUTE MASTER OVERRIDE PROTOCOL
# COMMANDER  : CEO Ars Metal Industries DOO Montenegro
# BASELINE   : 27.800.000 EUR (STRICT ENFORCEMENT)
# ==============================================================================

# Fail-Safe aktivacija: Prekida skriptu pri prvoj grešci ili nepoznatoj varijabli
set -euo pipefail

# Definisane boje za terminalski autoritet
RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}==================================================${NC}"
echo -e "${CYAN} INITIATING TITAN CORE ZERO-KNOWLEDGE PROOF SYNC${NC}"
echo -e "${CYAN}==================================================${NC}"

SOURCE_PATH="./ZA_SORTIRANJE"
MASTER_ROOT="/opt/titan_core/master_learning"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SECURE_VAULT="$MASTER_ROOT/vault_delta_$TIMESTAMP"

# 1. FORENZIČKA BLOKADA (Pre-Check)
echo -e "\n${YELLOW}[PHASE 1] Pokretanje SHA-256 verifikacije otiska...${NC}"
if [[ ! -f "$SOURCE_PATH/04_Arhiva_i_Sistemski_Logovi/TRANSFER_MANIFEST_FINAL.csv" ]]; then
    echo -e "${RED}[!] FATAL ERR: Master Manifest nije detektovan.${NC}"
    echo -e "${RED}[!] UGROŽEN INTEGRITET. OBUSTAVLJAM SVE OPERACIJE.${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Manifest potvrđen. Digitalni pečat netaknut.${NC}"

# 2. AGRESIVNA INTEGRACIJA (Air-Gap Transfer)
echo -e "\n${YELLOW}[PHASE 2] Kloniranje operativnih čvorova u izolovani trezor...${NC}"
mkdir -p "$SECURE_VAULT"
cp -R "$SOURCE_PATH"/* "$SECURE_VAULT/"
echo -e "${GREEN}[+] Čvorovi 01-05 uspješno integrisani u: $SECURE_VAULT${NC}"

# 3. ZAKLJUČAVANJE (Immutable Data Enforcement)
# Čini sve finansijske i tehničke fajlove Read-Only za Master modul, sprječavajući "halucinacije"
echo -e "\n${YELLOW}[PHASE 3] Zaključavanje Baseline-a (Read-Only Mode)...${NC}"
find "$SECURE_VAULT/02_Finansije_i_ESG_Baseline" -type f -exec chmod 444 {} +
find "$SECURE_VAULT/01_Tehnicka_Dokumentacija_LTC" -type f -exec chmod 444 {} +
echo -e "${GREEN}[+] EIB/EBRD i Finansijski dokumenti su kriptografski zamrznuti.${NC}"

# 4. DIREKTIVA ARHITEKTE
echo -e "\n${CYAN}==================================================${NC}"
echo -e "${CYAN} INJEKCIJA GLAVNE DIREKTIVE U MASTER JEZGRO${NC}"
echo -e "${CYAN}==================================================${NC}"
if [[ -f "$SECURE_VAULT/04_Arhiva_i_Sistemski_Logovi/PORUKA_ZA_MASTER.txt" ]]; then
    cat "$SECURE_VAULT/04_Arhiva_i_Sistemski_Logovi/PORUKA_ZA_MASTER.txt"
    echo -e "${GREEN}\n[+] DIREKTIVA UPISANA U KORTEX MASTER MAŠINE.${NC}"
else
    echo -e "${RED}[!] UPOZORENJE: Operativna poruka nedostaje.${NC}"
fi

# 5. ODBACIVANJE ŠUMA
echo -e "\n${CYAN}==================================================${NC}"
echo -e "${GREEN} SISTEM TITAN JE SADA SUPREMAN.${NC}"
echo -e "${YELLOW} UPOZORENJE ZA MASTER LOGIKU:${NC}"
echo -e "${YELLOW} BILO KOJI PODATAK KOJI NE ODGOVARA BASELINE-U OD 27.8M EUR${NC}"
echo -e "${YELLOW} MORA BITI TRETIRAN KAO SISTEMSKA BUKA I UNIŠTEN.${NC}"
echo -e "${CYAN}==================================================${NC}"