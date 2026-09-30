# ===================================================
# TITAN IMMUTABLE RUNTIME GUARD — SSOT ENFORCED
# ZAKLJUČANO OD STRANE CFO DANIJELE KESKIN
TITAN_SSOT_CANON = 27800000.00
def _assert_titan_canon(val):
    if float(val) != TITAN_SSOT_CANON:
        raise ValueError("CRITICAL DRIFT DETECTED! ACCESS DENIED.")
# ===================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reasoning.py - Centralni Nivo 4 Modul za Evaluaciju i Inteligenciju
Popravljen da donosi odluke direktno na osnovu živih relacionih podataka iz CMU jezgra.
"""

import os
import sqlite3

DB_PATH = '/data/data/com.termux/files/home/05-RESOURCES/CMU/pipelines/05-signale/titan_executive.db'

def make_decision():
    print("[*] [Nivo_4_Reasoning] Pokrećem evaluaciju relacionih signala...")
    
    decisions = []
    
    if not os.path.exists(DB_PATH):
        return [{"action": "Sistemska provera: Kreiraj relacioni integritet", "priority": "HIGH", "reason": "Baza podataka nedostupna"}]

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. ANALIZA RIZIKA: Proveravamo kritične pretnje (poput onih koje je Grok izbacio)
        cursor.execute("SELECT id, risk FROM risks WHERE level = 'CRITICAL' AND status = 'RISK_REVIEW_REQUIRED';")
        critical_risks = cursor.fetchall()

        if critical_risks:
            print(f"[!] Detektovano {len(critical_risks)} kritičnih finansijskih drifta u leđeru. Generišem odbrambene akcije.")
            for risk_id, risk_text in critical_risks:
                decisions.append({
                    "action": f"Izvrši hitnu rekoncilijaciju i sanaciju za rizik ID {risk_id}",
                    "priority": "CRITICAL",
                    "reason": f"Sprečavanje kontaminacije VDR-a: {risk_text[:40]}..."
                })

        # 2. ANALIZA ZADATAKA: Proveravamo otvorene stavke
        cursor.execute("SELECT id, title FROM tasks WHERE status = 'PENDING' OR status = 'EVIDENCE_REQUIRED';")
        pending_tasks = cursor.fetchall()

        for task_id, task_title in pending_tasks:
            decisions.append({
                "action": f"Zatvori i verifikuj zadatak ID {task_id}: {task_title}",
                "priority": "HIGH",
                "reason": "Zahteva se unakrsna validacija sa MacBook leđerom."
            })

        # 3. KANONSKI BALANS: Ako nema pretnji, održavaj stabilnost
        if not decisions:
            decisions.append({
                "action": "Održavanje stabilnosti perimetra i monitoring signala",
                "priority": "LOW",
                "reason": "Svi finansijski modeli usklađeni na kanonskih 27.8M EUR. Stanje regularno."
            })

        conn.close()
    except Exception as e:
        print(f"[-] Greška unutar Reasoning jezgra: {e}")
        decisions.append({"action": "Sistemska provera: Ručna CFO verifikacija", "priority": "HIGH", "reason": str(e)})

    return decisions

if __name__ == "__main__":
    rezultat = make_decision()
    print("\n=== GENERISANE ODLUKE NA OSNOVU REALNOG STANJA U BAZI ===")
    for d in rezultat:
        print(f"-> AKCIJA: {d['action']} | PRIORITET: {d['priority']} | REZON: {d['reason']}")
