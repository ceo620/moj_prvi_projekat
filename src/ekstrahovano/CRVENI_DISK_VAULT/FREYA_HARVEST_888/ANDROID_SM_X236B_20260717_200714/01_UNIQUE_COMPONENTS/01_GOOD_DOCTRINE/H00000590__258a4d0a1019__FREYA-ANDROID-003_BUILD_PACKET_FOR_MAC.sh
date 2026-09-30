#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"
DATE="$(date +%Y%m%d_%H%M%S)"
OUT="$BASE/09_SYNC_PACKETS/TO_MAC"
PACK="$OUT/FREYA_ANDROID_TO_MAC_PACKET_V2_$DATE"

mkdir -p "$PACK"

# 1. Include unpacked iPhone knowledge packet
LATEST_IPHONE=$(ls -td "$BASE/09_SYNC_PACKETS/REVIEW_ONLY_FROM_IPHONE"/FREYA_IPHONE_KNOWLEDGE_PACKET_V1_* 2>/dev/null | head -1)
if [ -n "$LATEST_IPHONE" ]; then
  mkdir -p "$PACK/01_FROM_IPHONE_REVIEW_ONLY"
  cp -R "$LATEST_IPHONE" "$PACK/01_FROM_IPHONE_REVIEW_ONLY/"
fi

# 2. Include Android doctrine/register/status layer
mkdir -p "$PACK/02_ANDROID_DOCTRINE"
cp -R "$BASE/01_DOCTRINE" "$PACK/02_ANDROID_DOCTRINE/" 2>/dev/null || true
cp -R "$BASE/07_REGISTERS" "$PACK/03_ANDROID_REGISTERS" 2>/dev/null || true
cp -R "$BASE/03_COMPANION_MEMORY" "$PACK/04_ANDROID_MEMORY" 2>/dev/null || true
cp -R "$BASE/10_SAFETY_LOCKS" "$PACK/05_SAFETY_LOCKS" 2>/dev/null || true

# 3. Build summary
cat > "$PACK/00_ANDROID_TO_MAC_README.md" <<EOT
FREYA ANDROID TO MAC PACKET V2

SOURCE:
FREYA_NODE_02_ANDROID_COMPANION

DESTINATION:
FREYA_NODE_03_MAC_PRIME

PURPOSE:
Send enriched iPhone knowledge plus Android doctrine/register/memory layer to Mac for SSOT merge and FREYA PRIME review.

INCLUDES:
- iPhone Knowledge Packet V1 unpacked review-only
- Android Doctrine System
- Android Registers
- Android Companion Memory
- Safety Locks

RULES:
No delete.
No runtime.
No auto-repair.
No final decision.
Human Gate active.
Mac receives for review and merge only.

CREATED:
$(date)
EOT

cat > "$PACK/03_HUMAN_GATE.md" <<'EOT'
HUMAN GATE FOR MAC

APPROVED:
Receive packet.
Verify hashes.
Index content.
Merge into FREYA PRIME review layer.
Prepare canonical review.

NOT APPROVED:
Delete originals.
Overwrite Mac canon without review.
Run scripts from packet.
Publish externally.
Make final decisions.
EOT

# 4. Manifest + hashes
find "$PACK" -type f | sort > "$PACK/01_PACKET_MANIFEST.tsv"
sha256sum $(cat "$PACK/01_PACKET_MANIFEST.tsv") > "$PACK/02_PACKET_HASHES.sha256" 2>/dev/null

# 5. Archive
tar -czf "$OUT/$(basename "$PACK").tar.gz" -C "$OUT" "$(basename "$PACK")"
sha256sum "$OUT/$(basename "$PACK").tar.gz" > "$OUT/$(basename "$PACK").tar.gz.sha256"

echo "ANDROID TO MAC PACKET CREATED:"
ls -lh "$OUT/$(basename "$PACK").tar.gz" "$OUT/$(basename "$PACK").tar.gz.sha256"
echo ""
echo "PACKET:"
echo "$OUT/$(basename "$PACK").tar.gz"
