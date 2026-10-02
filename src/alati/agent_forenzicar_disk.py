# Forenzički skener za analizu Crvenog Diska (/mnt/d)
import os

RED_DISK = '/mnt/d'
TARGET_FOLDERS = [
    'AI_AGENT_PRODUCTION_GATE',
    'FREYA_HARVEST_888',
    'FREYA_HUMAN_GATE_SELECTED_COPY',
    'FREYA_LENOVO_NODE_888',
    'FREYA_MAC_RED_UNION_888',
    'FREYA_PORTABLE_FACTORY_888',
    'IPHONE_KRITICNA_KOPIJA_888_nu3ErN',
    'MAC_ZIP_020_BACKUP_20260919',
    'SORTED_RECOVERY_2026'
]

def analiziraj_disk():
    if not os.path.exists(RED_DISK):
        print("Crveni disk nije montiran na /mnt/d")
        return

    print("=== INVENTAR CRVENOG DISKA (/mnt/d) ===")
    total_py = 0
    total_sh = 0
    total_env_txt = 0

    for folder in TARGET_FOLDERS:
        path = os.path.join(RED_DISK, folder)
        if not os.path.exists(path):
            continue

        py_cnt, sh_cnt, doc_cnt = 0, 0, 0
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith('.py'): py_cnt += 1
                elif f.endswith('.sh'): sh_cnt += 1
                elif f.endswith(('.txt', '.env', '.json', '.md')): doc_cnt += 1

        total_py += py_cnt
        total_sh += sh_cnt
        total_env_txt += doc_cnt

        print(f"📁 [{folder}]")
        print(f"   ├─ Python skripte (.py): {py_cnt}")
        print(f"   ├─ Shell skripte (.sh):  {sh_cnt}")
        print(f"   └─ Dokazni ugovori/podešavanja: {doc_cnt}\n")

    print(f"UKUPNO PRONAĐENO NA DISKU: {total_py} .py | {total_sh} .sh | {total_env_txt} ugovora/dokumenata")

if __name__ == "__main__":
    analiziraj_disk()
