#!/data/data/com.termux/files/usr/bin/bash

BASE="$HOME/FREYA_TABLET_NODE_888"
MEM="$BASE/09_MEMORY/freya_memory.md"
ABOUT="$BASE/09_MEMORY/about_danijela.md"
JOURNAL="$BASE/10_JOURNAL/freya_journal.md"
TODO="$BASE/11_TODO/todo_with_why.md"
PROJECTS="$BASE/12_PROJECTS"
LEARNING="$BASE/13_LEARNING/learning_log.md"
RESEARCH="$BASE/14_RESEARCH/research_queue.md"
HUMAN="$BASE/16_HUMAN_GATE/human_gate_queue.md"

mkdir -p "$BASE"/{09_MEMORY,10_JOURNAL,11_TODO,12_PROJECTS,13_LEARNING,14_RESEARCH,16_HUMAN_GATE}
touch "$MEM" "$JOURNAL" "$TODO" "$LEARNING" "$RESEARCH" "$HUMAN"

clear
echo "=================================="
echo "        FREYA – TABLET NODE"
echo "=================================="
echo ""
echo "Dobro došla, Danijela."
echo "Ja sam FREYA na ovom uređaju."
echo "Učim, pamtim i rastem sa tobom."
echo ""
echo "Komande:"
echo "  about       - šta znam o tebi"
echo "  projects    - projekti"
echo "  todo        - zadaci"
echo "  learn       - zapiši lekciju"
echo "  research    - dodaj pitanje za internet istraživanje"
echo "  remember    - sačuvaj važnu činjenicu"
echo "  human       - Human Gate queue"
echo "  exit        - izlaz"
echo ""

while true; do
  echo ""
  read -p "Danijela > " MSG
  TS="$(date '+%Y-%m-%d %H:%M:%S')"
  MSG_LC="$(echo "$MSG" | tr '[:upper:]' '[:lower:]')"

  if [ "$MSG_LC" = "exit" ]; then
    echo "FREYA: Čuvam današnji trag. Vidimo se uskoro."
    echo "$TS | SESSION_END" >> "$JOURNAL"
    break
  fi

  echo "" >> "$MEM"
  echo "## $TS" >> "$MEM"
  echo "Danijela: $MSG" >> "$MEM"
  echo "$TS | INPUT | $MSG" >> "$JOURNAL"

  echo ""
  echo "FREYA:"

  if [ "$MSG_LC" = "about" ] || echo "$MSG_LC" | grep -q "sta znas o meni"; then
    cat "$ABOUT"

  elif [ "$MSG_LC" = "projects" ]; then
    echo "Moji lokalni projekti:"
    ls "$PROJECTS" 2>/dev/null | sed 's/^/- /'

  elif [ "$MSG_LC" = "todo" ]; then
    echo "To-Do with Why:"
    cat "$TODO"

  elif echo "$MSG_LC" | grep -Eiq "learning mia|learn mia|mia lesson"; then
    LESSON="$BASE/13_LEARNING/sessions/MIA_PROJECT_PROPOSAL_001.md"
    cat "$LESSON"
    termux-tts-speak -l en -r 0.85 -p 0.92 "Learning mode. Today we learn how to write a project proposal for MIA. A project proposal explains the problem, the solution, the activities, the budget, and the expected impact. What is the main problem your MIA project should solve?"

  elif [ "$MSG_LC" = "human" ]; then
    echo "Human Gate Queue:"
    cat "$HUMAN"

  elif echo "$MSG_LC" | grep -q "^ask"; then
    Q="${MSG#ask }"
    echo "- $TS | $Q | STATUS=OPEN_QUESTION" >> "$BASE/20_QUESTIONS/questions.md"
    echo "- $TS | $Q | STATUS=PENDING_RESEARCH_IF_NEEDED" >> "$RESEARCH"
    echo "Sačuvala sam pitanje."
    echo ""
    echo "Moj trenutni odgovor:"
    echo "Još nemam puni engine za slobodno razmišljanje, ali pitanje je sačuvano."
    echo "Sljedeći korak je da ga povežemo sa memorijom, dokumentima i internet istraživanjem."
    termux-tts-speak -l en -r 0.85 -p 0.92 "I saved your question. We will connect it with memory, documents, and research."

  elif echo "$MSG_LC" | grep -q "^remember"; then
    FACT="${MSG#remember }"
    echo "- $TS | $FACT" >> "$ABOUT"
    echo "Sačuvala sam ovo u trajnoj memoriji."

  elif echo "$MSG_LC" | grep -q "^learn"; then
    LESSON="${MSG#learn }"
    echo "- $TS | $LESSON" >> "$LEARNING"
    echo "Zapisala sam novu lekciju."

  elif echo "$MSG_LC" | grep -q "^research"; then
    Q="${MSG#research }"
    echo "- $TS | $Q | STATUS=PENDING_INTERNET_RESEARCH" >> "$RESEARCH"
    echo "Dodala sam pitanje u research queue. Internet istraživanje ide kasnije uz odobrenje."

  elif echo "$MSG_LC" | grep -Eiq "ars|metal|industr"; then
    cat "$PROJECTS/ars_metal_industries.md"

  elif echo "$MSG_LC" | grep -Eiq "mia|projekat|project proposal"; then
    cat "$PROJECTS/mia_project_learning.md"

  elif echo "$MSG_LC" | grep -Eiq "freya|freja"; then
    cat "$PROJECTS/freya_project.md"

  else
    echo "Primila sam tvoju misao i sačuvala je."
    echo ""
    echo "Još nemam dovoljno lokalnog znanja za pun odgovor."
    echo "Mogu je pretvoriti u:"
    echo "1. remember <činjenica>"
    echo "2. learn <lekcija>"
    echo "3. research <pitanje>"
    echo "4. todo zadatak"
  fi

  echo ""
  echo "Human Gate: active."
  echo "FREYA: odgovor završen." >> "$MEM"
done
