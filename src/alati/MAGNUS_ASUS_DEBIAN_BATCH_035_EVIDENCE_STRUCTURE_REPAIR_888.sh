#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 035"
echo " EVIDENCE STRUCTURE AUDIT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_035_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=035"
echo "MODE=READ_ONLY_EVIDENCE_STRUCTURE_AUDIT"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type d \
\( \
-iname "*evidence*" -o \
-iname "*proof*" -o \
-iname "*manifest*" -o \
-iname "*hash*" -o \
-iname "*receipt*" \
\) \
2>/dev/null \
| sort \
> "$OUT/EVIDENCE_DIRECTORIES.txt"


find "$ROOT" \
-type f \
\( \
-iname "*manifest*" -o \
-iname "*hash*" -o \
-iname "*proof*" -o \
-iname "*receipt*" -o \
-iname "*.sha256" -o \
-iname "*.env" \
\) \
2>/dev/null \
| sort \
> "$OUT/EVIDENCE_ARTIFACT_FILES.txt"


: > "$OUT/MANIFEST_SIGNALS.txt"
: > "$OUT/HASH_SIGNALS.txt"
: > "$OUT/PROOF_SIGNALS.txt"
: > "$OUT/RECEIPT_SIGNALS.txt"


while IFS= read -r FILE
do

grep -Ei \
'MANIFEST|ROOT_MANIFEST|MANIFEST\.sha|MANIFEST_SHA|SOURCE_COPY_VERIFICATION' \
"$FILE" \
2>/dev/null \
>> "$OUT/MANIFEST_SIGNALS.txt" || true


grep -Ei \
'SHA256|SHA-256|HASH|CHECKSUM|DIGEST' \
"$FILE" \
2>/dev/null \
>> "$OUT/HASH_SIGNALS.txt" || true


grep -Ei \
'PROOF|VALIDATION|VERIFIED|CERTIFICATE|SEAL' \
"$FILE" \
2>/dev/null \
>> "$OUT/PROOF_SIGNALS.txt" || true


grep -Ei \
'RECEIPT|ACK|ACKNOWLEDGE|TRANSITION' \
"$FILE" \
2>/dev/null \
>> "$OUT/RECEIPT_SIGNALS.txt" || true

done < "$OUT/EVIDENCE_ARTIFACT_FILES.txt"


echo "--- SUMMARY ---"

{
echo "EVIDENCE_DIRECTORY_COUNT=$(wc -l < "$OUT/EVIDENCE_DIRECTORIES.txt")"
echo "EVIDENCE_ARTIFACT_FILE_COUNT=$(wc -l < "$OUT/EVIDENCE_ARTIFACT_FILES.txt")"
echo "MANIFEST_SIGNAL_COUNT=$(wc -l < "$OUT/MANIFEST_SIGNALS.txt")"
echo "HASH_SIGNAL_COUNT=$(wc -l < "$OUT/HASH_SIGNALS.txt")"
echo "PROOF_SIGNAL_COUNT=$(wc -l < "$OUT/PROOF_SIGNALS.txt")"
echo "RECEIPT_SIGNAL_COUNT=$(wc -l < "$OUT/RECEIPT_SIGNALS.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- EVIDENCE DIRECTORY SAMPLE ---"
head -30 "$OUT/EVIDENCE_DIRECTORIES.txt" || true

echo "--- MANIFEST SAMPLE ---"
head -30 "$OUT/MANIFEST_SIGNALS.txt" || true

echo "--- HASH SAMPLE ---"
head -30 "$OUT/HASH_SIGNALS.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_036_HASH_EVIDENCE_STANDARDIZATION"
echo "============================================================"

