import os
import sys
import datetime
import urllib.request

def proveri_mrezu():
    vreme = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("izlaz/logovi", exist_ok=True)
    os.makedirs("izlaz/dokumenti", exist_ok=True)
    
    # HTTP provera preko urllib (radi bez mrežnih ograničenja na iOS/iSH)
    try:
        req = urllib.request.Request("https://1.1.1.1", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            mreza_ok = True
    except Exception:
        mreza_ok = False
        
    status_str = "ONLINE" if mreza_ok else "OFFLINE"
    log_putanja = os.path.abspath("izlaz/logovi/mrezni_status.log")
    
    with open(log_putanja, "a", encoding="utf-8") as f:
        f.write(f"[{vreme}] MREŽNI STATUS (iPhone iSH): {status_str}\n")
        
    print(f"[OK] Log upisan u: {log_putanja}")
    
    # Generisanje PDF izvještaja putem memorandum_factory
    try:
        from memorandum_factory import napravi_memorandum
        napravi_memorandum()
    except Exception as e:
        print(f"[ UPOZORENJE ] Generisanje PDF-a preskočeno: {e}")

if __name__ == '__main__':
    proveri_mrezu()
