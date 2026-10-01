# Forenzički skener mutacija za iPhone iSH (Lagano i bezbedno za RAM)
import os
from datetime import datetime

SEARCH_ROOTS = [
    os.path.expanduser('~'),
    os.path.expanduser('~/projekti/moj_prvi_projekat')
]

EXCLUDE_DIRS = {'node_modules', '.git', '.cache', 'TEŠKI_FAJLOVI'}

def analiziraj_ish_mutacije():
    print("=== FREYA HUMAN GATE · IPHONE iSH MUTACIJE ===")
    
    pronadjene_skripte = []
    
    for base in SEARCH_ROOTS:
        if not os.path.exists(base):
            continue
            
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for f in files:
                if f.endswith('.py') or f.endswith('.sh'):
                    full_path = os.path.join(root, f)
                    try:
                        stat = os.stat(full_path)
                        # Preskačemo teške fajlove ako ih ima
                        if stat.st_size > 10 * 1024 * 1024:
                            continue
                        pronadjene_skripte.append((full_path, stat.st_mtime, stat.st_size))
                    except Exception:
                        pass

    # Sortiranje po datumu poslednje izmene (najnovije prve)
    pronadjene_skripte.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Ukupno locirano skripti (.py / .sh): {len(pronadjene_skripte)}\n")
    print("📌 Poslednjih 15 izmenjenih/kreiranih skripti na iPhone-u:")
    
    for path, mtime, size in pronadjene_skripte[:15]:
        dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        print(f"  • [{dt}] {path} ({size} B)")

if __name__ == "__main__":
    analiziraj_ish_mutacije()
