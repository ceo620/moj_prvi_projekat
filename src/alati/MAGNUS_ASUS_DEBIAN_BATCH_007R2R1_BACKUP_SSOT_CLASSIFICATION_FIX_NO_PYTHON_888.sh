#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 007R2R1"
echo " BACKUP SSOT CLASSIFICATION FIX NO PYTHON — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_007R2R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=007R2R1"
echo "MODE=READ_ONLY_SSOT_CLASSIFICATION_NO_PYTHON"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


echo "--- SCANNING SSOT SIGNALS ---"

find "$ROOT" \
-type f \
\( \
-name "*SSOT*" -o \
-name "*AUTHORITY*" -o \
-name "*ROOT_MANIFEST*" -o \
-name "*CANONICAL*" \
\) \
2>/dev/null \
> "$OUT/all_ssot_signals.txt"


: > "$OUT/ACTIVE_SSOT.txt"
: > "$OUT/BACKUP_SSOT.txt"
: > "$OUT/ARCHIVE_SSOT.txt"
: > "$OUT/RECOVERY_SSOT.txt"
: > "$OUT/QUARANTINE_SSOT.txt"


while IFS= read -r FILE
do

UPPER="$(echo "$FILE" | tr '[:lower:]' '[:upper:]')"

case "$UPPER" in

*"/BACKUP/"*)
echo "$FILE" >> "$OUT/BACKUP_SSOT.txt"
;;

*"/RECOVERY/"*)
echo "$FILE" >> "$OUT/RECOVERY_SSOT.txt"
;;

*"/ARCHIVE/"*)
echo "$FILE" >> "$OUT/ARCHIVE_SSOT.txt"
;;

*"/QUARANTINE/"*)
echo "$FILE" >> "$OUT/QUARANTINE_SSOT.txt"
;;

*)
echo "$FILE" >> "$OUT/ACTIVE_SSOT.txt"
;;

esac

done < "$OUT/all_ssot_signals.txt"


echo "--- SUMMARY ---"

{
echo "ACTIVE_SSOT_COUNT=$(wc -l < "$OUT/ACTIVE_SSOT.txt")"
echo "BACKUP_SSOT_COUNT=$(wc -l < "$OUT/BACKUP_SSOT.txt")"
echo "ARCHIVE_SSOT_COUNT=$(wc -l < "$OUT/ARCHIVE_SSOT.txt")"
echo "RECOVERY_SSOT_COUNT=$(wc -l < "$OUT/RECOVERY_SSOT.txt")"
echo "QUARANTINE_SSOT_COUNT=$(wc -l < "$OUT/QUARANTINE_SSOT.txt")"
} | tee "$OUT/SUMMARY.env"


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

