#!/bin/sh
set -eu
umask 077
r=/root/FREYA_IPHONE_ISH_NODE_888
s="$r/03_ARHIVA/SOBE_IOS_REFERENCE/SOBA_4_EXPORTS_AND_OUTBOX"
set -- 20_MARKETING_IDEJA.txt FREYA_INVESTOR_WHITE_PAPER.txt \
KNJIGA_ZENA_BALKANSKA_KOMPLET.txt \
ZENA_BALKANSKA_PRODUCER_CUT.txt FREYA_SREDNJA_KLASA.txt
cd "$s"
for f do
  [ -f "$f" ] && [ ! -L "$f" ] || exit 3
done
d=$(mktemp -d "$r/04_HUMAN_GATE/SOBE_TEKSTOVI_XXXXXX")
sha256sum "$@" > "$d/IZVORI.sha256"
tar -czf "$d/NACRTI.tar.gz" "$@"
sha256sum -c "$d/IZVORI.sha256"
cd "$d"
tar -tzf NACRTI.tar.gz
sha256sum NACRTI.tar.gz > SHA256SUMS
sha256sum -c SHA256SUMS
printf '%s\n' 'HUMAN_REVIEW=PENDING' \
'CONTENT_VALIDATED=NO' 'EXTERNAL_SEND=NONE' > STATUS.txt
echo "REVIEW=$d"
