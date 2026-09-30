#!/bin/bash

# Skripta za provjeru integriteta fajlova prije slanja na digitalno potpisivanje
TARGET_FILE=$1
CHECKSUM_DIR="/mnt/d/FREYA_ZONE/vault/checksums"

if [ -z "$TARGET_FILE" ] || [ ! -f "$TARGET_FILE" ]; then
    echo "GRESKA: Navedite validnu putanju do fajla."
    exit 1
fi

FILENAME=$(basename "$TARGET_FILE")
RECORDED_SHA_FILE="$CHECKSUM_DIR/${FILENAME}.sha256"

if [ ! -f "$RECORDED_SHA_FILE" ]; then
    echo "STATUS: KRITIČNO - Kontrolna suma za ovaj dokument ne postoji u trezoru (Vault)!"
    exit 2
fi

RECORDED_SHA=$(cat "$RECORDED_SHA_FILE")
CURRENT_SHA=$(sha256sum "$TARGET_FILE" | awk '{print $1}')

if [ "$RECORDED_SHA" == "$CURRENT_SHA" ]; then
    echo "STATUS: VERIFIKOVAN (100% Integritet) - Dokument je spreman za potpis."
    exit 0
else
    echo "STATUS: KONTAMINIRAN! Fajl je izmijenjen nakon izlaska iz Document Factory sistema."
    exit 3
fi
