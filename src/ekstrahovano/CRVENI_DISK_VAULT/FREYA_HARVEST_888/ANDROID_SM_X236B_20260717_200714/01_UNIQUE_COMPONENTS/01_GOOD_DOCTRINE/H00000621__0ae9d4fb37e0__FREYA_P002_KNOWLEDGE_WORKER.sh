#!/data/data/com.termux/files/usr/bin/sh

FREYA_BASE="$HOME/HUMAN_GATE_TABLET_CONTROL/07_ANDROID_FREYA"
BG_DIR="$FREYA_BASE/28_BACKGROUND_PRODUCTION_CONTROL"

PID_FILE="$BG_DIR/FREYA_BACKGROUND_PRODUCER.pid"
STATE_FILE="$BG_DIR/FREYA_BACKGROUND_PRODUCER.state"
STOP_FILE="$BG_DIR/STOP_BACKGROUND_PRODUCTION.flag"
LOG_FILE="$BG_DIR/FREYA_BACKGROUND_PRODUCTION.log"

mkdir -p "$BG_DIR"

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
        *FREYA_P002_KNOWLEDGE_WORKER.sh*)
            {
                echo "P002_START_BLOCKED=$(date)"
                echo "REASON=ALREADY_RUNNING"
                echo "EXISTING_PID=$OLD_PID"
                echo "EXISTING_CMDLINE=$OLD_CMDLINE"
            } >> "$LOG_FILE"

            {
                echo "WORKER=P002_KNOWLEDGE_WORKER"
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
        echo "P002_START_BLOCKED=$(date)"
        echo "REASON=STOP_FILE_PRESENT"
        echo "STOP_FILE=$STOP_FILE"
    } >> "$LOG_FILE"

    {
        echo "WORKER=P002_KNOWLEDGE_WORKER"
        echo "STATE=BLOCKED_STOP_FILE_PRESENT"
        echo "STOP_FILE=$STOP_FILE"
        echo "CHECKED_AT=$(date)"
    } > "$STATE_FILE"

    exit 75
fi

RUN_ID="P002_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$BG_DIR/RUNS/$RUN_ID"
KNOWLEDGE_OUT="$RUN_DIR/KNOWLEDGE_BATCHES"

mkdir -p "$RUN_DIR" "$KNOWLEDGE_OUT"

STARTED_AT="$(date)"
EXIT_REASON="UNSPECIFIED"
LAST_COMPLETED_CYCLE=0

cleanup_p002() {
    EXIT_CODE="$?"

    trap - 0

    {
        echo "P002_RUNTIME_CLEANUP=$(date)"
        echo "RUN_ID=$RUN_ID"
        echo "PID=$$"
        echo "EXIT_CODE=$EXIT_CODE"
        echo "EXIT_REASON=$EXIT_REASON"
        echo "LAST_COMPLETED_CYCLE=$LAST_COMPLETED_CYCLE"
        echo "PID_FILE_CLEARED=YES"
    } >> "$LOG_FILE"

    {
        echo "WORKER=P002_KNOWLEDGE_WORKER"
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

trap cleanup_p002 0

trap '
    EXIT_REASON=SIGNAL_HUP
    echo "P002_SIGNAL_HUP=$(date)" >> "$LOG_FILE"
    exit 129
' 1

trap '
    EXIT_REASON=SIGNAL_INT
    echo "P002_SIGNAL_INT=$(date)" >> "$LOG_FILE"
    exit 130
' 2

trap '
    EXIT_REASON=SIGNAL_TERM
    echo "P002_SIGNAL_TERM=$(date)" >> "$LOG_FILE"
    exit 143
' 15

printf '%s\n' "$$" > "$PID_FILE"

{
    echo "WORKER=P002_KNOWLEDGE_WORKER"
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
    echo "FREYA_BACKGROUND_P002_STARTED=$STARTED_AT"
    echo "RUN_ID=$RUN_ID"
    echo "PID=$$"
    echo "HUMAN_GATE=ACTIVE"
    echo "MODE=LIMITED_BACKGROUND_KNOWLEDGE_PRODUCER"
    echo "DELETE=NO"
    echo "MOVE_ORIGINALS=NO"
    echo "RENAME_ORIGINALS=NO"
    echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
    echo "AUTO_INTERNET=NO"
    echo "AUTO_SEND=NO"
    echo "NO_PUBLICATION=YES"
    echo "RUN_4000_OLD_SCRIPTS=NO"
    echo "PID_LIFECYCLE_CONTROL=ENABLED"
    echo "DUPLICATE_START_PROTECTION=ENABLED"
} >> "$LOG_FILE"

SCRIPT_GOV="$(
    find "$FREYA_BASE/09_REPAIR_QUEUE" \
        -type f \
        -name 'FREYA_020_SCRIPT_GOVERNANCE_REGISTER.psv' \
        2>/dev/null |
    sort |
    tail -n 1
)"

CLASS_REG="$FREYA_BASE/25_DOCUMENT_CLASSIFICATION_SYSTEM/FREYA_DOCUMENT_CLASSIFICATION_REGISTER.psv"
KNOWLEDGE_MASTER="$FREYA_BASE/24_DOCUMENT_KNOWLEDGE_CARDS/FREYA_DOCUMENT_KNOWLEDGE_MASTER_INDEX.psv"

cycle=1
max_cycles=20
batch_size=50

while [ "$cycle" -le "$max_cycles" ]; do
    if [ -f "$STOP_FILE" ]; then
        EXIT_REASON="STOP_FILE_DETECTED"
        echo "P002_STOP_FILE_DETECTED=$(date)" >> "$LOG_FILE"
        break
    fi

    SNAP="$RUN_DIR/P002_LEARNING_SNAPSHOT_${cycle}.txt"
    BATCH="$KNOWLEDGE_OUT/P002_BATCH_${cycle}.psv"

    {
        echo "FREYA_P002_BACKGROUND_KNOWLEDGE_SNAPSHOT"
        echo "DATE=$(date)"
        echo "CYCLE=$cycle/$max_cycles"
        echo "HUMAN_GATE=ACTIVE"
        echo "BACKGROUND=YES_LIMITED"
        echo "DELETE=NO"
        echo "MOVE_ORIGINALS=NO"
        echo "RENAME_ORIGINALS=NO"
        echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
        echo "AUTO_INTERNET=NO"
        echo "AUTO_SEND=NO"
        echo "NO_PUBLICATION=YES"
        echo
        echo "SOURCE_REGISTERS:"
        echo "SCRIPT_GOV=$SCRIPT_GOV"
        echo "SCRIPT_GOV_EXISTS=$([ -f "$SCRIPT_GOV" ] && echo YES || echo NO)"
        echo "CLASS_REG=$CLASS_REG"
        echo "CLASS_REG_EXISTS=$([ -f "$CLASS_REG" ] && echo YES || echo NO)"
        echo "KNOWLEDGE_MASTER=$KNOWLEDGE_MASTER"
        echo "KNOWLEDGE_MASTER_EXISTS=$([ -f "$KNOWLEDGE_MASTER" ] && echo YES || echo NO)"
        echo
        echo "DOCUMENT_CLASSIFICATION_COUNTS:"

        if [ -f "$CLASS_REG" ]; then
            cut -d'|' -f9 "$CLASS_REG" |
                tail -n +2 |
                sort |
                uniq -c |
                sort -nr
        else
            echo "CLASS_REG_NOT_FOUND"
        fi

        echo
        echo "KNOWLEDGE_CARD_COUNT:"

        find "$FREYA_BASE/24_DOCUMENT_KNOWLEDGE_CARDS" \
            -maxdepth 1 \
            -type f \
            -name 'KNOWLEDGE_CARD_*.txt' \
            2>/dev/null |
        wc -l

        echo
        echo "SCRIPT_GOVERNANCE_SAMPLE_LEARNING:"
    } > "$SNAP"

    echo "LEARN_ID|DATE|SOURCE_TYPE|GOVERNANCE_CLASS|RUN_PERMISSION|PATCH_PERMISSION|SOURCE_PATH|LEARNING_STATUS|NEXT_SAFE_ACTION" > "$BATCH"

    if [ -f "$SCRIPT_GOV" ]; then
        start=$(( (cycle - 1) * batch_size + 2 ))
        end=$(( start + batch_size - 1 ))
        row=0

        sed -n "${start},${end}p" "$SCRIPT_GOV" |
        while IFS='|' read -r a b c d e f g h i j k l m rest; do
            row=$((row + 1))
            source_path="$rest"

            if [ -z "$source_path" ]; then
                source_path="$m"
            fi

            learn_id="LEARN_${cycle}_$(date +%H%M%S)_${row}"

            echo "$learn_id|$(date)|SCRIPT_GOVERNANCE_STATIC|$e|$f|$g|$source_path|LEARNED_AS_STATIC_RECORD_NO_RUN|CLASSIFY_OR_REPAIR_LAB_COPY_ONLY" >> "$BATCH"
        done
    fi

    {
        echo "BATCH_FILE=$BATCH"
        echo "BATCH_RECORDS=$(($(wc -l < "$BATCH") - 1))"
        echo "BATCH_PREVIEW:"
        sed -n '1,20p' "$BATCH"
        echo
        echo "P002_STATUS=PASS_CYCLE_CREATED_STATIC_LEARNING_BATCH"
    } >> "$SNAP"

    LAST_COMPLETED_CYCLE="$cycle"

    echo "P002_CYCLE=$cycle SNAPSHOT=$SNAP BATCH=$BATCH DATE=$(date)" >> "$LOG_FILE"

    cycle=$((cycle + 1))

    if [ "$cycle" -le "$max_cycles" ]; then
        sleep 60
    fi
done

if [ "$EXIT_REASON" = "UNSPECIFIED" ]; then
    EXIT_REASON="NORMAL_COMPLETION"
fi

{
    echo "FREYA_BACKGROUND_P002_FINISHED=$(date)"
    echo "CYCLES_COMPLETED=$LAST_COMPLETED_CYCLE"
    echo "RUN_DIR=$RUN_DIR"
    echo "BACKGROUND_PROCESS_EXITED=YES"
    echo "EXIT_REASON=$EXIT_REASON"
} >> "$LOG_FILE"

exit 0
