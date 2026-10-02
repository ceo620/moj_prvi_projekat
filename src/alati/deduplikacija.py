#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import hashlib
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

SEARCH_ROOTS = [
    "/mnt/c/Users/titangrid.info",
    "/mnt/c/Users/ceo"
]

DRY_RUN = True

EXCLUDE_DIRS = {'AppData', 'Program Files', 'Windows', '.git', '$RECYCLE.BIN', 'System Volume Information'}
EXCLUDE_FILES = {'NTUSER.DAT', 'ntuser.dat', 'usrclass.dat', 'desktop.ini'}

def get_sha256(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return None

def main():
    print("=== FAST DEDUPLIKACIJA (SIZE + SHA-256) ===")
    print(f"REŽIM: {'SIMULACIJA (DRY-RUN)' if DRY_RUN else 'PRODUKCIJA (STVARNO BRISANJE)'}\n")

    size_map = defaultdict(list)
    total_files = 0

    print("[1/2] Grupišem po veličini bajtova...")
    for root_dir in SEARCH_ROOTS:
        if not os.path.exists(root_dir):
            continue

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]

            for file in files:
                if file.startswith('~$') or file.endswith(('.tmp', '.ini', '.lnk')) or file in EXCLUDE_FILES:
                    continue

                full_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(full_path)
                    size_map[size].append(full_path)
                    total_files += 1
                except (PermissionError, OSError):
                    continue

    print(f"[✓] Skrenirano ukupno: {total_files} fajlova.")

    # Uzimamo samo fajlove koji imaju bar još jedan fajl identične veličine
    candidates = {size: paths for size, paths in size_map.items() if len(paths) > 1}
    candidates_count = sum(len(p) for p in candidates.values())
    print(f"[!] Potencijalnih duplikata po veličini: {candidates_count} fajlova u {len(candidates)} grupa.")

    print("\n[2/2] Računam SHA-256 samo za kandidate...")
    hash_map = defaultdict(list)
    processed = 0

    for size, paths in candidates.items():
        for path in paths:
            processed += 1
            if processed % 50 == 0 or processed == candidates_count:
                print(f"    Napredak heširanja: {processed}/{candidates_count}...", end='\r')
            
            sha_hash = get_sha256(path)
            if sha_hash:
                hash_map[sha_hash].append(path)

    print(f"\n\n[✓] Obrada završena.")

    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 2}
    print(f"[!] Grupa sa više od 2 identične kopije: {len(duplicates)}\n")

    to_delete_count = 0

    for sha_hash, paths in duplicates.items():
        print(f"GRUPA SHA-256: {sha_hash[:12]}...")
        print(f"  🟢 OSTAJE (Original): {paths[0]}")
        print(f"  🟢 OSTAJE (Kopija):   {paths[1]}")
        
        for delete_target in paths[2:]:
            to_delete_count += 1
            if DRY_RUN:
                print(f"  🔴 [SIMULACIJA] ZA BRISANJE: {delete_target}")
            else:
                try:
                    os.remove(delete_target)
                    print(f"  🔴 [OBRISANO]: {delete_target}")
                except Exception as e:
                    print(f"  ❌ GREŠKA: {e}")
        print("-" * 60)

    print(f"\n[✓] Ukupno označeno za brisanje: {to_delete_count}")

if __name__ == "__main__":
    main()
