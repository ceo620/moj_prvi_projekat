#!/bin/bash

D9="/home/titangridmne/FREYA_BUILDER/99_DAEMON_RUN_GATE/DAEMON_009_LENOVO_SCRIPT_CENSUS_STATIC_ONLY"
TS="$(date '+%Y%m%d_%H%M%S')"

ROOTS="$D9/LENOVO_SCRIPT_SCAN_ROOTS_$TS.txt"
REG="$D9/LENOVO_SCRIPT_CENSUS_REGISTER_$TS.tsv"
SUMMARY="$D9/LENOVO_SCRIPT_CENSUS_SUMMARY_$TS.md"
HEART="$D9/HEARTBEAT.md"

cat > "$ROOTS" <<ROOTLIST
/home/titangridmne
/mnt/c/Users/titangrid.info
ROOTLIST

echo -e "SCRIPT_ID\tSOURCE_ROOT\tPATH\tEXT\tSIZE_BYTES\tMTIME\tSHA256\tRISK_CLASS\tSYSTEM_HINT\tRUNTIME_ALLOWED" > "$REG"

{
  echo "DAEMON_009_LENOVO_SCRIPT_CENSUS_STATIC_ONLY"
  echo ""
  echo "STARTED_AT=$TS"
  echo "STATUS=RUNNING"
  echo "MODE=STATIC_CENSUS_ONLY"
  echo "RUNTIME=NO"
  echo "SCRIPT_EXECUTION=NO"
  echo "DELETE=NO"
  echo "MOVE=NO"
  echo "RENAME=NO"
  echo "HUMAN_GATE=ACTIVE"
  echo ""
  echo "REGISTER=$REG"
} > "$HEART"

ID=0

while read -r ROOT_SCAN; do
  [ -d "$ROOT_SCAN" ] || continue

  echo "CURRENT_ROOT=$ROOT_SCAN" >> "$HEART"

  find "$ROOT_SCAN" \
    \( -path "*/node_modules/*" -o -path "*/.git/*" -o -path "*/__pycache__/*" -o -path "*/AppData/Local/Temp/*" -o -path "*/Cache/*" \) -prune -o \
    -type f \( \
      -iname "*.ps1" -o -iname "*.psm1" -o -iname "*.psd1" -o \
      -iname "*.sh" -o -iname "*.bash" -o -iname "*.zsh" -o \
      -iname "*.py" -o -iname "*.ipynb" -o \
      -iname "*.bat" -o -iname "*.cmd" -o \
      -iname "*.js" -o -iname "*.mjs" -o -iname "*.cjs" -o -iname "*.ts" -o \
      -iname "*.vbs" -o -iname "*.jar" -o \
      -iname "*.exe" -o -iname "*.dll" -o -iname "*.so" \
    \) -print0 2>/dev/null | while IFS= read -r -d '' F; do

      ID=$((ID+1))
      SID="$(printf "LENOVO_SCRIPT_%06d" "$ID")"
      EXT="$(basename "$F" | awk -F'.' '{print tolower($NF)}')"
      SIZE="$(stat -c '%s' "$F" 2>/dev/null || echo "NA")"
      MTIME="$(stat -c '%y' "$F" 2>/dev/null | cut -d'.' -f1 || echo "NA")"
      SHA="$(sha256sum "$F" 2>/dev/null | awk '{print $1}')"
      [ -z "$SHA" ] && SHA="HASH_FAILED"

      RISK="LOW_STATIC_FILE"
      case "$EXT" in
        exe|dll|so|jar) RISK="HIGH_BINARY_RUNTIME_HOLD" ;;
        ps1|psm1|psd1|bat|cmd|vbs) RISK="MEDIUM_WINDOWS_RUNTIME_HOLD" ;;
        sh|bash|zsh|py|js|mjs|cjs|ts) RISK="MEDIUM_SCRIPT_RUNTIME_HOLD" ;;
        ipynb) RISK="NOTEBOOK_STATIC_REVIEW_HOLD" ;;
      esac

      SYSTEM_HINT="GENERAL_SCRIPT"
      echo "$F" | grep -Eiq 'freya|titan|protokol|protocol|cmu|daemon|engine|ssot|matrix|orchestrator|ars|metal|data.room|vault|knowledge' && SYSTEM_HINT="FREYA_TITAN_RELEVANCE_CANDIDATE"

      printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tNO\n" \
        "$SID" "$ROOT_SCAN" "$F" "$EXT" "$SIZE" "$MTIME" "$SHA" "$RISK" "$SYSTEM_HINT" >> "$REG"
    done

done < "$ROOTS"

TOTAL="$(awk 'NR>1{c++} END{print c+0}' "$REG")"
FREYA_HINT="$(awk -F'\t' 'NR>1 && $9=="FREYA_TITAN_RELEVANCE_CANDIDATE"{c++} END{print c+0}' "$REG")"
HIGH="$(awk -F'\t' 'NR>1 && $8 ~ /HIGH/{c++} END{print c+0}' "$REG")"
MEDIUM="$(awk -F'\t' 'NR>1 && $8 ~ /MEDIUM/{c++} END{print c+0}' "$REG")"
NOTEBOOK="$(awk -F'\t' 'NR>1 && $8 ~ /NOTEBOOK/{c++} END{print c+0}' "$REG")"

cat > "$SUMMARY" <<REPORT
# DAEMON_009 Lenovo Script Census Static Only

COMPLETED_AT=$(date '+%Y%m%d_%H%M%S')

STATUS=COMPLETE
MODE=STATIC_CENSUS_ONLY

TOTAL_SCRIPT_CANDIDATES=$TOTAL
FREYA_TITAN_RELEVANCE_CANDIDATES=$FREYA_HINT
HIGH_BINARY_RUNTIME_HOLD=$HIGH
MEDIUM_SCRIPT_RUNTIME_HOLD=$MEDIUM
NOTEBOOK_STATIC_REVIEW_HOLD=$NOTEBOOK

REGISTER=$REG
SCAN_ROOTS=$ROOTS

RUNTIME_ALLOWED=NO
SCRIPT_EXECUTION=NO
AUTO_REPAIR=NO
DELETE=NO
MOVE=NO
RENAME=NO
HUMAN_GATE=ACTIVE

NEXT_ALLOWED:
DAEMON_010_LENOVO_SCRIPT_RISK_BUCKETS_STATIC_ONLY
REPORT

cat > "$HEART" <<REPORT
DAEMON_009_LENOVO_SCRIPT_CENSUS_STATIC_ONLY

STATUS=COMPLETE
MODE=STATIC_CENSUS_ONLY
TOTAL_SCRIPT_CANDIDATES=$TOTAL
FREYA_TITAN_RELEVANCE_CANDIDATES=$FREYA_HINT
HIGH_BINARY_RUNTIME_HOLD=$HIGH
MEDIUM_SCRIPT_RUNTIME_HOLD=$MEDIUM
NOTEBOOK_STATIC_REVIEW_HOLD=$NOTEBOOK

REGISTER=$REG
SUMMARY=$SUMMARY

RUNTIME_ALLOWED=NO
HUMAN_GATE=ACTIVE
NEXT_ALLOWED=DAEMON_010_LENOVO_SCRIPT_RISK_BUCKETS_STATIC_ONLY
REPORT
