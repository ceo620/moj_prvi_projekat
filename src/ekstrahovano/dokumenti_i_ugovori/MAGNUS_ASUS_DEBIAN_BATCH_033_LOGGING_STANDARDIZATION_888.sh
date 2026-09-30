#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 033"
echo " LOGGING STANDARDIZATION AUDIT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_033_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=033"
echo "MODE=READ_ONLY_LOGGING_AUDIT"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type d \
\( \
-iname "*log*" -o \
-iname "*evidence*" -o \
-iname "*report*" -o \
-iname "*receipt*" \
\) \
2>/dev/null \
| sort \
> "$OUT/LOG_EVIDENCE_DIRECTORIES.txt"


find "$ROOT" \
-type f \
\( \
-iname "*.log" -o \
-iname "*.txt" -o \
-iname "*.env" -o \
-iname "*.csv" \
\) \
2>/dev/null \
| sort \
> "$OUT/LOG_LIKE_FILES.txt"


: > "$OUT/TIMESTAMP_SIGNALS.txt"
: > "$OUT/UTC_TIMESTAMP_SIGNALS.txt"
: > "$OUT/EVIDENCE_SIGNALS.txt"
: > "$OUT/LOG_SIGNALS.txt"


while IFS= read -r FILE
do

grep -Eo \
'[0-9]{8}T[0-9]{6}Z|[0-9]{4}-[0-9]{2}-[0-9]{2}|date|timestamp|UTC|utc' \
"$FILE" \
2>/dev/null \
>> "$OUT/TIMESTAMP_SIGNALS.txt" || true


grep -Ei \
'UTC|Z$|START_UTC|END_UTC|TIMESTAMP' \
"$FILE" \
2>/dev/null \
>> "$OUT/UTC_TIMESTAMP_SIGNALS.txt" || true


grep -Ei \
'EVIDENCE|MANIFEST|RECEIPT|PROOF|VALIDATION|HASH' \
"$FILE" \
2>/dev/null \
>> "$OUT/EVIDENCE_SIGNALS.txt" || true


grep -Ei \
'LOG|ERROR|WARNING|INFO|DEBUG|TRACE' \
"$FILE" \
2>/dev/null \
>> "$OUT/LOG_SIGNALS.txt" || true

done < "$OUT/LOG_LIKE_FILES.txt"


echo "--- SUMMARY ---"

{
echo "LOG_EVIDENCE_DIRECTORY_COUNT=$(wc -l < "$OUT/LOG_EVIDENCE_DIRECTORIES.txt")"
echo "LOG_LIKE_FILE_COUNT=$(wc -l < "$OUT/LOG_LIKE_FILES.txt")"
echo "TIMESTAMP_SIGNAL_COUNT=$(wc -l < "$OUT/TIMESTAMP_SIGNALS.txt")"
echo "UTC_TIMESTAMP_SIGNAL_COUNT=$(wc -l < "$OUT/UTC_TIMESTAMP_SIGNALS.txt")"
echo "EVIDENCE_SIGNAL_COUNT=$(wc -l < "$OUT/EVIDENCE_SIGNALS.txt")"
echo "LOG_SIGNAL_COUNT=$(wc -l < "$OUT/LOG_SIGNALS.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- LOG DIRECTORY SAMPLE ---"
head -30 "$OUT/LOG_EVIDENCE_DIRECTORIES.txt" || true

echo "--- UTC SAMPLE ---"
head -30 "$OUT/UTC_TIMESTAMP_SIGNALS.txt" || true

echo "--- EVIDENCE SAMPLE ---"
head -30 "$OUT/EVIDENCE_SIGNALS.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_034_UTC_TIMESTAMP_STANDARDIZATION"
echo "============================================================"

