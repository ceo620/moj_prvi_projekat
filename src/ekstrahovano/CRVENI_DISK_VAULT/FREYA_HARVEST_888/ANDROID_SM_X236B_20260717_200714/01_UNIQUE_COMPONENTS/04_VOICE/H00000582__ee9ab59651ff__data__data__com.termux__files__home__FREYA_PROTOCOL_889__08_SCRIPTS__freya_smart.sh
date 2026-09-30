#!/data/data/com.termux/files/usr/bin/bash

BASE="$HOME/FREYA_PROTOCOL_889"
PUBLIC="$HOME/storage/shared/Documents/FREYA_TABLET_ASSISTANT"
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M:%S)"

mkdir -p \
  "$BASE/01_DAILY" \
  "$BASE/02_INBOX" \
  "$BASE/03_TASKS" \
  "$BASE/04_DECISIONS" \
  "$BASE/05_MORNING_BRIEF" \
  "$BASE/06_SYNC_TO_LENOVO_QUEUE" \
  "$BASE/10_INTELLIGENCE" \
  "$BASE/11_REPORTS" \
  "$PUBLIC/99_SYSTEM_STATUS"

DAILY="$BASE/01_DAILY/DAILY_$DATE.md"
INBOX="$BASE/02_INBOX/INBOX_$DATE.md"
TASKS="$BASE/03_TASKS/TASKS_$DATE.md"
DECISIONS="$BASE/04_DECISIONS/DECISIONS_$DATE.md"
BRIEF="$BASE/05_MORNING_BRIEF/TITAN_GRID_MORNING_BRIEF_$DATE.md"
MEMORY="$BASE/10_INTELLIGENCE/FREYA_889_MEMORY_INDEX.tsv"
DASH="$PUBLIC/99_SYSTEM_STATUS/FREYA_889_SMART_DASHBOARD.md"

ensure_files() {
  [ -f "$DAILY" ] || echo "# DAILY JOURNAL — $DATE" > "$DAILY"
  [ -f "$INBOX" ] || echo "# INBOX — $DATE" > "$INBOX"
  [ -f "$TASKS" ] || echo "# TASKS — $DATE" > "$TASKS"
  [ -f "$DECISIONS" ] || {
    echo "# DECISIONS — $DATE" > "$DECISIONS"
    echo "| Time | Decision | Why | Risk | Human Gate |" >> "$DECISIONS"
    echo "|---|---|---|---|---|" >> "$DECISIONS"
  }
  [ -f "$BRIEF" ] || {
    echo "# TITAN GRID MORNING BRIEF — $DATE" > "$BRIEF"
    echo "" >> "$BRIEF"
    echo "STATUS=DRAFT_CREATED_BY_FREYA_889" >> "$BRIEF"
    echo "HUMAN_GATE=ACTIVE" >> "$BRIEF"
  }
}

classify_text() {
  TXT="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

  CATEGORY="GENERAL"
  PRIORITY="NORMAL"
  RISK="LOW"
  HUMAN_GATE="NO"

  echo "$TXT" | grep -Eiq 'ars|metal|cfo|ugovor|anex|investitor|bank|eib|ebrd|data room' && CATEGORY="ARS_CFO"
  echo "$TXT" | grep -Eiq 'freya|titan|grid|daemon|protokol|lenovo|android|mac|msi|ssot' && CATEGORY="FREYA_SYSTEM"
  echo "$TXT" | grep -Eiq 'hitno|urgent|odmah|rok|danas|sjutra|deadline' && PRIORITY="HIGH"
  echo "$TXT" | grep -Eiq 'bris|delete|uninstall|move|rename|repair|runtime|pokreni|demon' && RISK="HIGH"
  echo "$TXT" | grep -Eiq 'odobri|odluka|human gate|ugovor|bris|delete|runtime|investitor|javna objava|public' && HUMAN_GATE="YES"

  echo "$CATEGORY|$PRIORITY|$RISK|$HUMAN_GATE"
}

add_memory() {
  TYPE="$1"
  TEXT="$2"
  META="$3"
  HASH="$(printf "%s|%s|%s|%s" "$DATE" "$TIME" "$TYPE" "$TEXT" | sha256sum | cut -d' ' -f1)"
  printf "%s\t%s\t%s\t%s\t%s\n" "$DATE" "$TIME" "$TYPE" "$HASH" "$TEXT | $META" >> "$MEMORY"
}

cmd_note() {
  ensure_files
  TEXT="$*"
  [ -n "$TEXT" ] || {
    echo "Upotreba: fnote \"tekst bilješke\""
    exit 0
  }

  META="$(classify_text "$TEXT")"
  CATEGORY="$(echo "$META" | cut -d'|' -f1)"
  PRIORITY="$(echo "$META" | cut -d'|' -f2)"
  RISK="$(echo "$META" | cut -d'|' -f3)"
  HG="$(echo "$META" | cut -d'|' -f4)"

  {
    echo ""
    echo "## $TIME — SMART NOTE"
    echo "TEXT=$TEXT"
    echo "CATEGORY=$CATEGORY"
    echo "PRIORITY=$PRIORITY"
    echo "RISK=$RISK"
    echo "HUMAN_GATE_NEEDED=$HG"
  } >> "$INBOX"

  add_memory "NOTE" "$TEXT" "$META"

  termux-notification --title "🟣 FREYA Note" --content "$CATEGORY / $PRIORITY / HG=$HG" 2>/dev/null || true
  echo "NOTE_SAVED"
  echo "CATEGORY=$CATEGORY PRIORITY=$PRIORITY RISK=$RISK HUMAN_GATE=$HG"
}

cmd_task() {
  ensure_files
  TEXT="$*"
  [ -n "$TEXT" ] || {
    echo "Upotreba: ftask \"tekst zadatka\""
    exit 0
  }

  META="$(classify_text "$TEXT")"
  CATEGORY="$(echo "$META" | cut -d'|' -f1)"
  PRIORITY="$(echo "$META" | cut -d'|' -f2)"
  RISK="$(echo "$META" | cut -d'|' -f3)"
  HG="$(echo "$META" | cut -d'|' -f4)"

  {
    echo ""
    echo "- [ ] $TEXT  <!-- time=$TIME category=$CATEGORY priority=$PRIORITY risk=$RISK human_gate=$HG -->"
  } >> "$TASKS"

  add_memory "TASK" "$TEXT" "$META"

  termux-notification --title "🟣 FREYA Task" --content "$PRIORITY / $CATEGORY" 2>/dev/null || true
  echo "TASK_SAVED"
  echo "CATEGORY=$CATEGORY PRIORITY=$PRIORITY RISK=$RISK HUMAN_GATE=$HG"
}

cmd_decision() {
  ensure_files
  TEXT="$*"
  [ -n "$TEXT" ] || {
    echo "Upotreba: fdecision \"tekst odluke\""
    exit 0
  }

  META="$(classify_text "$TEXT")"
  CATEGORY="$(echo "$META" | cut -d'|' -f1)"
  PRIORITY="$(echo "$META" | cut -d'|' -f2)"
  RISK="$(echo "$META" | cut -d'|' -f3)"
  HG="$(echo "$META" | cut -d'|' -f4)"

  echo "| $TIME | $TEXT | category=$CATEGORY priority=$PRIORITY | $RISK | ACTIVE |" >> "$DECISIONS"
  add_memory "DECISION" "$TEXT" "$META"

  termux-notification --title "🟣 FREYA Decision" --content "Risk=$RISK / HG=$HG" 2>/dev/null || true
  echo "DECISION_SAVED"
  echo "CATEGORY=$CATEGORY PRIORITY=$PRIORITY RISK=$RISK HUMAN_GATE=$HG"
}

cmd_brief() {
  ensure_files

  REPORT="$BASE/11_REPORTS/FREYA_889_INTELLIGENT_BRIEF_$DATE.md"

  HIGH_TASKS="$(grep -i 'priority=HIGH' "$TASKS" 2>/dev/null | tail -10)"
  HG_ITEMS="$(grep -i 'human_gate=YES\|HUMAN_GATE_NEEDED=YES' "$INBOX" "$TASKS" "$DECISIONS" 2>/dev/null | tail -20)"
  SYSTEM_ITEMS="$(grep -i 'FREYA_SYSTEM\|titan\|freya\|daemon\|protokol\|lenovo' "$INBOX" "$TASKS" "$DECISIONS" 2>/dev/null | tail -20)"
  ARS_ITEMS="$(grep -i 'ARS_CFO\|ars\|metal\|cfo\|eib\|ebrd\|data room' "$INBOX" "$TASKS" "$DECISIONS" 2>/dev/null | tail -20)"

  cat > "$REPORT" <<EOD
# 🟣 FREYA 889 INTELLIGENT BRIEF — $DATE

STATUS=LOCAL_INTELLIGENCE_SUMMARY
MODE=REPORT_ONLY
DELETE=NO
MASTER_EDIT=NO
HUMAN_GATE=ACTIVE

## 1. Executive Summary

FREYA 889 je aktivna kao Android 24h personalni asistent.  
Danas prati bilješke, zadatke, odluke, rizike, Human Gate signale i sync paket za Lenovo.

## 2. High Priority Tasks

$HIGH_TASKS

## 3. Human Gate Items

$HG_ITEMS

## 4. FREYA / TITAN GRID Signals

$SYSTEM_ITEMS

## 5. ARS / CFO / Data Room Signals

$ARS_ITEMS

## 6. Recommended Next Actions

- Pregledati Human Gate stavke.
- Završiti najvažnije HIGH taskove.
- Napraviti sync packet za Lenovo.
- Ne pokretati runtime nad master fajlovima.
- Ne brisati i ne čistiti dok Lenovo canonical sync nije potvrđen.

## 7. Safe Status

DELETE=NO  
UNINSTALL=NO  
MOVE=NO  
RENAME=NO  
MASTER_EDIT=NO  
RUNTIME_ON_USER_FILES=NO  
SCRIPT_EXECUTION_OF_USER_FILES=NO  
HUMAN_GATE=ACTIVE
EOD

  cp "$REPORT" "$BRIEF" 2>/dev/null || true
  cp "$REPORT" "$PUBLIC/04_MORNING_BRIEF/" 2>/dev/null || true

  echo "INTELLIGENT_BRIEF_CREATED=$REPORT"
  cat "$REPORT"
}

cmd_search() {
  ensure_files
  Q="$*"
  [ -n "$Q" ] || {
    echo "Upotreba: fsearch \"riječ ili tema\""
    exit 0
  }

  echo "=== FREYA SEARCH: $Q ==="
  grep -Rin -- "$Q" "$BASE/01_DAILY" "$BASE/02_INBOX" "$BASE/03_TASKS" "$BASE/04_DECISIONS" "$BASE/05_MORNING_BRIEF" "$BASE/10_INTELLIGENCE" 2>/dev/null | head -50
}

cmd_dashboard() {
  ensure_files

  NOTE_COUNT="$(grep -c 'SMART NOTE' "$INBOX" 2>/dev/null || echo 0)"
  TASK_COUNT="$(grep -c '^- \[ \]' "$TASKS" 2>/dev/null || echo 0)"
  DECISION_COUNT="$(grep -c '^|' "$DECISIONS" 2>/dev/null || echo 0)"
  HG_COUNT="$(grep -Rih 'human_gate=YES\|HUMAN_GATE_NEEDED=YES' "$BASE/02_INBOX" "$BASE/03_TASKS" "$BASE/04_DECISIONS" 2>/dev/null | wc -l | tr -d ' ')"

  cat > "$DASH" <<EOD
# 🟣 FREYA 889 SMART DASHBOARD

DATE=$DATE
TIME=$TIME
STATUS=ACTIVE
MODE=ANDROID_24H_PERSONAL_ASSISTANT
HUMAN_GATE=ACTIVE

## COUNTS

NOTES_TODAY=$NOTE_COUNT  
TASKS_TODAY=$TASK_COUNT  
DECISION_LINES=$DECISION_COUNT  
HUMAN_GATE_SIGNALS=$HG_COUNT  

## SMART COMMANDS

\`\`\`bash
f889
fnote "tekst"
ftask "tekst"
fdecision "tekst"
fbrief
fsearch "tema"
fdash
fsync
\`\`\`

## SAFE RULES

DELETE=NO  
UNINSTALL=NO  
MASTER_EDIT=NO  
RUNTIME_ON_USER_FILES=NO  
SCRIPT_EXECUTION_OF_USER_FILES=NO  
HUMAN_GATE=ACTIVE
EOD

  cat "$DASH"
}

cmd_sync() {
  ensure_files
  TS="$(date +%Y%m%d_%H%M%S)"
  OUT="$BASE/06_SYNC_TO_LENOVO_QUEUE/FREYA_889_SMART_SYNC_PACKET_$TS.tar.gz"

  tar -czf "$OUT" \
    -C "$BASE" \
    00_STATUS 01_DAILY 02_INBOX 03_TASKS 04_DECISIONS 05_MORNING_BRIEF 07_LOGS 09_THEME 10_INTELLIGENCE 11_REPORTS

  sha256sum "$OUT" > "$OUT.sha256"

  echo "SMART_SYNC_PACKET_CREATED=$OUT"
  cat "$OUT.sha256"
}

cmd_health() {
  PIDFILE="$BASE/00_STATUS/freya_889.pid"
  STATUS="$BASE/00_STATUS/PROTOCOL_889_STATUS.txt"
  LOG="$BASE/07_LOGS/freya_889_daemon.log"

  echo "=== 🟣 FREYA 889 SMART HEALTH ==="
  echo "TIME=$(date)"
  echo "PID=$(cat "$PIDFILE" 2>/dev/null)"
  ps -p "$(cat "$PIDFILE" 2>/dev/null)" >/dev/null 2>&1 && echo "DAEMON_RUNNING=YES" || echo "DAEMON_RUNNING=NO"
  echo ""
  cat "$STATUS" 2>/dev/null
  echo ""
  echo "--- LAST LOG ---"
  tail -10 "$LOG" 2>/dev/null
}

cmd_help() {
  cat <<EOD
🟣 FREYA 889 INTELLIGENCE V2

Komande:

f889
  health check

fnote "tekst"
  pametna bilješka + klasifikacija

ftask "tekst"
  pametni task + prioritet

fdecision "tekst"
  odluka + risk/Human Gate signal

fbrief
  napravi inteligentni lokalni brief

fsearch "tema"
  pretraži FREYA 889 memoriju

fdash
  dashboard

fsync
  napravi sync packet za Lenovo

fhelp
  pomoć
EOD
}

ensure_files

ACTION="$1"
shift || true

case "$ACTION" in
  note) cmd_note "$@" ;;
  task) cmd_task "$@" ;;
  decision) cmd_decision "$@" ;;
  brief) cmd_brief ;;
  search) cmd_search "$@" ;;
  dash) cmd_dashboard ;;
  sync) cmd_sync ;;
  health) cmd_health ;;
  help|"") cmd_help ;;
  *) echo "UNKNOWN_ACTION=$ACTION"; cmd_help ;;
esac
