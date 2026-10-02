# ==============================================================================
# TITAN MAX_TRUST 88 PILLAR FORENSIC MASTER SCRIPT 888
# STATUS: SYSTEM RED - STEP102 LOCKED - NO FINAL USE
# MODE: READ_ONLY | ZERO_TRUST | NO_NETWORK | NO_EXECUTION
# ==============================================================================

import os
import hashlib
import json
import csv
from datetime import datetime, timezone
import time

# --- CONFIGURATION & SAFE BOUNDARIES ---
AUTHORIZED_ROOTS = [
    r"C:\Users\Korisnik\Documents\Codex\2026-05-05\files-mentioned-by-the-user-titan\outputs\titan_ultimate_final_blend",
    r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE",
    r"C:\Users\Korisnik\Desktop\firma final",
    r"C:\DANIJELA"
]

PROTECTED_DIRS = [
    r"C:\Users\Korisnik\Desktop\TITAN_BACKUPS"
]

VOLATILE_DIRS = [
    "runtime_state", ".git", "__pycache__", "temp"
]

UNSAFE_WORDS = [
    "lender-ready", "bankable", "approved", "confirmed", "validated",
    "fully aligned", "eligible asset", "grant secured", "financing secured",
    "ready-to-go", "guaranteed", "final", "live", "green", "no risk",
    "Step102 accepted", "creditor-ready", "success story", "institutional shield"
]

OUTPUT_DIR = r"C:\Users\Korisnik\Desktop\TITAN_FORENSIC_OUTPUT_888"

# --- CORE FORENSIC FUNCTIONS ---

def get_utc_epoch():
    return datetime.now(timezone.utc).isoformat()

def calculate_sha256(filepath):
    """Dynamically calculates SHA256 from physical file bytes. NO HALLUCINATION."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        hash_val = sha256_hash.hexdigest()
        return hash_val, hash_val[:16]
    except Exception as e:
        return "UNVERIFIED_NO_ACCESS", "UNVERIFIED"

def scan_text_for_quarantine(filepath):
    """Scans readable text files for prohibited unsafe wording."""
    if not filepath.endswith(('.txt', '.md', '.csv', '.json')):
        return False, []
    
    found_unsafe_words = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            for word in UNSAFE_WORDS:
                if word in content:
                    found_unsafe_words.append(word)
    except Exception:
        pass
    
    return len(found_unsafe_words) > 0, found_unsafe_words

def enforce_boundaries(directory):
    """Ensures we do not deep-scan volatile or protected areas."""
    for protected in PROTECTED_DIRS:
        if directory.startswith(protected):
            return "PROTECTED_REGISTER_ONLY"
    for vol in VOLATILE_DIRS:
        if vol in directory:
            return "VOLATILE_EXCLUDED"
    return "AUTHORIZED"

# --- MAIN EXECUTION ---

def run_forensic_scan():
    print("INITIATING MAX_TRUST FORENSIC SCAN...")
    print("MODE: READ_ONLY | ZERO_TRUST")
    start_time = time.time()
    scan_epoch = get_utc_epoch()

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    master_register = []
    quarantine_register = []
    error_log = []
    
    files_scanned = 0
    unsafe_flags = 0

    for root_dir in AUTHORIZED_ROOTS:
        if not os.path.exists(root_dir):
            error_log.append({"path": root_dir, "error": "ROOT_NOT_FOUND"})
            continue

        for subdir, dirs, files in os.walk(root_dir):
            status = enforce_boundaries(subdir)
            if status != "AUTHORIZED":
                dirs[:] = [] # Stop traversing this branch
                continue
            
            for file in files:
                files_scanned += 1
                filepath = os.path.join(subdir, file)
                
                # 1. Integrity Check & Hashing
                sha256_full, sha256_16 = calculate_sha256(filepath)
                file_size = os.path.getsize(filepath) if sha256_full != "UNVERIFIED_NO_ACCESS" else 0
                
                # 2. Content Safety Check (Ring 2)
                is_unsafe, flagged_words = scan_text_for_quarantine(filepath)
                if is_unsafe:
                    unsafe_flags += 1
                    quarantine_register.append({
                        "file_path": filepath,
                        "flagged_words": " | ".join(flagged_words),
                        "action": "NEEDS_REWRITE",
                        "final_use_allowed": "NO"
                    })

                master_register.append({
                    "file_name": file,
                    "file_path": filepath,
                    "size_bytes": file_size,
                    "sha256": sha256_full,
                    "sha256_16": sha256_16,
                    "unsafe_wording_flag": "YES" if is_unsafe else "NO",
                    "final_use_allowed": "NO"
                })

    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)

    # --- OUTPUT GENERATION ---
    
    # 1. Master CSV
    master_csv_path = os.path.join(OUTPUT_DIR, "TITAN_MAX_TRUST_MASTER_REGISTER.csv")
    with open(master_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "file_path", "size_bytes", "sha256", "sha256_16", "unsafe_wording_flag", "final_use_allowed"])
        writer.writeheader()
        writer.writerows(master_register)

    # 2. Quarantine CSV
    quarantine_csv_path = os.path.join(OUTPUT_DIR, "TITAN_MAX_TRUST_UNSAFE_QUARANTINE.csv")
    with open(quarantine_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "flagged_words", "action", "final_use_allowed"])
        writer.writeheader()
        writer.writerows(quarantine_register)

    # 3. Summary JSON
    summary_data = {
        "execution_mode": "READ_ONLY_ZERO_TRUST",
        "scan_epoch_utc": scan_epoch,
        "execution_duration_ms": duration_ms,
        "source_files_modified": "NO",
        "total_files_reviewed": files_scanned,
        "unsafe_wording_count": unsafe_flags,
        "final_use_allowed_yes_count": 0,
        "final_verdict": "TITAN_MAX_TRUST_88_PILLAR_FORENSIC_MASTER_888_REVIEW_REQUIRED" if unsafe_flags > 0 else "TITAN_MAX_TRUST_88_PILLAR_FORENSIC_MASTER_888_COMPLETE_REPORT_ONLY"
    }
    
    summary_path = os.path.join(OUTPUT_DIR, "TITAN_MAX_TRUST_SUMMARY.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=4)

    # 4. Hash Manifest
    manifest_path = os.path.join(OUTPUT_DIR, "TITAN_MAX_TRUST_HASH_MANIFEST.txt")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(f"# TITAN MAX_TRUST HASH MANIFEST 888\n")
        f.write(f"# EPOCH: {scan_epoch}\n")
        f.write(f"# STATUS: SYSTEM RED - NO FINAL USE\n\n")
        for reg in master_register:
            if reg['sha256'] != "UNVERIFIED_NO_ACCESS":
                f.write(f"{reg['sha256']}  {reg['file_name']}\n")

    print(f"\n[OK] FORENSIC SCAN COMPLETE.")
    print(f"DURATION: {duration_ms} ms")
    print(f"FILES SCANNED: {files_scanned}")
    print(f"QUARANTINED FILES: {unsafe_flags}")
    print(f"OUTPUT DIRECTORY: {OUTPUT_DIR}")
    print("\nSYSTEM RED — STEP102 LOCKED — NO FINAL USE.")

if __name__ == "__main__":
    run_forensic_scan()