#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 005"
echo " SSOT DISCOVERY — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_005_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=005"
echo "MODE=READ_ONLY_SSOT_DISCOVERY"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


echo "--- ROOT MANIFEST ---"

find "$ROOT" -maxdepth 6 \
\( \
-name "ROOT_MANIFEST*" -o \
-name "*SSOT*" -o \
-name "*CANONICAL*" -o \
-name "*AUTHORITY*" \
\) \
2>/dev/null | tee "$OUT/root_ssot_candidates.txt"


echo "--- SSOT FILE CONTENT PREVIEW ---"

while IFS= read -r FILE
do
echo "------------------------------------------------"
echo "FILE=$FILE"

case "$FILE" in
*.env|*.txt|*.json|*.csv)
head -50 "$FILE" 2>/dev/null || true
;;
esac

done < "$OUT/root_ssot_candidates.txt" \
| tee "$OUT/ssot_content_preview.txt"


echo "--- SSOT NAME INVENTORY ---"

find "$ROOT" -type f \
\( \
-iname "*SSOT*" -o \
-iname "*ROOT_MANIFEST*" -o \
-iname "*AUTHORITY*" -o \
-iname "*CANONICAL*" \
\) \
2>/dev/null \
| sort \
| tee "$OUT/ssot_inventory.txt"


echo "--- REGISTRY CONNECTIONS ---"

find "$ROOT" -type f \
\( \
-iname "*REGISTRY*" -o \
-iname "*MANIFEST*" \
\) \
2>/dev/null \
| sort \
| tee "$OUT/registry_manifest_links.txt"


echo "--- DUPLICATE SSOT SEARCH ---"

find /mnt/c \
-maxdepth 6 \
-type f \
\( \
-iname "*SSOT*" -o \
-iname "*ROOT_MANIFEST*" -o \
-iname "*CANONICAL_SSOT*" \
\) \
2>/dev/null \
| sort \
| tee "$OUT/global_ssot_candidates.txt"


echo "--- SSOT COUNT ---"

{
echo "LOCAL_SSOT_COUNT=$(grep -Ei 'SSOT|ROOT_MANIFEST|AUTHORITY|CANONICAL' "$OUT/ssot_inventory.txt" | wc -l)"
echo "GLOBAL_SSOT_COUNT=$(grep -Ei 'SSOT|ROOT_MANIFEST|CANONICAL' "$OUT/global_ssot_candidates.txt" | wc -l)"
} | tee "$OUT/ssot_count.txt"


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_006_SSOT_AUTHORITY_VALIDATION"
echo "============================================================"

