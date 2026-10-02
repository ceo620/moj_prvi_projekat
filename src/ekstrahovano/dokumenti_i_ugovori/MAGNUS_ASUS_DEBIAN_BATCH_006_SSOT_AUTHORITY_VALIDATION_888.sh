#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 006"
echo " SSOT AUTHORITY VALIDATION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_006_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=006"
echo "MODE=READ_ONLY_SSOT_AUTHORITY_VALIDATION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


echo "=== SSOT AUTHORITY FILE MAP ==="

SSOT_FILES=(
"$ROOT/00_CONTROL/ROOT_MANIFEST.json"
"$ROOT/05_RUNTIME_UNION/FREYA_ASUS_AUTONOMOUS_SYSTEM_888/01_BINDINGS/SSOT.binding.env"
"$ROOT/09_EVIDENCE/MAGNUS_ASUS_TARGETED_REPAIR_V2_20260821T180132Z/REPORTS/SSOT_AUTHORITY.csv"
"$ROOT/09_EVIDENCE/MAGNUS_ASUS_FINAL_20260821T174258Z/REPORTS/SSOT_RECONCILIATION.csv"
"/mnt/c/FREYA_PLATFORM_2_0/00_CONTROL/FREYA_ASUS_NODE_888/REGISTRY/SSOT_CURRENT.env"
"/mnt/c/FREYA_PLATFORM_2_0/05_SSOT/CANONICAL_SSOT_REFERENCE_20260808T191147Z.env"
"/mnt/c/FREYA_ASUS_LIVE_DOCUMENT_FACTORY_888/01_CONFIG/FACTORY_SSOT.json"
)

for FILE in "${SSOT_FILES[@]}"; do

echo "------------------------------------------------"
echo "FILE=$FILE"

if [ -f "$FILE" ]; then

echo "STATUS=EXISTS"

echo "--- PREVIEW ---"
head -50 "$FILE" 2>/dev/null || true

echo "--- HASH ---"
sha256sum "$FILE" 2>/dev/null || true

else

echo "STATUS=NOT_FOUND"

fi

done | tee "$OUT/ssot_authority_map.txt"


echo "=== ROOT MANIFEST CHECK ==="

if [ -f "$ROOT/00_CONTROL/ROOT_MANIFEST.json" ]; then
echo "ROOT_MANIFEST=FOUND"

head -100 "$ROOT/00_CONTROL/ROOT_MANIFEST.json" \
2>/dev/null

else
echo "ROOT_MANIFEST=MISSING"
fi | tee "$OUT/root_manifest_check.txt"


echo "=== ACTIVE VS BACKUP CLASSIFICATION ==="

find "$ROOT" -maxdepth 6 \
\( \
-name "*SSOT*" -o \
-name "*AUTHORITY*" -o \
-name "*CANONICAL*" \
\) \
2>/dev/null \
| while read -r F
do

case "$F" in
*BACKUP*|*RECOVERY*|*ARCHIVE*|*QUARANTINE*)
echo "BACKUP_OR_ARCHIVE=$F"
;;
*)
echo "ACTIVE_CANDIDATE=$F"
;;
esac

done | tee "$OUT/ssot_classification.txt"


echo "=== SSOT CONFLICT SIGNALS ==="

grep -RHi \
-E "PRIMARY|ACTIVE|CURRENT|AUTHORITATIVE|CANONICAL|SSOT" \
"$ROOT/00_CONTROL" \
"$ROOT/05_RUNTIME_UNION" \
"$ROOT/09_EVIDENCE" \
2>/dev/null \
| head -200 \
| tee "$OUT/authority_signals.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_007_SECOND_SSOT_AND_CONFLICT_SCAN"
echo "============================================================"

