#!/bin/sh
set -eu
BRIDGE="/root/FREYA_IPHONE_ISH_NODE_888/SHORTCUTS_BRIDGE_888"
INBOX="$BRIDGE/01_INBOX"
MAN="$BRIDGE/05_MANIFESTS"
OUT="$MAN/LATEST_SHA256_MANIFEST.txt"
TMP="$MAN/.manifest_new.$$"
mkdir -p "$MAN"
: > "$TMP"
find "$INBOX" -type f -print | sort | while IFS= read -r F; do
  H=$(sha256sum "$F" | awk "{print \$1}")
  S=$(wc -c < "$F" | tr -d " ")
  printf "%s\t%s\t%s\n" "$H" "$S" "$F" >> "$TMP"
done
mv "$TMP" "$OUT"
echo "PROTOCOL=888"
echo "ENGINE=MANIFEST_SHA256"
echo "MANIFEST=$OUT"
echo "MANIFEST_ROWS=$(wc -l < "$OUT" | tr -d " ")"
echo "MANIFEST_SHA256=$(sha256sum "$OUT" | awk "{print \$1}")"
echo "HASH_ENGINE=LIVE"
echo "RESULT=PASS"
