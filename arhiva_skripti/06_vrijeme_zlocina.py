#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import zipfile
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Primarni direktorijumi za pretragu
target_dirs = [
    "/home/danijela/projekti/moj_prvi_projekat/izlaz/dokumenti",
    "/home/danijela/projekti/moj_prvi_projekat/src/ekstrahovano"
]

DOMEN_META = "aadsmetal"

docx_files = []
for d in target_dirs:
    if os.path.exists(d):
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith(".docx") and not f.startswith("~$"):
                    docx_files.append(os.path.join(root, f))

if not docx_files:
    print("[-] Nije pronađen nijedan .docx fajl za analizu.")
    sys.exit()

print(f"\n[!] FORENZIČKA ANALIZA METAPODATAKA I SADRŽAJA (.docx)")
print(f"Traženi maliciozni domen/pojam: '{DOMEN_META}'")
print(f"Pronađeno fajlova za analizu: {len(docx_files)}")
print("==========================================================")

pronadjeni_detektovani = 0

for q_file in docx_files:
    print(f"\n📄 Dokument: {os.path.basename(q_file)}")
    print(f"📍 Putanja: {q_file}")
    
    try:
        with zipfile.ZipFile(q_file, 'r') as z:
            # 1. Analiza metapodataka
            app_xml = z.read('docProps/app.xml').decode('utf-8', errors='ignore') if 'docProps/app.xml' in z.namelist() else ""
            core_xml = z.read('docProps/core.xml').decode('utf-8', errors='ignore') if 'docProps/core.xml' in z.namelist() else ""

            vrijeme = re.search(r'<TotalTime>(\d+)</TotalTime>', app_xml)
            ukupno_minuta = vrijeme.group(1) if vrijeme else "Nepoznato"

            revizije = re.search(r'<cp:revision>(\d+)</cp:revision>', core_xml)
            broj_cuvanja = revizije.group(1) if revizije else "Nepoznato"

            autor = re.search(r'<dc:creator>(.*?)</dc:dc:creator>|<dc:creator>(.*?)</dc:creator>', core_xml)
            autor_ime = (autor.group(1) or autor.group(2)) if autor else "Nepoznato"

            print(f" ⏱️ Ukupno vrijeme uređivanja: {ukupno_minuta} minuta")
            print(f" 💾 Broj revizija (snimanja): {broj_cuvanja}")
            print(f" 👤 Autor: {autor_ime}")

            # 2. Skrening unutrašnjeg teksta i relacija za maliciozni domen
            sadrzaj_tekst = ""
            if 'word/document.xml' in z.namelist():
                sadrzaj_tekst += z.read('word/document.xml').decode('utf-8', errors='ignore')
            if 'word/_rels/document.xml.rels' in z.namelist():
                sadrzaj_tekst += z.read('word/_rels/document.xml.rels').decode('utf-8', errors='ignore')

            pogodci = re.findall(rf'.{{0,30}}{DOMEN_META}.{{0,30}}', sadrzaj_tekst, re.IGNORECASE)

            if pogodci:
                pronadjeni_detektovani += 1
                print(f" ⚠️ [DETEKCIJA] Pronađen domen '{DOMEN_META}' u sadržaju/linkovima!")
                print("   Kontekst koda/teksta:")
                for p in pogodci[:3]:
                    print(f"   >>> ...{p.strip()}...")
            else:
                print(f" 🔒 [ČISTO] Domen '{DOMEN_META}' nije pronađen u tekstu/linkovima.")

    except Exception as e:
        print(f" [!] Greška pri analizi: {e}")

print("\n==========================================================")
print(f"REREZULTAT PRETRAGE: {pronadjeni_detektovani}/{len(docx_files)} dokumenata sadrži '{DOMEN_META}'.")
print("==========================================================")
