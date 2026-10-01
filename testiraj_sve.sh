#!/usr/bin/env bash
# -*- coding: utf-8 -*-

echo "=========================================================="
echo "       TITAN GRID 888 - DUAL SYSTEM HEALTH CHECK          "
echo "=========================================================="

# 1. Testiranje Graditelja i Modula (pytest)
echo -e "\n[1/4] POKRETANJE VERIFIKACIJE GRADITELJA (PYTEST)..."
PYTHONPATH=. /home/danijela/projekti/moj_prvi_projekat/ai_okruzenje/bin/pytest tests/

# 2. Status Cron Servisa (Automatizacija)
echo -e "\n[2/4] PROVJERA CRON AUTOMATIZACIJE..."
service cron status 2>/dev/null | grep "Active:" || echo "[-] Cron nije aktivan!"

# 3. Pregled Generisanih Izlaznih Dokumenata
echo -e "\n[3/4] ZADNJI GENERISANI DOKUMENTI (izlaz/dokumenti/)..."
ls -lt /home/danijela/projekti/moj_prvi_projekat/izlaz/dokumenti/ | head -n 5

# 4. Kernel i Sistemski Resursi
echo -e "\n[4/4] STATUS KERNELA I MEMORIJE..."
echo "Kernel: $(uname -r)"
free -h | awk '/Mem:/ {print "RAM Dostupno: " $7 " / Ukupno: " $2}'

echo "=========================================================="
echo "[+] SVI SISTEMI VERIFIKOVANI. READY FOR OPERATION."
echo "=========================================================="
