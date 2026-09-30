#!/usr/bin/env bash
# ======================================================================
# TITAN PROTOKOL 888 - QUARANTINE FORENSIC VALIDATOR [2026]
# ARS METAL INDUSTRIES - SECURITY LAYER
# ======================================================================

BASE_DIR="/mnt/d/FREYA_ZONE"
QUARANTINE="$BASE_DIR/00_QUARANTINE"
VAULT="$BASE_DIR/vault/checksums"
LOG_FILE="$BASE_DIR/logs/quarantine_audit.log"

log_audit() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$1] $2" >> "$LOG_FILE"
}

echo "=== INICIJALIZACIJA PREGLEDA KARANTINA ==="

if [ ! -d "$QUARANTINE" ] || [ -z "$(ls -A "$QUARANTINE" 2>/dev/null)" ]; then
    echo "STATUS: Karantin je čist. Nema suspendovanih payload dokumenata."
    exit 0
fi

for file_path in "$QUARANTINE"/*; do
    [ -f "$file_path" ] || continue
    filename=$(basename -- "$file_path")
    
    echo "--------------------------------------------------"
    echo "Analiza fajla: $filename"
    
    # Provera podudaranja sa trezorom (Vault)
    RECORDED_SHA_FILE="$VAULT/${filename}.sha256"
    
    if [ ! -f "$RECORDED_SHA_FILE" ]; then
        log_audit "ALERT" "Fajl $filename je anoniman. Nema generisan otisak u trezoru!"
        echo "STATUS: ANONIMAN PAYLOAD (Kritično - Nepoznato poreklo)"
        continue
    fi
    
    # Izračunavanje trenutnog stanja
    CURRENT_SHA=$(sha256sum "$file_path" | awk '{print $1}')
    RECORDED_SHA=$(cat "$RECORDED_SHA_FILE" 2>/dev/null)
    
    if [ "$CURRENT_SHA" == "$RECORDED_SHA" ]; then
        log_audit "INTEGRITY-OK" "Fajl $filename ima validan potpis ali je izolovan zbog strukture imena."
        echo "STATUS: INTEGRITET VALIDAN (Izolovan zbog anomalije u nazivu/ekstenziji)"
    else
        log_audit "TAMPERED" "CRITICAL: Fajl $filename je modifikovan unutar karantinske zone!"
        echo "STATUS: KONTAMINIRAN! Sadržaj je menjan nakon presretanja."
    fi
done
