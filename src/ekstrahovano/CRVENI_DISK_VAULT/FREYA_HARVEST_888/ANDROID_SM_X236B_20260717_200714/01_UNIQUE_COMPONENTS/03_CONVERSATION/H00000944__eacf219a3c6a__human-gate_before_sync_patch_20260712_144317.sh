#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

HG="$HOME/HUMAN_GATE_COMMAND_CENTER"
FREYA_BASE="$HOME/HUMAN_GATE_TABLET_CONTROL/07_ANDROID_FREYA"
CAPTURE="$FREYA_BASE/00_CONTROL/FREYA_ANDROID_CAPTURE"
REPAIR_POINTER="$HOME/.freya_repair_current"

timestamp() {
    date '+%Y-%m-%dT%H:%M:%S%z'
}

safe_name() {
    printf '%s' "$1" |
    tr '[:lower:]' '[:upper:]' |
    tr -cs 'A-Z0-9._-' '_' |
    sed 's/^_*//;s/_*$//' |
    cut -c1-80
}

latest_files() {
    folder="$1"
    count="${2:-10}"

    if [ -d "$folder" ]; then
        find "$folder" -maxdepth 1 -type f -printf '%T@|%p\n' 2>/dev/null |
        sort -rn |
        head -n "$count" |
        cut -d'|' -f2-
    fi
}

show_policy_flags() {
    echo "HUMAN_GATE=ACTIVE"
    echo "DELETE=NO"
    echo "MOVE_ORIGINALS=NO"
    echo "RENAME_ORIGINALS=NO"
    echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
    echo "NEW_DAEMON_START=NO"
    echo "AUTO_INTERNET=NO"
    echo "AUTO_SEND=NO"
    echo "PUBLICATION=NO"
}

audit() {
    action="$1"
    detail="${2:-}"

    printf '%s|%s|%s|%s\n' \
        "$(timestamp)" \
        "Danijela_Djurovic_Keskin" \
        "$action" \
        "$detail" \
        >> "$HG/08_AUDIT_LOG/HUMAN_GATE_AUDIT.psv"
}

status_command() {
    echo "============================================================"
    echo "HUMAN GATE ANDROID STATUS"
    echo "============================================================"
    echo "UPDATED=$(timestamp)"
    echo "DEVICE_ROLE=PERSONAL_HUMAN_GATE_TERMINAL"
    echo "COMMAND_CENTER=$HG"
    echo

    show_policy_flags
    echo

    TASK_COUNT="$(find "$CAPTURE/tasks" -maxdepth 1 -type f 2>/dev/null | wc -l)"
    NOTE_COUNT="$(find "$CAPTURE/notes" -maxdepth 1 -type f 2>/dev/null | wc -l)"
    PROBLEM_COUNT="$(find "$CAPTURE/problems" -maxdepth 1 -type f 2>/dev/null | wc -l)"

    PENDING_COUNT="$(find "$HG/03_DECISIONS/PENDING" -maxdepth 1 -type f 2>/dev/null | wc -l)"
    APPROVED_COUNT="$(find "$HG/03_DECISIONS/APPROVED" -maxdepth 1 -type f 2>/dev/null | wc -l)"
    REJECTED_COUNT="$(find "$HG/03_DECISIONS/REJECTED" -maxdepth 1 -type f 2>/dev/null | wc -l)"
    HOLD_COUNT="$(find "$HG/03_DECISIONS/HOLD" -maxdepth 1 -type f 2>/dev/null | wc -l)"

    echo "FREYA_TASK_COUNT=$TASK_COUNT"
    echo "FREYA_NOTE_COUNT=$NOTE_COUNT"
    echo "FREYA_PROBLEM_COUNT=$PROBLEM_COUNT"
    echo "DECISIONS_PENDING=$PENDING_COUNT"
    echo "DECISIONS_APPROVED=$APPROVED_COUNT"
    echo "DECISIONS_REJECTED=$REJECTED_COUNT"
    echo "DECISIONS_HOLD=$HOLD_COUNT"
    echo

    if [ -f "$REPAIR_POINTER" ]; then
        BASE="$(cat "$REPAIR_POINTER" 2>/dev/null || true)"
        STATUS="$BASE/04_CONTROL/STATUS.txt"

        echo "=== CONTROLLED REPAIR DAEMON ==="

        if [ -f "$STATUS" ]; then
            sed -n \
              -e '/^STATE=/p' \
              -e '/^PID=/p' \
              -e '/^SCANNED=/p' \
              -e '/^COPIED_VERIFIED=/p' \
              -e '/^DUPLICATE_HASH_SKIPPED=/p' \
              -e '/^HOLD=/p' \
              -e '/^ERRORS=/p' \
              -e '/^EXTERNAL_FREE_GIB=/p' \
              -e '/^STOP_AT_LOCAL=/p' \
              "$STATUS"
        else
            echo "REPAIR_STATUS=STATUS_FILE_NOT_FOUND"
        fi
    else
        echo "REPAIR_DAEMON=NO_CURRENT_POINTER"
    fi

    echo
    echo "FINAL_STATUS=HUMAN_GATE_READY"
}

inbox_command() {
    echo "============================================================"
    echo "HUMAN GATE INBOX"
    echo "============================================================"

    echo
    echo "=== LATEST TASKS ==="
    latest_files "$CAPTURE/tasks" 10 | while IFS= read -r file; do
        [ -n "$file" ] || continue
        echo
        echo "FILE=$file"
        sed -n '1,20p' "$file"
    done

    echo
    echo "=== LATEST PROBLEMS ==="
    latest_files "$CAPTURE/problems" 5 | while IFS= read -r file; do
        [ -n "$file" ] || continue
        echo
        echo "FILE=$file"
        sed -n '1,20p' "$file"
    done

    echo
    echo "=== PENDING DECISIONS ==="
    latest_files "$HG/03_DECISIONS/PENDING" 20 | while IFS= read -r file; do
        [ -n "$file" ] || continue
        echo
        echo "FILE=$file"
        sed -n '1,40p' "$file"
    done

    audit "INBOX_VIEWED"
}

daemon_command() {
    echo "============================================================"
    echo "CONTROLLED REPAIR DAEMON — READ ONLY STATUS"
    echo "============================================================"

    if command -v freya-repair-status >/dev/null 2>&1; then
        freya-repair-status
    elif [ -f "$REPAIR_POINTER" ]; then
        BASE="$(cat "$REPAIR_POINTER")"
        cat "$BASE/04_CONTROL/STATUS.txt" 2>/dev/null ||
            echo "STATUS_FILE_NOT_FOUND"
    else
        echo "FINAL_STATUS=NO_CURRENT_REPAIR_DAEMON"
    fi

    echo
    echo "ACTION_PERFORMED=STATUS_READ_ONLY"
    echo "DAEMON_STARTED=NO"
    echo "DAEMON_STOPPED=NO"
}

case_command() {
    case_id="$(safe_name "${1:-}")"

    if [ -z "$case_id" ]; then
        echo "USAGE=hg case CASE_ID"
        exit 2
    fi

    case_dir="$HG/02_CASES/$case_id"

    if [ ! -d "$case_dir" ]; then
        echo "FINAL_STATUS=CASE_NOT_FOUND"
        echo "CASE_ID=$case_id"
        exit 1
    fi

    echo "============================================================"
    echo "HUMAN GATE CASE"
    echo "============================================================"

    find "$case_dir" -maxdepth 1 -type f -print | sort |
    while IFS= read -r file; do
        echo
        echo "=== $(basename "$file") ==="
        sed -n '1,220p' "$file"
    done

    audit "CASE_VIEWED" "$case_id"
}

new_case_command() {
    case_id="$(safe_name "${1:-}")"
    shift || true
    title="$*"

    if [ -z "$case_id" ] || [ -z "$title" ]; then
        echo 'USAGE=hg new-case CASE_ID "naziv predmeta"'
        exit 2
    fi

    case_dir="$HG/02_CASES/$case_id"
    mkdir -p "$case_dir"

    card="$case_dir/CASE_CARD.txt"

    if [ -f "$card" ]; then
        echo "FINAL_STATUS=CASE_ALREADY_EXISTS"
        echo "CASE=$case_dir"
        exit 1
    fi

    cat > "$card" <<EOF
HUMAN_GATE_CASE_CARD

CASE_ID=$case_id
TITLE=$title
CREATED_AT=$(timestamp)
CREATED_BY=Danijela_Djurovic_Keskin
STATUS=HUMAN_GATE_REVIEW_REQUIRED

KNOWN_FACTS:
- EVIDENCE_REQUIRED

EVIDENCE_AVAILABLE:
- TO_BE_REGISTERED

EVIDENCE_MISSING:
- TO_BE_REGISTERED

OPEN_QUESTIONS:
- TO_BE_REGISTERED

RISKS:
- Unsupported claim risk
- Deadline risk
- Incomplete evidence risk

NEXT_SAFE_ACTION:
- Review evidence and create one exact decision request.

HUMAN_GATE=ACTIVE
AUTO_SEND=NO
PUBLICATION=NO
EOF

    audit "CASE_CREATED" "$case_id|$title"

    echo "CASE_CREATED=$case_dir"
    echo "FINAL_STATUS=HUMAN_GATE_CASE_CREATED"
}

decision_command() {
    subject="${1:-}"
    shift || true
    scope="$*"

    if [ -z "$subject" ] || [ -z "$scope" ]; then
        echo 'USAGE=hg decision SUBJECT "tačan opseg odluke"'
        exit 2
    fi

    id="DECISION_$(date '+%Y%m%d_%H%M%S')_$(safe_name "$subject")"
    file="$HG/03_DECISIONS/PENDING/$id.txt"

    cat > "$file" <<EOF
HUMAN_GATE_DECISION_REQUEST

DECISION_ID=$id
CREATED_AT=$(timestamp)
CREATED_BY=Danijela_Djurovic_Keskin
STATUS=PENDING

SUBJECT=$subject
EXACT_SCOPE=$scope

EVIDENCE_REFERENCES:
- REQUIRED

PERMITTED_ACTION:
- NOT_YET_APPROVED

PROHIBITED_ACTIONS:
- delete
- move originals
- rename originals
- execute scripts from evidence
- start new daemon
- automatic internet
- automatic send
- publication

DECISION_EFFECT:
Governance record only.
No external or machine action is executed by this record.

HUMAN_GATE=Danijela_Djurovic_Keskin
EOF

    audit "DECISION_REQUEST_CREATED" "$id|$subject"

    echo "DECISION_REQUEST=$file"
    echo "STATUS=PENDING"
    echo "FINAL_STATUS=DECISION_RECORDED_PENDING_REVIEW"
}

set_decision_status() {
    target_status="$1"
    decision_id="$(safe_name "${2:-}")"
    shift 2 || true
    reason="$*"

    if [ -z "$decision_id" ] || [ -z "$reason" ]; then
        echo "USAGE=hg $(printf '%s' "$target_status" | tr '[:upper:]' '[:lower:]') DECISION_ID \"reason\""
        exit 2
    fi

    source="$HG/03_DECISIONS/PENDING/$decision_id.txt"
    destination="$HG/03_DECISIONS/$target_status/$decision_id.txt"

    if [ ! -f "$source" ]; then
        echo "FINAL_STATUS=PENDING_DECISION_NOT_FOUND"
        echo "EXPECTED=$source"
        exit 1
    fi

    {
        cat "$source"
        echo
        echo "FINAL_DECISION_STATUS=$target_status"
        echo "DECIDED_AT=$(timestamp)"
        echo "DECIDED_BY=Danijela_Djurovic_Keskin"
        echo "DECISION_REASON=$reason"
        echo "EXECUTION_TRIGGERED=NO"
        echo "AUTO_SEND=NO"
        echo "PUBLICATION=NO"
    } > "$destination"

    rm -f "$source"

    audit "DECISION_STATUS_CHANGED" "$decision_id|$target_status|$reason"

    echo "DECISION_RECORD=$destination"
    echo "STATUS=$target_status"
    echo "EXECUTION_TRIGGERED=NO"
    echo "FINAL_STATUS=HUMAN_GATE_DECISION_RECORDED"
}

today_command() {
    focus="$HG/05_DAILY_FOCUS/DAILY_FOCUS_$(date '+%Y%m%d').txt"

    latest_task="$(latest_files "$CAPTURE/tasks" 1 || true)"
    pending_count="$(find "$HG/03_DECISIONS/PENDING" -maxdepth 1 -type f 2>/dev/null | wc -l)"

    {
        echo "HUMAN_GATE_DAILY_FOCUS"
        echo "DATE=$(date '+%Y-%m-%d')"
        echo "UPDATED=$(timestamp)"
        echo
        echo "PRIMARY_RULE=ONE_EVIDENCE_ONE_TASK_ONE_DECISION"
        echo
        echo "LATEST_FREYA_TASK=${latest_task:-NONE}"
        echo "PENDING_DECISIONS=$pending_count"
        echo
        echo "TODAY_PRIORITY:"
        echo "1. Preserve current controlled repair daemon."
        echo "2. Review Civil Engineering case intake."
        echo "3. Attach evidence references."
        echo "4. Record one exact Human Gate decision."
        echo
        echo "NO_DELETE=YES"
        echo "NO_MOVE_ORIGINALS=YES"
        echo "NO_NEW_DAEMON_START=YES"
        echo "NO_AUTO_SEND=YES"
        echo "NO_PUBLICATION=YES"
    } > "$focus"

    cat "$focus"
    audit "DAILY_FOCUS_VIEWED"
}

help_command() {
    cat <<'EOF'
HUMAN GATE COMMANDS

  hg status
      Trenutno stanje Human Gate sistema i repair daemona.

  hg inbox
      Posljednji FREYA taskovi, problemi i odluke na čekanju.

  hg daemon
      READ_ONLY status postojećeg repair daemona.

  hg today
      Jedan dnevni Human Gate fokus.

  hg new-case CASE_ID "naziv predmeta"
      Kreira Human Gate predmet bez izvršenja akcija.

  hg case CASE_ID
      Prikazuje predmet.

  hg decision SUBJECT "tačan opseg odluke"
      Kreira PENDING zahtjev za odluku.

  hg approve DECISION_ID "razlog"
  hg reject DECISION_ID "razlog"
  hg hold DECISION_ID "razlog"
      Evidentira odluku, ali ništa automatski ne izvršava.

  hg help
EOF
}

command="${1:-status}"
shift || true

case "$command" in
    status)
        status_command
        ;;
    inbox)
        inbox_command
        ;;
    daemon)
        daemon_command
        ;;
    today)
        today_command
        ;;
    new-case)
        new_case_command "$@"
        ;;
    case)
        case_command "$@"
        ;;
    decision)
        decision_command "$@"
        ;;
    approve)
        set_decision_status "APPROVED" "$@"
        ;;
    reject)
        set_decision_status "REJECTED" "$@"
        ;;
    hold)
        set_decision_status "HOLD" "$@"
        ;;
    help|--help|-h)
        help_command
        ;;
    *)
        echo "UNKNOWN_COMMAND=$command"
        help_command
        exit 2
        ;;
esac
