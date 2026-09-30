#!/data/data/com.termux/files/usr/bin/bash

BASE="$HOME/FREYA_NOTIFIER_KNOWLEDGE_OVEN"
WATCH="$BASE/WATCH_PATHS.tsv"
SEEN="$BASE/SEEN_PRODUCTS.tsv"
LOG="$BASE/NOTIFICATION_LOG.tsv"

notify_freya() {
  TITLE="$1"
  MSG="$2"

  if command -v termux-notification >/dev/null 2>&1; then
    termux-notification \
      --title "$TITLE" \
      --content "$MSG" \
      --priority high \
      --id 888
  else
    echo "NOTIFICATION_TOOL_MISSING: pkg install termux-api + install Termux:API app"
  fi
}

echo "FREYA notifier started: $(date)" >> "$LOG"
notify_freya "FREYA pećnica znanja" "Notifier je aktivan. Javljam kad izađe novi proizvod."

while true; do
  while IFS= read -r DIR; do
    [ -z "$DIR" ] && continue
    [ ! -d "$DIR" ] && continue

    find "$DIR" -type f \( -name "*.docx" -o -name "*.xlsx" -o -name "*.md" -o -name "*.tsv" -o -name "*.csv" -o -name "*.txt" \) 2>/dev/null |
    while IFS= read -r F; do
      [ -z "$F" ] && continue

      if ! grep -Fqx "$F" "$SEEN" 2>/dev/null; then
        echo "$F" >> "$SEEN"

        NAME="$(basename "$F")"
        TIME="$(date '+%Y-%m-%d %H:%M:%S')"

        echo "$TIMENEW_PRODUCT$F" >> "$LOG"

        notify_freya \
          "Novi proizvod iz pećnice znanja" \
          "$NAME"
      fi
    done
  done < "$WATCH"

  sleep 60
done
