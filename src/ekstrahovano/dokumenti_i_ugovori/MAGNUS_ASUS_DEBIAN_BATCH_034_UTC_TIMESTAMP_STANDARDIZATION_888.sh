#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 034"
echo " UTC TIMESTAMP AUDIT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_034_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=034"
echo "MODE=READ_ONLY_UTC_TIMESTAMP_AUDIT"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
\( \
-name "*.sh" -o \
-name "*.env" -o \
-name "*.txt" -o \
-name "*.csv" -o \
-name "*.json" \
\) \
2>/dev/null \
| sort \
> "$OUT/TIMESTAMP_SCAN_FILES.txt"


: > "$OUT/UTC_Z_TIMESTAMP.txt"
: > "$OUT/LOCAL_DATE_TIMESTAMP.txt"
: > "$OUT/GENERIC_TIMESTAMP.txt"
: > "$OUT/TIMESTAMP_VARIANCE.txt"


while IFS= read -r FILE
do

grep -E \
'[0-9]{8}T[0-9]{6}Z|[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z' \
"$FILE" \
2>/dev/null \
>> "$OUT/UTC_Z_TIMESTAMP.txt" || true


grep -E \
'[0-9]{4}-[0-9]{2}-[0-9]{2}(_| )[0-9]{6}|[0-9]{8}_[0-9]{6}' \
"$FILE" \
2>/dev/null \
>> "$OUT/LOCAL_DATE_TIMESTAMP.txt" || true


grep -Ei \
'timestamp|time|date|utc|created|modified|last_write|start|end' \
"$FILE" \
2>/dev/null \
>> "$OUT/GENERIC_TIMESTAMP.txt" || true


done < "$OUT/TIMESTAMP_SCAN_FILES.txt"


cat "$OUT/UTC_Z_TIMESTAMP.txt" \
"$OUT/LOCAL_DATE_TIMESTAMP.txt" \
"$OUT/GENERIC_TIMESTAMP.txt" \
2>/dev/null \
| sort -u \
> "$OUT/TIMESTAMP_VARIANCE.txt"


echo "--- SUMMARY ---"

{
echo "SCANNED_FILE_COUNT=$(wc -l < "$OUT/TIMESTAMP_SCAN_FILES.txt")"
echo "UTC_Z_TIMESTAMP_COUNT=$(wc -l < "$OUT/UTC_Z_TIMESTAMP.txt")"
echo "LOCAL_TIMESTAMP_COUNT=$(wc -l < "$OUT/LOCAL_DATE_TIMESTAMP.txt")"
echo "GENERIC_TIMESTAMP_COUNT=$(wc -l < "$OUT/GENERIC_TIMESTAMP.txt")"
echo "TIMESTAMP_VARIANCE_COUNT=$(wc -l < "$OUT/TIMESTAMP_VARIANCE.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- UTC SAMPLE ---"
head -30 "$OUT/UTC_Z_TIMESTAMP.txt" || true

echo "--- LOCAL SAMPLE ---"
head -30 "$OUT/LOCAL_DATE_TIMESTAMP.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_035_EVIDENCE_STRUCTURE_REPAIR"
echo "============================================================"

