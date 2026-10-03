#!/bin/sh
set -eu
[ "$#" -eq 1 ] || exit 2
r=/root/FREYA_IPHONE_ISH_NODE_888
s=$1
case "$s" in "$r"/03_ARHIVA/*/*.tar.gz) ;; *) exit 2;; esac
[ -f "$s" ] && [ ! -L "$s" ] || exit 3
[ "$(stat -c %s "$s")" -le 10485760 ] || exit 4
umask 077
h=$(sha256sum "$s")
gzip -t "$s"
d=$(mktemp -d "$r/04_HUMAN_GATE/SOBE_IZVOZ_XXXXXX")
cp "$s" "$d/PAKET.tar.gz"
cmp "$s" "$d/PAKET.tar.gz"
[ "$(sha256sum "$s")" = "$h" ] || exit 5
cd "$d"
sha256sum PAKET.tar.gz > SHA256SUMS
sha256sum -c SHA256SUMS
printf '%s\n' 'HUMAN_REVIEW=PENDING' \
'EXTERNAL_COPY=NO' > STATUS.txt
echo "REVIEW=$d"
