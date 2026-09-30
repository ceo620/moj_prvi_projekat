import os
import sys
import json
import subprocess
from titan_notifier import send_alert

TODO_PATH = os.path.expanduser("~/staged_scripts/ml_data/titan_todo.json")

def ucitaj_zadatke():
    if not os.path.exists(TODO_PATH):
        # Kreiranje podrazumevanih zadataka ako baza ne postoji
        os.makedirs(os.path.dirname(TODO_PATH), exist_ok=True)
        default_tasks = [
            {"id": 1, "kategorija": "Administracija", "task": "Predati popunjena 3 zahteva Upravi za vode (Faza 1 - 18.2M)", "status": "U TOKU"},
            {"id": 2, "kategorija": "Pravni Sektor", "task": "Pripremiti ugovor o unosu Know-How Equity-ja (Faza 0 - 12.8M)", "status": "CEKANJE"},
            {"id": 3, "kategorija": "Infrastruktura", "task": "Uvezati ostale uređaje radi povlačenja energetskih podataka (Faza 2 - 43.5M)", "status": "CEKANJE"}
        ]
        with open(TODO_PATH, 'w') as f:
            json.dump(default_tasks, f, indent=4)
        return default_tasks
    with open(TODO_PATH, 'r') as f:
        return json.load(f)

def proveri_i_generisi_dokument(task_id):
    try:
        import titan_document_factory as df
        if task_id == 1:
            df.kreiraj_zahtjev_vode()
        elif task_id == 2:
            df.kreiraj_ugovor_know_how()
    except Exception as e:
        pass

def proveri_zdravlje_sistema():
    print("\n=======================================================")
    print("          TITAN CORE MONITOR: STATUS SISTEMA          ")
    print("=======================================================")
    
    procesi = {
        "LIVE WATCHDOG (Osmatrač)": "titan_live_watchdog.py",
        "GLOBAL VACUUM (Usisivač)": "titan_global_vacuum.py",
        "HARVESTER DAEMON (Mreža)": "titan_harvester_daemon.py"
    }
    
    sve_ok = True
    for ime, skripta in procesi.items():
        check = subprocess.run(["pgrep", "-f", skripta], capture_output=True, text=True)
        if check.stdout.strip():
            print(f" [🟢] {ime:<30} -> AKTIVAN (PID: {check.stdout.strip().split()[0]})")
        else:
            print(f" [🔴] {ime:<30} -> ISKLJUČEN!")
            sve_ok = False
            
    ingest_dir = os.path.expanduser("~/staged_scripts/ml_data/drive_ingest")
    broj_fajlova = len(os.listdir(ingest_dir)) if os.path.exists(ingest_dir) else 0
    print(f" [📊] Ukupno usisanih eksternih baza znanja: {broj_fajlova} fajlova")
    print("=======================================================")
    
    if sve_ok:
        print(" [🛡️] STATUS: Sistem je 100% zdrav i autonoman.")
    else:
        print(" [⚠️] STATUS: DETEKTOVAN PREKID! Pokrenite 'python3 ~/staged_scripts/titan_self_healer.py'")

def prikazi_listu():
    tasks = ucitaj_zadatke()
    print("\n=======================================================")
    print("             TITAN ŽIVA OPERATIVNA TO-DO LISTA         ")
    print("=======================================================")
    for t in tasks:
        if t["status"] == "ZAVRSENO":
            status_icon = "🟢"
        else:
            status_icon = "⏳" if t["status"] == "U TOKU" else "🛑"
        print(f" [{t['id']}] {status_icon} [{t['kategorija']}] {t['task']} -> Status: {t['status']}")
    print("=======================================================")

if __name__ == "__main__":
    tasks = ucitaj_zadatke()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            proveri_zdravlje_sistema()
        elif cmd == "done" and len(sys.argv) > 2:
            task_id = int(sys.argv[2])
            for t in tasks:
                if t["id"] == task_id:
                    t["status"] = "ZAVRSENO"
                    send_alert("TITAN TODO", f"Zadatak završen: {t['task']}")
                    proveri_i_generisi_dokument(task_id)
            with open(TODO_PATH, 'w') as f:
                json.dump(tasks, f, indent=4)
            prikazi_listu()
    else:
        prikazi_listu()
