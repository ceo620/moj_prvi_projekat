#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"

mkdir -p \
"$BASE/00_ARCHITECTURE" \
"$BASE/01_DOCTRINE" \
"$BASE/02_HUMAN_GATE" \
"$BASE/03_COMPANION_MEMORY" \
"$BASE/04_CAPTURE_INBOX" \
"$BASE/05_LEARNING_SESSIONS" \
"$BASE/06_FIELD_KNOWLEDGE" \
"$BASE/07_REGISTERS" \
"$BASE/08_MINI_ENGINES" \
"$BASE/09_SYNC_PACKETS" \
"$BASE/10_SAFETY_LOCKS" \
"$BASE/11_VOICE_JOURNAL" \
"$BASE/12_PROJECT_COMPANION" \
"$BASE/99_EXPORTS"

cat > "$BASE/00_ARCHITECTURE/FREYA_ANDROID_COMPANION_ARCHITECTURE.md" <<'EOT'
FREYA ANDROID COMPANION NODE

ROLE:
Mobile, safe, living companion node.

NOT A TOY.
NOT A TEMP COPY.
NOT A RUNTIME AUTHORITY.

LAYERS:
00 Architecture
01 Doctrine
02 Human Gate
03 Companion Memory
04 Capture Inbox
05 Learning Sessions
06 Field Knowledge
07 Registers
08 Mini Engines
09 Sync Packets
10 Safety Locks
11 Voice Journal
12 Project Companion
99 Exports

RULES:
No delete.
No runtime without Human Gate.
Original documents never modified.
Evidence before conclusions.
Human will always be safe.
EOT

cat > "$BASE/10_SAFETY_LOCKS/SAFETY_LOCK.md" <<'EOT'
FREYA ANDROID SAFETY LOCK

NO_DELETE=YES
NO_RUNTIME=YES
NO_AUTO_REPAIR=YES
NO_FINAL_DECISION=YES
HUMAN_GATE=ACTIVE
EOT

echo "FREYA ANDROID COMPANION CREATED"
find "$BASE" -maxdepth 2 -type d | sort
