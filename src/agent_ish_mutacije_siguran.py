import os
from datetime import datetime

# Skeniramo SAMO projekat
PROJECT_DIR = os.path.expanduser('~/projekti/moj_prvi_projekat')

def sigurno_skeniraj():
    print("=== IPHONE iSH: SIGURNO SKENIRANJE PROJEKTA ===")
    fajlovi = []
    
    for root, dirs, files in os.walk(PROJECT_DIR):
        if '.git' in dirs:
            dirs.remove('.git')
            
        for f in files:
            if f.endswith('.py') or f.endswith('.sh'):
                full_path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    fajlovi.append((full_path, mtime, size))
                except Exception:
                    pass

    fajlovi.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Pronađeno skripti unutar projekta: {len(fajlovi)}\n")
    for path, mtime, size in fajlovi[:15]:
        dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        rel_path = os.path.relpath(path, PROJECT_DIR)
        print(f"  • [{dt}] {rel_path} ({size} B)")

if __name__ == "__main__":
    sigurno_skeniraj()
