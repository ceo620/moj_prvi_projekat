#!/usr/bin/env python3
import datetime, os, glob

VAULT_PATH = "/data/data/com.termux/files/home/Citadel"

def scan_markdown_checkboxes(file_path):
    if not os.path.exists(file_path):
        return {"total": 0, "done": 0, "progress": 0}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    total = content.count('- [ ]') + content.count('- [x]')
    done = content.count('- [x]')
    progress = round((done / total * 100), 1) if total > 0 else 0
    return {"total": total, "done": done, "progress": progress}

def perception_scan():
    t = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{t}] 👁️ CMU PERCEPTION — Nivo 2 AKTIVIRAN")

    # === NAJDUBLJI DIAMOND HARVEST — PROTOKOL 888 ===
    DEEPEST_DIAMOND_PATH = "/data/data/com.termux/files/home/Citadel/05-RESOURCES/CMU/Doctrine/Diamond_Harvest/TITAN_GRID_DOCUMENTS_DEEPEST"
    files_to_scan = [DEEPEST_DIAMOND_PATH]
    print(f"[{t}] 👁️ Perception: NAJDUBLJI HARVEST — dodato {len(glob.glob(DEEPEST_DIAMOND_PATH + '/*.docx'))} skrivenih dijamanta (adapteri, kerneli, algoritmi, neuromape)")

    key_files = {
        "packing": f"{VAULT_PATH}/04-LOGISTICS/Packing-List.md",
        "medical": f"{VAULT_PATH}/01-MEDICAL/MEDICAL-CMU-SUMMARY-ANKARA-2026.md",
        "daily": f"{VAULT_PATH}/03-DAILY/DAILY-TODO-ANKARA.md",
        "strategic": f"{VAULT_PATH}/02-STRATEGIC/TITAN-STRATEGIC-MASTER-ANKARA-2026.md",
        "home": f"{VAULT_PATH}/Titan-Home.md"
    }

    report = {"timestamp": datetime.datetime.now().isoformat(), "files": {}}

    for name, path in key_files.items():
        report["files"][name] = scan_markdown_checkboxes(path)

    # Guardian integracija
    packing_progress = report["files"]["packing"]["progress"]
    if packing_progress < 100:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Guardian upozorenje: Packing List samo {packing_progress}%")

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 👁️ Perception scan završen — {len(report['files'])} fajlova analizirano")
    return report

if __name__ == "__main__":
    perception_scan()

    # === FULL HARMONISATION UPGRADE — PROTOKOL 888 ===
    # Trajno skeniranje master harvest dokumenta i svih dijamanta
    MASTER_HARVEST = "/data/data/com.termux/files/home/Citadel/02_CORE_DOCTRINE/TITAN_CORE_HARVEST_v2.0.md"
    if os.path.exists(MASTER_HARVEST):
        report["files"]["master_harvest"] = scan_markdown_checkboxes(MASTER_HARVEST)
        print(f"[{t}] 👁️ Perception: Upitan TITAN CORE HARVEST v2.0 (full harmonisation)")

    # Priprema za 2 dodatna diska (kasnije ćeš dodati putanje)
    print(f"[{t}] 👁️ Perception: Spreman za 2 dodatna diska — čeka tvoju naredbu")

