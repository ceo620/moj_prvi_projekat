#!/bin/sh
set -eu
[ "$#" -eq 1 ] || exit 2
s=$1
case "$s" in /*) ;; *) exit 2;; esac
[ -f "$s" ] && [ ! -L "$s" ] || exit 3
[ "$(stat -c %s "$s")" -le 1048576 ] || exit 4
umask 077
r=/root/FREYA_IPHONE_ISH_NODE_888
d=$(mktemp -d "$r/04_HUMAN_GATE/SOBE_PRIJEM_XXXXXX")
mkdir "$d/PODACI"
h=$(sha256sum "$s")
cp "$s" "$d/PODACI/${s##*/}"
cmp "$s" "$d/PODACI/${s##*/}"
[ "$(sha256sum "$s")" = "$h" ] || exit 5
printf '%s\n' "$s" > "$d/IZVOR.txt"
echo "HUMAN_REVIEW=PENDING" > "$d/STATUS.txt"
echo "REVIEW=$d"
