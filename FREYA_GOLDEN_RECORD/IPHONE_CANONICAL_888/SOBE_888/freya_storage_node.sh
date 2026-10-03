#!/bin/sh
set -eu
umask 077
r=/root/FREYA_IPHONE_ISH_NODE_888
sh "$r/05_SYSTEM_RUNTIME/SOBE_888/titan_self_heal.sh"
d=$(mktemp -d "$r/03_ARHIVA/SOBE_BACKUP_XXXXXX")
tar -czf "$d/SOBE_RUNTIME.tar.gz" \
-C / root/FREYA_IPHONE_ISH_NODE_888/05_SYSTEM_RUNTIME/SOBE_888 usr/local/bin/freya-sobe
gzip -t "$d/SOBE_RUNTIME.tar.gz"
tar -tzf "$d/SOBE_RUNTIME.tar.gz" >/dev/null
sh "$r/05_SYSTEM_RUNTIME/SOBE_888/titan_self_heal.sh"
cd "$d"
sha256sum SOBE_RUNTIME.tar.gz > SHA256SUMS
sha256sum -c SHA256SUMS
printf '%s\n' 'SCOPE=SOBE_CODE_AND_LAUNCHER' \
'FULL_IPHONE_BACKUP=NO' 'EXTERNAL_COPY=NO' > STATUS.txt
echo "BACKUP=$d"
