#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import zipfile
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

q_dir = "/mnt/c/Users/ceo/OneDrive/Desktop/FIRMA_DOKUMENTACIJA/QUARANTINE"
q_file = None

if os.path.exists(q_dir):
    for f in os.listdir(q_dir):
        if f.endswith(".docx"):
            q_file = os.path.join(q_dir, f)
            break

if not q_file:
    print("[-] Karantin je prazan ili fajl nije pronađen.")
    sys.exit()

print(f"\n[!] PROMPT 003: IZDVAJANJE VREMENA I REVIZIJA IZ KARANTINA...")
print(f"Analiziram fajl: {os.path.basename(q_file)}")
print("==========================================================")

try:
    with zipfile.ZipFile(q_file, 'r') as z:
        app_xml = z.read('docProps/app.xml').decode('utf-8')
        core_xml = z.read('docProps/core.xml').decode('utf-8')
        
        # Traženje vremena u minutama
        vrijeme = re.search(r'<TotalTime>(\d+)</TotalTime>', app_xml)
        ukupno_minuta = vrijeme.group(1) if vrijeme else "Nepoznato"
        
        # Traženje broja čuvanja
        revizije = re.search(r'<cp:revision>(\d+)</cp:revision>', core_xml)
        broj_cuvanja = revizije.group(1) if revizije else "Nepoznato"
        
        print(f" ⏱️ Ukupno vrijeme uređivanja fajla: {ukupno_minuta} minuta")
        print(f" 💾 Broj čuvanja (revizija): {broj_cuvanja} puta")
        
        if ukupno_minuta.isdigit() and int(ukupno_minuta) < 5:
            print("\n[*] FORENZIČKI ZAKLJUČAK: Napad je bio 'Hit & Run'. Brzo otvaranje, lijepljenje 'aadsmetal' domena i snimanje.")
        elif ukupno_minuta.isdigit() and int(ukupno_minuta) > 60:
            print("\n[*] FORENZIČKI ZAKLJUČAK: Napadač je proveo sate radeći na ovom dokumentu. Moguće da je dokument kompletno otkucan na tom Lenovo računaru.")
            
except Exception as e:
    print(f"[!] Greška pri čitanju ZIP arhiva: {e}")

print("==========================================================")
