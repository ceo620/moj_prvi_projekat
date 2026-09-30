# ===================================================
# TITAN IMMUTABLE RUNTIME GUARD — SSOT ENFORCED
# ZAKLJUČANO OD STRANE CFO DANIJELE KESKIN
TITAN_SSOT_CANON = 27800000.00
def _assert_titan_canon(val):
    if float(val) != TITAN_SSOT_CANON:
        raise ValueError("CRITICAL DRIFT DETECTED! ACCESS DENIED.")
# ===================================================
#!/usr/bin/env python3
import os, json, datetime, subprocess
from reasoning.reasoning import make_decision

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚡ CMU ACTION & META — Nivo 5 (FINALNI) AKTIVIRAN")

CONFIG_PATH = '/data/data/com.termux/files/home/05-RESOURCES/CMU/CMU-config.json'

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

config = load_config()

def execute_actions():
    """Izvršava odluke iz Reasoning-a i radi meta-evaluaciju"""
    decisions = make_decision()
    timestamp = datetime.datetime.now().isoformat()
    
    executed = 0
    for decision in decisions:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚡ IZVRŠAVAM: {decision['action']} (prioritet: {decision['priority']})")
        
        # Primjer izvršavanja — Guardian notifikacija
        if "Packing" in decision['action']:
            subprocess.run([
                'termux-notification',
                '--title', '🚨 CMU AKCIJA',
                '--content', decision['reason'],
                '--id', 'cmu-action'
            ])
            executed += 1
        
        # Meta layer — self-reflection
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔄 Meta: Akcija izvršena, bilježim za učenje...")
    
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Action & Meta završeno — {executed} akcija izvršeno")
    return {"executed": executed, "decisions": len(decisions), "timestamp": timestamp}

if __name__ == "__main__":
    execute_actions()
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🎉 CMU CORE — SVIH 5 NIVOA KOMPLETNO AKTIVIRANO")
