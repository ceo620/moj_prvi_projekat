import os
import sys
from datetime import datetime
from pathlib import Path

# Putanja za logove unutar izlazne arhitekture
LOG_DIR = Path.home() / "projekti" / "moj_prvi_projekat" / "izlaz" / "logovi"
LOG_DIR.mkdir(parents=True, exist_ok=True)

try:
    from memorandum_factory import napravi_memorandum
except ImportError:
    napravi_memorandum = None

NODES = {
    "LENOVO_DELTA_MASTER": "localhost",
    "ASUS_SATELLITE_WSL": "localhost",
    "MACBOOK_SATELLITE": "macbook.local",
    "MSI_SATELLITE": "msi.local",
    "ANDROID_TERMUX_NODE": "android.local",
    "IPHONE_ISH_NODE": "iphone.local"
}

def proveri_mrezu():
    vreme = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    statusi = []
    
    for name, host in NODES.items():
        if host == "localhost":
            st = "ONLINE (Master/Local)"
        else:
            # Brza mrežna provjera
            res = os.system(f"ping -c 1 -w 1 {host} > /dev/null 2>&1")
            st = "ONLINE" if res == 0 else "STANDBY / OFFLINE"
        
        statusi.append(f"{name}: {st}")

    # 1. Zapisivanje u log fajl na Desktopu (IZLAZ_Logovi)
    log_fajl = LOG_DIR / "mrezni_status.log"
    with open(log_fajl, "a", encoding="utf-8") as f:
        f.write(f"=== MREŽNI PREGLED [{vreme}] ===\n")
        for line in statusi:
            f.write(f"  - {line}\n")
        f.write("\n")
        
    print(f"[OK] Log upisan u: {log_fajl}")

    # 2. Generisanje PDF izvještaja ako je fabrika dostupna
    if napravi_memorandum:
        tekst_pdf = "<br/>".join([f"• <b>{s.split(':')[0]}</b>:{s.split(':')[1]}" for s in statusi])
        pdf_path = napravi_memorandum(
            klijent="MREŽNI KONTROLOR 888",
            predmet="Status Čvorova Mreže",
            tekst=f"Automatska mrežna dijagnostika izvršena u {vreme}:<br/><br/>{tekst_pdf}"
        )
        print(f"[OK] Mrežni PDF izvještaj kreiran: {pdf_path}")

if __name__ == "__main__":
    proveri_mrezu()
