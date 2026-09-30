#!/bin/sh

BASE="$HOME/FREYA_IPHONE"
DATE="$(date +%Y%m%d_%H%M%S)"
PACK="$BASE/18_BUILD_PACKET/FREYA_IPHONE_TO_ANDROID_PACKET_$DATE"

mkdir -p "$PACK"

cat > "$PACK/00_MESSAGE.md" <<EOT
FREYA IPHONE TO ANDROID PACKET

SOURCE:
FREYA_NODE_01_IPHONE

DESTINATION:
FREYA_NODE_02_ANDROID

PURPOSE:
Send captured iPhone knowledge to Android for classification, hashing, enrichment, and review.

RULE:
Original iPhone files not modified.
No delete.
No runtime.
Human Gate active.

CREATED:
$(date)
EOT

find "$BASE" -type f \
  ! -path "$BASE/18_BUILD_PACKET/*" \
  ! -path "$BASE/99_EXPORTS/*" \
  > "$PACK/01_SOURCE_MANIFEST.tsv"

sha256sum $(cat "$PACK/01_SOURCE_MANIFEST.tsv") > "$PACK/02_HASHES.sha256" 2>/dev/null

cat > "$PACK/03_HUMAN_GATE.md" <<'EOT'
HUMAN GATE

APPROVED FOR:
Transfer to Android for read-only classification and enrichment.

NOT APPROVED FOR:
Delete.
Move originals.
Runtime.
External sharing.
Final decisions.
EOT

tar -czf "$BASE/99_EXPORTS/$(basename "$PACK").tar.gz" -C "$BASE/18_BUILD_PACKET" "$(basename "$PACK")"

echo "IPHONE EXPORT PACKET CREATED:"
ls -lh "$BASE/99_EXPORTS/$(basename "$PACK").tar.gz"
