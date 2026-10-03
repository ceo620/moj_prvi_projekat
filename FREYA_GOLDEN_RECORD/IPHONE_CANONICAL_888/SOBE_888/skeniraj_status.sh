#!/bin/sh
set -eu
echo "PROTOCOL=888; HUMAN_GATE=ACTIVE"
date -u
free -m
r=/root/FREYA_IPHONE_ISH_NODE_888
echo "POSLJEDNJI_CHECKPOINT — NIJE NOVI TEST"
p="$r/05_SYSTEM_RUNTIME/STATE/CHECKPOINT.env"
if [ -f "$p" ]; then
  ls -l "$p"
  cat "$p"
else
  echo "CHECKPOINT=MISSING"
  exit 1
fi
