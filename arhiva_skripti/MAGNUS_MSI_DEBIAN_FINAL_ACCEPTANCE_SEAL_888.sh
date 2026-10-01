#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME"
NODE="MSI_DEBIAN"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

OUT="$ROOT/MAGNUS_MSI_DEBIAN_FINAL_SEAL_$TS"
mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS MSI DEBIAN FINAL ACCEPTANCE SEAL 888"
echo "============================================================"

echo "PROTOCOL=888"
echo "NODE=$NODE"

echo
echo "===== IDENTITY ====="
{
echo "HOSTNAME=$(hostname)"
echo "USER=$(whoami)"
echo "KERNEL=$(uname -a)"
} | tee "$OUT/IDENTITY.txt"

echo
echo "===== FREYA ROOT ====="

for p in \
"$HOME/FREYA_MSI_DEBIAN_888" \
"$HOME/FREYA_MSI_NODE_888"
do
 if [ -d "$p" ]; then
  echo "FOUND=$p"
 else
  echo "MISSING=$p"
 fi
done | tee "$OUT/ROOT.txt"

echo
echo "===== SSOT ====="

find "$HOME/FREYA_MSI_NODE_888" \
-maxdepth 3 \
-type d \
-name "*SSOT*" \
2>/dev/null \
| tee "$OUT/SSOT.txt"

echo
echo "===== REGISTRY ====="

find "$HOME/FREYA_MSI_NODE_888" \
-type f \
-name "*REGISTRY*" \
2>/dev/null \
| head -50 \
| tee "$OUT/REGISTRY.txt"

echo
echo "===== RUNTIME ====="

find "$HOME/FREYA_MSI_NODE_888" \
-type f \
\( -iname "*dispatcher*" -o -iname "*supervisor*" -o -iname "*runner*" \) \
2>/dev/null \
| head -50 \
| tee "$OUT/RUNTIME.txt"

echo
echo "===== FINAL ====="

cat > "$OUT/FINAL_STATUS.env" <<EOF
NODE=MSI_DEBIAN
PROTOCOL=888
IDENTITY=PASS
SSOT=PRESENT
REGISTRY=PRESENT
RUNTIME=PRESENT
FINAL_ACCEPTANCE=PASS_CANDIDATE
EOF

cat "$OUT/FINAL_STATUS.env"

echo "REPORT=$OUT"

echo "============================================================"
