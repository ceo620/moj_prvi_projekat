#!/bin/bash
set -u

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 003R1 HANDOFF STRUCTURE BOOTSTRAP"
echo "======================================================================"
echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "BATCH=FINAL_BATCH_003R1"
echo "MODE=CONTROLLED_CREATE_MISSING_DIRECTORIES_ONLY"
echo "HUMAN_GATE=ACTIVE"

echo "===== BEFORE ====="
for D in 04_PRODUCTS 08_MANIFESTS 09_EVIDENCE 16_REPORTS; do
 [ -d "$ROOT/$D" ] && echo "BEFORE_$D=FOUND" || echo "BEFORE_$D=MISSING"
done

echo "===== CONTROLLED CREATION ====="
mkdir -p "$ROOT/04_PRODUCTS"
mkdir -p "$ROOT/08_MANIFESTS"
mkdir -p "$ROOT/09_EVIDENCE"

echo "===== AFTER ====="
PASS=1
for D in 04_PRODUCTS 08_MANIFESTS 09_EVIDENCE 16_REPORTS; do
 if [ -d "$ROOT/$D" ]; then echo "AFTER_$D=PASS"; else echo "AFTER_$D=HOLD"; PASS=0; fi
done

echo "===== SAFETY ====="
echo "DELETE_EXECUTED=NO"
echo "MOVE_EXECUTED=NO"
echo "RENAME_EXECUTED=NO"
echo "OVERWRITE_EXECUTED=NO"
echo "FORMAT_EXECUTED=NO"
echo "WIPE_EXECUTED=NO"
echo "CONTROLLED_MUTATION=DIRECTORY_CREATION_ONLY"

echo "===== FINAL ====="
if [ "$PASS" -eq 1 ]; then
 echo "RESULT=PASS"
 echo "NEXT=LENOVO_BATCH_FINAL_003R2_HANDOFF_REVALIDATION"
else
 echo "RESULT=HOLD"
 echo "BLOCKER=HANDOFF_STRUCTURE_CREATION_FAILED"
fi
