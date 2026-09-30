#!/data/data/com.termux/files/usr/bin/bash
BOOK="$HOME/storage/shared/Documents/FREYA_TABLET_ASSISTANT/07_PERSONAL/FREYA_BOOK_VAULT"
DATE="$(date +%Y-%m-%d)"
BRIEF="$BOOK/06_BOOK_BRIEFS/FREYA_BOOK_BRIEF_$DATE.md"

mkdir -p "$BOOK/06_BOOK_BRIEFS"

SCENE_COUNT="$(find "$BOOK/01_RAW_SCENES" -type f -name '*.md' | wc -l | tr -d ' ')"

{
  echo "# FREYA BOOK BRIEF — $DATE"
  echo ""
  echo "STATUS=BOOK_VAULT_ACTIVE"
  echo "SCENE_COUNT=$SCENE_COUNT"
  echo "HUMAN_GATE=ACTIVE"
  echo ""
  echo "## ŠTA IMAMO"
  echo ""
  find "$BOOK/01_RAW_SCENES" -type f -name '*.md' | sort | tail -20 | while read -r F; do
    echo "- $(head -1 "$F" | sed 's/^# //')"
  done
  echo ""
  echo "## SLJEDEĆE"
  echo ""
  echo "- Nastaviti pisati raw scene."
  echo "- Ne sređivati prerano."
  echo "- Ne brisati."
  echo "- Kad bude 10 scena, pravimo prvu strukturu poglavlja."
} > "$BRIEF"

cat "$BRIEF"
