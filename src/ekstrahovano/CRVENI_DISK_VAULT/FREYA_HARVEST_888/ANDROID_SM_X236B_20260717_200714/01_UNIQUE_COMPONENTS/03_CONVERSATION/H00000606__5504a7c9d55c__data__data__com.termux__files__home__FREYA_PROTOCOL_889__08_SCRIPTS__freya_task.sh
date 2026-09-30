#!/data/data/com.termux/files/usr/bin/bash
BASE="$HOME/FREYA_PROTOCOL_889"
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M:%S)"
TASKS="$BASE/03_TASKS/TASKS_$DATE.md"

mkdir -p "$BASE/03_TASKS"

if command -v termux-dialog >/dev/null 2>&1; then
  TASK="$(termux-dialog text -t "FREYA New Task" 2>/dev/null | jq -r '.text // empty' 2>/dev/null)"
else
  echo "Upiši task:"
  read -r TASK
fi

[ -n "$TASK" ] || exit 0

{
  echo ""
  echo "- [ ] $TASK  <!-- $TIME -->"
} >> "$TASKS"

termux-notification --title "FREYA Task added" --content "$TASK" 2>/dev/null || true
echo "TASK_SAVED=$TASKS"
