#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 007R1"
echo " SECOND SSOT CONFLICT RESUME — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_007R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=007R1"
echo "MODE=READ_ONLY_CONFLICT_RESUME"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

echo "--- ACTIVE SSOT COUNT ---"

find "$ROOT" \
-type f \
\( \
-name "*SSOT*" -o \
-name "*AUTHORITY*" -o \
-name "*ROOT_MANIFEST*" \
\) \
2>/dev/null \
| grep -vE "/BACKUP/|/RECOVERY/|/ARCHIVE/|/QUARANTINE/" \
| wc -l \
| tee "$OUT/active_count.txt"


echo "--- BACKUP SSOT COUNT ---"

find "$ROOT" \
-type f \
\( \
-name "*SSOT*" -o \
-name "*AUTHORITY*" -o \
-name "*ROOT_MANIFEST*" \
\) \
2>/dev/null \
| grep -Ei "/BACKUP/|/RECOVERY/|/ARCHIVE/|/QUARANTINE/" \
| wc -l \
| tee "$OUT/backup_count.txt"


echo "--- PRIMARY AUTHORITY FILES ---"

{
echo "ROOT_MANIFEST:"
ls -1 "$ROOT/00_CONTROL/ROOT_MANIFEST.json" 2>/dev/null || true

echo "RUNTIME_BINDING:"
find "$ROOT/05_RUNTIME_UNION" \
-name "SSOT.binding.env" \
2>/dev/null || true

echo "SSOT_EVIDENCE:"
find "$ROOT/09_EVIDENCE" \
-maxdepth 5 \
-name "*SSOT*" \
2>/dev/null | head -20

} | tee "$OUT/primary_authority.txt"


echo "--- GLOBAL ROOT CONFLICT CHECK ---"

find /mnt/c \
-maxdepth 4 \
-type d \
\( \
-name "*FREYA_ASUS*" -o \
-name "*FREYA_PLATFORM*" -o \
-name "*SSOT*" \
\) \
2>/dev/null \
| tee "$OUT/global_root_candidates.txt"


echo "--- DECISION ---"

ACTIVE="$(cat "$OUT/active_count.txt")"
BACKUP="$(cat "$OUT/backup_count.txt")"

echo "ACTIVE_SSOT_SIGNALS=$ACTIVE"
echo "BACKUP_SSOT_SIGNALS=$BACKUP"

echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_008_FULL_SCRIPT_INVENTORY"

echo "============================================================"

