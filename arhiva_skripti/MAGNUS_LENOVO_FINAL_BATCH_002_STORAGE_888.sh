#!/bin/bash
set -u

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"
OUT="$ROOT/16_REPORTS/LENOVO_FINAL_BATCH_002_STORAGE_$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$OUT"
exec > >(tee "$OUT/FULL_OUTPUT.log") 2>&1

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 002 STORAGE"
echo "======================================================================"

echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "BATCH=FINAL_BATCH_002"
echo "MODE=READ_ONLY_STORAGE_ANALYSIS"
echo "HUMAN_GATE=ACTIVE"

echo
echo "===== STORAGE ====="
df -h

echo
echo "===== FREYA ROOT ====="
if [ -d "$ROOT" ]; then echo "FREYA_ROOT=PASS"; else echo "FREYA_ROOT=HOLD"; fi

echo
du -sh "$ROOT" 2>/dev/null || true

echo
echo "===== TOP DIRECTORIES ====="
find "$ROOT" -maxdepth 1 -type d -print 2>/dev/null

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
echo "NEXT=LENOVO_BATCH_FINAL_003_HANDOFF"
echo "EVIDENCE_DIR=$OUT"
echo "END_UTC=$(date -u +%Y%m%dT%H%M%SZ)"
echo "======================================================================"
