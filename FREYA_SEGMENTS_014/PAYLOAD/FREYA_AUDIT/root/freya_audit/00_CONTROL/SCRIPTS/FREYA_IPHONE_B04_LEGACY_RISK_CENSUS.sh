#!/bin/sh
set -eu
umask 077
export LC_ALL=C TZ=UTC

B="FREYA_IPHONE_B04_LEGACY_RISK_CENSUS"
C="/root/freya_audit/00_CONTROL"
O="$C/BATCHES/$B/${B}_$(date -u +%Y%m%dT%H%M%SZ)_PID$$"
mkdir -p "$O"

ps -ef > "$O/PROCESSES.txt" 2>/dev/null ||
ps > "$O/PROCESSES.txt" 2>/dev/null || true

{
for F in \
    /etc/crontabs/root \
    /etc/crontab \
    /etc/local.d \
    /etc/init.d \
    /root/.profile \
    /root/.ashrc \
    /root/.shrc
do
    [ -e "$F" ] && printf '%s\n' "$F"
done
} > "$O/AUTOSTART_PATHS.txt"

{
find /root/freya_audit /root/CENTRALNI_MODUL_UCENJA \
    -type f \( -name '*.sh' -o -name '*.py' \) 2>/dev/null |
while IFS= read -r F; do
    M="$(grep -Eil \
    'curl|wget|ssh|scp|nc |netcat|socket|smtp|sendmail|cron|crond|daemon|nohup|heartbeat|while[[:space:]]+true|sleep[[:space:]]+[0-9]+' \
    "$F" 2>/dev/null || true)"
    [ -n "$M" ] && printf '%s\n' "$F"
done
} | sort -u > "$O/RISK_SCRIPT_PATHS.txt"

ACTIVE_NET="$(
grep -Ei 'ssh|scp|curl|wget|nc |netcat|smtp|sendmail' \
"$O/PROCESSES.txt" 2>/dev/null |
grep -v 'grep' || true
)"

ACTIVE_DAEMON="$(
grep -Ei 'cron|crond|daemon|nohup|heartbeat' \
"$O/PROCESSES.txt" 2>/dev/null |
grep -v 'grep' || true
)"

NET_COUNT="$(printf '%s\n' "$ACTIVE_NET" | sed '/^$/d' | wc -l | tr -d ' ')"
DAEMON_COUNT="$(printf '%s\n' "$ACTIVE_DAEMON" | sed '/^$/d' | wc -l | tr -d ' ')"
SCRIPT_COUNT="$(wc -l < "$O/RISK_SCRIPT_PATHS.txt" | tr -d ' ')"
AUTO_COUNT="$(wc -l < "$O/AUTOSTART_PATHS.txt" | tr -d ' ')"

R=PASS
X=NONE
[ "$NET_COUNT" -eq 0 ] || {
    R=HOLD
    X=ACTIVE_NETWORK_CAPABLE_PROCESS_FOUND
}

printf '%s\n' "$ACTIVE_NET" > "$O/ACTIVE_NETWORK_PROCESSES.txt"
printf '%s\n' "$ACTIVE_DAEMON" > "$O/ACTIVE_DAEMON_PROCESSES.txt"

{
printf '%s\n' \
"PROTOCOL=888" \
"NODE=FREYA_IPHONE_ISH_NODE_888" \
"BATCH_ID=$B" \
"RESULT=$R" \
"BLOCKED_REASON=$X" \
"PROCESS_CENSUS=COMPLETE" \
"AUTOSTART_PATH_COUNT=$AUTO_COUNT" \
"RISK_SCRIPT_COUNT=$SCRIPT_COUNT" \
"ACTIVE_NETWORK_PROCESS_COUNT=$NET_COUNT" \
"ACTIVE_DAEMON_PROCESS_COUNT=$DAEMON_COUNT" \
"CLASSIFICATION_POLICY=KEEP_REVIEW_QUARANTINE_DENY" \
"FILES_MODIFIED=NO" \
"PROCESSES_TERMINATED=NO" \
"CRON_MODIFIED=NO" \
"NETWORK_ACTION=NONE"
} > "$O/BATCH_RECEIPT.txt"

sha256sum "$O"/*.txt > "$O/EVIDENCE_MANIFEST.sha256"

cat "$O/BATCH_RECEIPT.txt"
printf '%s\n' \
"EVIDENCE_DIR=$O" \
"EVIDENCE_MANIFEST_SHA256=$(sha256sum "$O/EVIDENCE_MANIFEST.sha256" | awk '{print $1}')" \
"CHECKPOINT_STATE=$([ "$R" = PASS ] && echo LEGACY_RISK_CENSUS_SEALED || echo HOLD)" \
"NEXT_BATCH=$([ "$R" = PASS ] && echo FREYA_IPHONE_B05_COMPONENT_CLASSIFICATION || echo FREYA_IPHONE_B04_R1_TARGETED_RECOVERY)" \
"SCRIPT_EXIT_CODE=$([ "$R" = PASS ] && echo 0 || echo 1)" \
"LAUNCHER_COMPLETED=YES"

[ "$R" = PASS ]
