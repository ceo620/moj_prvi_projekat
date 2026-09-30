#!/bin/bash
set -euo pipefail

LOCK_FILE="/dev/shm/titan_factory_engine.runtime_lock"
WATCH_DIR="/mnt/d/FREYA_ZONE/DROP_ZONE"
TARGET_ARS="/mnt/d/FREYA_ZONE/projects/active/ARS_METAL"
TARGET_FIN="/mnt/d/FREYA_ZONE/FINANCE"
QUARANTINE_DIR="/mnt/d/FREYA_ZONE/00_QUARANTINE"
VAULT_DIR="/mnt/d/FREYA_ZONE/vault/checksums"

if [ -e "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "Unknown")
    echo "Kritična greška: Daemon je već pokrenut pod PID-om $PID." >&2
    exit 1
fi
echo $$ > "$LOCK_FILE"

cleanup() {
    rm -f "$LOCK_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] TITAN V4 ugašen. Lock očišćen."
}
trap cleanup INT TERM EXIT

mkdir -p "$TARGET_ARS" "$TARGET_FIN" "$QUARANTINE_DIR"

process_queue() {
    find "$WATCH_DIR" -type f 2>/dev/null | while read -r file; do
        [ -f "$file" ] || continue
        local filename
        filename=$(basename "$file")
        
        local size1 size2
        size1=$(stat -c %s "$file")
        sleep 3
        size2=$(stat -c %s "$file")
        if [ "$size1" -ne "$size2" ]; then
            continue
        fi

        if [[ ! "$filename" =~ \.([jJ][sS][oO][nN]|[mM][dD]|[xX][lL][sS][xX])$ ]]; then
            mv "$file" "$QUARANTINE_DIR/"
            continue
        fi

        local dest_dir=""
        if [[ "$filename" =~ [Aa][Rr][Ss]_[Mm][Ee][Tt][Aa][Ll] ]]; then
            dest_dir="$TARGET_ARS"
        elif [[ "$filename" =~ [Ff][Ii][Nn][Aa][Nn][Cc][Ee] ]]; then
            dest_dir="$TARGET_FIN"
        else
            mv "$file" "$QUARANTINE_DIR/"
            continue
        fi

        local dest_file="$dest_dir/$filename"
        mv "$file" "$dest_file"

        local sha256_hash
        sha256_hash=$(sha256sum "$dest_file" | awk '{print $1}')
        echo "$sha256_hash  $dest_file" > "$VAULT_DIR/${filename}.sha256"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] Procesuiran: $filename"
    done
}

echo "TITAN PROTOKOL 888 V4 Daemon inicijalizovan pod PID: $$"
while true; do
    process_queue
    sleep 60
done
