#!/bin/sh
set -eu
umask 077
export LC_ALL=C TZ=UTC

B="FREYA_IPHONE_B03_IMPORT_LANE_STABILIZATION"
C="/root/freya_audit/00_CONTROL"
O="$C/BATCHES/$B/${B}_$(date -u +%Y%m%dT%H%M%SZ)_PID$$"
L="$C/SCRIPTS/FREYA_IPHONE_SHA256_IMPORT_LAUNCHER.sh"
mkdir -p "$O"

{
    printf '%s\n' "/mnt" "/root/Downloads" "/root"
    find /mnt -mindepth 1 -maxdepth 2 -type d 2>/dev/null || true
} | awk '!seen[$0]++' > "$O/IMPORT_ROOTS.txt"

cat > "$L.tmp.$$" <<'LAUNCH'
#!/bin/sh
set -eu
umask 077

[ "$#" -eq 1 ] || {
    echo "USAGE: $0 EXPECTED_SHA256"
    exit 2
}

X="$1"
case "$X" in
    [0-9a-fA-F][0-9a-fA-F]*)
        [ "${#X}" -eq 64 ] || exit 2
        ;;
    *) exit 2 ;;
esac

M="$(mktemp)"
trap 'rm -f "$M"' EXIT

for R in /mnt /root/Downloads; do
    [ -d "$R" ] || continue
    find "$R" -type f 2>/dev/null |
    while IFS= read -r F; do
        [ "$(sha256sum "$F" 2>/dev/null | awk '{print $1}')" = "$X" ] &&
        printf '%s\n' "$F"
    done
done | sort -u > "$M"

N="$(wc -l < "$M" | tr -d ' ')"
printf '%s\n' "MATCH_COUNT=$N"

[ "$N" -eq 1 ] || {
    printf '%s\n' \
    "RESULT=HOLD" \
    "BLOCKED_REASON=SHA256_MATCH_COUNT_$N" \
    "SCRIPT_EXIT_CODE=1" \
    "LAUNCHER_COMPLETED=YES"
    exit 1
}

F="$(cat "$M")"
printf '%s\n' \
"RESULT=PASS" \
"VERIFIED_FILE=$F" \
"ACTUAL_SHA256=$(sha256sum "$F" | awk '{print $1}')" \
"EXECUTED=NO" \
"SCRIPT_EXIT_CODE=0" \
"LAUNCHER_COMPLETED=YES"
LAUNCH

chmod 700 "$L.tmp.$$"
sh -n "$L.tmp.$$"

if [ -e "$L" ]; then
    A="$(sha256sum "$L" | awk '{print $1}')"
    N="$(sha256sum "$L.tmp.$$" | awk '{print $1}')"
    if [ "$A" != "$N" ]; then
        rm -f "$L.tmp.$$"
        R=HOLD
        X=IMPORT_LAUNCHER_CONFLICT
    else
        rm -f "$L.tmp.$$"
        R=PASS
        X=NONE
    fi
else
    mv "$L.tmp.$$" "$L"
    R=PASS
    X=NONE
fi

{
printf '%s\n' \
"PROTOCOL=888" \
"NODE=FREYA_IPHONE_ISH_NODE_888" \
"BATCH_ID=$B" \
"RESULT=$R" \
"BLOCKED_REASON=$X" \
"IMPORT_METHOD=IOS_MOUNT_OR_ON_MY_IPHONE" \
"SEARCH_POLICY=SHA256_ONLY" \
"IMPORT_LAUNCHER=$L" \
"IMPORT_LAUNCHER_SHA256=$(sha256sum "$L" 2>/dev/null | awk '{print $1}')" \
"FOUND_FILE_EXECUTION=NO" \
"NETWORK_ACTION=NONE" \
"INSTALL_ACTION=NONE"
} > "$O/BATCH_RECEIPT.txt"

sha256sum "$O/BATCH_RECEIPT.txt" "$O/IMPORT_ROOTS.txt" > "$O/EVIDENCE_MANIFEST.sha256"

cat "$O/BATCH_RECEIPT.txt"
printf '%s\n' \
"EVIDENCE_DIR=$O" \
"EVIDENCE_MANIFEST_SHA256=$(sha256sum "$O/EVIDENCE_MANIFEST.sha256" | awk '{print $1}')" \
"CHECKPOINT_STATE=$([ "$R" = PASS ] && echo IMPORT_LANE_SEALED || echo HOLD)" \
"NEXT_BATCH=$([ "$R" = PASS ] && echo FREYA_IPHONE_B04_LEGACY_RISK_CENSUS || echo FREYA_IPHONE_B03_R1_RECOVERY)" \
"SCRIPT_EXIT_CODE=$([ "$R" = PASS ] && echo 0 || echo 1)" \
"LAUNCHER_COMPLETED=YES"

[ "$R" = PASS ]
