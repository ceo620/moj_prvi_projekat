#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import zipfile
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

TARGET_DIRS = [
    "/home/danijela/projekti/moj_prvi_projekat/izlaz/dokumenti",
    "/home/danijela/projekti/moj_prvi_projekat/src/ekstrahovano",
    "/mnt/c/Users/ceo/OneDrive/Desktop/FIRMA_DOKUMENTACIJA"
]

print("\n[!] SUS PROMPT 002: INICIJALIZACIJA DUBOKE XML EKSTRAKCIJE (PROJECT + ARCHIVE)...")
print("==========================================================")

docx_files = []
for d in TARGET_DIRS:
    if os.path.exists(d):
        docx_files.extend(glob.glob(os.path.join(d, "**/*.docx"), recursive=True))

suspektni_korisnici = set()
fajlovi_sa_tragovima = []

path_pattern = re.compile(r"[a-zA-Z]:[\\/]Users[\\/]([^\\/\"']+)", re.IGNORECASE)

for doc_path in docx_files:
    if os.path.basename(doc_path).startswith("~$"):
        continue

    try:
        with zipfile.ZipFile(doc_path, 'r') as z:
            for item in z.namelist():
                if item.endswith('.xml') or item.endswith('.rels'):
                    sadrzaj = z.read(item).decode('utf-8', errors='ignore')
                    pronadjeno = path_pattern.findall(sadrzaj)
                    for user in pronadjeno:
                        if user.lower() not in ["ceo", "public", "default", "lenovo", "administrator", "danijela"]:
                            suspektni_korisnici.add(user)
                            fajlovi_sa_tragovima.append({
                                "fajl": os.path.basename(doc_path),
                                "skriveni_user": user
                            })
    except Exception as e:
        pass

if fajlovi_sa_tragovima:
    print(f"[⚠] BINGO! PRONAĐENI SU SKRIVENI WINDOWS NALOZI DUBOKO U XML KODU:\n")
    for s in fajlovi_sa_tragovima:
        print(f" 📄 FAJL: {s['fajl']} | 🕵️ SKRIVENI NALOG: {s['skriveni_user']}")

    print("\n==========================================================")
    print(f"[!] JEDINSTVENA IMENA KRTICA NAĐENA U SISTEMU: {', '.join(suspektni_korisnici)}")
    print("[*] Forenzički zaključak: Ovo su prava imena ljudi (ili računara) koji su manipulisali fajlovima!")
else:
    print(f"\n[-] Pregledano {len(docx_files)} dokumenata. Nema procurelih nepoznatih Windows putanja u XML fajlovima.")

print("==========================================================")
