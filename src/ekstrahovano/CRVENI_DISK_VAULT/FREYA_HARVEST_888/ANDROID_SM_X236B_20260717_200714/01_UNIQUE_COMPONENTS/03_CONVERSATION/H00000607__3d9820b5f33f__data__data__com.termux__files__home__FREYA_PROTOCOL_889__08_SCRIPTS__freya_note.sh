#!/data/data/com.termux/files/usr/bin/bash
BASE="$HOME/FREYA_PROTOCOL_889"
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M:%S)"
INBOX="$BASE/02_INBOX/INBOX_$DATE.md"

mkdir -p "$BASE/02_INBOX"

if command -v termux-dialog >/dev/null 2>&1; then
  NOTE="$(termux-dialog text -t "FREYA Quick Note" 2>/dev/null | jq -r '.text // empty' 2>/dev/null)"
else
  echo "Upiši note:"
  read -r NOTE
fi

[ -n "$NOTE" ] || exit 0

{
  echo ""
  echo "## $TIME"
  echo "$NOTE"
} >> "$INBOX"

termux-notification --title "FREYA Note saved" --content "$NOTE" 2>/dev/null || true
echo "NOTE_SAVED=$INBOX"
