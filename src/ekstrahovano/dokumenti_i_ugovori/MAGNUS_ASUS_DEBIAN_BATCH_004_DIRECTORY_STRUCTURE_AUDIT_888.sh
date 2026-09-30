#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 004"
echo " DIRECTORY STRUCTURE AUDIT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_004_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=004"
echo "MODE=READ_ONLY_DIRECTORY_AUDIT"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

echo "--- ROOT CHECK ---"

if [ -d "$ROOT" ]; then
echo "ROOT_STATUS=EXISTS"
else
echo "ROOT_STATUS=MISSING"
echo "RESULT=HOLD"
exit 0
fi

echo "--- TOP LEVEL STRUCTURE ---"

find "$ROOT" -maxdepth 1 -mindepth 1 -printf "%f\n" \
| sort | tee "$OUT/top_level_structure.txt"


echo "--- DIRECTORY COUNT ---"

find "$ROOT" -type d 2>/dev/null | wc -l \
| tee "$OUT/directory_count.txt"


echo "--- FILE COUNT ---"

find "$ROOT" -type f 2>/dev/null | wc -l \
| tee "$OUT/file_count.txt"


echo "--- CORE AREAS ---"

for D in \
00_CONTROL \
01_DOCTRINE \
02_REGISTRY \
03_AGENTS_ACTIVE \
05_RUNTIME_UNION \
06_ASUS_INGEST \
07_DOCUMENT_FACTORY \
08_PACKET_FACTORY \
09_EVIDENCE \
11_BACKUP \
12_LOGS \
13_TESTS \
14_CONFIG \
15_STATE \
16_HEALTH \
17_RECOVERY
do

if [ -d "$ROOT/$D" ]; then
echo "$D=PASS"
else
echo "$D=MISSING"
fi

done | tee "$OUT/core_structure_check.txt"


echo "--- SSOT DISCOVERY ---"

find "$ROOT" -maxdepth 5 \
\( -iname "*SSOT*" -o -iname "*ROOT_MANIFEST*" -o -iname "*CANONICAL*" \) \
2>/dev/null | tee "$OUT/ssot_structure.txt"


echo "--- AGENT STRUCTURE ---"

find "$ROOT" -maxdepth 5 \
\( -iname "*AGENT*" -o -iname "*REGISTRY*" \) \
2>/dev/null | tee "$OUT/agent_structure.txt"


echo "--- DOCUMENT FACTORY STRUCTURE ---"

find "$ROOT" -maxdepth 5 \
\( -iname "*DOCUMENT*" -o -iname "*FACTORY*" \) \
2>/dev/null | tee "$OUT/document_factory_structure.txt"


echo "--- EVIDENCE STRUCTURE ---"

find "$ROOT" -maxdepth 4 \
-iname "*EVIDENCE*" \
2>/dev/null | tee "$OUT/evidence_structure.txt"


echo "--- BACKUP RECOVERY STRUCTURE ---"

find "$ROOT" -maxdepth 5 \
\( -iname "*BACKUP*" -o -iname "*ROLLBACK*" -o -iname "*RECOVERY*" \) \
2>/dev/null | tee "$OUT/recovery_structure.txt"


echo "--- LARGE DIRECTORIES ---"

du -xh "$ROOT" 2>/dev/null \
| sort -h \
| tail -30 \
| tee "$OUT/large_directories.txt"


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_005_SSOT_DISCOVERY"
echo "============================================================"

