#!/data/data/com.termux/files/usr/bin/bash
BASE="$HOME/FREYA_PROTOCOL_889"
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M:%S)"
DEC="$BASE/04_DECISIONS/DECISIONS_$DATE.md"

mkdir -p "$BASE/04_DECISIONS"

if command -v termux-dialog >/dev/null 2>&1; then
  D="$(termux-dialog text -t "FREYA Decision" 2>/dev/null | jq -r '.text // empty' 2>/dev/null)"
else
  echo "Upiši odluku:"
  read -r D
fi

[ -n "$D" ] || exit 0

echo "| $TIME | $D | Pending reason | Medium | ACTIVE |" >> "$DEC"

termux-notification --title "FREYA Decision logged" --content "$D" 2>/dev/null || true
echo "DECISION_SAVED=$DEC"
