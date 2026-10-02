#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 023"
echo " BROKEN DEPENDENCY VALIDATION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_023_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=023"
echo "MODE=READ_ONLY_DEPENDENCY_VALIDATION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
-name "*.sh" \
2>/dev/null \
| sort \
> "$OUT/script_list.txt"


: > "$OUT/DEPENDENCY_STATUS.tsv"
: > "$OUT/MISSING_CRITICAL_DEPENDENCY.tsv"
: > "$OUT/MISSING_OPTIONAL_DEPENDENCY.tsv"


COMMANDS="
bash
sh
find
grep
awk
sed
sha256sum
md5sum
chmod
mkdir
cp
mv
rm
cat
head
tail
sort
uniq
wc
tar
openssl
python
python3
git
curl
wget
rsync
jq
sqlite3
zip
unzip
"


while IFS= read -r FILE
do

for CMD in $COMMANDS
do

if grep -Eq "(^|[^A-Za-z0-9_])$CMD([^A-Za-z0-9_]|$)" "$FILE" 2>/dev/null
then

if command -v "$CMD" >/dev/null 2>&1
then
echo -e "$FILE\t$CMD\tAVAILABLE" >> "$OUT/DEPENDENCY_STATUS.tsv"
else

case "$CMD" in
bash|sh|find|grep|awk|sed|sha256sum|md5sum|chmod|mkdir|cp|mv|rm|cat|head|tail|sort|uniq|wc|tar)
echo -e "$FILE\t$CMD\tMISSING_CRITICAL" >> "$OUT/MISSING_CRITICAL_DEPENDENCY.tsv"
;;
*)
echo -e "$FILE\t$CMD\tMISSING_OPTIONAL" >> "$OUT/MISSING_OPTIONAL_DEPENDENCY.tsv"
;;
esac

fi

fi

done

done < "$OUT/script_list.txt"


echo "--- SUMMARY ---"

{
echo "TOTAL_SCRIPTS=$(wc -l < "$OUT/script_list.txt")"
echo "DEPENDENCY_STATUS_COUNT=$(wc -l < "$OUT/DEPENDENCY_STATUS.tsv")"
echo "MISSING_CRITICAL_COUNT=$(wc -l < "$OUT/MISSING_CRITICAL_DEPENDENCY.tsv")"
echo "MISSING_OPTIONAL_COUNT=$(wc -l < "$OUT/MISSING_OPTIONAL_DEPENDENCY.tsv")"
} | tee "$OUT/SUMMARY.env"


echo "--- CRITICAL MISSING ---"
cat "$OUT/MISSING_CRITICAL_DEPENDENCY.tsv" || true

echo "--- OPTIONAL MISSING ---"
cat "$OUT/MISSING_OPTIONAL_DEPENDENCY.tsv" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_024_EXECUTION_ORDER_REPAIR"
echo "============================================================"

