import os
import subprocess
from pathlib import Path

def analiziraj_fajl(putanja):
    try:
        # Čitamo stvarni tip fajla preko komande 'file'
        ishod = subprocess.run(['file', '--mime-type', '-b', putanja], capture_output=True, text=True)
        mime_tip = ishod.stdout.strip()
        velicina_mb = os.path.getsize(putanja) / (1024 * 1024)
        return mime_tip, velicina_mb
    except Exception:
        return "nepoznato", 0

def skeniraj_direktorijum(ciljni_folder, min_velicina_mb=10):
    print(f"=== SKENIRANJE MEMORIJE: {ciljni_folder} (Fajlovi > {min_velicina_mb}MB) ===\n")
    katalog = {}
    
    for koren, _, fajlovi in os.walk(ciljni_folder):
        for f in fajlovi:
            full_path = os.path.join(koren, f)
            if os.path.islink(full_path):
                continue
            
            velicina_mb = os.path.getsize(full_path) / (1024 * 1024)
            if velicina_mb >= min_velicina_mb:
                mime_tip, _ = analiziraj_fajl(full_path)
                if mime_tip not in katalog:
                    katalog[mime_tip] = []
                katalog[mime_tip].append((full_path, velicina_mb))
    
    print(f"{'STVARNI TIP FAJLA (MIME)':<35} | {'BROJ FAJLOVA':<12} | {'UKUPNO (MB)':<10}")
    print("-" * 65)
    
    for tip, lista in sorted(katalog.items(), key=lambda x: sum(f[1] for f in x[1]), reverse=True):
        ukupno_mb = sum(f[1] for f in lista)
        print(f"{tip:<35} | {len(lista):<12} | {ukupno_mb:<10.2f} MB")
        
    return katalog

if __name__ == "__main__":
    import sys
    meta = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
    skeniraj_direktorijum(meta, min_velicina_mb=20)
