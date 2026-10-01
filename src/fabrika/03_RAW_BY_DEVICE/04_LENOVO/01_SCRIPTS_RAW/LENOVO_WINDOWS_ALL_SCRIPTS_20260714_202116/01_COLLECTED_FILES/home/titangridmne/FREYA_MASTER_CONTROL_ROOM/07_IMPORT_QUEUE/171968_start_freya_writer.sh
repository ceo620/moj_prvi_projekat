#!/bin/bash
set -u

TARGET="/mnt/c/Users/titangrid.info/Desktop/FREYA_150_FROM_MAC_REVIEW_ONLY – kopija"
SOURCE="/mnt/c/Users/titangrid.info/Desktop/FREYA_150_FROM_MAC_REVIEW_ONLY"
DAEMON="$TARGET/_FREYA_DAEMON_OUTPUT"
PIDF="$DAEMON/FREYA_WRITER.pid"

mkdir -p "$TARGET"

if [ -d "$SOURCE" ] && [ ! -d "$TARGET/FREYA_SLOT_001" ]; then
  cp -a "$SOURCE"/. "$TARGET"/
fi

mkdir -p "$DAEMON/logs" "$DAEMON/reports" "$DAEMON/registers"

if [ -f "$PIDF" ]; then
  OLD="$(cat "$PIDF" 2>/dev/null || true)"
  [ -n "$OLD" ] && kill "$OLD" 2>/dev/null || true
fi

(
  while true; do
    TS="$(date '+%Y-%m-%d %H:%M:%S')"
    RUN="$(date '+%Y%m%d_%H%M%S')"
    REPORT="$DAEMON/reports/FREYA_WRITER_TICK_$RUN.md"

    {
      echo "FREYA WRITER DAEMON"
      echo "TIME=$TS"
      echo "TARGET=$TARGET"
      echo "MODE=WRITE_REPORTS_ONLY"
      echo "RUNTIME=BLOCKED"
      echo "DELETE=BLOCKED"
      echo "UNPACK=BLOCKED"
      echo "HUMAN_GATE=ACTIVE"
      echo "SLOT_COUNT=$(find "$TARGET" -maxdepth 1 -type d -name 'FREYA_SLOT_*' | wc -l)"
    } > "$REPORT"

    for SLOT in "$TARGET"/FREYA_SLOT_*; do
      [ -d "$SLOT" ] || continue
      echo "$TS	FREYA_WRITER_ACTIVE	RUNTIME_BLOCKED	DELETE_BLOCKED	UNPACK_BLOCKED" >> "$SLOT/SLOT_DAEMON_LOG.tsv"
      cat > "$SLOT/CURRENT_SLOT_STATUS.md" <<SLOTSTATUS
FREYA SLOT STATUS

LAST_TICK=$TS
WRITER_DAEMON=ACTIVE
MAC_PACKET_RECEIVED=NO
RUNTIME=BLOCKED
DELETE=BLOCKED
UNPACK=BLOCKED
HUMAN_GATE=ACTIVE
SLOTSTATUS
    done

    echo "$TS	WRITER_TICK_OK	$REPORT" >> "$DAEMON/registers/FREYA_WRITER_TICKS.tsv"
    sleep 300
  done
) >> "$DAEMON/logs/FREYA_WRITER.log" 2>&1 &

echo $! > "$PIDF"

echo "=== FREYA WRITER STARTED ==="
echo "PID=$(cat "$PIDF")"
echo "TARGET=$TARGET"
echo "SLOT_COUNT=$(find "$TARGET" -maxdepth 1 -type d -name 'FREYA_SLOT_*' | wc -l)"
echo "STATUS=WRITING_REPORTS_ONLY"
echo "NO_RUNTIME=YES"
echo "NO_DELETE=YES"
echo "NO_UNPACK=YES"
