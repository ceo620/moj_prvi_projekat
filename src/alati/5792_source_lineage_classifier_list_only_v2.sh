#!/bin/bash
D4="/home/titangridmne/FREYA_BUILDER/99_DAEMON_RUN_GATE/DAEMON_004_SOURCE_LINEAGE_CLASSIFIER_LIST_ONLY"
DROP="/mnt/c/Users/titangrid.info/Desktop/FREYA_LENOVO_RECEIVER_DROPZONES/FROM_MAC"

while true; do
  TS="$(date '+%Y%m%d_%H%M%S')"
  LIST="$(ls -t "$DROP"/MAC_PACKET_CONTENTS_LIST_*.txt 2>/dev/null | head -1)"
  OUT="$D4/SOURCE_LINEAGE_CLASSIFICATION_V2.tsv"

  {
    echo -e "CLASS\tPATH"
    if [ -f "$LIST" ]; then
      while IFS= read -r P; do
        case "$P" in
          */01_MAC_LAPTOP_KNOWLEDGE/*) echo -e "MAC\t$P" ;;
          */02_DISK_KNOWLEDGE/*) echo -e "DISK\t$P" ;;
          */03_ANDROID_DELIVERED_KNOWLEDGE/*IPHONE*) echo -e "IPHONE\t$P" ;;
          */03_ANDROID_DELIVERED_KNOWLEDGE/*) echo -e "ANDROID\t$P" ;;
          */04_SOURCE_REGISTERS/*) echo -e "SOURCE_REGISTER\t$P" ;;
          */05_HASHES/*) echo -e "HASH\t$P" ;;
          */06_HUMAN_GATE/*) echo -e "HUMAN_GATE\t$P" ;;
          */07_TRANSFER_READY/*) echo -e "TRANSFER_READY\t$P" ;;
          */00_README/*) echo -e "README\t$P" ;;
        esac
      done < "$LIST"
    fi
  } > "$OUT"

  {
    echo "DAEMON_004_SOURCE_LINEAGE_CLASSIFIER_LIST_ONLY_V2"
    echo ""
    echo "LAST_HEARTBEAT=$TS"
    echo "STATUS=ACTIVE"
    echo "MODE=LIST_ONLY_SECTION_BASED"
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
    echo "NEXT_ALLOWED=DAEMON_005_SAFE_EXTRACT_GATE_PREVIEW"
  } > "$D4/HEARTBEAT.md"

  echo "$TS DAEMON_004_V2 heartbeat section-based-list-only" >> "$D4/daemon_004_v2.log"
  sleep 30
done
