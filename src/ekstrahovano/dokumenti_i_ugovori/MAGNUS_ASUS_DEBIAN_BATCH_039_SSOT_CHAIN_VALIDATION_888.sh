#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 039"
echo " SSOT CHAIN VALIDATION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_039_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=039"
echo "MODE=READ_ONLY_SSOT_CHAIN_VALIDATION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
\( \
-iname "*SSOT*" -o \
-iname "*AUTHORITY*" -o \
-iname "*CANONICAL*" -o \
-iname "*ROOT_MANIFEST*" -o \
-iname "*REGISTER*" -o \
-iname "*.json" -o \
-iname "*.csv" -o \
-iname "*.tsv" -o \
-iname "*.env" \
\) \
2>/dev/null \
| sort \
> "$OUT/SSOT_FILES.txt"


: > "$OUT/SSOT_SIGNALS.txt"
: > "$OUT/AUTHORITY_SIGNALS.txt"
: > "$OUT/CANONICAL_SIGNALS.txt"
: > "$OUT/SECOND_SSOT_CANDIDATES.txt"
: > "$OUT/CONFLICT_SIGNALS.txt"


while IFS= read -r FILE
do

grep -Ei \
'SSOT|SOVEREIGN|SINGLE_SOURCE|SOURCE_OF_TRUTH' \
"$FILE" \
2>/dev/null \
>> "$OUT/SSOT_SIGNALS.txt" || true


grep -Ei \
'AUTHORITY|OWNER|PRIMARY|MASTER|CONTROL' \
"$FILE" \
2>/dev/null \
>> "$OUT/AUTHORITY_SIGNALS.txt" || true


grep -Ei \
'CANONICAL|ROOT|REGISTER|CURRENT|ACTIVE' \
"$FILE" \
2>/dev/null \
>> "$OUT/CANONICAL_SIGNALS.txt" || true


grep -Ei \
'SECOND_SSOT|PARALLEL_SSOT|DUPLICATE_SSOT|MULTIPLE_SSOT' \
"$FILE" \
2>/dev/null \
>> "$OUT/SECOND_SSOT_CANDIDATES.txt" || true


grep -Ei \
'CONFLICT|COLLISION|DUPLICATE|AMBIGUOUS|UNRESOLVED' \
"$FILE" \
2>/dev/null \
>> "$OUT/CONFLICT_SIGNALS.txt" || true


done < "$OUT/SSOT_FILES.txt"


echo "--- SUMMARY ---"

{
echo "SSOT_FILE_COUNT=$(wc -l < "$OUT/SSOT_FILES.txt")"
echo "SSOT_SIGNAL_COUNT=$(wc -l < "$OUT/SSOT_SIGNALS.txt")"
echo "AUTHORITY_SIGNAL_COUNT=$(wc -l < "$OUT/AUTHORITY_SIGNALS.txt")"
echo "CANONICAL_SIGNAL_COUNT=$(wc -l < "$OUT/CANONICAL_SIGNALS.txt")"
echo "SECOND_SSOT_CANDIDATE_COUNT=$(wc -l < "$OUT/SECOND_SSOT_CANDIDATES.txt")"
echo "CONFLICT_SIGNAL_COUNT=$(wc -l < "$OUT/CONFLICT_SIGNALS.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- SECOND SSOT SAMPLE ---"
head -30 "$OUT/SECOND_SSOT_CANDIDATES.txt" || true

echo "--- CONFLICT SAMPLE ---"
head -30 "$OUT/CONFLICT_SIGNALS.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_040_AUTHORITY_RESOLUTION_AUDIT"
echo "============================================================"

