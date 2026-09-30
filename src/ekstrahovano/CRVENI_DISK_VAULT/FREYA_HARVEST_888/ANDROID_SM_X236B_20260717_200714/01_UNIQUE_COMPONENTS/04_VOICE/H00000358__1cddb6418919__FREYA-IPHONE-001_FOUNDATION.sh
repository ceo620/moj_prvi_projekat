#!/bin/sh

BASE="$HOME/FREYA_IPHONE"

mkdir -p \
"$BASE/00_ARCHITECTURE" \
"$BASE/01_DOCTRINE" \
"$BASE/02_HUMAN_GATE" \
"$BASE/03_DAILY_NOTES" \
"$BASE/04_VOICE_NOTES" \
"$BASE/05_PHOTOS_EVIDENCE" \
"$BASE/06_PEOPLE" \
"$BASE/07_PROJECTS" \
"$BASE/08_TASKS" \
"$BASE/09_BOOKS" \
"$BASE/10_WEB_CLIPPINGS" \
"$BASE/11_EMAIL_IDEAS" \
"$BASE/12_CAPTURE" \
"$BASE/13_MEMORY" \
"$BASE/14_LESSONS" \
"$BASE/15_DECISIONS" \
"$BASE/16_QUESTIONS" \
"$BASE/17_MORNING_BRIEF" \
"$BASE/18_BUILD_PACKET" \
"$BASE/19_REGISTERS" \
"$BASE/20_STATUS" \
"$BASE/99_EXPORTS" \
"$BASE/scripts"

cat > "$BASE/00_ARCHITECTURE/NODE_REGISTER.md" <<'EOT'
NODE_ID:
FREYA_NODE_01

NODE_NAME:
FREYA ALPINE

DEVICE:
iPhone 17 Pro Max / iSH Alpine

ROLE:
Knowledge Capture Node

MISSION:
Capture Danijela's ideas, notes, evidence, people, projects, questions, and daily knowledge.

NEXT_NODE:
FREYA_NODE_02_ANDROID_COMPANION

AUTHORITY:
Not runtime authority.
Not deployment authority.
Not final decision authority.

HUMAN_GATE:
ACTIVE
EOT

cat > "$BASE/02_HUMAN_GATE/HUMAN_GATE.md" <<'EOT'
FREYA IPHONE HUMAN GATE

RULES:
No delete.
No move.
No auto-send.
No auto-share.
No final decision.
No runtime execution.
No external publication.

Everything captured stays pending until Danijela reviews it.
EOT

cat > "$BASE/20_STATUS/STATUS.md" <<'EOT'
FREYA IPHONE STATUS

FOUNDATION:
OK

NODE:
FREYA_NODE_01

ROLE:
Knowledge Capture Node

HUMAN_GATE:
ACTIVE

KNOWLEDGE_OBJECTS:
0

BUILD_PACKETS_EXPORTED:
0

STATUS:
FOUNDATION_READY
EOT

cat > "$BASE/00_ARCHITECTURE/README.md" <<'EOT'
FREYA ALPINE is the iPhone capture node.

It collects knowledge.
It preserves source context.
It does not decide.
It does not delete.
It sends structured packets to Android for enrichment.
EOT

echo "FREYA-IPHONE-001 FOUNDATION COMPLETE"
echo ""
cat "$BASE/20_STATUS/STATUS.md"
echo ""
echo "FOLDER CHECK:"
find "$BASE" -maxdepth 1 -type d | sort
