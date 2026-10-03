#!/bin/sh
set -eu
[ "$#" -eq 0 ] || exit 2
unset ENV BASH_ENV PYTHONPATH PYTHONHOME
export PATH=/usr/bin:/bin
r=/root/FREYA_IPHONE_ISH_NODE_888
exec /usr/bin/python3 -I -S -B \
"$r/15_RUNTIME/HUMAN_GATE_CONSOLE_V1/freya_gate.py"
