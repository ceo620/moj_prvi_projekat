# Forenzički Agent za detekciju skrivenih baza, ključeva i tajni
import os
import re

ARCHIVE_DIR = os.path.expanduser('~/TITAN_ASUS_MAGNUS_ARCHIVE')

SENSITIVE_PATTERNS = {
    'SSH/Kripto Ključevi': r'-----BEGIN (RSA|OPENSSH|PRIVATE|PUBLIC) KEY-----',
    'Lozinke/Tokeni/API': r'(api[_-]?key|secret|password|token|bearer|passwd)\s*[:=]\s*[\'"][^\'"]+[\'"]',
    'Database/SQL Dump': r'(CREATE TABLE|INSERT INTO|SQLite format|BEGIN TRANSACTION)',
    'Mrežne Konfiguracije': r'(bind-address|LISTEN_PORT|ProxyPass|route add|iptables)',
    'Skrivene Env Varijable': r'export\s+[A-Z0-9_]+\s*='
}

def forenzika():
    if not os.path.exists(ARCHIVE_DIR):
        print(f"Direktorijum {ARCHIVE_DIR} ne postoji.")
        return

    pronadjeno = {}
    total_fajlova = 0

    for root, _, files in os.walk(ARCHIVE_DIR):
        for f in files:
            total_fajlova += 1
            path = os.path.join(root, f)

            if os.path.getsize(path) > 20 * 1024 * 1024:
                continue

            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    sadrzaj = fp.read()

                    for kategorija, pattern in SENSITIVE_PATTERNS.items():
                        if re.search(pattern, sadrzaj, re.IGNORECASE):
                            if kategorija not in pronadjeno:
                                pronadjeno[kategorija] = []
                            pronadjeno[kategorija].append(path.replace(os.path.expanduser('~'), '~'))
            except Exception:
                pass

    print(f"=== REZULTATI DUBINSKE FORENZIKE (Skenirano fajlova: {total_fajlova}) ===")
    if not pronadjeno:
        print("Nije pronađen nijedan osjetljiv ključ, baza ili token u skeniranim fajlovima.")
    for kat, fajlovi in pronadjeno.items():
        print(f"\n🔑 [{kat}] - Pronađeno: {len(fajlovi)} fajlova")
        for f in fajlovi[:10]:
            print(f"   └─ {f}")
        if len(fajlovi) > 10:
            print(f"   ... i još {len(fajlovi) - 10} fajlova.")

if __name__ == "__main__":
    forenzika()
