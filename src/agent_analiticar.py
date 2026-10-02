# Deep Content Extractor - Grupiše stvarni kôd iz arhive
import os
import re
import shutil

ARCHIVE_DIR = os.path.expanduser('~/TITAN_ASUS_MAGNUS_ARCHIVE')
EXPORT_DIR = os.path.expanduser('~/projekti/moj_prvi_projekat/src/ekstrahovano')

def klasifikuj_i_ekstrahuj():
    if not os.path.exists(ARCHIVE_DIR):
        print("Arhivski direktorijum ne postoji.")
        return

    os.makedirs(os.path.join(EXPORT_DIR, 'python_skripte'), exist_ok=True)
    os.makedirs(os.path.join(EXPORT_DIR, 'mrezne_skripte'), exist_ok=True)
    os.makedirs(os.path.join(EXPORT_DIR, 'dokumenti_i_ugovori'), exist_ok=True)

    kopirano = 0
    for root, _, files in os.walk(ARCHIVE_DIR):
        for f in files:
            path = os.path.join(root, f)
            if os.path.getsize(path) > 5 * 1024 * 1024:
                continue

            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    sadrzaj = fp.read()

                    # 1. Python kôd
                    if "import " in sadrzaj or "def " in sadrzaj or "class " in sadrzaj:
                        shutil.copy2(path, os.path.join(EXPORT_DIR, 'python_skripte', f))
                        kopirano += 1
                    # 2. Mrežne i sistemske skripte
                    elif "curl" in sadrzaj or "ssh" in sadrzaj or "apt" in sadrzaj:
                        shutil.copy2(path, os.path.join(EXPORT_DIR, 'mrezne_skripte', f))
                        kopirano += 1
                    # 3. Ugovori, protokoli i specifikacije
                    elif "EVIDENCE" in sadrzaj or "CERTIFICATION" in sadrzaj or "MANIFEST" in sadrzaj:
                        shutil.copy2(path, os.path.join(EXPORT_DIR, 'dokumenti_i_ugovori', f))
                        kopirano += 1
            except Exception:
                pass

    print(f"=== EKSTRAKCIJA ZAVRŠENA ===")
    print(f"Uspešno razvrstano i sačuvano {kopirano} fajlova u {EXPORT_DIR}")

if __name__ == "__main__":
    klasifikuj_i_ekstrahuj()
