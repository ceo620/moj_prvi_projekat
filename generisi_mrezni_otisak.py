import os
import hashlib
import json

FOLDERS_TO_HASH = [
    os.path.expanduser('~/sst_ekstrahovano_zlato'),
    os.path.expanduser('~/sst_ekstrahovani_ssot_resursi'),
    os.path.join(os.getcwd(), 'src')
]

master_hashes = set()

for folder in FOLDERS_TO_HASH:
    if os.path.exists(folder):
        for root, _, files in os.walk(folder):
            for f in files:
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, 'rb') as fp:
                        h = hashlib.sha256(fp.read()).hexdigest()
                        master_hashes.add(h)
                except Exception:
                    pass

output_path = os.path.join(os.getcwd(), 'EXISTING_GRID_HASHES.json')
with open(output_path, 'w', encoding='utf-8') as fp:
    json.dump(list(master_hashes), fp)

print(f"[+] Registar postojećih otisaka uspešno sačuvan u: {output_path}")
print(f"[+] Ukupno zabeleženo jedinstvenih otisaka: {len(master_hashes)}")
