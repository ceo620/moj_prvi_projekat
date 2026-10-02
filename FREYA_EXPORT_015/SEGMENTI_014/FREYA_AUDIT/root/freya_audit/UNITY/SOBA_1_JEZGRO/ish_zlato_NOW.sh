#!/bin/sh

TS="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/ISH_ZLATO_FINAL_$TS"

mkdir -p "$OUT/01_EXPORTS"
mkdir -p "$OUT/02_ARS_CAPEX_VDR"
mkdir -p "$OUT/03_TCC_888"
mkdir -p "$OUT/04_REGISTRI"
mkdir -p "$OUT/05_SKRIPTE"
mkdir -p "$OUT/06_SLIKE"
mkdir -p "$OUT/90_DUPLIKATI"
mkdir -p "$OUT/98_SECRET"
mkdir -p "$OUT/99_REGISTRI"

LOG="$OUT/99_REGISTRI/MOVE_LOG.txt"
HASH="$OUT/99_REGISTRI/FINAL_SHA256.txt"

echo "ISH_ZLATO RUN $TS" > "$LOG"

find "$HOME" -type f 2>/dev/null \
| grep -v "$OUT" \
| grep -Ev '/\.cache/|/tmp/|/node_modules/|/venv/|/\.git/' \
| grep -Ei 'ARS|METAL|Marel|ADS|Ankara|CAPEX|OPEX|DSCR|VDR|DATA|DUE|REGISTER|LEDGER|MANIFEST|SHA256|SOURCE|LINEAGE|DECISION|HUMAN|GATE|CLOSURE|README|SSOT|TCC|TITAN|PROTOKOL|888|orchestrator|daemon|governance|evidence|contract|annex|project|urbanizam|vodni|elaborat|DWG|DXF|CONTROL|CMU|dashboard|matrix|kernel|harvest|MVP|pilot|IPHONE|EXPORT|STATIC|CENSUS|secret|token|password|credential|private|\.pem|\.pfx|\.key|\.env|jpg|jpeg|png|heic|mov|mp4' \
| while read f
do
  [ -f "$f" ] || continue
  base="$(basename "$f")"
  h="$(sha256sum "$f" 2>/dev/null | awk '{print $1}')"

  if [ -z "$h" ]; then
    echo "HASH_FAILED | $f" >> "$LOG"
    continue
  fi

  if grep -q "$h" "$LOG"; then
    dest="$OUT/90_DUPLIKATI/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "DUPLICATE_MOVED | $h | $f | $dest" >> "$LOG"
    continue
  fi

  echo "$f" | grep -Eiq 'secret|token|password|credential|private|\.pem$|\.pfx$|\.key$|\.env$'
  if [ $? -eq 0 ]; then
    dest="$OUT/98_SECRET/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "SECRET_MOVED_NO_READ | $h | $f | $dest" >> "$LOG"
    continue
  fi

  echo "$base" | grep -Eiq '\.(jpg|jpeg|png|heic|heif|mov|mp4|m4v)$'
  if [ $? -eq 0 ]; then
    dest="$OUT/06_SLIKE/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "IMAGE_MOVED | $h | $f | $dest" >> "$LOG"
    continue
  fi

  echo "$f" | grep -Eiq 'REGISTER|LEDGER|MANIFEST|SHA256|SOURCE|LINEAGE|DECISION|HUMAN|GATE|CLOSURE|README'
  if [ $? -eq 0 ]; then
    dest="$OUT/04_REGISTRI/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "REGISTER_MOVED | $h | $f | $dest" >> "$LOG"
    continue
  fi

  echo "$f" | grep -Eiq 'TCC|TITAN|PROTOKOL|888|SSOT|orchestrator|daemon|CMU|CONTROL'
  if [ $? -eq 0 ]; then
    dest="$OUT/03_TCC_888/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "TCC_MOVED | $h | $f | $dest" >> "$LOG"
    continue
  fi

  echo "$base" | grep -Eiq '\.(py|sh|ps1|js|ts|ipynb|sql)$'
  if [ $? -eq 0 ]; then
    dest="$OUT/05_SKRIPTE/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "SCRIPT_MOVED | $h | $f | $dest" >> "$LOG"
    continue
  fi

  echo "$f" | grep -Eiq 'ARS|METAL|Marel|ADS|Ankara|CAPEX|OPEX|DSCR|VDR|DATA|DUE'
  if [ $? -eq 0 ]; then
    dest="$OUT/02_ARS_CAPEX_VDR/${h}_$base"
    mv "$f" "$dest" 2>/dev/null
    echo "ARS_CAPEX_MOVED | $h | $f | $dest" >> "$LOG"
    continue
  fi

  dest="$OUT/01_EXPORTS/${h}_$base"
  mv "$f" "$dest" 2>/dev/null
  echo "EXPORT_MOVED | $h | $f | $dest" >> "$LOG"
done

if [ -d "$OUT/06_SLIKE" ]; then
  tar -czf "$OUT/ISH_SLIKE_$TS.tar.gz" -C "$OUT/06_SLIKE" . 2>/dev/null
fi

find "$OUT" -type f 2>/dev/null | while read f
do
  sha256sum "$f" >> "$HASH" 2>/dev/null
done

SUMMARY="$OUT/00_ISH_ZLATO_SUMMARY.txt"
{
echo "ISH_ZLATO_FINAL SUMMARY"
echo "CREATED_AT=$TS"
echo "FOLDER=$OUT"
echo "MODE=MOVE_NOT_COPY"
echo "NO_DELETE=YES"
echo "NO_SCRIPT_RUNTIME=YES"
echo ""
echo "REGISTER_MOVED=$(grep -c '^REGISTER_MOVED' "$LOG")"
echo "TCC_MOVED=$(grep -c '^TCC_MOVED' "$LOG")"
echo "SCRIPT_MOVED=$(grep -c '^SCRIPT_MOVED' "$LOG")"
echo "ARS_CAPEX_MOVED=$(grep -c '^ARS_CAPEX_MOVED' "$LOG")"
echo "IMAGE_MOVED=$(grep -c '^IMAGE_MOVED' "$LOG")"
echo "SECRET_MOVED_NO_READ=$(grep -c '^SECRET_MOVED_NO_READ' "$LOG")"
echo "DUPLICATE_MOVED=$(grep -c '^DUPLICATE_MOVED' "$LOG")"
echo "HASH_FAILED=$(grep -c '^HASH_FAILED' "$LOG")"
echo ""
echo "LOG=$LOG"
echo "HASH=$HASH"
echo "IMAGE_PACK=$OUT/ISH_SLIKE_$TS.tar.gz"
echo ""
echo "NEXT=Prebaci cijeli folder ISH_ZLATO_FINAL na Mac."
} > "$SUMMARY"

cat "$SUMMARY"
