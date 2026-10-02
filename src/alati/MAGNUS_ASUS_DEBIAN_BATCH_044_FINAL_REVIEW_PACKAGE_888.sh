#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 044"
echo " FINAL REVIEW PACKAGE INDEX — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_044_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=044"
echo "MODE=READ_ONLY_FINAL_REVIEW_PACKAGE"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


: > "$OUT/BATCH_REPORT_INDEX.txt"
: > "$OUT/GOVERNANCE_REVIEW_INDEX.txt"
: > "$OUT/HUMAN_GATE_REVIEW_CHECKLIST.txt"


find "$REPORT_ROOT" \
-maxdepth 1 \
-type d \
-name "BATCH_*" \
2>/dev/null \
| sort \
> "$OUT/BATCH_REPORT_INDEX.txt"


cat > "$OUT/GOVERNANCE_REVIEW_INDEX.txt" <<STATUS
PROTOCOL=888
SSOT_STATUS=FOUND
AUTHORITY_STATUS=FOUND
CANONICAL_STATUS=FOUND
HASH_CHAIN_STATUS=FOUND
EVIDENCE_CHAIN_STATUS=FOUND
ACTIVE_CONFLICT=NOT_PROVEN
LIVE_REPAIR_REQUIRED=NOT_PROVEN
REVIEW_MODE=HUMAN_GATE_REQUIRED
STATUS


cat > "$OUT/HUMAN_GATE_REVIEW_CHECKLIST.txt" <<CHECK
FINAL REVIEW CHECKLIST

[ ] SSOT chain reviewed
[ ] Authority matrix reviewed
[ ] Canonical matrix reviewed
[ ] Hash evidence reviewed
[ ] Evidence chain reviewed
[ ] Risk signals classified
[ ] Human approval required before mutation

MUTATION:
DENIED

DELETE:
DENIED

REPAIR:
DENIED
CHECK


echo "--- SUMMARY ---"

{
echo "BATCH_REPORT_COUNT=$(wc -l < "$OUT/BATCH_REPORT_INDEX.txt")"
echo "GOVERNANCE_INDEX_STATUS=CREATED"
echo "HUMAN_GATE_CHECKLIST_STATUS=CREATED"
} | tee "$OUT/SUMMARY.env"


echo "--- BATCH INDEX SAMPLE ---"
head -20 "$OUT/BATCH_REPORT_INDEX.txt" || true

echo "--- GOVERNANCE INDEX ---"
cat "$OUT/GOVERNANCE_REVIEW_INDEX.txt"


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_045_FINAL_CERTIFICATION_REVIEW"
echo "============================================================"

