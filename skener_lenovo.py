import os
import shutil
import ast
import hashlib
import json

BASE_PATH = os.getcwd()
HASHES_FILE = os.path.join(BASE_PATH, 'EXISTING_GRID_HASHES.json')
OUT_PATH = os.path.expanduser('~/lenovo_ekstrahovano_zlato')

existing_hashes = set()
if os.path.exists(HASHES_FILE):
    with open(HASHES_FILE, 'r', encoding='utf-8') as fp:
        existing_hashes = set(json.load(fp))
print(f"[+] Učitano {len(existing_hashes)} mrežnih otisaka (iPhone + Android + ASUS). Skeniram Lenovo arhivu...")

os.makedirs(OUT_PATH, exist_ok=True)
count_found = 0
count_new_unique = 0

for root, _, files in os.walk(BASE_PATH):
    if 'lenovo_ekstrahovano_zlato' in root or '.git' in root or 'node_modules' in root:
        continue
    for f in files:
        if f.endswith('.py') and f != 'skener_lenovo.py':
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
                    count_new_unique += 1
                    print(f"[NOVO ZLATO - LENOVO UNIKAT] {f}")
            except Exception:
                pass

print(f"\n[REZULTAT LENOVO] Ukupno analizirano: {count_found} Python fajlova.")
print(f"[REZULTAT LENOVO] Izvučeno potpuno NOVIH, unikatnih modula: {count_new_unique}")
