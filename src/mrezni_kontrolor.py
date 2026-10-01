import os
import sys
import datetime
import urllib.request

def proveri_mrezu():
    vreme = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("izlaz/logovi", exist_ok=True)
    os.makedirs("izlaz/dokumenti", exist_ok=True)
    
    # Provera internet konekcije preko HTTP-a (pouzdanije na iOS/iSH)
    try:
        urllib.request.urlopen("https://1.1.1.1", timeout=3)
        mreza_ok = True
    except Exception:
        mreza_ok = False
        
    log_putanja = os.path.abspath("izlaz/logovi/mrezni_status.log")
    with open(log_putanja, "a", encoding="utf-8") as f:
        status_str = "ONLINE" if mreza_ok else "OFFLINE"
        f.write(f"[{vreme}] MREŽNI STATUS (iPhone Node): {status_str}\n")
        
    print(f"[OK] Log upisan u: {log_putanja}")
    
    # Generisanje PDF izvještaja
    try:
        from memorandum_factory import napravi_memorandum
        napravi_memorandum()
    except Exception as e:
        print(f"[UPOZORENJE] Generisanje memoranduma preskočeno: {e}")

if __name__ == '__main__':
    proveri_mrezu()
