#!/bin/bash
D6="/home/titangridmne/FREYA_BUILDER/99_DAEMON_RUN_GATE/DAEMON_006_EXTRACTED_PACKET_REVIEW_WATCHER_LIST_ONLY"
EXBASE="/mnt/c/Users/titangrid.info/Desktop/FREYA_LENOVO_RECEIVER_DROPZONES/FROM_MAC_REVIEW_ONLY_EXTRACTS"

while true; do
  TS="$(date '+%Y%m%d_%H%M%S')"
  LATEST="$(find "$EXBASE" -maxdepth 1 -type d -name 'REVIEW_ONLY_EXTRACT_*' 2>/dev/null | sort | tail -1)"

  {
    echo "DAEMON_006_EXTRACTED_PACKET_REVIEW_WATCHER_LIST_ONLY"
    echo ""
    echo "LAST_HEARTBEAT=$TS"
    echo "STATUS=ACTIVE"
    echo "MODE=EXTRACTED_REVIEW_LIST_ONLY"
    echo "RUNTIME=NO"
    echo "OLD_SCRIPT_RUNTIME=NO"
    echo "DELETE=NO"
    echo "MOVE_ORIGINALS=NO"
    echo "HUMAN_GATE=ACTIVE"
    echo ""
    echo "LATEST_EXTRACT=$LATEST"

    if [ -d "$LATEST" ]; then
      echo ""
      echo "RECEIPT:"
      grep -E 'EXTRACT_FOLDER=|SHA_STATUS=|MODE=|RUNTIME=|HUMAN_GATE=|NEXT_ALLOWED' "$LATEST/REVIEW_ONLY_EXTRACT_RECEIPT.md" 2>/dev/null || true

      echo ""
      echo "TOTAL_FILES=$(find "$LATEST" -type f | wc -l | tr -d ' ')"
      echo "TOTAL_DIRS=$(find "$LATEST" -type d | wc -l | tr -d ' ')"

      echo ""
      echo "TOP_LEVEL_STRUCTURE:"
      find "$LATEST" -mindepth 1 -maxdepth 3 -type d | sed "s|$LATEST/||" | sort | head -80

      echo ""
      echo "KEY_REVIEW_FILES:"
      find "$LATEST" -type f | sed "s|$LATEST/||" | grep -Ei 'README|REGISTER|MANIFEST|SOURCE|LINEAGE|HASH|HUMAN_GATE|SAFETY|DOCTRINE|KNOWLEDGE|IPHONE|ANDROID|MAC|DISK' | sort | head -120

      echo ""
      echo "RUNTIME_HINT_FILES:"
      find "$LATEST" -type f | grep -Ei '\.(sh|ps1|py|exe|bat|cmd|js|vbs|jar|dll|so)$' | sed "s|$LATEST/||" | sort | head -80

      echo ""
      echo "NEXT_ALLOWED=DAEMON_007_SOURCE_REGISTER_READER_STATIC"
    else
      echo ""
      echo "NO_REVIEW_ONLY_EXTRACT_FOUND"
      echo "NEXT_ALLOWED=NONE"
    fi
  } > "$D6/HEARTBEAT.md"

  echo "$TS DAEMON_006 heartbeat extracted-review-list-only" >> "$D6/daemon_006.log"
  sleep 30
done
