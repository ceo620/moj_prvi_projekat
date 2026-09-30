#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"
IN="$BASE/09_SYNC_PACKETS/FROM_IPHONE"
OUT="$BASE/09_SYNC_PACKETS/ANDROID_ENRICHED"
REG="$BASE/07_REGISTERS/IPHONE_PACKET_RECEIVE_REGISTER.tsv"

mkdir -p "$IN" "$OUT" "$BASE/07_REGISTERS"

echo -e "TIME\tSOURCE\tFILES\tSTATUS\tNOTES" > "$REG"

COUNT=$(find "$IN" -type f 2>/dev/null | wc -l)

find "$IN" -type f 2>/dev/null > "$OUT/iphone_received_files.txt"
find "$IN" -type f 2>/dev/null -exec sha256sum {} \; > "$OUT/iphone_received_hashes.sha256"

cat > "$OUT/ANDROID_RECEIVE_STATUS.md" <<EOT
ANDROID RECEIVED IPHONE PACKET

STATUS:
RECEIVE_LAYER_READY

FILES_RECEIVED:
$COUNT

RULES:
No delete.
No move.
No runtime.
No auto-repair.
No final decision.
Human Gate active.

NEXT:
Classify iPhone knowledge into:
- Daily Notes
- Capture
- People
- Projects
- Evidence
- Questions
- Tasks
- Memory
EOT

echo -e "$(date)\tIPHONE_PACKET\t$COUNT\tRECEIVED_REGISTERED\tNo runtime, no delete" >> "$REG"

cat "$OUT/ANDROID_RECEIVE_STATUS.md"
