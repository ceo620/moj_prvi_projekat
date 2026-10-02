#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 002"
echo " CANONICAL ROOT DISCOVERY — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_002_$START_UTC"

mkdir -p "$OUT"

echo "PROTOCOL=888" > "$OUT/BATCH.env"
echo "MACHINE=ASUS" >> "$OUT/BATCH.env"
echo "NODE=FREYA_ASUS_DEBIAN_888" >> "$OUT/BATCH.env"
echo "BATCH=002" >> "$OUT/BATCH.env"
echo "MODE=READ_ONLY_DISCOVERY" >> "$OUT/BATCH.env"
echo "START_UTC=$START_UTC" >> "$OUT/BATCH.env"

CANDIDATES=(
"/mnt/c/FREYA_ASUS_888"
"/mnt/c/FREYA_ASUS_LIVE_DOCUMENT_FACTORY_888"
"/mnt/c/FREYA_ASUS_NODE_888"
"/mnt/c/FREYA_ASUS_RED_DISK_P0_BACKUP_888"
"/mnt/c/FREYA_PLATFORM_2_0"
)

echo "=== CANDIDATE MAP ==="

for P in "${CANDIDATES[@]}"; do
    echo "------------------------------------------------"
    echo "PATH=$P"

    if [ -e "$P" ]; then
        echo "STATUS=EXISTS"

        stat "$P" > "$OUT/$(basename "$P")_stat.txt" 2>/dev/null || true

        du -sh "$P" 2>/dev/null || true

        echo "--- TOP LEVEL ---"
        find "$P" -maxdepth 1 -mindepth 1 -printf "%f\n" 2>/dev/null | head -50

        echo "--- MARKERS ---"
        find "$P" -maxdepth 3 \
        \( \
        -iname "*SSOT*" -o \
        -iname "*MANIFEST*" -o \
        -iname "*AGENT*" -o \
        -iname "*FACTORY*" -o \
        -iname "*DOCUMENT*" -o \
        -iname "*QUEUE*" -o \
        -iname "*BACKUP*" -o \
        -iname "*ROLLBACK*" \
        \) 2>/dev/null | head -100

    else
        echo "STATUS=NOT_FOUND"
    fi
done | tee "$OUT/CANONICAL_ROOT_DISCOVERY.txt"

echo "=== GLOBAL ASUS SEARCH ==="

find /mnt/c \
-maxdepth 3 \
\( -iname "*FREYA_ASUS*" -o -iname "*FREYA_PLATFORM*" \) \
2>/dev/null | tee "$OUT/ASUS_ROOT_SEARCH.txt"

echo "=== HASHABLE ROOT SUMMARY ==="

for P in "${CANDIDATES[@]}"; do
    if [ -d "$P" ]; then
        echo "ROOT=$P"
        find "$P" -maxdepth 2 -type f 2>/dev/null | wc -l | awk '{print "FILES_LEVEL2="$1}'
    fi
done | tee "$OUT/ROOT_SUMMARY.txt"

echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_003_ASUS_EXISTING_FACTORY_DISCOVERY"
echo "============================================================"

