#!/data/data/com.termux/files/usr/bin/bash

BASE="$HOME/FREYA_TABLET_NODE_888"
IMPORT="$BASE/18_LIBRARY/IMPORT"
INDEX="$BASE/18_LIBRARY/INDEX"

echo "=== FREYA LIBRARY SCAN ==="

find "$IMPORT" -type f \( \
-iname "*.pdf" -o \
-iname "*.epub" -o \
-iname "*.docx" \
\) > "$INDEX/books_found.txt"

COUNT=$(wc -l < "$INDEX/books_found.txt")

echo ""
echo "Books detected: $COUNT"
echo ""

cat "$INDEX/books_found.txt"

echo ""
echo "Ready for learning."
