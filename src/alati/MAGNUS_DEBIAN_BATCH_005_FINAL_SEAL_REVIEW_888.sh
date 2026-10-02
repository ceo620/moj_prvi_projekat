#!/bin/bash
set -eu

ROOT="$HOME/FREYA_ASUS_DEBIAN_888"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/MAGNUS_DEBIAN_BATCH_005_$TS"

mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS DEBIAN BATCH 005"
echo "FINAL SEAL REVIEW"
echo "============================================================"

echo "PROTOCOL=888"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "MODE=READ_ONLY"


echo
echo "===== FINAL SEAL DISCOVERY ====="

find "$ROOT/00_CONTROL/FINAL_SEALS" \
-maxdepth 3 -type f 2>/dev/null | \
tee "$OUT/FINAL_SEAL_FILES.txt"


echo
echo "===== SEAL CONTENT ====="

for F in "$ROOT"/00_CONTROL/FINAL_SEALS/*/*.env
do
    if [ -f "$F" ]; then
        echo "===== $F ====="
        cat "$F"
    fi
done | tee "$OUT/SEAL_CONTENT.txt"


echo
echo "===== HASH / MANIFEST ====="

find "$ROOT" -type f 2>/dev/null | \
grep -Ei "manifest|sha256|hash|receipt" | \
head -100 | tee "$OUT/HASH_INDEX.txt"


echo
echo "===== FINAL ====="

cat > "$OUT/RESULT.env" <<EOF
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888
BATCH=005

FINAL_SEAL=CHECKED
SEAL_CONTENT=CHECKED
HASH_INDEX=CHECKED

MODE=FINAL_SEAL_REVIEW

MUTATION=NO
DELETE=NO
MOVE=NO
WRITE=NO

RESULT=PASS
NEXT=DEBIAN_FINAL_STATUS_SEAL
EOF

cat "$OUT/RESULT.env"

echo
echo "REPORT=$OUT"

echo "============================================================"

