#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 007R2"
echo " BACKUP SSOT CLASSIFICATION FIX — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_007R2_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=007R2"
echo "MODE=READ_ONLY_SSOT_CLASSIFICATION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


python3 <<PY
import os

root = "$ROOT"
out = "$OUT"

keywords = (
    "SSOT",
    "AUTHORITY",
    "ROOT_MANIFEST",
    "CANONICAL"
)

ignore_ext = (
    ".pyc",
)

active=[]
backup=[]
archive=[]
recovery=[]
quarantine=[]

for base, dirs, files in os.walk(root):
    for f in files:
        if f.lower().endswith(ignore_ext):
            continue

        path=os.path.join(base,f)

        upper=path.upper()

        if not any(k in upper for k in keywords):
            continue

        if "/BACKUP/" in upper or "\\BACKUP\\" in upper:
            backup.append(path)
        elif "/RECOVERY/" in upper or "\\RECOVERY\\" in upper:
            recovery.append(path)
        elif "/ARCHIVE/" in upper or "\\ARCHIVE\\" in upper:
            archive.append(path)
        elif "/QUARANTINE/" in upper or "\\QUARANTINE\\" in upper:
            quarantine.append(path)
        else:
            active.append(path)

def write(name,data):
    with open(os.path.join(out,name),"w",encoding="utf-8") as f:
        for x in sorted(data):
            f.write(x+"\n")

write("ACTIVE_SSOT.txt",active)
write("BACKUP_SSOT.txt",backup)
write("ARCHIVE_SSOT.txt",archive)
write("RECOVERY_SSOT.txt",recovery)
write("QUARANTINE_SSOT.txt",quarantine)

with open(os.path.join(out,"SUMMARY.env"),"w") as f:
    f.write(f"ACTIVE_SSOT_COUNT={len(active)}\n")
    f.write(f"BACKUP_SSOT_COUNT={len(backup)}\n")
    f.write(f"ARCHIVE_SSOT_COUNT={len(archive)}\n")
    f.write(f"RECOVERY_SSOT_COUNT={len(recovery)}\n")
    f.write(f"QUARANTINE_SSOT_COUNT={len(quarantine)}\n")

PY


echo "--- SUMMARY ---"
cat "$OUT/SUMMARY.env"

echo "--- ACTIVE SAMPLE ---"
head -20 "$OUT/ACTIVE_SSOT.txt" || true

echo "--- BACKUP SAMPLE ---"
head -20 "$OUT/BACKUP_SSOT.txt" || true

echo "--- ARCHIVE SAMPLE ---"
head -20 "$OUT/ARCHIVE_SSOT.txt" || true

echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_008_FULL_SCRIPT_INVENTORY"
echo "============================================================"

