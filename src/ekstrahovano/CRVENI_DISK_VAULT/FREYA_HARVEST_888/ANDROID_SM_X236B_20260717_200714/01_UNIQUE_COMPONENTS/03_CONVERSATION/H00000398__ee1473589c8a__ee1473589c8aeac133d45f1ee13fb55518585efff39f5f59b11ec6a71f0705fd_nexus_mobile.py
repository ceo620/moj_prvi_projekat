# ===================================================
# TITAN IMMUTABLE RUNTIME GUARD — SSOT ENFORCED
# ZAKLJUČANO OD STRANE CFO DANIJELE KESKIN
TITAN_SSOT_CANON = 27800000.00
def _assert_titan_canon(val):
    if float(val) != TITAN_SSOT_CANON:
        raise ValueError("CRITICAL DRIFT DETECTED! ACCESS DENIED.")
# ===================================================
import json
import time
import os
import requests
import subprocess
from datetime import datetime
from delta_v4_5 import DeltaV45

MEMORY_PATH = "/sdcard/delta_v4_memory.json"
NTFY_TOPIC = "titan_grid_888_alerts"
LENOVO_IP = "192.168.1.119" # Promeni ako je IP adresa tvog Lenovo računara drugačija

class DeltaOmniScanner:
    def __init__(self):
        self.d = DeltaV45()
        self.last_mtime = 0
        self.last_alert_hash = None
        print("🧠 DELTA OMNI-SCANNER v1.5 UKLJUČEN.")

    def ping_device(self, ip_address):
        """Skenira mrežnu dostupnost uređaja."""
        try:
            # Pokreće ping komandu sa limitom od 1 paketa i 2 sekunde timeout-a
            output = subprocess.run(["ping", "-c", "1", "-W", "2", ip_address], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return output.returncode == 0
        except:
            return False

    def scan_android(self):
        """Skenira lokalni Android čvor."""
        status = {"status": "ONLINE", "storage": "OK"}
        if not os.path.exists(MEMORY_PATH):
            status["storage"] = "WARN (Nema baze)"
        return status

    def scan_lenovo(self):
        """Skenira Lenovo server."""
        # Privremena adresa, ako skripta prepozna konekciju koristiće nju
        is_alive = self.ping_device(LENOVO_IP)
        return {
            "status": "ONLINE" if is_alive else "OFFLINE (Proveri IP/Mrežu)",
            "ip": LENOVO_IP
        }

    def scan_iphone(self):
        """Skenira komunikacioni most sa iPhone-om."""
        try:
            # Provera da li je ntfy server dostupan za iPhone push
            r = requests.get(f"https://ntfy.sh/{NTFY_TOPIC}/json?poll=1", timeout=5)
            return {"status": "ONLINE", "bridge": "CONNECTED" if r.status_code == 200 else "ERROR"}
        except:
            return {"status": "OFFLINE", "bridge": "DISCONNECTED"}

    def run_full_scan(self):
        """Izvršava kompletan sken mreže i ispisuje izveštaj."""
        print(f"\n================ [ OMNI-SCAN: {datetime.now().strftime('%H:%M:%S')} ] ================")
        
        android = self.scan_android()
        print(f"🤖 [ANDROID] Status: {android['status']} | Baza: {android['storage']}")
        
        lenovo = self.scan_lenovo()
        print(f"💻 [LENOVO]  Status: {lenovo['status']} | Ciljna IP: {lenovo['ip']}")
        
        iphone = self.scan_iphone()
        print(f"📱 [IPHONE]  Status: {iphone['status']} | ntfy Most: {iphone['bridge']}")
        print("================================================================\n")
        
        # Ingestija rezultata skeniranja u Delta centralnu memoriju
        self.d.ingest(f"""
## Omni-Scan Izveštaj: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Android Čvor: {android['status']}
- Lenovo Čvor: {lenovo['status']}
- iPhone Čvor: {iphone['status']} (Most: {iphone['bridge']})
""")

    def check_memory_updates(self):
        """Standardni nadzor za proboje."""
        if not os.path.exists(MEMORY_PATH): return
        mtime = os.path.getmtime(MEMORY_PATH)
        if mtime <= self.last_mtime: return
        self.last_mtime = mtime
        
        try:
            with open(MEMORY_PATH, 'r') as f:
                data = json.load(f)
            last_entry = data.get("chat_history", [])[-1].get("content", "")
            
            if any(k in last_entry.upper() for k in ["PROBOJ", "SENTINEL", "DSCR", "27.8M", "HARVEST"]):
                h = hash(last_entry)
                if h != self.last_alert_hash:
                    self.last_alert_hash = h
                    # Slanje na ntfy za iPhone
                    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
                        data=f"Uvid: {last_entry[:100]}...".encode('utf-8'),
                        headers={"Title": "⚡ DELTA UKRŠTANJE", "Priority": "high", "Tags": "radar"}, 
                        timeout=10)
                    print("📱 Signal poslat na iPhone nakon izmene u bazi.")
        except: pass

    def start_loop(self):
        while True:
            self.run_full_scan()
            self.check_memory_updates()
            time.sleep(30) # Skenira celu mrežu svakih 30 sekundi

if __name__ == "__main__":
    DeltaOmniScanner().start_loop()
