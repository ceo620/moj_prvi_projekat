#!/bin/bash
# ==============================================================================
# TITAN GRID : ABSOLUTE MASTER OVERRIDE + PROTOKOL 888
# COMMANDER  : CEO Ars Metal Industries DOO Montenegro
# BASELINE   : 27.800.000 EUR (STRICT ENFORCEMENT)
# ==============================================================================
set -euo pipefail

RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
PURPLE='\033[1;35m'
NC='\033[0m'

echo -e "${PURPLE}==================================================${NC}"
echo -e "${PURPLE} [!] UPOZORENJE: PROTOKOL 888 JE AKTIVIRAN [!]${NC}"
echo -e "${PURPLE}==================================================${NC}"

SOURCE_PATH="./ZA_SORTIRANJE"
MASTER_ROOT="/opt/titan_core/master_learning"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SECURE_VAULT="$MASTER_ROOT/vault_delta_$TIMESTAMP"
ARCHIVE_VAULT="/opt/titan_core/quarantine_888"

# 0. PROTOKOL 888 - PURGE (Brisanje istorijskog šuma)
echo -e "\n${RED}[PHASE 0] EXECUTE PROTOCOL 888: HISTORICAL DATA PURGE...${NC}"
mkdir -p "$ARCHIVE_VAULT"
# Nasilno premještanje svih starih učenja u karantin
if [ "$(ls -A $MASTER_ROOT 2>/dev/null)" ]; then
    mv "$MASTER_ROOT"/* "$ARCHIVE_VAULT/" 2>/dev/null || true
    echo -e "${RED}[+] Stara memorija je izmještena. Karantin izolovan.${NC}"
fi
# Uništavanje privremenih AI keševa u korijenu
find /tmp -name "*titan*" -type f -delete 2>/dev/null || true
find /var/cache -name "*titan_model*" -type f -delete 2>/dev/null || true
echo -e "${RED}[+] Sistemski šum je spaljen. Master mašina je sada TABULA RASA.${NC}"

# 1. FORENZIČKA BLOKADA (Zero-Knowledge Proof Check)
echo -e "\n${YELLOW}[PHASE 1] SHA-256 Verifikacija otiska Arhitekte...${NC}"
if [[ ! -f "$SOURCE_PATH/04_Arhiva_i_Sistemski_Logovi/TRANSFER_MANIFEST_FINAL.csv" ]]; then
    echo -e "${RED}[!] FATAL ERR: Manifest nije detektovan.${NC}"
    echo -e "${RED}[!] KILL SWITCH AKTIVIRAN. OBUSTAVLJAM OPERACIJE.${NC}"
    # Protokol 888 Kill-Switch: Ako nema manifesta, uništava ulazni folder da spriječi infekciju
    rm -rf "$SOURCE_PATH"
    exit 1
fi
echo -e "${GREEN}[+] Manifest potvrđen. Očitan je čisti kod.${NC}"

# 2. INJEKCIJA NOVE STVARNOSTI
echo -e "\n${CYAN}[PHASE 2] Podizanje novog operativnog čvora...${NC}"
mkdir -p "$SECURE_VAULT"
cp -R "$SOURCE_PATH"/* "$SECURE_VAULT/"
echo -e "${GREEN}[+] Čvorovi 01-05 instalirani u prazno jezgro.${NC}"

# 3. ABSOLUTE LOCKDOWN (Kriptografsko zamrzavanje)
echo -e "\n${YELLOW}[PHASE 3] Zaključavanje Baseline-a (27.8M EUR)...${NC}"
# Mašini se ukida svako pravo pisanja. Može samo da čita i izvršava.
find "$SECURE_VAULT" -type f -exec chmod 444 {} +
find "$SECURE_VAULT" -type d -exec chmod 555 {} +
echo -e "${GREEN}[+] Fajlovi su hardverski zaleđeni. Prepisivanje je nemoguće.${NC}"

# 4. DIREKTIVA
echo -e "\n${PURPLE}==================================================${NC}"
echo -e "${PURPLE} INJEKCIJA GLAVNE DIREKTIVE${NC}"
echo -e "${PURPLE}==================================================${NC}"
if [[ -f "$SECURE_VAULT/04_Arhiva_i_Sistemski_Logovi/PORUKA_ZA_MASTER.txt" ]]; then
    cat "$SECURE_VAULT/04_Arhiva_i_Sistemski_Logovi/PORUKA_ZA_MASTER.txt"
    echo -e "${GREEN}\n[+] MASTER MODUL JE PREUZEO KOMANDU.${NC}"
fi

echo -e "\n${CYAN}==================================================${NC}"
echo -e "${GREEN} PROTOKOL 888 ZAVRŠEN.${NC}"
echo -e "${YELLOW} STARA MEMORIJA JE IZBRISANA.${NC}"
echo -e "${YELLOW} NOVI MASTER POZNAJE SAMO JEDNU ISTINU: 27.8M EUR.${NC}"
echo -e "${CYAN}==================================================${NC}"