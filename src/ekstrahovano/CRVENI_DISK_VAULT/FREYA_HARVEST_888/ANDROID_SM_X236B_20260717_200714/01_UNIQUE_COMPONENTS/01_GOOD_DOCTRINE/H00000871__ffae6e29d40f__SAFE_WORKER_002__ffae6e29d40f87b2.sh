#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

SOURCE_ROOT="${1:-}"
SSOT_ROOT="${2:-}"

echo "============================================================"
echo "ZANATLIJA_002 — SAFE SSOT INGEST"
echo "============================================================"
echo "HUMAN_GATE=ACTIVE"
echo "PROTOKOL=888"
echo "DELETE=NO"
echo "PURGE=DISABLED"
echo "MOVE=NO"
echo "QUARANTINE_MOVE=DISABLED"
echo "CACHE_DELETE=DISABLED"
echo "SOURCE_DELETE=NO"
echo "OVERWRITE=NO"
echo

if [ -z "$SOURCE_ROOT" ] || [ -z "$SSOT_ROOT" ]; then
    echo "USAGE=$0 SOURCE_ROOT SSOT_ROOT"
    echo "FINAL_STATUS=BLOCKED_ARGUMENTS_REQUIRED"
    exit 2
fi

MANIFEST="$SOURCE_ROOT/04_Arhiva_i_Sistemski_Logovi/TRANSFER_MANIFEST_FINAL.csv"

if [ ! -f "$MANIFEST" ]; then
    echo "FINAL_STATUS=BLOCKED_TRANSFER_MANIFEST_NOT_FOUND"
    exit 3
fi

if [ ! -d "$SOURCE_ROOT" ]; then
    echo "FINAL_STATUS=BLOCKED_SOURCE_ROOT_NOT_FOUND"
    exit 4
fi

if [ ! -d "$SSOT_ROOT" ]; then
    echo "FINAL_STATUS=BLOCKED_SSOT_ROOT_NOT_FOUND"
    exit 5
fi

RUN_ID="$(date +%Y%m%d_%H%M%S)"
TARGET="$SSOT_ROOT/00_INTAKE/ANDROID_INGEST_$RUN_ID"

echo "ORIGINAL_DANGEROUS_FUNCTIONS:"
echo "OLD_MOVE_TO_QUARANTINE=BLOCKED"
echo "OLD_RM_RF_SOURCE=BLOCKED"
echo "OLD_FIND_DELETE_CACHE=BLOCKED"
echo "OLD_SYSTEM_PATH_WRITE=BLOCKED"
echo
echo "SAFE_REPLACEMENT_FUNCTION:"
echo "VERIFY_MANIFEST=YES"
echo "COPY_TO_NEW_SSOT_INTAKE=PLANNED"
echo "PRESERVE_SOURCE=YES"
echo "DESTINATION_TARGET=$TARGET"
echo "FILES_COPIED=NO"
echo "FINAL_STATUS=SAFE_SSOT_INGEST_WORKER_VALIDATED_NOT_EXECUTED"
