#!/bin/bash
D2="/home/titangridmne/FREYA_BUILDER/99_DAEMON_RUN_GATE/DAEMON_002_RECEIVER_WATCHER_LIST_ONLY"
DROP="/mnt/c/Users/titangrid.info/Desktop/FREYA_LENOVO_RECEIVER_DROPZONES"

while true; do
  TS="$(date '+%Y%m%d_%H%M%S')"
  {
    echo "DAEMON_002_RECEIVER_WATCHER_LIST_ONLY"
    echo ""
    echo "LAST_HEARTBEAT=$TS"
    echo "STATUS=ACTIVE"
    echo "MODE=LIST_ONLY"
    echo "UNPACK=NO"
    echo "OLD_SCRIPT_RUNTIME=NO"
    echo "HUMAN_GATE=ACTIVE"
    echo ""
    echo "DROPZONE_FILE_COUNTS:"
    for z in FROM_MAC FROM_ANDROID FROM_IPHONE FROM_MSI FROM_EXTERNAL_DISK FROM_WINDOWS_DESKTOP_DROP; do
      C="$(find "$DROP/$z" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')"
      echo "$z=$C"
    done
    echo ""
    echo "FROM_MAC_FILES:"
    find "$DROP/FROM_MAC" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | sort
    echo ""
    echo "NEXT_ALLOWED=DAEMON_003_PACKET_INDEXER_LIST_ONLY"
  } > "$D2/HEARTBEAT.md"

  echo "$TS DAEMON_002 heartbeat list-only" >> "$D2/daemon_002.log"
  sleep 30
done
