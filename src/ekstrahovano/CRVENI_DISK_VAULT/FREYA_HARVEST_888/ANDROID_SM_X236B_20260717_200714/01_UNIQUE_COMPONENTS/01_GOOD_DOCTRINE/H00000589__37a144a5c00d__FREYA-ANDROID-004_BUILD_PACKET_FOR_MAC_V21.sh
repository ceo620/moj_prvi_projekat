#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"
DATE="$(date +%Y%m%d_%H%M%S)"
OUT="$BASE/09_SYNC_PACKETS/TO_MAC"
PACK="$OUT/FREYA_ANDROID_TO_MAC_PACKET_V2_1_$DATE"

mkdir -p "$PACK"/{01_FROM_IPHONE_REVIEW_ONLY,02_ANDROID_DOCTRINE,03_ANDROID_REGISTERS,04_ANDROID_MEMORY,05_SAFETY_LOCKS,06_ANDROID_SIGNAL_MAPS,07_ANDROID_ALGORITHMS_TOKENS}

LATEST_IPHONE=$(ls -td "$BASE/09_SYNC_PACKETS/REVIEW_ONLY_FROM_IPHONE"/FREYA_IPHONE_KNOWLEDGE_PACKET_V1_* 2>/dev/null | head -1)
[ -n "$LATEST_IPHONE" ] && cp -R "$LATEST_IPHONE" "$PACK/01_FROM_IPHONE_REVIEW_ONLY/"

cp -R "$BASE/01_DOCTRINE" "$PACK/02_ANDROID_DOCTRINE/" 2>/dev/null || true
cp -R "$BASE/07_REGISTERS" "$PACK/03_ANDROID_REGISTERS/" 2>/dev/null || true
cp -R "$BASE/03_COMPANION_MEMORY" "$PACK/04_ANDROID_MEMORY/" 2>/dev/null || true
cp -R "$BASE/10_SAFETY_LOCKS" "$PACK/05_SAFETY_LOCKS/" 2>/dev/null || true

find "$BASE" -type f \( \
  -iname "*signal*" -o -iname "*map*" -o -iname "*daemon*" -o -iname "*engine*" -o \
  -iname "*token*" -o -iname "*algorithm*" -o -iname "*algoritam*" -o \
  -iname "*orchestrator*" -o -iname "*register*" \
\) 2>/dev/null > "$PACK/06_ANDROID_SIGNAL_MAPS/android_signal_algorithm_candidates.txt"

find "$BASE" -type f \( \
  -iname "*.py" -o -iname "*.sh" -o -iname "*.json" -o -iname "*.md" -o -iname "*.txt" -o -iname "*.tsv" -o -iname "*.csv" \
\) 2>/dev/null | grep -Ei "signal|daemon|engine|token|algorithm|orchestrator|registry|register|map|ssot|doctrine|human_gate|freya|titan" \
> "$PACK/07_ANDROID_ALGORITHMS_TOKENS/android_algorithm_token_paths.txt" || true

cat > "$PACK/00_ANDROID_TO_MAC_README.md" <<EOT
FREYA ANDROID TO MAC PACKET V2.1

SOURCE:
FREYA_NODE_02_ANDROID_COMPANION

DESTINATION:
FREYA_NODE_03_MAC_PRIME

INCLUDES:
- iPhone Knowledge Packet V1
- Android Doctrine
- Android Registers
- Android Companion Memory
- Safety Locks
- Android signal maps
- Android algorithms/tokens/engine candidates

RULES:
No delete.
No runtime.
No auto-repair.
No final decision.
Human Gate active.

CREATED:
$(date)
EOT

cat > "$PACK/03_HUMAN_GATE.md" <<'EOT'
HUMAN GATE FOR MAC

APPROVED:
Receive, verify, index, classify, and merge into FREYA PRIME review layer.

NOT APPROVED:
Delete originals.
Run scripts.
Overwrite canon.
Publish externally.
Make final decisions.
EOT

find "$PACK" -type f | sort > "$PACK/01_PACKET_MANIFEST.tsv"
sha256sum $(cat "$PACK/01_PACKET_MANIFEST.tsv") > "$PACK/02_PACKET_HASHES.sha256" 2>/dev/null

tar -czf "$OUT/$(basename "$PACK").tar.gz" -C "$OUT" "$(basename "$PACK")"
sha256sum "$OUT/$(basename "$PACK").tar.gz" > "$OUT/$(basename "$PACK").tar.gz.sha256"

echo "ANDROID TO MAC V2.1 PACKET CREATED:"
ls -lh "$OUT/$(basename "$PACK").tar.gz" "$OUT/$(basename "$PACK").tar.gz.sha256"
echo "$OUT/$(basename "$PACK").tar.gz"
