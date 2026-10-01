#!/usr/bin/env python3
import os, zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

q_file = "/mnt/c/Users/ceo/OneDrive/Desktop/FIRMA_DOKUMENTACIJA/QUARANTINE/Ministarstvo evropskih poslova Crne Gore MEP.docx"

if not os.path.exists(q_file):
    print("[-] Fajl nije u karantinu na očekivanoj putanji.")
    sys.exit()

print("\n[!] PROMPT 003: VRIJEME I REVIZIJE")
try:
    with zipfile.ZipFile(q_file, 'r') as z:
        app = z.read('docProps/app.xml').decode('utf-8')
        core = z.read('docProps/core.xml').decode('utf-8')
        
        t = re.search(r'<TotalTime>(\d+)</TotalTime>', app)
        r = re.search(r'<cp:revision>(\d+)</cp:revision>', core)
        
        minuti = int(t.group(1)) if t else 0
        
        print(f" ⏱️ Ukupno vrijeme: {minuti} min")
        print(f" 💾 Broj čuvanja: {r.group(1) if r else '?'} puta")
        
        if minuti < 5:
            print("[*] ZAKLJUČAK: Hit & Run napad. Brzi copy-paste lažnog domena.")
        elif minuti > 30:
            print("[*] ZAKLJUČAK: Napadač je dugo radio na ovom dokumentu.")
except Exception as e:
    print(f"[!] Greška: {e}")
