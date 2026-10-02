import os
import shutil
import ast
import hashlib

# Skeniramo od trenutnog projektnog foldera naniže
BASE_PATH = os.getcwd()
OUT_PATH = os.path.expanduser('~/sst_ekstrahovano_zlato')
existing_hashes = set()

os.makedirs(OUT_PATH, exist_ok=True)
print(f"[+] Skeniram sve Python datoteke unutar: {BASE_PATH}")

count_found = 0
count_valid = 0

for root, dirs, files in os.walk(BASE_PATH):
    # Preskačemo već izvučeno zlato i git
    if 'sst_ekstrahovano_zlato' in root or '.git' in root:
        continue
    for f in files:
        if f.endswith('.py') and f != 'skener_arhive.py':
            count_found += 1
            full_path = os.path.join(root, f)
            try:
                with open(full_path, 'rb') as fp:
                    content = fp.read()
                ast.parse(content)
                h = hashlib.sha256(content).hexdigest()
                if h not in existing_hashes:
                    existing_hashes.add(h)
                    dest = os.path.join(OUT_PATH, f)
                    shutil.copy(full_path, dest)
                    count_valid += 1
                    print(f"[OK] Izvučen čist modul: {f}")
            except Exception:
                pass

print(f"\n[REZULTAT] Pronađeno ukupno: {count_found} Python fajlova.")
print(f"[REZULTAT] Ekstrahovano: {count_valid} unikatnih i ispravnih modul(a) u {OUT_PATH}")
