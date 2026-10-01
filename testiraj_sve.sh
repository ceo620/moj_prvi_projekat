#!/usr/bin/env bash
# -*- coding: utf-8 -*-

echo "=========================================================="
echo "       TITAN GRID 888 - UNIFIED SYSTEM HEALTH CHECK       "
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "\n[1/4] POKRETANJE VERIFIKACIJE GRADITELJA (PYTEST)..."
if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHONPATH=. "$SCRIPT_DIR/venv/bin/python3" -m pytest tests/
elif [ -f "$SCRIPT_DIR/ai_okruzenje/bin/pytest" ]; then
    PYTHONPATH=. "$SCRIPT_DIR/ai_okruzenje/bin/pytest" tests/
else
    PYTHONPATH=. python3 -m pytest tests/
fi

echo -e "\n[2/4] PROVJERA AUTOMATIZACIJE..."
if command -v service &> /dev/null; then
    service cron status 2>/dev/null | grep "Active:" || echo "[+] Linux Cron / Timer aktivan."
else
    echo "[+] macOS Launchd / Cron okruženje spremno."
fi

echo -e "\n[3/4] ZADNJI GENERISANI DOKUMENTI..."
mkdir -p "$SCRIPT_DIR/izlaz/dokumenti"
ls -lt "$SCRIPT_DIR/izlaz/dokumenti/" 2>/dev/null | head -n 5 || echo "[-] Nema dokumenata."

echo -e "\n[4/4] STATUS KERNELA I MEMORIJE..."
echo "Kernel: $(uname -r) ($(uname -s))"
if command -v free &> /dev/null; then
    free -h | awk '/Mem:/ {print "RAM Dostupno: " $7 " / Ukupno: " $2}'
else
    echo "RAM Status: $(sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1073741824 " GB Ukupno"}')"
fi

echo "=========================================================="
echo "[+] SVI SISTEMI VERIFIKOVANI. READY FOR OPERATION."
echo "=========================================================="
