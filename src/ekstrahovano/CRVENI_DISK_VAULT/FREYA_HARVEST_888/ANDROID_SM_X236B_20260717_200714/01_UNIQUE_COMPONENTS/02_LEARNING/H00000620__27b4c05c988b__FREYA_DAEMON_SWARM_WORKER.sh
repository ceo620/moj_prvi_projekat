#!/data/data/com.termux/files/usr/bin/sh
FREYA_BASE="$HOME/HUMAN_GATE_TABLET_CONTROL/07_ANDROID_FREYA"
DAEMON_DIR="$FREYA_BASE/29_ACTIVE_DAEMON_SWARM"
PID_FILE="$DAEMON_DIR/FREYA_DAEMON_SWARM.pid"
STATE_FILE="$DAEMON_DIR/FREYA_DAEMON_SWARM.state"
STOP_FILE="$DAEMON_DIR/STOP_DAEMON_SWARM.flag"
LOG_FILE="$DAEMON_DIR/FREYA_DAEMON_SWARM.log"
mkdir -p "$DAEMON_DIR"

OLD_PID=""
RAW_PID=""

if [ -f "$PID_FILE" ]; then
  RAW_PID="$(tr -d '[:space:]' < "$PID_FILE" 2>/dev/null)"

  case "$RAW_PID" in
    ''|*[!0-9]*)
      OLD_PID=""
      ;;
    *)
      OLD_PID="$RAW_PID"
      ;;
  esac
fi

if [ -n "$OLD_PID" ] && [ -d "/proc/$OLD_PID" ]; then
  OLD_CMDLINE="$(tr '\0' ' ' < "/proc/$OLD_PID/cmdline" 2>/dev/null)"

  case "$OLD_CMDLINE" in
    *FREYA_DAEMON_SWARM_WORKER.sh*)
      {
        echo "DAEMON_SWARM_START_BLOCKED=$(date)"
        echo "REASON=ALREADY_RUNNING"
        echo "EXISTING_PID=$OLD_PID"
        echo "EXISTING_CMDLINE=$OLD_CMDLINE"
      } >> "$LOG_FILE"

      {
        echo "WORKER=FREYA_DAEMON_SWARM_WORKER"
        echo "STATE=ALREADY_RUNNING"
        echo "PID=$OLD_PID"
        echo "CHECKED_AT=$(date)"
      } > "$STATE_FILE"

      exit 73
      ;;
  esac
fi

if [ -f "$STOP_FILE" ]; then
  {
    echo "DAEMON_SWARM_START_BLOCKED=$(date)"
    echo "REASON=STOP_FILE_PRESENT"
    echo "STOP_FILE=$STOP_FILE"
  } >> "$LOG_FILE"

  {
    echo "WORKER=FREYA_DAEMON_SWARM_WORKER"
    echo "STATE=BLOCKED_STOP_FILE_PRESENT"
    echo "STOP_FILE=$STOP_FILE"
    echo "CHECKED_AT=$(date)"
  } > "$STATE_FILE"

  exit 75
fi

RUN_ID="DAEMON_SWARM_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$DAEMON_DIR/RUNS/$RUN_ID"
mkdir -p "$RUN_DIR"

STARTED_AT="$(date)"
EXIT_REASON="UNSPECIFIED"
LAST_COMPLETED_CYCLE=0

cleanup_daemon_swarm() {
  EXIT_CODE="$?"

  trap - 0

  if [ "$EXIT_REASON" = "UNSPECIFIED" ]; then
    if [ "$EXIT_CODE" -eq 0 ]; then
      EXIT_REASON="NORMAL_COMPLETION"
    else
      EXIT_REASON="UNEXPECTED_EXIT"
    fi
  fi

  {
    echo "DAEMON_SWARM_RUNTIME_CLEANUP=$(date)"
    echo "RUN_ID=$RUN_ID"
    echo "PID=$$"
    echo "EXIT_CODE=$EXIT_CODE"
    echo "EXIT_REASON=$EXIT_REASON"
    echo "LAST_COMPLETED_CYCLE=$LAST_COMPLETED_CYCLE"
    echo "PID_FILE_CLEARED=YES"
  } >> "$LOG_FILE"

  {
    echo "WORKER=FREYA_DAEMON_SWARM_WORKER"
    echo "STATE=STOPPED"
    echo "RUN_ID=$RUN_ID"
    echo "LAST_PID=$$"
    echo "STARTED_AT=$STARTED_AT"
    echo "STOPPED_AT=$(date)"
    echo "EXIT_CODE=$EXIT_CODE"
    echo "EXIT_REASON=$EXIT_REASON"
    echo "LAST_COMPLETED_CYCLE=$LAST_COMPLETED_CYCLE"
    echo "PID_FILE=$PID_FILE"
    echo "PID_FILE_CLEARED=YES"
  } > "$STATE_FILE"

  : > "$PID_FILE"

  exit "$EXIT_CODE"
}

trap cleanup_daemon_swarm 0

trap '
  EXIT_REASON=SIGNAL_HUP
  echo "DAEMON_SWARM_SIGNAL_HUP=$(date)" >> "$LOG_FILE"
  exit 129
' 1

trap '
  EXIT_REASON=SIGNAL_INT
  echo "DAEMON_SWARM_SIGNAL_INT=$(date)" >> "$LOG_FILE"
  exit 130
' 2

trap '
  EXIT_REASON=SIGNAL_TERM
  echo "DAEMON_SWARM_SIGNAL_TERM=$(date)" >> "$LOG_FILE"
  exit 143
' 15

printf '%s\n' "$$" > "$PID_FILE"

{
  echo "WORKER=FREYA_DAEMON_SWARM_WORKER"
  echo "STATE=RUNNING"
  echo "RUN_ID=$RUN_ID"
  echo "PID=$$"
  echo "STARTED_AT=$STARTED_AT"

  if [ -n "$OLD_PID" ]; then
    echo "STALE_OR_REUSED_PREVIOUS_PID=$OLD_PID"
  else
    echo "STALE_OR_REUSED_PREVIOUS_PID=NONE"
  fi
} > "$STATE_FILE"

{
  echo "FREYA_DAEMON_SWARM_STARTED=$(date)"
  echo "RUN_ID=$RUN_ID"
  echo "PID=$$"
  echo "HUMAN_GATE=ACTIVE"
  echo "MODE=CONTROLLED_BACKGROUND_DAEMON_SWARM"
  echo "DAEMONS_ACTIVE=8"
  echo "DELETE=NO"
  echo "MOVE_ORIGINALS=NO"
  echo "RENAME_ORIGINALS=NO"
  echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
  echo "RUN_4000_OLD_SCRIPTS=NO"
  echo "AUTO_INTERNET=NO"
  echo "AUTO_SEND=NO"
  echo "NO_PUBLICATION=YES"
  echo "PID_LIFECYCLE_CONTROL=ENABLED"
  echo "DUPLICATE_START_PROTECTION=ENABLED"
} >> "$LOG_FILE"

cycle=1
max_cycles=30

while [ "$cycle" -le "$max_cycles" ]; do
  if [ -f "$STOP_FILE" ]; then
    EXIT_REASON="STOP_FILE_DETECTED"
      echo "DAEMON_SWARM_STOP_FILE_DETECTED=$(date)" >> "$LOG_FILE"
    break
  fi

  SNAP="$RUN_DIR/DAEMON_SWARM_CYCLE_${cycle}.txt"

  {
    echo "FREYA_DAEMON_SWARM_CYCLE"
    echo "DATE=$(date)"
    echo "CYCLE=$cycle/$max_cycles"
    echo "HUMAN_GATE=ACTIVE"
    echo "BACKGROUND=YES_CONTROLLED"
    echo "DAEMONS_ACTIVE=8"
    echo "DELETE=NO"
    echo "MOVE_ORIGINALS=NO"
    echo "RENAME_ORIGINALS=NO"
    echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
    echo "RUN_4000_OLD_SCRIPTS=NO"
    echo "AUTO_INTERNET=NO"
    echo "AUTO_SEND=NO"
    echo "NO_PUBLICATION=YES"
    echo

    echo "D001_STATUS_DAEMON:"
    [ -f "$FREYA_BASE/10_ANDROID_DEVICE_STATUS/FREYA_ANDROID_CURRENT_STATUS.txt" ] && tail -n 20 "$FREYA_BASE/10_ANDROID_DEVICE_STATUS/FREYA_ANDROID_CURRENT_STATUS.txt" || echo "CURRENT_STATUS_MISSING"
    echo

    echo "D002_TASK_DAEMON:"
    if [ -f "$FREYA_BASE/14_TASK_SYSTEM/FREYA_TASK_REGISTER.psv" ]; then
      echo "TASKS=$(($(wc -l < "$FREYA_BASE/14_TASK_SYSTEM/FREYA_TASK_REGISTER.psv") - 1))"
      cut -d'|' -f4 "$FREYA_BASE/14_TASK_SYSTEM/FREYA_TASK_REGISTER.psv" | tail -n +2 | sort | uniq -c | sort -nr
    else
      echo "TASK_REGISTER_MISSING"
    fi
    echo

    echo "D003_EVIDENCE_DAEMON:"
    [ -f "$FREYA_BASE/16_EVIDENCE_SYSTEM/FREYA_EVIDENCE_REGISTER.psv" ] && echo "EVIDENCE_RECORDS=$(($(wc -l < "$FREYA_BASE/16_EVIDENCE_SYSTEM/FREYA_EVIDENCE_REGISTER.psv") - 1))" || echo "EVIDENCE_REGISTER_MISSING"
    [ -f "$FREYA_BASE/18_HASH_LINEAGE_SYSTEM/FREYA_HASH_LINEAGE_REGISTER.psv" ] && echo "HASH_RECORDS=$(($(wc -l < "$FREYA_BASE/18_HASH_LINEAGE_SYSTEM/FREYA_HASH_LINEAGE_REGISTER.psv") - 1))" || echo "HASH_REGISTER_MISSING"
    echo

    echo "D004_QUEUE_DAEMON:"
    if [ -f "$FREYA_BASE/17_QUEUE_SYSTEM/FREYA_QUEUE_REGISTER.psv" ]; then
      echo "QUEUE_ITEMS=$(($(wc -l < "$FREYA_BASE/17_QUEUE_SYSTEM/FREYA_QUEUE_REGISTER.psv") - 1))"
      cut -d'|' -f7 "$FREYA_BASE/17_QUEUE_SYSTEM/FREYA_QUEUE_REGISTER.psv" | tail -n +2 | sort | uniq -c | sort -nr
    else
      echo "QUEUE_REGISTER_MISSING"
    fi
    echo

    echo "D005_ARS_DAEMON:"
    if [ -f "$FREYA_BASE/25_DOCUMENT_CLASSIFICATION_SYSTEM/FREYA_DOCUMENT_CLASSIFICATION_REGISTER.psv" ]; then
      echo "CLASSIFICATION_RECORDS=$(($(wc -l < "$FREYA_BASE/25_DOCUMENT_CLASSIFICATION_SYSTEM/FREYA_DOCUMENT_CLASSIFICATION_REGISTER.psv") - 1))"
      cut -d'|' -f9 "$FREYA_BASE/25_DOCUMENT_CLASSIFICATION_SYSTEM/FREYA_DOCUMENT_CLASSIFICATION_REGISTER.psv" | tail -n +2 | sort | uniq -c | sort -nr
    else
      echo "CLASSIFICATION_REGISTER_MISSING"
    fi
    echo

    echo "D006_REPAIR_DAEMON:"
    latest_repair="$(find "$FREYA_BASE/09_REPAIR_QUEUE" -type f -name 'FREYA_036_REPAIR_INDEX.psv' 2>/dev/null | sort | tail -n 1)"
    echo "LATEST_REPAIR_INDEX=$latest_repair"
    [ -f "$latest_repair" ] && cut -d'|' -f5 "$latest_repair" | tail -n +2 | sort | uniq -c | sort -nr
    echo

    echo "D007_HUMAN_GATE_DAEMON:"
    if [ -f "$FREYA_BASE/22_HUMAN_GATE_DECISION_CENTER/FREYA_HUMAN_GATE_DECISION_REGISTER.psv" ]; then
      echo "DECISIONS=$(($(wc -l < "$FREYA_BASE/22_HUMAN_GATE_DECISION_CENTER/FREYA_HUMAN_GATE_DECISION_REGISTER.psv") - 1))"
      tail -n 5 "$FREYA_BASE/22_HUMAN_GATE_DECISION_CENTER/FREYA_HUMAN_GATE_DECISION_REGISTER.psv"
    else
      echo "DECISION_REGISTER_MISSING"
    fi
    echo

    echo "D008_HEALTH_DAEMON:"
    df -h "$HOME" 2>/dev/null
    echo

    echo "CYCLE_OUTPUT=$SNAP"
    echo "CYCLE_STATUS=PASS_8_DAEMONS_REPORTED_NO_OLD_SCRIPT_RUN"
  } > "$SNAP"

  echo "DAEMON_SWARM_CYCLE=$cycle SNAPSHOT=$SNAP DATE=$(date)" >> "$LOG_FILE"

  LAST_COMPLETED_CYCLE="$cycle"

  cycle=$((cycle + 1))
  sleep 60
done

{
  echo "FREYA_DAEMON_SWARM_FINISHED=$(date)"
  echo "CYCLES_COMPLETED=$((cycle - 1))"
  echo "RUN_DIR=$RUN_DIR"
  echo "BACKGROUND_PROCESS_EXITED=YES"
} >> "$LOG_FILE"
