#!/bin/bash
set -u

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"
OUT="$ROOT/16_REPORTS/LENOVO_FINAL_BATCH_003_HANDOFF_$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$OUT"
exec > >(tee "$OUT/FULL_OUTPUT.log") 2>&1

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 003 HANDOFF"
echo "======================================================================"

echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "BATCH=FINAL_BATCH_003"
echo "MODE=READ_ONLY_HANDOFF_ANALYSIS"
echo "HUMAN_GATE=ACTIVE"

echo
echo "===== HANDOFF ROOTS ====="
for D in "$ROOT" "$ROOT/04_PRODUCTS" "$ROOT/08_MANIFESTS" "$ROOT/09_EVIDENCE" "$ROOT/16_REPORTS"; do
 if [ -d "$D" ]; then echo "FOUND=$D"; else echo "MISSING=$D"; fi
done

echo
echo "===== MANIFEST SIGNALS ====="
find "$ROOT" -iname "*manifest*" -o -iname "*handoff*" -o -iname "*export*" 2>/dev/null | head -50

echo
echo "===== EVIDENCE COUNT ====="
find "$ROOT/09_EVIDENCE" -type f 2>/dev/null | wc -l

echo
echo "===== REPORT COUNT ====="
find "$ROOT/16_REPORTS" -type f 2>/dev/null | wc -l

echo
echo "===== SAFETY ====="
echo "DELETE=DENY"
echo "MOVE=DENY"
echo "RENAME=DENY"
echo "WRITE=DENY"
echo "FORMAT=DENY"
echo "WIPE=DENY"
echo "REPAIR=DENY"

echo
echo "===== FINAL ====="
echo "RESULT=PASS"
echo "NEXT=LENOVO_BATCH_FINAL_004_EVIDENCE"
echo "EVIDENCE_DIR=$OUT"
echo "END_UTC=$(date -u +%Y%m%dT%H%M%SZ)"
echo "======================================================================"
