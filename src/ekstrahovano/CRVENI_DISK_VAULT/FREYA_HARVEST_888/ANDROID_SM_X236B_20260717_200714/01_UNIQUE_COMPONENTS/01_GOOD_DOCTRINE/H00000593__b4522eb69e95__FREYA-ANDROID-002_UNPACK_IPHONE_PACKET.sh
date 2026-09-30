#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"
IN="$BASE/09_SYNC_PACKETS/FROM_IPHONE"
REVIEW="$BASE/09_SYNC_PACKETS/REVIEW_ONLY_FROM_IPHONE"
REG="$BASE/07_REGISTERS/IPHONE_PACKET_UNPACK_REGISTER.tsv"

mkdir -p "$IN" "$REVIEW" "$BASE/07_REGISTERS"

PACK=$(ls -t "$IN"/FREYA_IPHONE_KNOWLEDGE_PACKET_V1_*.tar.gz 2>/dev/null | head -1)

[ -n "$PACK" ] || { echo "NO_IPHONE_KNOWLEDGE_PACKET_FOUND"; exit 1; }

NAME=$(basename "$PACK" .tar.gz)
DEST="$REVIEW/$NAME"
mkdir -p "$DEST"

SIZE=$(wc -c < "$PACK" | tr -d ' ')
SHA=$(sha256sum "$PACK" | awk '{print $1}')

if [ -f "$PACK.sha256" ]; then
  EXPECTED=$(awk '{print $1}' "$PACK.sha256")
  [ "$SHA" = "$EXPECTED" ] || { echo "SHA256_MISMATCH"; exit 1; }
  VERIFY_STATUS="SHA256_OK"
else
  VERIFY_STATUS="NO_SHA256_FILE_LOCAL_HASH_ONLY"
fi

tar -xzf "$PACK" -C "$DEST"

echo -e "TIME\tPACKET\tSIZE\tSHA256\tSTATUS\tDEST" > "$REG"
echo -e "$(date)\t$PACK\t$SIZE\t$SHA\tUNPACKED_REVIEW_ONLY_$VERIFY_STATUS\t$DEST" >> "$REG"

cat > "$DEST/ANDROID_UNPACK_STATUS.md" <<EOT
ANDROID UNPACKED IPHONE KNOWLEDGE PACKET

STATUS:
UNPACKED_REVIEW_ONLY_$VERIFY_STATUS

PACKET:
$PACK

SIZE_BYTES:
$SIZE

SHA256:
$SHA

DESTINATION:
$DEST

RULES:
No delete.
No move originals.
No runtime.
No auto-repair.
No final decision.
Human Gate active.

NEXT:
Android Knowledge Enrichment Engine.
EOT

echo "=== ANDROID UNPACK COMPLETE ==="
cat "$DEST/ANDROID_UNPACK_STATUS.md"
echo ""
echo "PACK
ET CONTENT:"
find "$DEST" -maxdepth 3 -type f | sort
