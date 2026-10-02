#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 036"
echo " HASH EVIDENCE STANDARDIZATION AUDIT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_036_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=036"
echo "MODE=READ_ONLY_HASH_EVIDENCE_AUDIT"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
\( \
-iname "*.sha256" -o \
-iname "*hash*" -o \
-iname "*manifest*" -o \
-iname "*.csv" -o \
-iname "*.tsv" -o \
-iname "*.env" \
\) \
2>/dev/null \
| sort \
> "$OUT/HASH_ARTIFACT_FILES.txt"


: > "$OUT/SHA256_SIGNALS.txt"
: > "$OUT/MANIFEST_HASH_LINKS.txt"
: > "$OUT/HASH_REGISTER_SIGNALS.txt"
: > "$OUT/HASH_STATUS_SIGNALS.txt"


while IFS= read -r FILE
do

grep -Ei \
'SHA256|SHA-256|sha256|HASH|CHECKSUM|DIGEST' \
"$FILE" \
2>/dev/null \
>> "$OUT/SHA256_SIGNALS.txt" || true


grep -Ei \
'MANIFEST|PACKAGE_MANIFEST|SOURCE_COPY_VERIFICATION|ROOT_MANIFEST' \
"$FILE" \
2>/dev/null \
>> "$OUT/MANIFEST_HASH_LINKS.txt" || true


grep -Ei \
'HASH_REGISTER|CURRENT_HASH_REGISTER|REGISTER_TYPE|TARGET_REGISTER' \
"$FILE" \
2>/dev/null \
>> "$OUT/HASH_REGISTER_SIGNALS.txt" || true


grep -Ei \
'HASHED|HASH_STATUS|HASH_VERIFIED|HASH_MISMATCH|READ_ERRORS|COPIED_HASH_VERIFIED' \
"$FILE" \
2>/dev/null \
>> "$OUT/HASH_STATUS_SIGNALS.txt" || true


done < "$OUT/HASH_ARTIFACT_FILES.txt"


echo "--- SUMMARY ---"

{
echo "HASH_ARTIFACT_FILE_COUNT=$(wc -l < "$OUT/HASH_ARTIFACT_FILES.txt")"
echo "SHA256_SIGNAL_COUNT=$(wc -l < "$OUT/SHA256_SIGNALS.txt")"
echo "MANIFEST_HASH_LINK_COUNT=$(wc -l < "$OUT/MANIFEST_HASH_LINKS.txt")"
echo "HASH_REGISTER_SIGNAL_COUNT=$(wc -l < "$OUT/HASH_REGISTER_SIGNALS.txt")"
echo "HASH_STATUS_SIGNAL_COUNT=$(wc -l < "$OUT/HASH_STATUS_SIGNALS.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- HASH REGISTER SAMPLE ---"
head -30 "$OUT/HASH_REGISTER_SIGNALS.txt" || true

echo "--- HASH STATUS SAMPLE ---"
head -30 "$OUT/HASH_STATUS_SIGNALS.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_037_MANIFEST_DISCOVERY"
echo "============================================================"

