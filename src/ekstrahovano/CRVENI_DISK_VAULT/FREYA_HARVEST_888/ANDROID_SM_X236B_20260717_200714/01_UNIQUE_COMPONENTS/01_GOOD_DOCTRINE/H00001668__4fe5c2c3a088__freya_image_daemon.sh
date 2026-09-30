#!/data/data/com.termux/files/usr/bin/bash

SRC="$HOME/storage/pictures/Screenshots"
BASE="$HOME/HUMAN_GATE_TABLET_CONTROL/07_ANDROID_FREYA/17_MARKETING"
DEST="$BASE/02_SCREENSHOTS"
HASH="$BASE/03_SHA256"
LOG="$BASE/04_LOGS/daemon.log"

mkdir -p "$DEST" "$HASH" "$(dirname "$LOG")"

while true; do
    find "$SRC" -maxdepth 1 -type f \
      \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) \
      -mmin +1 -print0 2>/dev/null |
    while IFS= read -r -d '' FILE; do
        SUM="$(sha256sum "$FILE" | awk '{print $1}')"
        EXT="${FILE##*.}"
        TARGET="$DEST/${SUM}.${EXT,,}"

        if [ ! -f "$TARGET" ]; then
            cp -p "$FILE" "$TARGET" &&
            printf '%s  %s\n' "$SUM" "$TARGET" > "$HASH/${SUM}.sha256" &&
            printf '%s COPIED_VERIFIED source=%q target=%q sha256=%s\n' \
              "$(date '+%F %T')" "$FILE" "$TARGET" "$SUM" >> "$LOG"
        fi
    done

    sleep 60
done
