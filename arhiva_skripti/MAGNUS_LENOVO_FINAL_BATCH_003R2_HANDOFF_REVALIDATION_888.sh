#!/bin/bash
set -u

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"
OUT="$ROOT/16_REPORTS/LENOVO_FINAL_BATCH_003R2_HANDOFF_REVALIDATION_$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$OUT"
exec > >(tee "$OUT/FULL_OUTPUT.log") 2>&1

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 003R2 HANDOFF REVALIDATION"
echo "======================================================================"
echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "BATCH=FINAL_BATCH_003R2"
echo "MODE=READ_ONLY_HANDOFF_REVALIDATION"
echo "HUMAN_GATE=ACTIVE"

PASS=1
echo "===== STRUCTURE GATES ====="
for D in 04_PRODUCTS 08_MANIFESTS 09_EVIDENCE 16_REPORTS; do
 if [ -d "$ROOT/$D" ]; then echo "${D}_GATE=PASS"; else echo "${D}_GATE=HOLD"; PASS=0; fi
done

echo "===== CONTENT COUNTS ====="
echo "PRODUCT_COUNT=$(find "$ROOT/04_PRODUCTS" -type f 2>/dev/null | wc -l)"
echo "MANIFEST_COUNT=$(find "$ROOT/08_MANIFESTS" -type f 2>/dev/null | wc -l)"
echo "EVIDENCE_COUNT=$(find "$ROOT/09_EVIDENCE" -type f 2>/dev/null | wc -l)"
echo "REPORT_COUNT=$(find "$ROOT/16_REPORTS" -type f 2>/dev/null | wc -l)"

echo "===== SAFETY ====="
echo "DELETE_EXECUTED=NO"
echo "MOVE_EXECUTED=NO"
echo "RENAME_EXECUTED=NO"
echo "WRITE_TO_EXISTING_DATA=NO"
echo "FORMAT_EXECUTED=NO"
echo "WIPE_EXECUTED=NO"

echo "===== FINAL ====="
if [ "$PASS" -eq 1 ]; then
 echo "RESULT=PASS"
 echo "BLOCKER=NONE"
 echo "NEXT=LENOVO_BATCH_FINAL_004_EVIDENCE"
else
 echo "RESULT=HOLD"
 echo "BLOCKER=HANDOFF_STRUCTURE_REVALIDATION_FAILED"
fi
echo "EVIDENCE_DIR=$OUT"
