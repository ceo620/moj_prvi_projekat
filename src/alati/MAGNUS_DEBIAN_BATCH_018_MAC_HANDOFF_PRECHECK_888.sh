#!/bin/bash
set -eu

ROOT="$HOME/FREYA_ASUS_DEBIAN_888"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/MAGNUS_DEBIAN_BATCH_018_MAC_HANDOFF_PRECHECK_$TS"

mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS DEBIAN BATCH 018"
echo "MAC HANDOFF PRECHECK"
echo "============================================================"

echo "PROTOCOL=888"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "MODE=READ_ONLY"

echo
echo "===== FINAL SEALS ====="

find "$ROOT/00_CONTROL/FINAL_SEALS" \
-maxdepth 3 -type f -name "*.env" 2>/dev/null \
| tee "$OUT/FINAL_SEALS.txt"

echo
echo "===== SSOT ====="

cat "$ROOT/02_SSOT/SSOT_AUTHORITY_888.env" \
2>/dev/null | tee "$OUT/SSOT.txt"

echo
echo "===== HANDOFF TO MAC CANDIDATES ====="

find "$ROOT" \
-type f \
\( -iname "*MAC*" -o -iname "*HANDOFF*" -o -iname "*MANIFEST*" \) \
2>/dev/null \
| sort \
| tee "$OUT/MAC_HANDOFF_CANDIDATES.txt"

echo
echo "===== FINAL ====="

echo "PROTOCOL=888"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=018"
echo "MODE=READ_ONLY"
echo "MUTATION=NO"
echo "DELETE=NO"
echo "MOVE=NO"
echo "WRITE=NO"
echo "RESULT=PASS"
echo "STOP=HUMAN_GATE"
echo "REPORT=$OUT"

echo "============================================================"
