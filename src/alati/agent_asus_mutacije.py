# Forenzički skener za dubinsku detekciju mutacija na Asus čvoru
import os
import re

SEARCH_PATHS = [
    os.path.expanduser('~'),
    '/mnt/c/Users/danijela',
    '/mnt/d'
]

EXCLUDE_DIRS = {'node_modules', '.git', '.cache', '$RECYCLE.BIN', 'System Volume Information', '.Spotlight-V100'}

def dubinska_analiza_asusa():
    print("=== DUBINSKA INSPEKCIJA ASUS ČVORA (MUTACIJE I ARHIVA) ===")
    
    python_fajlovi = []
    env_i_konfig = []
    json_i_logovi = []
    
    for base_path in SEARCH_PATHS:
        if not os.path.exists(base_path):
            continue
            
        print(f"🔍 Pretražujem lokaciju: {base_path}...")
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for f in files:
                full_path = os.path.join(root, f)
                
                # Izbegavamo fajlove veće od 100MB radi brzine
                try:
                    size = os.path.getsize(full_path)
                    if size > 100 * 1024 * 1024:
                        continue
                except Exception:
                    continue

                if f.endswith('.py'):
                    python_fajlovi.append((full_path, size))
                elif f.endswith(('.env', '.config', '.ini', '.txt')) and any(k in f.upper() for k in ['FREYA', 'TITAN', 'GATE', 'RECEIPT', 'POSTURE']):
                    env_i_konfig.append((full_path, size))
                elif f.endswith(('.json', '.log')) and any(k in f.upper() for k in ['RECORD', 'SEAL', 'CANARY', 'STATUS', 'EVIDENCE']):
                    json_i_logovi.append((full_path, size))

    print(f"\n📊 REZULTATI DUBINSKE INSPEKCIJE:")
    print(f"  ├─ Pronađeno Python skripti (mutacija/verzija): {len(python_fajlovi)}")
    print(f"  ├─ Pronađeno konfig i postura fajlova: {len(env_i_konfig)}")
    print(f"  └─ Pronađeno dokaznih logova i JSON pečata: {len(json_i_logovi)}")
    
    print("\n📄 Top 15 najskorije izmenjenih Python skripti na Asus-u:")
    python_fajlovi.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
    for path, size in python_fajlovi[:15]:
        mtime = os.path.getmtime(path)
        from datetime import datetime
        dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        print(f"  • [{dt}] {path} ({size} B)")

if __name__ == "__main__":
    dubinska_analiza_asusa()
