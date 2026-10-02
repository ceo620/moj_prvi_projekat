#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 022"
echo " DEPENDENCY GRAPH BUILD — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_022_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=022"
echo "MODE=READ_ONLY_DEPENDENCY_GRAPH_BUILD"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$ROOT" \
-type f \
-name "*.sh" \
2>/dev/null \
| sort \
> "$OUT/script_list.txt"


: > "$OUT/SCRIPT_COMMAND_GRAPH.tsv"
: > "$OUT/CRITICAL_DEPENDENCY.tsv"
: > "$OUT/OPTIONAL_DEPENDENCY.tsv"


COMMANDS="
bash
sh
python
python3
git
curl
wget
rsync
jq
sqlite3
openssl
tar
zip
unzip
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
"


while IFS= read -r FILE
do

for CMD in $COMMANDS
do

if grep -Eq "(^|[^A-Za-z0-9_])$CMD([^A-Za-z0-9_]|$)" "$FILE" 2>/dev/null
then

echo -e "$FILE\t$CMD" >> "$OUT/SCRIPT_COMMAND_GRAPH.tsv"

case "$CMD" in

bash|sh|find|grep|awk|sed|sha256sum|chmod|mkdir|cp|mv|rm|cat|head|tail|sort|uniq|wc|tar)
echo -e "$FILE\t$CMD\tCORE" >> "$OUT/CRITICAL_DEPENDENCY.tsv"
;;

python|python3|git|curl|wget|rsync|jq|sqlite3|openssl|zip|unzip)
echo -e "$FILE\t$CMD\tOPTIONAL" >> "$OUT/OPTIONAL_DEPENDENCY.tsv"
;;

esac

fi

done

done < "$OUT/script_list.txt"


echo "--- COMMAND AVAILABILITY ---"

for CMD in $COMMANDS
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
echo "GRAPH_ENTRIES=$(wc -l < "$OUT/SCRIPT_COMMAND_GRAPH.tsv")"
echo "CORE_DEPENDENCY_ENTRIES=$(wc -l < "$OUT/CRITICAL_DEPENDENCY.tsv")"
echo "OPTIONAL_DEPENDENCY_ENTRIES=$(wc -l < "$OUT/OPTIONAL_DEPENDENCY.tsv")"
} | tee "$OUT/SUMMARY.env"


echo "--- OPTIONAL DEPENDENCY SAMPLE ---"
head -50 "$OUT/OPTIONAL_DEPENDENCY.tsv" || true


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_023_BROKEN_DEPENDENCY_REPAIR"
echo "============================================================"

