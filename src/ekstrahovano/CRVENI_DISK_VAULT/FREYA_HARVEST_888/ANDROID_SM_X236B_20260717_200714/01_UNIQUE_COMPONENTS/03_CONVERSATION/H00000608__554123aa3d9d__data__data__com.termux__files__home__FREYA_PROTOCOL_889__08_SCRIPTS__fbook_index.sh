#!/data/data/com.termux/files/usr/bin/bash
BOOK="$HOME/storage/shared/Documents/FREYA_TABLET_ASSISTANT/07_PERSONAL/FREYA_BOOK_VAULT"
INDEX="$BOOK/02_SCENE_INDEX/BOOK_INDEX.md"

mkdir -p "$BOOK/02_SCENE_INDEX"

{
  echo "# FREYA BOOK — SCENE INDEX"
  echo ""
  echo "UPDATED=$(date)"
  echo ""
  echo "## RAW SCENES"
  echo ""
  find "$BOOK/01_RAW_SCENES" -type f -name '*.md' | sort | while read -r F; do
    TITLE="$(head -1 "$F" 2>/dev/null | sed 's/^# //')"
    echo "- $TITLE"
    echo "  - FILE=$F"
  done
} > "$INDEX"

cat "$INDEX"
