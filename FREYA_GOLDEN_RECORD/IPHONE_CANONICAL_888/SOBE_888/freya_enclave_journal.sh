#!/bin/sh
set -eu
[ "$#" -eq 1 ] && [ -n "$1" ] || exit 2
umask 077
r=/root/FREYA_IPHONE_ISH_NODE_888
p="$r/05_SYSTEM_RUNTIME/STATE/SOBE_DNEVNIK.txt"
[ ! -L "$p" ] || exit 3
[ ! -e "$p" ] || [ -f "$p" ] || exit 3
{
  /usr/bin/flock -x 9
  printf '%s | %s\n' "$(date -u +%FT%TZ)" "$1" >&9
} 9>>"$p"
echo "JOURNAL_APPEND=PASS; ENCRYPTED=NO"
