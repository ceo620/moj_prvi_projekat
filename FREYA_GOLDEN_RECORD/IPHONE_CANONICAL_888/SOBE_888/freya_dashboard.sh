#!/bin/sh
set -eu
r=/root/FREYA_IPHONE_ISH_NODE_888
echo "=== FREYA COMMAND CENTER · 888 ==="
sh "$r/05_SYSTEM_RUNTIME/SOBE_888/skeniraj_status.sh"
echo "=== POSLJEDNJIH 5 ZAPISA ==="
p="$r/05_SYSTEM_RUNTIME/STATE/SOBE_888_STATUS.log"
if [ -f "$p" ]; then
  tail -n 5 "$p"
else
  echo "LOG=MISSING"
fi
echo "SOBE: status i logger rucno testirani."
echo "Ostale funkcije: aktivacija nije potvrdjena."
echo "Zastita i rad 24/7: nisu provjereni."
