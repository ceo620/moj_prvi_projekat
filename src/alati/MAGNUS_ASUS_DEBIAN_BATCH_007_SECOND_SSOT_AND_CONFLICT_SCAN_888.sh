#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 007"
echo " SECOND SSOT AND CONFLICT SCAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_007_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=007"
echo "MODE=READ_ONLY_CONFLICT_SCAN"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


echo "=== ACTIVE SSOT CANDIDATES ==="

find "$ROOT" \
-maxdepth 7 \
-type f \
\( \
-name "*SSOT*" -o \
-name "*AUTHORITY*" -o \
-name "*ROOT_MANIFEST*" -o \
-name "*CANONICAL*" \
\) \
2>/dev/null \
| grep -vE "/BACKUP/|/RECOVERY/|/ARCHIVE/|/QUARANTINE/" \
| tee "$OUT/active_ssot_candidates.txt"


echo "=== BACKUP SSOT CANDIDATES ==="

find "$ROOT" \
-type f \
\( \
-name "*SSOT*" -o \
-name "*AUTHORITY*" -o \
-name "*ROOT_MANIFEST*" -o \
-name "*CANONICAL*" \
\) \
2>/dev/null \
| grep -Ei "/BACKUP/|/RECOVERY/|/ARCHIVE/|/QUARANTINE/" \
| tee "$OUT/backup_ssot_candidates.txt"


echo "=== GLOBAL SSOT SEARCH ==="

find /mnt/c \
-maxdepth 6 \
-type f \
\( \
-name "*SSOT*" -o \
-name "*ROOT_MANIFEST*" -o \
-name "*CANONICAL_SSOT*" -o \
-name "*SSOT_CURRENT*" \
\) \
2>/dev/null \
| tee "$OUT/global_ssot_candidates.txt"


echo "=== ROOT AUTHORITY SIGNALS ==="

grep -RHi \
-E "PRIMARY|ACTIVE|CURRENT|AUTHORITATIVE|CANONICAL|SOVEREIGN|SSOT" \
"$ROOT/00_CONTROL" \
"$ROOT/05_RUNTIME_UNION" \
"$ROOT/09_EVIDENCE" \
2>/dev/null \
| head -300 \
| tee "$OUT/root_authority_signals.txt" || true


echo "=== DUPLICATE AUTHORITY NAMES ==="

find "$ROOT" \
-type f \
\( \
-name "*AUTHORITY*" -o \
-name "*SSOT_CURRENT*" -o \
-name "ROOT_MANIFEST*" \
\) \
2>/dev/null \
| sed 's#.*/##' \
| sort \
| uniq -c \
| sort -nr \
| tee "$OUT/duplicate_authority_names.txt"


echo "=== ROLE CLASSIFICATION ==="

{
echo "RUNTIME_SSOT="
grep -Ei "RUNTIME|BINDING|SSOT.binding" "$OUT/active_ssot_candidates.txt" || true

echo "PLATFORM_SSOT="
grep -Ei "PLATFORM|05_SSOT|SSOT_CURRENT" "$OUT/global_ssot_candidates.txt" || true

echo "DOCUMENT_FACTORY_SSOT="
grep -Ei "DOCUMENT_FACTORY|FACTORY_SSOT" "$OUT/global_ssot_candidates.txt" || true

} | tee "$OUT/ssot_role_classification.txt"


echo "=== CONFLICT CHECK ==="

ACTIVE_COUNT=$(wc -l < "$OUT/active_ssot_candidates.txt" || echo 0)
GLOBAL_COUNT=$(wc -l < "$OUT/global_ssot_candidates.txt" || echo 0)

echo "ACTIVE_SSOT_SIGNAL_COUNT=$ACTIVE_COUNT"
echo "GLOBAL_SSOT_SIGNAL_COUNT=$GLOBAL_COUNT"


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_008_FULL_SCRIPT_INVENTORY"
echo "============================================================"

