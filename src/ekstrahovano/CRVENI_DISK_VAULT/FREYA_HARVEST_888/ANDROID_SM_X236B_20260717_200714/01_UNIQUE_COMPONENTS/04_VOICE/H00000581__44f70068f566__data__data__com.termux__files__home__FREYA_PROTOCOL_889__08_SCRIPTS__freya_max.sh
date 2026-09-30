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
  "$BASE/12_RESEARCH" \
  "$BASE/13_CLIPBOARD" \
  "$BASE/14_AGENDA" \
  "$BASE/15_MAX_REPORTS" \
  "$PUBLIC/04_MORNING_BRIEF" \
  "$PUBLIC/08_SOURCE_ANSWERS" \
  "$PUBLIC/99_SYSTEM_STATUS"

DAILY="$BASE/01_DAILY/DAILY_$DATE.md"
INBOX="$BASE/02_INBOX/INBOX_$DATE.md"
TASKS="$BASE/03_TASKS/TASKS_$DATE.md"
DECISIONS="$BASE/04_DECISIONS/DECISIONS_$DATE.md"
BRIEF="$BASE/05_MORNING_BRIEF/TITAN_GRID_MORNING_BRIEF_$DATE.md"
MEMORY="$BASE/10_INTELLIGENCE/FREYA_889_MEMORY_INDEX.tsv"
SOURCES="$BASE/12_RESEARCH/SOURCE_LIST.tsv"
RAW="$BASE/12_RESEARCH/RAW_RESEARCH_$DATE.txt"
ANALYSIS="$BASE/12_RESEARCH/RESEARCH_ANALYSIS_$DATE.md"
MAXREPORT="$BASE/15_MAX_REPORTS/FREYA_889_MAX_REPORT_$DATE.md"
DASH="$PUBLIC/99_SYSTEM_STATUS/FREYA_889_MAX_DASHBOARD.md"

ensure_files() {
  [ -f "$DAILY" ] || echo "# DAILY JOURNAL — $DATE" > "$DAILY"
  [ -f "$INBOX" ] || echo "# INBOX — $DATE" > "$INBOX"
  [ -f "$TASKS" ] || echo "# TASKS — $DATE" > "$TASKS"
  [ -f "$DECISIONS" ] || {
    echo "# DECISIONS — $DATE" > "$DECISIONS"
    echo "| Time | Decision | Why | Risk | Human Gate |" >> "$DECISIONS"
    echo "|---|---|---|---|---|" >> "$DECISIONS"
  }
  [ -f "$BRIEF" ] || echo "# TITAN GRID MORNING BRIEF — $DATE" > "$BRIEF"

  [ -f "$SOURCES" ] || cat > "$SOURCES" <<EOS
TYPENAMEURLKEYWORDS
QUERYTITAN GRID AI governancehttps://news.google.com/rss/search?q=AI+governance+digital+governance+compliance+automationtitan,ai,governance,compliance
QUERYEBRD EIB industrial financehttps://news.google.com/rss/search?q=EBRD+EIB+industrial+finance+energy+infrastructureebrd,eib,finance,industry
QUERYsmart contract governancehttps://news.google.com/rss/search?q=smart+contract+governance+compliancesmart,contract,governance
QUERYdata room investmenthttps://news.google.com/rss/search?q=investor+data+room+due+diligence+industrialdata,room,investor,diligence
QUERYMontenegro investment energyhttps://news.google.com/rss/search?q=Montenegro+investment+energy+infrastructuremontenegro,investment,energy
EOS
}

classify() {
  TXT="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
  CATEGORY="GENERAL"
  PRIORITY="NORMAL"
  RISK="LOW"
  HG="NO"

  echo "$TXT" | grep -Eiq 'ars|metal|cfo|investitor|bank|ebrd|eib|data room|due diligence' && CATEGORY="ARS_CFO"
  echo "$TXT" | grep -Eiq 'freya|titan|grid|ai governance|digital governance|compliance|smart contract|daemon|protocol|protokol' && CATEGORY="FREYA_SYSTEM"
  echo "$TXT" | grep -Eiq 'urgent|hitno|deadline|risk|regulation|law|legal|compliance|sanction|security' && PRIORITY="HIGH"
  echo "$TXT" | grep -Eiq 'delete|bris|uninstall|runtime|repair|execute|pokreni|public claim|endorsement|certification' && RISK="HIGH"
  echo "$TXT" | grep -Eiq 'decision|odluka|approve|odobri|contract|ugovor|investor|public|runtime|delete|human gate' && HG="YES"

  echo "$CATEGORY|$PRIORITY|$RISK|$HG"
}

memory_add() {
  TYPE="$1"
  TEXT="$2"
  META="$3"
  HASH="$(printf "%s|%s|%s|%s" "$DATE" "$TIME" "$TYPE" "$TEXT" | sha256sum | cut -d' ' -f1)"
  printf "%s\t%s\t%s\t%s\t%s\n" "$DATE" "$TIME" "$TYPE" "$HASH" "$TEXT | $META" >> "$MEMORY"
}

cmd_capture() {
  ensure_files
  TXT="$*"
  [ -n "$TXT" ] || { echo 'Usage: fcapture "text"'; exit 0; }
  META="$(classify "$TXT")"

  {
    echo ""
    echo "## $TIME — CAPTURE"
    echo "TEXT=$TXT"
    echo "META=$META"
  } >> "$INBOX"

  memory_add "CAPTURE" "$TXT" "$META"
  echo "CAPTURED: $META"
}

cmd_clip() {
  ensure_files
  if command -v termux-clipboard-get >/dev/null 2>&1; then
    TXT="$(termux-clipboard-get 2>/dev/null)"
  else
    TXT=""
  fi

  [ -n "$TXT" ] || { echo "CLIPBOARD_EMPTY_OR_NOT_ALLOWED"; exit 0; }

  META="$(classify "$TXT")"

  {
    echo ""
    echo "## $TIME — CLIPBOARD CAPTURE"
    echo "$TXT"
    echo ""
    echo "META=$META"
  } >> "$BASE/13_CLIPBOARD/CLIPBOARD_$DATE.md"

  memory_add "CLIPBOARD" "$TXT" "$META"
  echo "CLIPBOARD_CAPTURED: $META"
}

cmd_agenda() {
  ensure_files
  OUT="$BASE/14_AGENDA/AGENDA_$DATE.md"

  HIGH="$(grep -i 'priority=HIGH\|PRIORITY=HIGH' "$TASKS" "$INBOX" 2>/dev/null | tail -20)"
  HG="$(grep -Ri 'human_gate=YES\|HUMAN_GATE_NEEDED=YES' "$BASE/02_INBOX" "$BASE/03_TASKS" "$BASE/04_DECISIONS" 2>/dev/null | tail -20)"
  DEC="$(tail -20 "$DECISIONS" 2>/dev/null)"

  cat > "$OUT" <<EOD
# 🟣 FREYA 889 AGENDA — $DATE

## 1. Today Focus

- Pregledati HIGH taskove
- Pregledati Human Gate signale
- Napraviti sync za Lenovo
- Ne dirati master fajlove

## 2. High Priority

$HIGH

## 3. Human Gate

$HG

## 4. Latest Decisions

$DEC

## 5. Safe Status

DELETE=NO
UNINSTALL=NO
MASTER_EDIT=NO
RUNTIME_ON_USER_FILES=NO
HUMAN_GATE=ACTIVE
EOD

  cp "$OUT" "$PUBLIC/99_SYSTEM_STATUS/" 2>/dev/null || true
  cat "$OUT"
}

cmd_research() {
  ensure_files
  : > "$RAW"

  echo "FREYA 889 PUBLIC RESEARCH RUN — $DATE $TIME" >> "$RAW"
  echo "MODE=PUBLIC_SOURCE_FETCH_ONLY" >> "$RAW"
  echo "DELETE=NO MASTER_EDIT=NO HUMAN_GATE=ACTIVE" >> "$RAW"
  echo "" >> "$RAW"

  while IFS=$'\t' read -r TYPE NAME URL KEYS; do
    [ "$TYPE" = "TYPE" ] && continue
    [ -z "$URL" ] && continue

    echo "" >> "$RAW"
    echo "===== SOURCE: $NAME =====" >> "$RAW"
    echo "URL=$URL" >> "$RAW"
    echo "KEYWORDS=$KEYS" >> "$RAW"

    if command -v curl >/dev/null 2>&1; then
      curl -L --max-time 20 --silent "$URL" \
        | sed 's/<[^>]*>/ /g' \
        | tr -s ' ' \
        | head -80 >> "$RAW" 2>/dev/null || echo "FETCH_FAILED" >> "$RAW"
    else
      echo "CURL_NOT_AVAILABLE" >> "$RAW"
    fi
  done < "$SOURCES"

  echo "RESEARCH_RAW_CREATED=$RAW"
}

cmd_analyze() {
  ensure_files
  [ -f "$RAW" ] || "$0" research

  AI_COUNT="$(grep -Eic 'ai|governance|compliance|regulation|digital' "$RAW" 2>/dev/null || echo 0)"
  FIN_COUNT="$(grep -Eic 'ebrd|eib|investment|finance|bank|infrastructure' "$RAW" 2>/dev/null || echo 0)"
  DATA_COUNT="$(grep -Eic 'data room|due diligence|investor|document' "$RAW" 2>/dev/null || echo 0)"
  RISK_COUNT="$(grep -Eic 'risk|law|regulation|security|sanction|compliance' "$RAW" 2>/dev/null || echo 0)"

  TOP_LINES="$(grep -Ein 'ai|governance|compliance|ebrd|eib|data room|due diligence|smart contract|montenegro|investment|infrastructure' "$RAW" 2>/dev/null | head -40)"

  cat > "$ANALYSIS" <<EOD
# 🟣 FREYA 889 RESEARCH ANALYSIS — $DATE

STATUS=LOCAL_PUBLIC_SOURCE_ANALYSIS
MODE=REPORT_ONLY
PUBLIC_FETCH=YES
DELETE=NO
MASTER_EDIT=NO
HUMAN_GATE=ACTIVE

## Signal Counts

AI_GOVERNANCE_SIGNALS=$AI_COUNT
FINANCE_INFRASTRUCTURE_SIGNALS=$FIN_COUNT
DATA_ROOM_SIGNALS=$DATA_COUNT
RISK_REGULATION_SIGNALS=$RISK_COUNT

## Extracted Signals

$TOP_LINES

## FREYA Interpretation

- Ako su AI governance/compliance signali visoki: TITAN GRID positioning treba pojačati kao governance/compliance architecture.
- Ako su EBRD/EIB/infrastructure signali visoki: ARS/Data Room treba držati spreman za institutional due diligence.
- Ako su Data Room signali visoki: prioritet je canonical evidence register i investor-facing packet.
- Ako su risk/regulation signali visoki: Human Gate mora pregledati prije bilo kakve javne tvrdnje.

## Human Gate Required

- Nema claim-a o partnerstvu, certifikaciji, odobrenju ili validaciji bez dokaza.
- Nema runtime nad master fajlovima.
- Nema brisanja kopija dok Lenovo canonical sync nije potvrđen.
EOD

  cp "$ANALYSIS" "$PUBLIC/08_SOURCE_ANSWERS/" 2>/dev/null || true
  cat "$ANALYSIS"
}

cmd_morning() {
  ensure_files
  "$0" agenda >/dev/null 2>&1 || true
  "$0" analyze >/dev/null 2>&1 || true

  AGENDA="$BASE/14_AGENDA/AGENDA_$DATE.md"

  cat > "$MAXREPORT" <<EOD
# 🟣 FREYA 889 MAX MORNING BRIEF — $DATE

STATUS=MAX_ANDROID_REPORT
MODE=PUBLIC_RESEARCH_PLUS_LOCAL_MEMORY
DELETE=NO
UNINSTALL=NO
MASTER_EDIT=NO
RUNTIME_ON_USER_FILES=NO
HUMAN_GATE=ACTIVE

## 1. Executive Summary

Android tablet sada radi kao FREYA field console: dnevnik, inbox, taskovi, odluke, clipboard capture, public research watcher, agenda, local analysis, morning brief i Lenovo sync queue.

## 2. Local Agenda

$(cat "$AGENDA" 2>/dev/null)

## 3. Public Research Analysis

$(cat "$ANALYSIS" 2>/dev/null)

## 4. Recommended Next Actions

- Pregledati Human Gate stavke.
- Otvoriti Mac kao CFO/Human Gate kontrolu.
- Prebaciti sync packet na Lenovo kao canonical brain.
- Na Mac-u napraviti Desktop Drop folder.
- Ne pokretati destructive cleanup.
- Ne pokretati user scripts.

## 5. Final Android Role

ANDROID=FREYA_PERSONAL_ASSISTANT_AND_FIELD_CONSOLE
LENOVO=CANONICAL_BRAIN_AND_RESEARCH_SERVER
MAC=CFO_HUMAN_GATE_CONTROL
EOD

  cp "$MAXREPORT" "$BRIEF" 2>/dev/null || true
  cp "$MAXREPORT" "$PUBLIC/04_MORNING_BRIEF/" 2>/dev/null || true

  termux-notification --title "🟣 FREYA MAX Brief" --content "Max morning brief created." 2>/dev/null || true

  echo "MAX_MORNING_BRIEF_CREATED=$MAXREPORT"
  cat "$MAXREPORT"
}

cmd_dash() {
  ensure_files

  NOTES="$(grep -Rci 'SMART NOTE\|CAPTURE' "$BASE/02_INBOX" 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')"
  TASKS_COUNT="$(grep -Rci '^- \[ \]' "$BASE/03_TASKS" 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')"
  HG="$(grep -Rih 'human_gate=YES\|HUMAN_GATE_NEEDED=YES' "$BASE/02_INBOX" "$BASE/03_TASKS" "$BASE/04_DECISIONS" 2>/dev/null | wc -l | tr -d ' ')"
  PACKETS="$(find "$BASE/06_SYNC_TO_LENOVO_QUEUE" -type f -name '*.tar.gz' 2>/dev/null | wc -l | tr -d ' ')"

  cat > "$DASH" <<EOD
# 🟣 FREYA 889 MAX DASHBOARD

DATE=$DATE
TIME=$TIME
STATUS=ACTIVE
LEVEL=MAX_ANDROID_SAFE
HUMAN_GATE=ACTIVE

## COUNTS

CAPTURES_AND_NOTES=$NOTES
TASKS=$TASKS_COUNT
HUMAN_GATE_SIGNALS=$HG
SYNC_PACKETS=$PACKETS

## MAX COMMANDS

\`\`\`bash
fmax
fcapture "tekst"
fclip
fagenda
fresearch
fanalyze
fmorning
fsearch "tema"
fdash
fsync
\`\`\`

## SAFE BOUNDARY

ANDROID DOES:
- capture
- classify
- brief
- notify
- public-source fetch
- sync packet

ANDROID DOES NOT:
- delete
- uninstall
- edit master
- run user scripts
- repair systems
- make public claims
EOD

  cp "$DASH" "$PUBLIC/99_SYSTEM_STATUS/" 2>/dev/null || true
  cat "$DASH"
}

cmd_sync() {
  ensure_files
  TS="$(date +%Y%m%d_%H%M%S)"
  OUT="$BASE/06_SYNC_TO_LENOVO_QUEUE/FREYA_889_MAX_SYNC_PACKET_$TS.tar.gz"

  tar -czf "$OUT" \
    -C "$BASE" \
    00_STATUS 01_DAILY 02_INBOX 03_TASKS 04_DECISIONS 05_MORNING_BRIEF 06_SYNC_TO_LENOVO_QUEUE 07_LOGS 09_THEME 10_INTELLIGENCE 11_REPORTS 12_RESEARCH 13_CLIPBOARD 14_AGENDA 15_MAX_REPORTS

  sha256sum "$OUT" > "$OUT.sha256"

  echo "MAX_SYNC_PACKET_CREATED=$OUT"
  cat "$OUT.sha256"
}

cmd_help() {
  cat <<EOD
🟣 FREYA 889 MAX V3

fmax
  pokaži maximum meni

fcapture "tekst"
  pametni capture + klasifikacija

fclip
  uhvati clipboard

fagenda
  napravi dnevnu agendu

fresearch
  povuci javne izvore iz SOURCE_LIST.tsv

fanalyze
  analiziraj javne izvore + signale

fmorning
  napravi MAX morning brief

fsearch "tema"
  pretraži FREYA memoriju

fdash
  pokaži MAX dashboard

fsync
  napravi MAX sync packet za Lenovo
EOD
}

cmd_search() {
  Q="$*"
  [ -n "$Q" ] || { echo 'Usage: fsearch "tema"'; exit 0; }
  grep -Rin -- "$Q" "$BASE" 2>/dev/null | head -80
}

ensure_files

ACTION="$1"
shift || true

case "$ACTION" in
  capture) cmd_capture "$@" ;;
  clip) cmd_clip ;;
  agenda) cmd_agenda ;;
  research) cmd_research ;;
  analyze) cmd_analyze ;;
  morning) cmd_morning ;;
  dash) cmd_dash ;;
  sync) cmd_sync ;;
  search) cmd_search "$@" ;;
  help|"") cmd_help ;;
  *) echo "UNKNOWN_ACTION=$ACTION"; cmd_help ;;
esac
