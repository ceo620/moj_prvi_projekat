# Agent za potpunu ekstrakciju i indeksiranje svih skripti i ugovora sa Crvenog Diska
import os
import shutil

RED_DISK = '/mnt/d'
DEST_BASE = os.path.expanduser('~/projekti/moj_prvi_projekat/src/ekstrahovano/CRVENI_DISK_VAULT')

TARGET_FOLDERS = [
    'AI_AGENT_PRODUCTION_GATE',
    'FREYA_HARVEST_888',
    'FREYA_HUMAN_GATE_SELECTED_COPY',
    'FREYA_LENOVO_NODE_888',
    'FREYA_MAC_RED_UNION_888',
    'FREYA_PORTABLE_FACTORY_888',
    'IPHONE_KRITICNA_KOPIJA_888_nu3ErN',
    'MAC_ZIP_020_BACKUP_20260919',
    'SORTED_RECOVERY_2026'
]

ALLOWED_EXTENSIONS = ('.py', '.sh', '.env', '.json', '.md', '.txt', '.yml', '.yaml')

def masovna_ekstrakcija():
    if not os.path.exists(RED_DISK):
        print("Crveni disk nije prisutan na /mnt/d")
        return

    os.makedirs(DEST_BASE, exist_ok=True)
    print("=== POKRETANJE POTPUNE EKSTRAKCIJE SA CRVENOG DISKA ===")

    ukupno_kopirano = 0
    kopirano_po_ekstenziji = {}

    for folder in TARGET_FOLDERS:
        src_path = os.path.join(RED_DISK, folder)
        if not os.path.exists(src_path):
            continue

        target_dir = os.path.join(DEST_BASE, folder)
        os.makedirs(target_dir, exist_ok=True)

        for root, _, files in os.walk(src_path):
            for f in files:
                if f.endswith(ALLOWED_EXTENSIONS):
                    rel_path = os.path.relpath(root, src_path)
                    dest_dir = os.path.join(target_dir, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)

                    src_file = os.path.join(root, f)
                    dest_file = os.path.join(dest_dir, f)

                    if not os.path.exists(dest_file):
                        try:
                            # Preskačemo fajlove veće od 50MB
                            if os.path.getsize(src_file) <= 50 * 1024 * 1024:
                                shutil.copy2(src_file, dest_file)
                                ukupno_kopirano += 1
                                ext = os.path.splitext(f)[1].lower()
                                kopirano_po_ekstenziji[ext] = kopirano_po_ekstenziji.get(ext, 0) + 1
                        except Exception:
                            pass

    print(f"\n✅ EKSTRAKCIJA ZAVRŠENA! Ukupno bezbedno izvučeno fajlova: {ukupno_kopirano}")
    for ext, count in kopirano_po_ekstenziji.items():
        print(f"   └─ [{ext}]: {count} fajlova")

if __name__ == "__main__":
    masovna_ekstrakcija()
