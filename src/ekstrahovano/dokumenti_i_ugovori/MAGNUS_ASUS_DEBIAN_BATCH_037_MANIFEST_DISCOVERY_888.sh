#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 037"
echo " MANIFEST DISCOVERY — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_037_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=037"
echo "MODE=READ_ONLY_MANIFEST_DISCOVERY"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
\( \
-iname "*manifest*" -o \
-iname "*root*" -o \
-iname "*package*" -o \
-iname "*source*" -o \
-iname "*.sha256" -o \
-iname "*.json" -o \
-iname "*.csv" -o \
-iname "*.tsv" \
\) \
2>/dev/null \
| sort \
> "$OUT/MANIFEST_FILES.txt"


: > "$OUT/ROOT_MANIFEST_SIGNALS.txt"
: > "$OUT/PACKAGE_MANIFEST_SIGNALS.txt"
: > "$OUT/SOURCE_MANIFEST_SIGNALS.txt"
: > "$OUT/SSOT_MANIFEST_SIGNALS.txt"
: > "$OUT/MANIFEST_HASH_LINKS.txt"


while IFS= read -r FILE
do

grep -Ei \
'ROOT_MANIFEST|ROOT.*MANIFEST|CANONICAL_ROOT|SSOT_ROOT' \
"$FILE" \
2>/dev/null \
>> "$OUT/ROOT_MANIFEST_SIGNALS.txt" || true


grep -Ei \
'PACKAGE_MANIFEST|PACKAGE|BUILD_MANIFEST|RELEASE_MANIFEST' \
"$FILE" \
2>/dev/null \
>> "$OUT/PACKAGE_MANIFEST_SIGNALS.txt" || true


grep -Ei \
'SOURCE_MANIFEST|SOURCE_COPY|SOURCE_CATALOG|SOURCE_VERIFICATION' \
"$FILE" \
2>/dev/null \
>> "$OUT/SOURCE_MANIFEST_SIGNALS.txt" || true


grep -Ei \
'SSOT|CANONICAL|AUTHORITY|REGISTER' \
"$FILE" \
2>/dev/null \
>> "$OUT/SSOT_MANIFEST_SIGNALS.txt" || true


grep -Ei \
'SHA256|HASH|CHECKSUM|DIGEST|MANIFEST' \
"$FILE" \
2>/dev/null \
>> "$OUT/MANIFEST_HASH_LINKS.txt" || true


done < "$OUT/MANIFEST_FILES.txt"


echo "--- SUMMARY ---"

{
echo "MANIFEST_FILE_COUNT=$(wc -l < "$OUT/MANIFEST_FILES.txt")"
echo "ROOT_MANIFEST_SIGNAL_COUNT=$(wc -l < "$OUT/ROOT_MANIFEST_SIGNALS.txt")"
echo "PACKAGE_MANIFEST_SIGNAL_COUNT=$(wc -l < "$OUT/PACKAGE_MANIFEST_SIGNALS.txt")"
echo "SOURCE_MANIFEST_SIGNAL_COUNT=$(wc -l < "$OUT/SOURCE_MANIFEST_SIGNALS.txt")"
echo "SSOT_MANIFEST_SIGNAL_COUNT=$(wc -l < "$OUT/SSOT_MANIFEST_SIGNALS.txt")"
echo "MANIFEST_HASH_LINK_COUNT=$(wc -l < "$OUT/MANIFEST_HASH_LINKS.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- ROOT SAMPLE ---"
head -30 "$OUT/ROOT_MANIFEST_SIGNALS.txt" || true

echo "--- PACKAGE SAMPLE ---"
head -30 "$OUT/PACKAGE_MANIFEST_SIGNALS.txt" || true

echo "--- SSOT SAMPLE ---"
head -30 "$OUT/SSOT_MANIFEST_SIGNALS.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_038_MANIFEST_CHAIN_VALIDATION"
echo "============================================================"

