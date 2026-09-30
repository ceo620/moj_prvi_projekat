#!/data/data/com.termux/files/usr/bin/bash
BOOK="$HOME/storage/shared/Documents/FREYA_TABLET_ASSISTANT/07_PERSONAL/FREYA_BOOK_VAULT"
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M:%S)"
TEXT="$*"

mkdir -p "$BOOK/01_RAW_SCENES" "$BOOK/02_SCENE_INDEX" "$BOOK/03_QUOTES"

if [ -z "$TEXT" ]; then
  echo 'Upotreba: fbook "tekst scene ili misli"'
  exit 0
fi

COUNT="$(find "$BOOK/01_RAW_SCENES" -type f -name 'SCENA_*.md' | wc -l | tr -d ' ')"
NEXT="$(printf "%03d" $((COUNT + 1)))"
FILE="$BOOK/01_RAW_SCENES/SCENA_${NEXT}_RAW_${DATE}.md"

cat > "$FILE" <<EOD
# SCENA $NEXT — RAW

DATUM=$DATE
TIME=$TIME
STATUS=RAW_SCENE
FREYA_REVIEW=WAITING
HUMAN_GATE=ACTIVE

## RAW TEXT

$TEXT

## FREYA NOTES

- Theme: pending
- Chapter candidate: pending
- Strongest sentence: pending
- Risk/legal sensitivity: pending

EOD

echo "$DATE" $TIME SCENA_$NEXT$FILERAW" >> "$BOOK/02_SCENE_INDEX/SCENE_INDEX.tsv"

echo "BOOK_SCENE_CREATED=$FILE"
