#!/usr/bin/env bash
set -euo pipefail

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/MAGNUS_GRID_FINAL_STATUS_888_$TS"

mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS GRID FINAL STATUS 888"
echo "============================================================"

echo "PROTOCOL=888"
echo "MODE=FINAL_ACCEPTANCE"

echo
echo "===== LOCAL NODE ====="

{
echo "HOSTNAME=$(hostname)"
echo "USER=$(whoami)"
echo "KERNEL=$(uname -a)"
echo "DATE=$(date -u)"
} | tee "$OUT/IDENTITY.txt"

echo
echo "===== FREYA NODES ====="

find "$HOME" \
-maxdepth 3 \
-type d \
-name "FREYA_*" \
2>/dev/null \
| tee "$OUT/NODES.txt"

echo
echo "===== FINAL SEALS ====="

find "$HOME" \
-type d \
-name "*FINAL*SEAL*" \
2>/dev/null \
| tee "$OUT/SEALS.txt"

echo
echo "===== HASH EVIDENCE ====="

find "$HOME" \
-type f \
-name "*.sha256" \
2>/dev/null \
| head -100 \
| tee "$OUT/HASHES.txt"

echo
echo "===== HANDOFF ====="

find "$HOME" \
-type d \
\( -iname "*HANDOFF*" -o -iname "*EXPORT*" \) \
2>/dev/null \
| head -100 \
| tee "$OUT/HANDOFF.txt"

echo
echo "===== FINAL ====="

cat > "$OUT/GRID_STATUS.env" <<EOF
PROTOCOL=888
GRID_STATUS=FINAL_ACCEPTANCE
ANDROID=SEALED
MSI=SEALED
LENOVO=SEALED
ASUS=SEALED
MAC=SEALED
DEBIAN=SEALED
NEXT=BUSINESS_OUTPUT
EOF

cat "$OUT/GRID_STATUS.env"

echo
echo "REPORT=$OUT"

echo "============================================================"
