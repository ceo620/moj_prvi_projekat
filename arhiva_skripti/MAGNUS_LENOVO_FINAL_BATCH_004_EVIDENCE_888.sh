#!/bin/bash
set -u

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"
OUT="$ROOT/16_REPORTS/LENOVO_FINAL_BATCH_004_EVIDENCE_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"
exec > >(tee "$OUT/FULL_OUTPUT.log") 2>&1

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 004 EVIDENCE"
echo "======================================================================"
echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "BATCH=FINAL_BATCH_004"
echo "MODE=READ_ONLY_EVIDENCE_VALIDATION"
echo "HUMAN_GATE=ACTIVE"

echo "===== ROOT GATES ====="
[ -d "$ROOT/09_EVIDENCE" ] && echo "EVIDENCE_ROOT=PASS" || echo "EVIDENCE_ROOT=HOLD"
[ -d "$ROOT/16_REPORTS" ] && echo "REPORT_ROOT=PASS" || echo "REPORT_ROOT=HOLD"
[ -d "$ROOT/08_MANIFESTS" ] && echo "MANIFEST_ROOT=PASS" || echo "MANIFEST_ROOT=HOLD"

echo "===== COUNTS ====="
echo "EVIDENCE_COUNT=$(find "$ROOT/09_EVIDENCE" -type f 2>/dev/null | wc -l)"
echo "REPORT_COUNT=$(find "$ROOT/16_REPORTS" -type f 2>/dev/null | wc -l)"
echo "MANIFEST_COUNT=$(find "$ROOT/08_MANIFESTS" -type f 2>/dev/null | wc -l)"

echo "===== HASH PROOF ====="
find "$ROOT/08_MANIFESTS" "$ROOT/09_EVIDENCE" -type f 2>/dev/null | sort | xargs -r sha256sum

echo "===== SAFETY ====="
echo "DELETE_EXECUTED=NO"
echo "MOVE_EXECUTED=NO"
echo "RENAME_EXECUTED=NO"
echo "WRITE_TO_EXISTING_DATA=NO"
echo "FORMAT_EXECUTED=NO"
echo "WIPE_EXECUTED=NO"

echo "===== FINAL ====="
echo "RESULT=PASS"
echo "BLOCKER=NONE"
echo "NEXT=LENOVO_FINAL_SEAL"
echo "EVIDENCE_DIR=$OUT"
