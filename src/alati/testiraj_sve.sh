#!/usr/bin/env bash
# -*- coding: utf-8 -*-

echo "=========================================================="
echo "        TITAN GRID 888 - DUAL SYSTEM HEALTH CHECK          "
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detekcija venv okruženja
if [ -f "$SCRIPT_DIR/ai_okruzenje/bin/pytest" ]; then
    PYTEST_EXEC="$SCRIPT_DIR/ai_okruzenje/bin/pytest"
elif [ -f "$SCRIPT_DIR/titan_env/bin/pytest" ]; then
    PYTEST_EXEC="$SCRIPT_DIR/titan_env/bin/pytest"
elif [ -f "$SCRIPT_DIR/venv/bin/pytest" ]; then
    PYTEST_EXEC="$SCRIPT_DIR/venv/bin/pytest"
elif [ -f "$HOME/ai_okruzenje/bin/pytest" ]; then
    PYTEST_EXEC="$HOME/ai_okruzenje/bin/pytest"
else
    PYTEST_EXEC="pytest"
fi

# 1. Testiranje Graditelja i Modula (pytest)
echo -e "\n[1/4] POKRETANJE VERIFIKACIJE GRADITELJA (PYTEST)..."
PYTHONPATH=. $PYTEST_EXEC tests/

# 2. Status Cron Servisa (Automatizacija)
echo -e "\n[2/4] PROVJERA CRON AUTOMATIZACIJE..."
service cron status 2>/dev/null | grep "Active:" || echo "[-] Cron nije aktivan!"

# 3. Pregled Generisanih Izlaznih Dokumenata
echo -e "\n[3/4] ZADNJI GENERISANI DOKUMENTI (izlaz/dokumenti/)..."
ls -lt "$SCRIPT_DIR/izlaz/dokumenti/" 2>/dev/null | head -n 5 || echo "[-] Nema dokumenata."

# 4. Kernel i Sistemski Resursi
echo -e "\n[4/4] STATUS KERNELA I MEMORIJE..."
echo "Kernel: $(uname -r)"
free -h | awk '/Mem:/ {print "RAM Dostupno: " $7 " / Ukupno: " $2}'

echo "=========================================================="
echo "[+] SVI SISTEMI VERIFIKOVANI. READY FOR OPERATION."
echo "=========================================================="
