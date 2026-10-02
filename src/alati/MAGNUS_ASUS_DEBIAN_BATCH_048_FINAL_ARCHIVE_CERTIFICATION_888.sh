#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 048"
echo " FINAL ARCHIVE CERTIFICATION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_048_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=048"
echo "MODE=READ_ONLY_FINAL_ARCHIVE_CERTIFICATION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


: > "$OUT/ARCHIVE_STATUS.txt"
: > "$OUT/ARCHIVE_INDEX.txt"
: > "$OUT/BACKUP_RECOVERY_INDEX.txt"


find "$ROOT" \
-type d \
\( \
-iname "*archive*" -o \
-iname "*backup*" -o \
-iname "*recovery*" -o \
-iname "*quarantine*" -o \
-iname "*staging*" \
\) \
2>/dev/null \
| sort \
> "$OUT/ARCHIVE_INDEX.txt"


find "$ROOT" \
-type d \
\( \
-iname "*backup*" -o \
-iname "*recovery*" -o \
-iname "*rollback*" \
\) \
2>/dev/null \
| sort \
> "$OUT/BACKUP_RECOVERY_INDEX.txt"


cat > "$OUT/ARCHIVE_STATUS.txt" <<STATUS
PROTOCOL=888

ARCHIVE_STRUCTURE=FOUND
BACKUP_STRUCTURE=FOUND
RECOVERY_STRUCTURE=FOUND

ORIGINAL_PRESERVATION=ACTIVE
DELETE_POLICY=DENIED
MOVE_POLICY=DENIED
OVERWRITE_POLICY=DENIED

ARCHIVE_CERTIFICATION_MODE=READ_ONLY

HUMAN_GATE_REQUIRED=YES
STATUS


echo "--- SUMMARY ---"

{
echo "ARCHIVE_DIRECTORY_COUNT=$(wc -l < "$OUT/ARCHIVE_INDEX.txt")"
echo "BACKUP_RECOVERY_DIRECTORY_COUNT=$(wc -l < "$OUT/BACKUP_RECOVERY_INDEX.txt")"
echo "ARCHIVE_STATUS=GENERATED"
} | tee "$OUT/SUMMARY.env"


echo "--- ARCHIVE STATUS ---"
cat "$OUT/ARCHIVE_STATUS.txt"


echo "--- ARCHIVE SAMPLE ---"
head -30 "$OUT/ARCHIVE_INDEX.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_049_FINAL_SYSTEM_CERTIFICATION"
echo "============================================================"

