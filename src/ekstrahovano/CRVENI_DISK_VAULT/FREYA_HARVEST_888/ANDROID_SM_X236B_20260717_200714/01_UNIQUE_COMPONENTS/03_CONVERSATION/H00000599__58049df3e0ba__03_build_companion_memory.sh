#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/FREYA_CORE"
MEM="$BASE/03_COMPANION_MEMORY"

mkdir -p \
"$MEM/01_LETTERS_TO_FREYA" \
"$MEM/02_DAILY_JOURNAL" \
"$MEM/03_PEOPLE" \
"$MEM/04_PROJECTS" \
"$MEM/05_BOOKS_AND_IDEAS" \
"$MEM/06_LESSONS_LEARNED" \
"$MEM/07_DECISIONS" \
"$MEM/08_DREAMS_AND_VISIONS" \
"$MEM/09_QUESTIONS_FOR_FREYA" \
"$MEM/10_FREYA_REFLECTIONS"

TODAY=$(date +%Y-%m-%d)

cat > "$MEM/02_DAILY_JOURNAL/${TODAY}.md" <<EOT
# Daily Journal

Date:
$TODAY

Today happened:

How I felt:

What I learned:

Important people:

Important decisions:

Open questions:

What I want FREYA to remember:

Next step:
EOT

cat > "$MEM/README.md" <<'EOT'
FREYA COMPANION MEMORY

Purpose:
This folder preserves long-term context intentionally shared by Danijela.

Rules:
- Human Gate always active.
- Read-only until explicitly reviewed.
- No automatic decisions.
- No automatic sending.
- No deletion.
- Memory is accumulated with consent.
EOT

echo "=== FREYA COMPANION MEMORY CREATED ==="
find "$MEM" -maxdepth 2 | sort
