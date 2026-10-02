#!/bin/bash
D3="/home/titangridmne/FREYA_BUILDER/99_DAEMON_RUN_GATE/DAEMON_003_PACKET_INDEXER_LIST_ONLY"
DROP="/mnt/c/Users/titangrid.info/Desktop/FREYA_LENOVO_RECEIVER_DROPZONES/FROM_MAC"

while true; do
  TS="$(date '+%Y%m%d_%H%M%S')"
  LIST="$(ls -t "$DROP"/MAC_PACKET_CONTENTS_LIST_*.txt 2>/dev/null | head -1)"

  {
    echo "DAEMON_003_PACKET_INDEXER_LIST_ONLY"
    echo ""
    echo "LAST_HEARTBEAT=$TS"
    echo "STATUS=ACTIVE"
    echo "MODE=LIST_ONLY"
    echo "UNPACK=NO"
    echo "OLD_SCRIPT_RUNTIME=NO"
    echo "HUMAN_GATE=ACTIVE"
    echo ""
    echo "SOURCE_LIST=$LIST"
    echo ""

    if [ -f "$LIST" ]; then
      echo "TOTAL_ARCHIVE_ENTRIES=$(wc -l < "$LIST" | tr -d ' ')"
      echo "TOP_LEVEL_SECTIONS:"
      awk -F'/' 'NF>1 {print $2}' "$LIST" | sort | uniq -c | sort -nr
      echo ""
      echo "HIGH_SIGNAL_FILES:"
      grep -Ei 'doctrine|register|manifest|source|lineage|hash|human_gate|knowledge|iphone|android|disk|mac' "$LIST" | head -80
    else
      echo "NO_CONTENT_LIST_FOUND"
    fi

    echo ""
    echo "NEXT_ALLOWED=DAEMON_004_SOURCE_LINEAGE_CLASSIFIER_LIST_ONLY"
  } > "$D3/HEARTBEAT.md"

  echo "$TS DAEMON_003 heartbeat packet-index-list-only" >> "$D3/daemon_003.log"
  sleep 30
done
