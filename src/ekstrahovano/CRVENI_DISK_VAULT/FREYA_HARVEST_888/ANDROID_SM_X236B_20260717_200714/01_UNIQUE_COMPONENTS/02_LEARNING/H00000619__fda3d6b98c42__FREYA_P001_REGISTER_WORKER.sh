#!/data/data/com.termux/files/usr/bin/sh

FREYA_BASE="$HOME/HUMAN_GATE_TABLET_CONTROL/07_ANDROID_FREYA"
BG_DIR="$FREYA_BASE/28_BACKGROUND_PRODUCTION_CONTROL"

PID_FILE="$BG_DIR/FREYA_P001_REGISTER_WORKER.pid"
STATE_FILE="$BG_DIR/FREYA_P001_REGISTER_WORKER.state"
STOP_FILE="$BG_DIR/STOP_P001_REGISTER_WORKER.flag"
LOG_FILE="$BG_DIR/FREYA_P001_REGISTER_WORKER.log"
RUNS_DIR="$BG_DIR/P001_RUNS"

mkdir -p "$BG_DIR" "$RUNS_DIR"

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
    OLD_CMDLINE="$(
        tr '\0' ' ' < "/proc/$OLD_PID/cmdline" 2>/dev/null
    )"

    case "$OLD_CMDLINE" in
        *FREYA_P001_REGISTER_WORKER.sh*)
            {
                echo "P001_START_BLOCKED=$(date)"
                echo "REASON=ALREADY_RUNNING"
                echo "EXISTING_PID=$OLD_PID"
                echo "EXISTING_CMDLINE=$OLD_CMDLINE"
            } >> "$LOG_FILE"

            {
                echo "WORKER=P001_REGISTER_WORKER"
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
        echo "P001_START_BLOCKED=$(date)"
        echo "REASON=STOP_FILE_PRESENT"
        echo "STOP_FILE=$STOP_FILE"
    } >> "$LOG_FILE"

    {
        echo "WORKER=P001_REGISTER_WORKER"
        echo "STATE=BLOCKED_STOP_FILE_PRESENT"
        echo "STOP_FILE=$STOP_FILE"
        echo "CHECKED_AT=$(date)"
    } > "$STATE_FILE"

    exit 75
fi

RUN_ID="P001_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$RUNS_DIR/$RUN_ID"

mkdir -p "$RUN_DIR"

STARTED_AT="$(date)"
EXIT_REASON="UNSPECIFIED"
LAST_COMPLETED_CYCLE=0
PID_FILE_CLEARED="NO"

cleanup_p001() {
    EXIT_CODE="$?"

    trap - 0

    if [ "$EXIT_REASON" = "UNSPECIFIED" ]; then
        if [ "$EXIT_CODE" -eq 0 ]; then
            EXIT_REASON="NORMAL_COMPLETION"
        else
            EXIT_REASON="UNEXPECTED_EXIT"
        fi
    fi

    CURRENT_PID_CONTENT="$(
        tr -d '[:space:]' < "$PID_FILE" 2>/dev/null
    )"

    if [ "$CURRENT_PID_CONTENT" = "$$" ]; then
        : > "$PID_FILE"
        PID_FILE_CLEARED="YES"
    else
        PID_FILE_CLEARED="NO_PID_OWNERSHIP_MISMATCH"
    fi

    {
        echo "P001_RUNTIME_CLEANUP=$(date)"
        echo "RUN_ID=$RUN_ID"
        echo "PID=$$"
        echo "EXIT_CODE=$EXIT_CODE"
        echo "EXIT_REASON=$EXIT_REASON"
        echo "LAST_COMPLETED_CYCLE=$LAST_COMPLETED_CYCLE"
        echo "PID_FILE_CLEARED=$PID_FILE_CLEARED"
    } >> "$LOG_FILE"

    {
        echo "WORKER=P001_REGISTER_WORKER"
        echo "STATE=STOPPED"
        echo "RUN_ID=$RUN_ID"
        echo "LAST_PID=$$"
        echo "STARTED_AT=$STARTED_AT"
        echo "STOPPED_AT=$(date)"
        echo "EXIT_CODE=$EXIT_CODE"
        echo "EXIT_REASON=$EXIT_REASON"
        echo "LAST_COMPLETED_CYCLE=$LAST_COMPLETED_CYCLE"
        echo "PID_FILE=$PID_FILE"
        echo "PID_FILE_CLEARED=$PID_FILE_CLEARED"
    } > "$STATE_FILE"

    exit "$EXIT_CODE"
}

trap cleanup_p001 0

trap '
    EXIT_REASON=SIGNAL_HUP
    echo "P001_SIGNAL_HUP=$(date)" >> "$LOG_FILE"
    exit 129
' 1

trap '
    EXIT_REASON=SIGNAL_INT
    echo "P001_SIGNAL_INT=$(date)" >> "$LOG_FILE"
    exit 130
' 2

trap '
    EXIT_REASON=SIGNAL_TERM
    echo "P001_SIGNAL_TERM=$(date)" >> "$LOG_FILE"
    exit 143
' 15

printf '%s\n' "$$" > "$PID_FILE"

{
    echo "WORKER=P001_REGISTER_WORKER"
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
    echo "FREYA_BACKGROUND_P001_STARTED=$(date)"
    echo "RUN_ID=$RUN_ID"
    echo "PID=$$"
    echo "HUMAN_GATE=ACTIVE"
    echo "MODE=FINITE_REGISTER_OBSERVER"
    echo "MAX_CYCLES=20"
    echo "SLEEP_SECONDS=60"
    echo "DELETE=NO"
    echo "MOVE_ORIGINALS=NO"
    echo "RENAME_ORIGINALS=NO"
    echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
    echo "RUN_OLD_SCRIPTS=NO"
    echo "AUTO_INTERNET=NO"
    echo "AUTO_SEND=NO"
    echo "NO_PUBLICATION=YES"
    echo "PID_LIFECYCLE_CONTROL=ENABLED"
    echo "DUPLICATE_START_PROTECTION=ENABLED"
    echo "DEDICATED_P001_NAMESPACE=YES"
} >> "$LOG_FILE"

cycle=1
max_cycles=20

while [ "$cycle" -le "$max_cycles" ]; do
    if [ -f "$STOP_FILE" ]; then
        EXIT_REASON="STOP_FILE_DETECTED"
        echo "P001_STOP_FILE_DETECTED=$(date)" >> "$LOG_FILE"
        break
    fi

    SNAP="$RUN_DIR/P001_SNAPSHOT_${cycle}.txt"

    {
        echo "FREYA_P001_REGISTER_PRODUCER_SNAPSHOT"
        echo "DATE=$(date)"
        echo "CYCLE=$cycle/$max_cycles"
        echo "HUMAN_GATE=ACTIVE"
        echo "WORKER_MODE=FINITE_REGISTER_OBSERVER"
        echo "BACKGROUND=YES_LIMITED"
        echo "DELETE=NO"
        echo "MOVE_ORIGINALS=NO"
        echo "RENAME_ORIGINALS=NO"
        echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
        echo "RUN_OLD_SCRIPTS=NO"
        echo "AUTO_INTERNET=NO"
        echo "AUTO_SEND=NO"
        echo "NO_PUBLICATION=YES"
        echo

        echo "DEVICE_SPACE:"
        df -h "$HOME" 2>/dev/null
        echo

        echo "TASK_STATUS:"

        if [ -f "$FREYA_BASE/14_TASK_SYSTEM/FREYA_TASK_REGISTER.psv" ]; then
            echo "TASKS=$(($(wc -l < "$FREYA_BASE/14_TASK_SYSTEM/FREYA_TASK_REGISTER.psv") - 1))"

            cut -d'|' -f4 \
                "$FREYA_BASE/14_TASK_SYSTEM/FREYA_TASK_REGISTER.psv" |
                tail -n +2 |
                sort |
                uniq -c |
                sort -nr
        else
            echo "TASK_REGISTER_MISSING"
        fi

        echo
        echo "QUEUE_STATUS:"

        if [ -f "$FREYA_BASE/17_QUEUE_SYSTEM/FREYA_QUEUE_REGISTER.psv" ]; then
            echo "QUEUE_ITEMS=$(($(wc -l < "$FREYA_BASE/17_QUEUE_SYSTEM/FREYA_QUEUE_REGISTER.psv") - 1))"

            cut -d'|' -f7 \
                "$FREYA_BASE/17_QUEUE_SYSTEM/FREYA_QUEUE_REGISTER.psv" |
                tail -n +2 |
                sort |
                uniq -c |
                sort -nr
        else
            echo "QUEUE_REGISTER_MISSING"
        fi

        echo
        echo "DOCUMENT_CLASSIFICATION:"

        CLASS_REGISTER="$FREYA_BASE/25_DOCUMENT_CLASSIFICATION_SYSTEM/FREYA_DOCUMENT_CLASSIFICATION_REGISTER.psv"

        if [ -f "$CLASS_REGISTER" ]; then
            echo "CLASSIFICATION_RECORDS=$(($(wc -l < "$CLASS_REGISTER") - 1))"

            cut -d'|' -f9 "$CLASS_REGISTER" |
                tail -n +2 |
                sort |
                uniq -c |
                sort -nr
        else
            echo "CLASSIFICATION_REGISTER_MISSING"
        fi

        echo
        echo "KNOWLEDGE_CARDS:"

        find "$FREYA_BASE/24_DOCUMENT_KNOWLEDGE_CARDS" \
            -maxdepth 1 \
            -type f \
            -name 'KNOWLEDGE_CARD_*.txt' \
            2>/dev/null |
            wc -l |
            awk '{print "KNOWLEDGE_CARD_COUNT=" $1}'

        echo
        echo "REPAIR_STATUS:"

        latest_repair="$(
            find "$FREYA_BASE/09_REPAIR_QUEUE" \
                -type f \
                -name 'FREYA_036_REPAIR_INDEX.psv' \
                -print 2>/dev/null |
                sort |
                tail -n 1
        )"

        echo "LATEST_REPAIR_INDEX=$latest_repair"

        if [ -f "$latest_repair" ]; then
            cut -d'|' -f5 "$latest_repair" |
                tail -n +2 |
                sort |
                uniq -c |
                sort -nr
        fi

        echo
        echo "PRODUCTION_RECOMMENDATION:"
        echo "1. Keep background production limited."
        echo "2. Do not run old or imported scripts."
        echo "3. Keep P001 and P002 control namespaces separate."
        echo "4. Disk usage is high; avoid heavy archive extraction."
        echo
        echo "SNAPSHOT_STATUS=PASS"
    } > "$SNAP"

    LAST_COMPLETED_CYCLE="$cycle"

    echo "P001_CYCLE=$cycle SNAPSHOT=$SNAP DATE=$(date)" >> "$LOG_FILE"

    cycle=$((cycle + 1))

    if [ "$cycle" -le "$max_cycles" ]; then
        sleep 60
    fi
done

{
    echo "FREYA_BACKGROUND_P001_FINISHED=$(date)"
    echo "CYCLES_COMPLETED=$LAST_COMPLETED_CYCLE"
    echo "RUN_DIR=$RUN_DIR"
    echo "BACKGROUND_PROCESS_EXITED=YES"
    echo "EXIT_REASON=$EXIT_REASON"
} >> "$LOG_FILE"
