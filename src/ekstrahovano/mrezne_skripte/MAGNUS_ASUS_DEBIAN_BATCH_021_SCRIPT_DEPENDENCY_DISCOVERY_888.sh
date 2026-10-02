#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 021"
echo " SCRIPT DEPENDENCY DISCOVERY — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_021_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=021"
echo "MODE=READ_ONLY_DEPENDENCY_DISCOVERY"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
-name "*.sh" \
2>/dev/null \
| sort \
> "$OUT/script_list.txt"


: > "$OUT/COMMAND_REFERENCES.txt"
: > "$OUT/SYSTEM_COMMANDS.txt"
: > "$OUT/POSSIBLE_EXTERNAL_DEPENDENCIES.txt"


while IFS= read -r FILE
do

echo "================================================" >> "$OUT/COMMAND_REFERENCES.txt"
echo "SCRIPT=$FILE" >> "$OUT/COMMAND_REFERENCES.txt"

grep -Eo \
'\b(apt|apt-get|bash|sh|python|python3|perl|ruby|node|npm|git|curl|wget|rsync|ssh|scp|tar|zip|unzip|find|grep|awk|sed|jq|sqlite3|openssl|sha256sum|md5sum|docker|systemctl|cron|crontab)\b' \
"$FILE" \
2>/dev/null \
| sort -u \
>> "$OUT/COMMAND_REFERENCES.txt" || true


grep -Eo \
'\b(bash|sh|find|grep|awk|sed|tar|sha256sum|md5sum|chmod|mkdir|cp|mv|rm|cat|head|tail|sort|uniq|wc)\b' \
"$FILE" \
2>/dev/null \
| sort -u \
>> "$OUT/SYSTEM_COMMANDS.txt" || true


grep -Eo \
'\b(python3?|node|npm|git|curl|wget|rsync|ssh|scp|jq|sqlite3|docker|openssl)\b' \
"$FILE" \
2>/dev/null \
| sort -u \
>> "$OUT/POSSIBLE_EXTERNAL_DEPENDENCIES.txt" || true

done < "$OUT/script_list.txt"


echo "--- AVAILABLE COMMAND CHECK ---"

for CMD in \
bash sh python python3 git curl wget rsync jq sqlite3 openssl
do

if command -v "$CMD" >/dev/null 2>&1
then
echo "$CMD=AVAILABLE"
else
echo "$CMD=NOT_FOUND"
fi

done | tee "$OUT/command_availability.txt"


echo "--- SUMMARY ---"

{
echo "TOTAL_SCRIPTS=$(wc -l < "$OUT/script_list.txt")"
echo "COMMAND_REFERENCE_COUNT=$(wc -l < "$OUT/COMMAND_REFERENCES.txt")"
echo "SYSTEM_COMMAND_COUNT=$(wc -l < "$OUT/SYSTEM_COMMANDS.txt")"
echo "EXTERNAL_DEPENDENCY_COUNT=$(wc -l < "$OUT/POSSIBLE_EXTERNAL_DEPENDENCIES.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- MISSING COMMAND SAMPLE ---"

grep "NOT_FOUND" "$OUT/command_availability.txt" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_022_DEPENDENCY_GRAPH_BUILD"
echo "============================================================"

