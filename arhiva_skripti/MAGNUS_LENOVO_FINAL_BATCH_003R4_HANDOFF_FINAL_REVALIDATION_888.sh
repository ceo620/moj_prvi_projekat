#!/bin/bash
set -u

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 003R4 HANDOFF FINAL REVALIDATION"
echo "======================================================================"
echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "BATCH=FINAL_BATCH_003R4"
echo "MODE=READ_ONLY_FINAL_HANDOFF_REVALIDATION"
echo "HUMAN_GATE=ACTIVE"

MAN="$(find "$ROOT/08_MANIFESTS" -maxdepth 1 -type f -name "LENOVO_FINAL_HANDOFF_MANIFEST_*.env" | sort | tail -1)"
EVD="$(find "$ROOT/09_EVIDENCE" -maxdepth 1 -type f -name "LENOVO_FINAL_HANDOFF_EVIDENCE_*.env" | sort | tail -1)"

echo "===== STRUCTURE ====="
for D in 04_PRODUCTS 08_MANIFESTS 09_EVIDENCE 16_REPORTS; do
 [ -d "$ROOT/$D" ] && echo "${D}_GATE=PASS" || echo "${D}_GATE=HOLD"
done

echo "===== CONTENT COUNTS ====="
echo "PRODUCT_COUNT=$(find "$ROOT/04_PRODUCTS" -type f 2>/dev/null | wc -l)"
echo "MANIFEST_COUNT=$(find "$ROOT/08_MANIFESTS" -type f 2>/dev/null | wc -l)"
echo "EVIDENCE_COUNT=$(find "$ROOT/09_EVIDENCE" -type f 2>/dev/null | wc -l)"
echo "REPORT_COUNT=$(find "$ROOT/16_REPORTS" -type f 2>/dev/null | wc -l)"

echo "===== FINAL HANDOFF OBJECTS ====="
echo "MANIFEST_FILE=${MAN:-NOT_FOUND}"
echo "EVIDENCE_FILE=${EVD:-NOT_FOUND}"
[ -n "$MAN" ] && sha256sum "$MAN"
[ -n "$EVD" ] && sha256sum "$EVD"

echo "===== SAFETY ====="
echo "DELETE_EXECUTED=NO"
echo "MOVE_EXECUTED=NO"
echo "RENAME_EXECUTED=NO"
echo "WRITE_EXECUTED=NO"
echo "FORMAT_EXECUTED=NO"
echo "WIPE_EXECUTED=NO"

echo "===== FINAL ====="
if [ -n "$MAN" ] && [ -n "$EVD" ]; then
 echo "RESULT=PASS"
 echo "BLOCKER=NONE"
 echo "NEXT=LENOVO_BATCH_FINAL_004_EVIDENCE"
else
 echo "RESULT=HOLD"
 echo "BLOCKER=FINAL_HANDOFF_PROOF_MISSING"
fi
