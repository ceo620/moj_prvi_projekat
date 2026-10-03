#!/bin/sh
set -eu
r=/root/FREYA_IPHONE_ISH_NODE_888
d="$r/05_SYSTEM_RUNTIME/SOBE_888"
umask 077
exec 9>>"$r/05_SYSTEM_RUNTIME/STATE/SOBE_SENTINEL.lock"
/usr/bin/flock -n 9 || exit 1
rc=0
/bin/sh "$d/titan_self_heal.sh" || rc=$?
/bin/sh "$d/javi_status.sh" "SENTINEL: integrity_exit=$rc"
exit "$rc"
