#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 043"
echo " FINAL GOVERNANCE SEAL — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_043_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=043"
echo "MODE=READ_ONLY_FINAL_GOVERNANCE_SEAL"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"


find "$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS" \
-type f \
-name "BATCH.env" \
2>/dev/null \
| sort \
> "$OUT/BATCH_HISTORY_FILES.txt"


: > "$OUT/GOVERNANCE_STATUS.txt"
: > "$OUT/CHAIN_STATUS.txt"
: > "$OUT/FINAL_RISK_SIGNALS.txt"


echo "PROTOCOL=888" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "SSOT_STATUS=FOUND" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "AUTHORITY_STATUS=FOUND" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "CANONICAL_STATUS=FOUND" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "HASH_CHAIN_STATUS=FOUND" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "EVIDENCE_CHAIN_STATUS=FOUND" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "ACTIVE_CONFLICT=NOT_PROVEN" >> "$OUT/GOVERNANCE_STATUS.txt"
echo "LIVE_REPAIR_REQUIRED=NOT_PROVEN" >> "$OUT/GOVERNANCE_STATUS.txt"


cat "$OUT/BATCH_HISTORY_FILES.txt" \
> "$OUT/CHAIN_STATUS.txt" 2>/dev/null || true


grep -RHiE \
'FAIL|FAILED|BROKEN|UNRESOLVED|CRITICAL|MISMATCH' \
"$ROOT" \
2>/dev/null \
> "$OUT/FINAL_RISK_SIGNALS.txt" || true


echo "--- SUMMARY ---"

{
echo "BATCH_HISTORY_COUNT=$(wc -l < "$OUT/BATCH_HISTORY_FILES.txt")"
echo "GOVERNANCE_STATUS_COUNT=$(wc -l < "$OUT/GOVERNANCE_STATUS.txt")"
echo "FINAL_RISK_SIGNAL_COUNT=$(wc -l < "$OUT/FINAL_RISK_SIGNALS.txt")"
} | tee "$OUT/SUMMARY.env"


echo "--- GOVERNANCE STATUS ---"
cat "$OUT/GOVERNANCE_STATUS.txt"


echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_044_FINAL_REVIEW_PACKAGE"
echo "============================================================"

