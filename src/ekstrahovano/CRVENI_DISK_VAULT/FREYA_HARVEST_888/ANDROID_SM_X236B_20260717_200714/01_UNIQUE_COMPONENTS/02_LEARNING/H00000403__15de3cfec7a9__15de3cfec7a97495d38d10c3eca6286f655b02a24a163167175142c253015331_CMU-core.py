#!/usr/bin/env python3
import time, datetime, json, os, sys, signal

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 CMU CORE — Nivo 1 (Core Engine) AKTIVIRAN")

# Učitaj config
CONFIG_PATH = '../CMU-config.json'
STATE_PATH = 'core/state.json'

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("❌ Config fajl nedostaje! Vraćam se na bootstrap.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)

def load_state():
    if not os.path.exists(STATE_PATH):
        return {"last_heartbeat": None, "current_level": 1, "total_cycles": 0, "errors_today": 0, "status": "initializing"}
    with open(STATE_PATH) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

config = load_config()
state = load_state()

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Core Engine učitan — Nivo {config['current_level']} | Status: {state['status']}")

# Glavni Core Engine loop
def core_engine_loop():
    while True:
        t = datetime.datetime.now().strftime('%H:%M:%S')
        state["last_heartbeat"] = t
        state["total_cycles"] += 1
        state["status"] = "running"
        
        print(f"[{t}] 🔥 CMU CORE ENGINE | Cycle #{state['total_cycles']} | Nivo {config['current_level']} | Stanje: {state['status']}")
        
        # Jednostavan error handling primjer
        try:
            # Ovdje će kasnije doći prava logika
            if state["total_cycles"] % 5 == 0:
                print(f"[{t}] 📡 Guardian integracija aktivna — šaljem status")
        except Exception as e:
            state["errors_today"] += 1
            print(f"[{t}] ⚠️ Greška u engine-u: {e}")
        
        save_state(state)
        time.sleep(60)  # 60 sekundi između ciklusa (možeš promijeniti)

def signal_handler(sig, frame):
    print("\n🛑 CMU CORE ENGINE zaustavljen ručno.")
    state["status"] = "stopped"
    save_state(state)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    try:
        core_engine_loop()
    except Exception as e:
        print(f"💥 Fatalna greška u Core Engine-u: {e}")
        state["status"] = "crashed"
        save_state(state)
