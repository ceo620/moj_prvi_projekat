#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 003"
echo " EXISTING FACTORY DISCOVERY — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_003_$START_UTC"

mkdir -p "$OUT"

cat > "$OUT/BATCH.env" <<EOT
PROTOCOL=888
MACHINE=ASUS
NODE=FREYA_ASUS_DEBIAN_888
BATCH=003
MODE=READ_ONLY_FACTORY_DISCOVERY
START_UTC=$START_UTC
EOT

CANDIDATES=(
"/mnt/c/FREYA_ASUS_NODE_888"
"/mnt/c/FREYA_PLATFORM_2_0"
"/mnt/c/FREYA_ASUS_LIVE_DOCUMENT_FACTORY_888"
)

echo "=== FACTORY CANDIDATE DISCOVERY ===" | tee "$OUT/factory_discovery.txt"

for ROOT in "${CANDIDATES[@]}"; do

echo "------------------------------------------------" | tee -a "$OUT/factory_discovery.txt"
echo "ROOT=$ROOT" | tee -a "$OUT/factory_discovery.txt"

if [ -d "$ROOT" ]; then

echo "STATUS=EXISTS" | tee -a "$OUT/factory_discovery.txt"

echo "--- SIZE ---" | tee -a "$OUT/factory_discovery.txt"
du -sh "$ROOT" 2>/dev/null | tee -a "$OUT/factory_discovery.txt"

echo "--- TIMESTAMP ---" | tee -a "$OUT/factory_discovery.txt"
stat "$ROOT" 2>/dev/null | grep -E "Modify|Birth|Access" | tee -a "$OUT/factory_discovery.txt"

echo "--- IMPORTANT FILES ---" | tee -a "$OUT/factory_discovery.txt"

find "$ROOT" -maxdepth 4 \
\( \
-name "FINAL*SEAL*" -o \
-name "*ROOT_MANIFEST*" -o \
-name "*SSOT*" -o \
-name "*MANIFEST*" -o \
-name "*REGISTRY*" -o \
-name "*FACTORY*" -o \
-name "*RUNTIME*" -o \
-name "*BACKUP*" -o \
-name "*ROLLBACK*" -o \
-name "*EVIDENCE*" \
\) 2>/dev/null | head -100 | tee -a "$OUT/factory_discovery.txt"

echo "--- TOP LEVEL ---" | tee -a "$OUT/factory_discovery.txt"
find "$ROOT" -maxdepth 1 -mindepth 1 -printf "%f\n" 2>/dev/null | tee -a "$OUT/factory_discovery.txt"

else

echo "STATUS=NOT_FOUND" | tee -a "$OUT/factory_discovery.txt"

fi

done

echo "=== SSOT SEARCH ==="

find /mnt/c \
-maxdepth 5 \
\( \
-name "*SSOT*" -o \
-name "*ROOT_MANIFEST*" -o \
-name "*CANONICAL*" \
\) 2>/dev/null | tee "$OUT/SSOT_DISCOVERY.txt"

echo "=== AGENT SEARCH ==="

find /mnt/c \
-maxdepth 5 \
\( \
-name "*AGENT*" -o \
-name "*REGISTRY*" \
\) 2>/dev/null | tee "$OUT/AGENT_DISCOVERY.txt"

echo "=== DOCUMENT FACTORY SEARCH ==="

find /mnt/c \
-maxdepth 5 \
\( \
-name "*DOCUMENT*" -o \
-name "*FACTORY*" \
\) 2>/dev/null | tee "$OUT/DOCUMENT_FACTORY_DISCOVERY.txt"

echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_004_DIRECTORY_STRUCTURE_AUDIT"
echo "============================================================"

