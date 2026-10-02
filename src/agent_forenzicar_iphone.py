# Forenzički skener za dubinsku analizu iPhone (iSH) čvora
import os
import re

ROOT_DIR = os.path.expanduser('~')
SKIP_DIRS = ['projekti', '.git', '.cache']

KEYWORDS = [
    r'def\s+\w+', r'class\s+\w+', r'SELECT\s+', r'CREATE\s+TABLE',
    r'TOKEN', r'API_KEY', r'FREYA', r'TITAN', r'EVIDENCE', r'CONTRACT'
]

def skeniraj_iphone():
    pronadjeno = []
    total = 0

    for root, dirs, files in os.walk(ROOT_DIR):
        # Preskačemo već sinhronizovane projekat foldere
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for f in files:
            total += 1
            path = os.path.join(root, f)
            
            # Preskačemo fajlove veće od 10MB radi brzine na iSH-u
            try:
                if os.path.getsize(path) > 10 * 1024 * 1024:
                    continue
                
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    sadrzaj = fp.read(5000)
                    nadji = []
                    for kw in KEYWORDS:
                        if re.search(kw, sadrzaj, re.IGNORECASE):
                            nadji.append(kw.replace('\\s+', ' ').replace('\\w+', ''))
                    
                    if nadji:
                        pronadjeno.append({
                            'fajl': f,
                            'putanja': path.replace(ROOT_DIR, '~'),
                            'otisci': list(set(nadji)),
                            'velicina': os.path.getsize(path)
                        })
            except Exception:
                pass

    print(f"=== REZULTATI FORENZIKE IPHONE ČVORA (Pregledano fajlova: {total}) ===")
    print(f"Pronađeno korisnih arhivskih fajlova van projekta: {len(pronadjeno)}\n")
    for r in pronadjeno[:15]:
        print(f"📄 {r['fajl']} ({r['velicina']} B)")
        print(f"   Putanja: {r['putanja']}")
        print(f"   Otisci: {', '.join(r['otisci'])}\n")

if __name__ == "__main__":
    skeniraj_iphone()
