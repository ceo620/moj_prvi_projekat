#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"
DOC="$BASE/01_DOCTRINE"
CARDS_OLD="$BASE/DOCTRINE_CARDS"
CASTLE_DOC="$BASE/CASTLE_MATERIAL_ANDROID/00_CORE_DOCTRINE"

mkdir -p \
"$DOC/00_DOCTRINE_LIBRARY" \
"$DOC/01_ANDROID_EXTRACT" \
"$DOC/02_EVIDENCE" \
"$DOC/03_REGISTERS" \
"$DOC/04_STATUS"

# 1. Copy existing doctrine cards, if present
if [ -d "$CARDS_OLD" ]; then
  cp -f "$CARDS_OLD"/*.md "$DOC/00_DOCTRINE_LIBRARY/" 2>/dev/null || true
fi

# 2. Link/copy Android core doctrine registers
cp -f "$CASTLE_DOC"/CORE_DOCTRINE_ANDROID_*.tsv "$DOC/03_REGISTERS/" 2>/dev/null || true
cp -f "$CASTLE_DOC"/ANDROID_00_CORE_DOCTRINE_STATUS.md "$DOC/04_STATUS/" 2>/dev/null || true
cp -f "$CASTLE_DOC"/00_CORE_DOCTRINE_MODULE_CARD.md "$DOC/04_STATUS/" 2>/dev/null || true

# 3. Create main doctrine register
REG="$DOC/03_REGISTERS/FREYA_DOCTRINE_REGISTER.tsv"
printf "DOCTRINE_ID\tTITLE\tSTATUS\tFILE\tSOURCE\n" > "$REG"

for F in "$DOC/00_DOCTRINE_LIBRARY"/D-*.md; do
  [ -f "$F" ] || continue
  ID=$(basename "$F" | cut -d_ -f1)
  TITLE=$(grep -A1 '^TITLE:' "$F" | tail -1 | sed 's/^[[:space:]]*//')
  [ -z "$TITLE" ] && TITLE=$(basename "$F" .md)
  printf "%s\t%s\tUNDER_REVIEW\t%s\tANDROID_COMPANION\n" "$ID" "$TITLE" "$F" >> "$REG"
done

# 4. Create doctrine system status
STATUS="$DOC/04_STATUS/ANDROID_DOCTRINE_SYSTEM_STATUS.md"
cat > "$STATUS" <<EOT
ANDROID DOCTRINE SYSTEM STATUS

STATUS:
DOCTRINE_SYSTEM_BUILT

RESULT:
Doctrine library created.
Doctrine cards copied.
Doctrine register created.
Android core doctrine extraction linked.
Human Gate remains active.

RULE:
No delete.
No runtime.
No doctrine becomes ACTIVE without Human Gate.

CREATED:
$(date)
EOT

echo "=== DOCTRINE SYSTEM BUILT ==="
cat "$STATUS"
echo ""
echo "=== DOCTRINE REGISTER ==="
cat "$REG"
