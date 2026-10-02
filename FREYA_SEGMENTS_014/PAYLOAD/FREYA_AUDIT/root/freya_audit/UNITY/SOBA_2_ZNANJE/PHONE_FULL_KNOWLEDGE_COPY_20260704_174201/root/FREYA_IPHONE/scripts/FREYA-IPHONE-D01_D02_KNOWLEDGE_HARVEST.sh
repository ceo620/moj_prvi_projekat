#!/bin/sh

BASE="$HOME"
OUT="$HOME/FREYA_IPHONE/21_KNOWLEDGE_HARVEST"
mkdir -p "$OUT"

echo "FREYA IPHONE KNOWLEDGE HARVEST"
echo "READ_ONLY=YES"
echo "NO_DELETE=YES"
echo "NO_RUNTIME=YES"
echo "HUMAN_GATE=ACTIVE"
echo ""

find "$BASE" -type f \
  ! -path "$HOME/FREYA_IPHONE/99_EXPORTS/*" \
  ! -path "$HOME/FREYA_IPHONE/18_BUILD_PACKET/*" \
  > "$OUT/01_ALL_FILES.txt"

find "$BASE" -type f \( \
  -iname "*.md" -o -iname "*.txt" -o -iname "*.csv" -o -iname "*.tsv" -o \
  -iname "*.json" -o -iname "*.db" -o -iname "*.sqlite" -o -iname "*.sqlite3" -o \
  -iname "*.pdf" -o -iname "*.docx" -o -iname "*.xlsx" \
\) > "$OUT/02_SMART_KNOWLEDGE_FILES.txt"

grep -Ei "FREYA|TITAN|ARS|SSOT|Human Gate|PROTOKOL|Protocol|EBRD|EIB|CAPEX|Data Room|VDR|doctrine|doktrina|engine|daemon|orchestrator|knowledge|memory|decision|risk|grant|funding|financial model" \
"$OUT/02_SMART_KNOWLEDGE_FILES.txt" \
> "$OUT/03_SIGNAL_PATHS.txt"

{
echo "HARVEST_STATUS=DONE"
echo "CREATED=$(date)"
echo "ALL_FILES=$(wc -l < "$OUT/01_ALL_FILES.txt")"
echo "SMART_FILES=$(wc -l < "$OUT/02_SMART_KNOWLEDGE_FILES.txt")"
echo "SIGNAL_PATHS=$(wc -l < "$OUT/03_SIGNAL_PATHS.txt")"
echo "RULE=No delete, no runtime, no original modified"
} > "$OUT/00_HARVEST_STATUS.txt"

cat "$OUT/00_HARVEST_STATUS.txt"
echo ""
echo "TOP SIGNALS:"
head -50 "$OUT/03_SIGNAL_PATHS.txt"
