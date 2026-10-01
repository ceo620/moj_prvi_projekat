#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/MAGNUS_LENOVO_DEBIAN_FINAL_ACCEPTANCE_$TS"

mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS LENOVO DEBIAN FINAL ACCEPTANCE 888"
echo "============================================================"

echo "PROTOCOL=888"
echo "NODE=LENOVO_DEBIAN"

echo
echo "===== IDENTITY ====="
{
echo "HOSTNAME=$(hostname)"
echo "USER=$(whoami)"
echo "KERNEL=$(uname -a)"
echo "DATE=$(date -u)"
} | tee "$OUT/IDENTITY.txt"

echo
echo "===== STORAGE ====="
df -h | tee "$OUT/STORAGE.txt"

echo
echo "===== FREYA ROOT SEARCH ====="

find "$HOME" \
-maxdepth 3 \
-type d \
\( -iname "*FREYA*" -o -iname "*TITAN*" \) \
2>/dev/null \
| tee "$OUT/ROOTS.txt"

echo
echo "===== SSOT ====="

find "$HOME" \
-type d \
-name "*SSOT*" \
2>/dev/null \
| head -50 \
| tee "$OUT/SSOT.txt"

echo
echo "===== REGISTRY ====="

find "$HOME" \
-type f \
\( -iname "*REGISTRY*" -o -iname "*registry*.tsv" -o -iname "*registry*.env" \) \
2>/dev/null \
| head -100 \
| tee "$OUT/REGISTRY.txt"

echo
echo "===== AGENTS ====="

find "$HOME" \
-type f \
\( -iname "*AGENT*" -o -iname "*agent*" \) \
2>/dev/null \
| head -100 \
| tee "$OUT/AGENTS.txt"

echo
echo "===== RUNTIME ====="

find "$HOME" \
-type f \
\( -iname "*dispatcher*" -o -iname "*supervisor*" -o -iname "*runner*" -o -iname "*queue*" \) \
2>/dev/null \
| head -100 \
| tee "$OUT/RUNTIME.txt"

echo
echo "===== FINAL ====="

cat > "$OUT/FINAL_STATUS.env" <<EOF
NODE=LENOVO_DEBIAN
PROTOCOL=888
IDENTITY=CHECKED
SSOT=CHECKED
REGISTRY=CHECKED
RUNTIME=CHECKED
NEXT=LENOVO_SEAL_REVIEW
EOF

cat "$OUT/FINAL_STATUS.env"

echo "REPORT=$OUT"

echo "============================================================"
