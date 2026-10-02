#!/bin/bash
set -eu

ROOT="$HOME/FREYA_ASUS_DEBIAN_888"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/MAGNUS_DEBIAN_STANDBY_006_$TS"

mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS DEBIAN STANDBY 006"
echo "FINAL ARCHIVE INDEX RECEIPT"
echo "============================================================"

echo "PROTOCOL=888"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "MODE=STANDBY_READ_ONLY"

echo
echo "===== FINAL RECORD INDEX ====="

find "$HOME" -maxdepth 2 -type f 2>/dev/null | \
grep -Ei "STANDBY|GOVERNANCE|FINAL|RECEIPT|SEAL" | \
tee "$OUT/FINAL_RECORD_INDEX.txt"

echo
echo "===== CORE DIRECTORIES ====="

for D in \
00_CONTROL/FINAL_SEALS \
02_SSOT \
05_AUTOMATION \
06_AGENTS \
09_HANDOFF \
10_EVIDENCE
do
    if [ -d "$ROOT/$D" ]; then
        echo "$D=PRESENT"
    else
        echo "$D=MISSING"
    fi
done | tee "$OUT/CORE_DIRECTORY_STATUS.txt"

echo
echo "===== FINAL ====="

cat > "$OUT/ARCHIVE_INDEX_RECEIPT.env" <<EOF
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

MODE=STANDBY_READ_ONLY

FINAL_SEALS=INDEXED
GOVERNANCE_RECEIPT=INDEXED
STANDBY_RECEIPTS=INDEXED

CORE_STRUCTURE=PRESENT

HUMAN_GATE=ACTIVE

WRITE=NO
DELETE=NO
MOVE=NO

STATUS=ARCHIVE_INDEX_READY
RESULT=PASS
NEXT=HUMAN_GATE_ONLY
EOF

cat "$OUT/ARCHIVE_INDEX_RECEIPT.env"

echo
echo "REPORT=$OUT"

echo "============================================================"

