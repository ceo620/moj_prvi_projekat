import os
import subprocess
import hashlib

def daj_mime_tip(putanja):
    try:
        ishod = subprocess.run(['file', '--mime-type', '-b', putanja], capture_output=True, text=True)
        return ishod.stdout.strip()
    except Exception:
        return "nepoznato"

def skeniraj_velike_fajlove(pocetni_folder, min_mb=100):
    print(f"\n============================================================")
    print(f"   DUBINSKA ANALIZA FAJLOVA VEĆIH OD {min_mb} MB")
    print(f"============================================================\n")
    
    rezultati = []
    ignorisani_dirs = ['/System', '/Library', '/Applications', '/.git', '/ai_okruzenje']
    
    for koren, dirs, fajlovi in os.walk(pocetni_folder):
        if any(ign in koren for ign in ignorisani_dirs):
            continue
            
        for f in fajlovi:
            full_path = os.path.join(koren, f)
            if os.path.islink(full_path):
                continue
            try:
                velicina_mb = os.path.getsize(full_path) / (1024 * 1024)
                if velicina_mb >= min_mb:
                    mime = daj_mime_tip(full_path)
                    rezultati.append((full_path, velicina_mb, mime))
            except Exception:
                pass

    rezultati.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'STVARNI TIP (MIME)':<30} | {'VELIČINA':<10} | {'PUTANJA FAJLA'}")
    print("-" * 85)
    for path, sz, mime in rezultati[:30]:  # Prikaz prvih 30 najvećih
        print(f"{mime:<30} | {sz:<7.1f} MB | {path}")

if __name__ == "__main__":
    import sys
    home = os.path.expanduser("~")
    skeniraj_velike_fajlove(home, min_mb=50)
