import os
import shutil
import hashlib

BASE_PATH = os.getcwd()
OUT_PATH = os.path.expanduser('~/sst_ekstrahovani_ssot_resursi')

SSOT_PATTERNS = [
    'manifest', 'canonical', 'ssot', 'evidence', 'protocol', 'registry',
    'schema', 'config', 'final_seal', 'chain', 'human_gate'
]

SSOT_EXTENSIONS = ('.json', '.sha256', '.env', '.docx', '.db', '.sqlite', '.md')

os.makedirs(OUT_PATH, exist_ok=True)
print(f"[+] Pokrećem dubinsku pretragu SSOT resursa unutar: {BASE_PATH}")

found_ssot = 0
existing_hashes = set()

for root, dirs, files in os.walk(BASE_PATH):
    if 'sst_ekstrahovani_ssot_resursi' in root or '.git' in root:
        continue
    for f in files:
        f_lower = f.lower()
        if f_lower.endswith(SSOT_EXTENSIONS) or any(p in f_lower for p in SSOT_PATTERNS):
            full_path = os.path.join(root, f)
            try:
                with open(full_path, 'rb') as fp:
                    content = fp.read()
                h = hashlib.sha256(content).hexdigest()
                if h not in existing_hashes:
                    existing_hashes.add(h)
                    dest = os.path.join(OUT_PATH, f)
                    if os.path.exists(dest):
                        dest = os.path.join(OUT_PATH, f"{h[:8]}_{f}")
                    shutil.copy(full_path, dest)
                    found_ssot += 1
                    print(f"[SSOT PRONAĐEN] {f} -> {dest}")
            except Exception:
                pass

print(f"\n[REZULTAT] Pronađeno i osigurano {found_ssot} kritičnih SSOT resursa u {OUT_PATH}")
