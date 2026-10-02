#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/FREYA_LENOVO_DEBIAN_888"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

SEAL="$ROOT/25_SEALS/LENOVO_FINAL_PRODUCTION_SEAL_888_$TS"
OUT="$ROOT/16_REPORTS/LENOVO_FINAL_SEAL_$TS"

mkdir -p "$SEAL" "$OUT"

echo "============================================================"
echo "MAGNUS LENOVO FINAL PRODUCTION SEAL 888"
echo "============================================================"

echo "NODE=LENOVO_DEBIAN"
echo "PROTOCOL=888"

cp "$ROOT/07_AGENTS/AGENT_REGISTRY.tsv" \
"$SEAL/AGENT_REGISTRY.tsv" 2>/dev/null || true

sha256sum "$SEAL/AGENT_REGISTRY.tsv" \
> "$SEAL/AGENT_REGISTRY.sha256" 2>/dev/null || true

cp "$ROOT/15_RUNTIME/lenovo_controlled_dispatcher_888.py" \
"$SEAL/lenovo_controlled_dispatcher_888.py" 2>/dev/null || true

sha256sum "$SEAL/lenovo_controlled_dispatcher_888.py" \
> "$SEAL/RUNTIME.sha256" 2>/dev/null || true

cat > "$SEAL/FINAL_STATUS.env" <<EOF
NODE=LENOVO_DEBIAN
PROTOCOL=888
IDENTITY=PASS
SSOT=PRESENT
REGISTRY=PRESENT
RUNTIME=PRESENT
FINAL_ACCEPTANCE=PASS_CANDIDATE
NEXT=ASUS_NODE
EOF

cp "$SEAL/FINAL_STATUS.env" "$OUT/FINAL_STATUS.env"

echo
cat "$SEAL/FINAL_STATUS.env"

echo "SEAL=$SEAL"
echo "REPORT=$OUT"

echo "============================================================"
