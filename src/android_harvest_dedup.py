#!/usr/bin/env python3
import os
import sys
import hashlib
from pathlib import Path

# Lista sistemskih ekstenzija i direktorijuma za ignorisanje
EXCLUDED_EXTENSIONS = {'.blf', '.regtrans-ms', '.lnk', '.dat', '.ini', '.sys'}
EXCLUDED_FILENAMES = {'ntuser.dat', 'desktop.ini', 'thumbs.db'}
EXCLUDED_DIRS = {'appdata', '.git', '$recycle.bin', 'system volume information'}

# Ciljni direktorijumi za skeniranje (prilagoditi po potrebi)
TARGET_PATHS = [
    Path.home(),
    Path("/mnt/c/Users/ceo") if Path("/mnt/c/Users/ceo").exists() else Path.home(),
]

# Mobilne sabirne magistrale
TARGET_PATTERNS = [
    "Android_Harvest_",
    "DELTA_ANDROID_",
    "TITAN_GRID_",
]

def is_system_or_locked(path: Path) -> bool:
    """Proverava da li je fajl ili direktorijum sistemski/zaštićen."""
    name_lower = path.name.lower()
    if name_lower in EXCLUDED_FILENAMES or path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return True
    for parent in path.parents:
        if parent.name.lower() in EXCLUDED_DIRS:
            return True
    return False

def calculate_sha256(filepath: Path, block_size: int = 65536) -> str:
    """Izračunava SHA-256 otisak fajla u blokovima radi uštede memorije."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError) as e:
        print(f"[SKIP] Pristup onemogućen: {filepath} ({e})")
        return None

def run_forensic_deduplication(roots):
    print("=" * 70)
    print("TITAN GRID / FORENZIČKA ANALIZA I DEDUPLIKACIJA (ANDROID HARVEST)")
    print("Pravilo: Zadržavanje 1 Master + 1 Bekap kopije po SHA-256 hešu")
    print("=" * 70)

    hash_map = {}
    scanned_files = 0
    skipped_files = 0

    for root_path in roots:
        if not root_path.exists():
            continue
        print(f"[*] Skeniranje magistrale: {root_path}")
        
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            # Filtriranje zaštićenih direktorijuma na licu mesta
            dirnames[:] = [d for d in dirnames if d.lower() not in EXCLUDED_DIRS]
            
            for fname in filenames:
                file_path = Path(dirpath) / fname

                if is_system_or_locked(file_path):
                    skipped_files += 1
                    continue

                if not file_path.is_file() or file_path.is_symlink():
                    continue

                sha256 = calculate_sha256(file_path)
                if sha256:
                    hash_map.setdefault(sha256, []).append(file_path)
                    scanned_files += 1

    print(f"\n[+] Skeniranje završeno.")
    print(f"    Ukupno analizirano fajlova: {scanned_files}")
    print(f"    Preskočeno sistemskih fajlova: {skipped_files}")
    print(f"    Jedinstvenih SHA-256 otisaka: {len(hash_map)}")

    deleted_count = 0
    freed_bytes = 0

    print("\n[*] Čišćenje prekomjernih duplikata (Zadržavanje maks 2 primjerka)...")
    
    for sha256, files in hash_map.items():
        if len(files) > 2:
            # Zadrži prva 2 (1 Master + 1 Bekap), ukloni sve preko 2
            keep = files[:2]
            remove = files[2:]

            for f_to_del in remove:
                try:
                    size = f_to_del.stat().st_size
                    f_to_del.unlink()
                    deleted_count += 1
                    freed_bytes += size
                    print(f"[OBRISANO] {f_to_del}")
                except (PermissionError, OSError) as e:
                    print(f"[GREŠKA] Nije moguće obrisati {f_to_del}: {e}")

    freed_mb = freed_bytes / (1024 * 1024)
    print("=" * 70)
    print(f"IZVJEŠTAJ DEDUPLIKACIJE:")
    print(f" - Uklonjeno prekobrojnih duplikata: {deleted_count}")
    print(f" - Oslobođeno prostora na disku: {freed_mb:.2f} MB")
    print("=" * 70)

if __name__ == "__main__":
    run_forensic_deduplication(TARGET_PATHS)
os

