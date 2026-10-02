#!/bin/bash
D4="/home/titangridmne/FREYA_BUILDER/99_DAEMON_RUN_GATE/DAEMON_004_SOURCE_LINEAGE_CLASSIFIER_LIST_ONLY"
DROP="/mnt/c/Users/titangrid.info/Desktop/FREYA_LENOVO_RECEIVER_DROPZONES/FROM_MAC"

while true; do
  TS="$(date '+%Y%m%d_%H%M%S')"
  LIST="$(ls -t "$DROP"/MAC_PACKET_CONTENTS_LIST_*.txt 2>/dev/null | head -1)"
  OUT="$D4/SOURCE_LINEAGE_CLASSIFICATION.tsv"

  {
    echo -e "CLASS\tPATH"
    if [ -f "$LIST" ]; then
      grep -Ei '01_MAC_LAPTOP_KNOWLEDGE|MAC_' "$LIST" | awk '{print "MAC\t"$0}'
      grep -Ei '02_DISK_KNOWLEDGE|DISK_' "$LIST" | awk '{print "DISK\t"$0}'
      grep -Ei '03_ANDROID_DELIVERED_KNOWLEDGE|ANDROID_' "$LIST" | awk '{print "ANDROID\t"$0}'
      grep -Ei 'IPHONE' "$LIST" | awk '{print "IPHONE\t"$0}'
      grep -Ei 'SOURCE_REGISTER|SOURCE_LINEAGE|PACKET_INTERNAL_FILELIST' "$LIST" | awk '{print "SOURCE_REGISTER\t"$0}'
      grep -Ei 'HASH|SHA256|sha256' "$LIST" | awk '{print "HASH\t"$0}'
      grep -Ei 'HUMAN_GATE|SAFETY_LOCK' "$LIST" | awk '{print "HUMAN_GATE\t"$0}'
      grep -Ei 'DOCTRINE|FREYA_DOCTRINE|CORE_DOCTRINE' "$LIST" | awk '{print "DOCTRINE\t"$0}'
    fi
  } > "$OUT"

  {
    echo "DAEMON_004_SOURCE_LINEAGE_CLASSIFIER_LIST_ONLY"
    echo ""
    echo "LAST_HEARTBEAT=$TS"
    echo "STATUS=ACTIVE"
    echo "MODE=LIST_ONLY"
    echo "UNPACK=NO"
    echo "OLD_SCRIPT_RUNTIME=NO"
    echo "HUMAN_GATE=ACTIVE"
    echo ""
    echo "SOURCE_LIST=$LIST"
    echo "CLASSIFICATION_REGISTER=$OUT"
    echo ""
    echo "CLASS_COUNTS:"
    awk -F'\t' 'NR>1 {c[$1]++} END {for (k in c) print k "=" c[k]}' "$OUT" | sort
    echo ""
    echo "TOP_ANDROID_SIGNALS:"
    awk -F'\t' '$1=="ANDROID"{print $2}' "$OUT" | head -20
    echo ""
    echo "TOP_IPHONE_SIGNALS:"
    awk -F'\t' '$1=="IPHONE"{print $2}' "$OUT" | head -20
    echo ""
    echo "NEXT_ALLOWED=DAEMON_005_SAFE_EXTRACT_GATE_PREVIEW"
  } > "$D4/HEARTBEAT.md"

  echo "$TS DAEMON_004 heartbeat source-lineage-list-only" >> "$D4/daemon_004.log"
  sleep 30
done
