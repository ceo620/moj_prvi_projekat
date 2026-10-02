"""
TITAN KERNEL - STEP 98: MASTER EVIDENCE GATE VALIDATOR
----------------------------------------------------
Execution Mode: LIVE_EVIDENCE_GATE_VALIDATOR
Target: TITAN_P0_Evidence_Gate_Closure_Queue_v1.0.xlsx
Function: Dynamically parses owner decisions and source hashes to evaluate SSOT Lock state.
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# --- ZERO-TRUST CONFIGURATION ---
# Putanja do tvog kanonskog fajla 
SOURCE_FILE = "TITAN_P0_Evidence_Gate_Closure_Queue_v1.0.xlsx"
OUTPUT_DIR = r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL\VDR_ROOT\REPORTS\SYSTEM_HARMONIZATION\MASTER_EVIDENCE_GATE_VALIDATION"

class EvidenceGateValidator:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.system_status = "RED - BLOCKED"
        self.ssot_lock_allowed = "NO"
        self.lender_use_allowed = "NO"
        self.validation_log = []

    def load_canonical_queue(self):
        print(f"[*] Inicijalizacija Step 98: MASTER EVIDENCE GATE VALIDATOR...")
        try:
            # Forenzičko čitanje strukture kanonskog fajla
            self.df_gates = pd.read_excel(SOURCE_FILE, sheet_name="EVIDENCE_GATE_QUEUE")
            print(f"[+] Fajl uspješno učitan: {SOURCE_FILE}")
            return True
        except FileNotFoundError:
            print(f"[!] FATAL ERROR: Fajl {SOURCE_FILE} nije pronađen. SSOT LOCK ostaje BLOCKED.")
            return False
        except Exception as e:
            print(f"[!] FATAL ERROR: Greška pri čitanju taba. Detalji: {e}")
            return False

    def validate_gates(self):
        total_gates = len(self.df_gates)
        closed_gates = 0
        
        for index, row in self.df_gates.iterrows():
            gate_id = str(row.get('gate_id', 'UNKNOWN')).strip()
            gate_name = str(row.get('gate_name', 'UNKNOWN')).strip()
            
            # Izvlačenje odluka vlasnika i kriptografskih dokaza
            owner_decision = str(row.get('owner_decision', '')).strip().upper()
            source_hash = str(row.get('source_hash', '')).strip()
            
            # --- THE ZERO-TRUST FILTER ---
            # Da bi kapija bila zatvorena, vlasnik MORA odobriti I MORA postojati heš putanje
            hash_is_valid = source_hash not in ["nan", "None", ""]
            
            if owner_decision == "APPROVED" and hash_is_valid:
                status = "CLOSED"
                closed_gates += 1
            else:
                status = "BLOCKED"
                
            self.validation_log.append({
                "gate_id": gate_id,
                "gate_name": gate_name,
                "owner_decision": owner_decision,
                "source_hash_present": "YES" if hash_is_valid else "NO",
                "calculated_status": status
            })
            
        print(f"[*] Validacija završena. Zatvorenih kapija sa dokazima: {closed_gates}/{total_gates}")
        
        # Hard Gate Logika: SVIH 10 kapija moraju biti zatvorene za Lender Use i SSOT Lock
        if closed_gates == total_gates and total_gates > 0:
            self.system_status = "GREEN - LENDER READY"
            self.ssot_lock_allowed = "YES"
            self.lender_use_allowed = "YES"
        else:
            self.system_status = "RED - BLOCKED"
            self.ssot_lock_allowed = "NO"
            self.lender_use_allowed = "NO"

    def export_validation_report(self):
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        report_path = Path(OUTPUT_DIR) / f"titan_step98_validation_report_{self.timestamp}.json"
        
        report_data = {
            "System_Step": 98,
            "Mode": "LIVE_EVIDENCE_GATE_VALIDATOR",
            "Target_Source": SOURCE_FILE,
            "System_Status": self.system_status,
            "SSOT_Lock_Allowed": self.ssot_lock_allowed,
            "Lender_Use_Allowed": self.lender_use_allowed,
            "Gate_Details": self.validation_log
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)
            
        print(f"\n[+] TITAN STEP 98 VERDIKT:")
        print(f"    Canonical Status : {self.system_status}")
        print(f"    SSOT Lock        : {self.ssot_lock_allowed}")
        print(f"    Lender Use       : {self.lender_use_allowed}")
        print(f"[+] Forenzički log sačuvan: {report_path}")

if __name__ == "__main__":
    validator = EvidenceGateValidator()
    if validator.load_canonical_queue():
        validator.validate_gates()
        validator.export_validation_report()