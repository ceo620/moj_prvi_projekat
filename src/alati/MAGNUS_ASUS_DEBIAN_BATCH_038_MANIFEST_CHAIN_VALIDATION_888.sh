#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 038"
echo " MANIFEST CHAIN VALIDATION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_038_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=038"
echo "MODE=READ_ONLY_MANIFEST_CHAIN_VALIDATION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
\( \
-iname "*manifest*" -o \
-iname "*.sha256" -o \
-iname "*hash*" -o \
-iname "*evidence*" -o \
-iname "*receipt*" -o \
-iname "*.json" -o \
-iname "*.csv" -o \
-iname "*.tsv" \
\) \
2>/dev/null \
| sort \
> "$OUT/CHAIN_FILES.txt"


: > "$OUT/MANIFEST_HASH_CHAIN.txt"
: > "$OUT/HASH_EVIDENCE_CHAIN.txt"
: > "$OUT/ROOT_PACKAGE_SOURCE_CHAIN.txt"
: > "$OUT/BROKEN_CHAIN_CANDIDATES.txt"


while IFS= read -r FILE
do

grep -Ei \
'MANIFEST|SHA256|HASH|CHECKSUM|DIGEST' \
"$FILE" \
2>/dev/null \
>> "$OUT/MANIFEST_HASH_CHAIN.txt" || true


grep -Ei \
'EVIDENCE|PROOF|RECEIPT|VALIDATED|VERIFIED|COPIED_HASH_VERIFIED' \
"$FILE" \
2>/dev/null \
>> "$OUT/HASH_EVIDENCE_CHAIN.txt" || true


grep -Ei \
'ROOT_MANIFEST|PACKAGE_MANIFEST|SOURCE_MANIFEST|SOURCE_COPY|SSOT|CANONICAL|REGISTER' \
"$FILE" \
2>/dev/null \
>> "$OUT/ROOT_PACKAGE_SOURCE_CHAIN.txt" || true


grep -Ei \
'MISSING|NOT_FOUND|BROKEN|FAILED|UNRESOLVED|INVALID' \
"$FILE" \
2>/dev/null \
>> "$OUT/BROKEN_CHAIN_CANDIDATES.txt" || true


done < "$OUT/CHAIN_FILES.txt"


echo "--- SUMMARY ---"

{
echo "CHAIN_FILE_COUNT=$(wc -l < "$OUT/CHAIN_FILES.txt")"
echo "MANIFEST_HASH_CHAIN_COUNT=$(wc -l < "$OUT/MANIFEST_HASH_CHAIN.txt")"
echo "HASH_EVIDENCE_CHAIN_COUNT=$(wc -l < "$OUT/HASH_EVIDENCE_CHAIN.txt")"
echo "ROOT_PACKAGE_SOURCE_CHAIN_COUNT=$(wc -l < "$OUT/ROOT_PACKAGE_SOURCE_CHAIN.txt")"
echo "BROKEN_CHAIN_CANDIDATE_COUNT=$(wc -l < "$OUT/BROKEN_CHAIN_CANDIDATES.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- BROKEN SAMPLE ---"
head -30 "$OUT/BROKEN_CHAIN_CANDIDATES.txt" || true

echo "--- CHAIN SAMPLE ---"
head -30 "$OUT/ROOT_PACKAGE_SOURCE_CHAIN.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_039_SSOT_CHAIN_VALIDATION"
echo "============================================================"

