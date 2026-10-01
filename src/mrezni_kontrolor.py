import os
import sys
import subprocess
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memorandum_factory import napravi_memorandum

CVOROVI = {
    "DELTA (Master)": "127.0.0.1",
    "ASUS (Doc Factory)": "192.168.1.10",
    "MacBook": "192.168.1.11",
    "MSI": "192.168.1.12",
    "Android (Termux)": "192.168.1.13",
    "iPhone (iSH)": "192.168.1.14"
}

def proveri_mrezu(generisi_pdf=True):
    log_dir = os.path.join(os.getcwd(), "izlaz", "logovi")
    doc_dir = os.path.join(os.getcwd(), "izlaz", "dokumenti")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(doc_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    izvjestaj_linije = [f"=== MREŽNI STATUS [TITAN-888] {timestamp} ==="]

    for naziv, ip in CVOROVI.items():
        res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = "ONLINE" if res.returncode == 0 else "OFFLINE"
        izvjestaj_linije.append(f"[{status}] {naziv} ({ip})")

    sadrzaj_tekst = "\n".join(izvjestaj_linije) + "\n\n"
    log_fajl = os.path.join(log_dir, "mrezni_status.log")

    with open(log_fajl, "a", encoding="utf-8") as f:
        f.write(sadrzaj_tekst)

    print(f"[OK] Log upisan u: {log_fajl}")

    if generisi_pdf:
        pdf_fajl = os.path.join(doc_dir, f"Memorandum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        napravi_memorandum("DELTA (Master)", sadrzaj_tekst, pdf_fajl)
        print(f"[OK] Mrežni PDF izvještaj kreiran: {pdf_fajl}")

if __name__ == "__main__":
    proveri_mrezu(generisi_pdf=True)
