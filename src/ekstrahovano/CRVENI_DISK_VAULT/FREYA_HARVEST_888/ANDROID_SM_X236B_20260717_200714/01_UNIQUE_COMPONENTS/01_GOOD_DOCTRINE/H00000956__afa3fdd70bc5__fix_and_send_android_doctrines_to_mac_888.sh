#!/data/data/com.termux/files/usr/bin/bash

set -u

RUN_ID="$(date +%Y%m%d_%H%M%S)"
BASE="$HOME/ANDROID_SCRIPT_DOCTRINES_FOR_MAC_$RUN_ID"
CONTROL="$BASE/00_CONTROL"
DOCS="$BASE/01_DOCTRINE_DOCUMENTS"
ZIP="$HOME/ANDROID_SCRIPT_DOCTRINES_FOR_MAC_$RUN_ID.zip"
SHA_FILE="$ZIP.sha256"

MAC_USER="danijeladjurovic"
MAC_HOST="Danijelas-MacBook-Air.local"
MAC_DEST="Downloads"

mkdir -p "$CONTROL" "$DOCS"

CANDIDATES="$CONTROL/01_CANDIDATE_PATHS.txt"
MANIFEST="$CONTROL/02_DOCTRINE_MANIFEST.tsv"
ERRORS="$CONTROL/03_ERRORS.log"
STATUS="$CONTROL/04_STATUS.txt"

: > "$CANDIDATES"
: > "$ERRORS"
printf 'SHA256\tSIZE_BYTES\tSOURCE_PATH\tPACKAGE_PATH\n' > "$MANIFEST"

echo "============================================================"
echo "ANDROID → MAC — DOCTRINE PACKAGE AND WIFI TRANSFER"
echo "============================================================"
echo "HUMAN_GATE=Danijela_Djurovic_Keskin"
echo "PROTOKOL=888"
echo "DELETE=NO"
echo "MOVE_ORIGINALS=NO"
echo "RENAME_ORIGINALS=NO"
echo "SCRIPT_EXECUTION_FROM_CONTENT=NO"
echo "DAEMON_START=NO"
echo

ROOTS=("$HOME")
[ -d "/storage/emulated/0" ] && ROOTS+=("/storage/emulated/0")
[ -d "/storage/2983-487E" ] && ROOTS+=("/storage/2983-487E")
[ -d "/storage/DADB-D2A1" ] && ROOTS+=("/storage/DADB-D2A1")

find "${ROOTS[@]}" -type f 2>>"$ERRORS" |
grep -Ei \
'doctrine|doctrines|doktrina|doktrine|governance|human[_ -]?gate|protocol|protokol|ssot|evidence[_ -]?first|script[_ -]?governance|daemon[_ -]?orchestrator|freya[_ -]?titan[_ -]?doctrine' |
grep -Ei \
'android|termux|freya|titan|script|skript|daemon|relay|mobile|tablet|governance|doctrine|doktrina' |
grep -Eiv \
'\.(sh|bash|zsh|fish|py|pyc|ps1|bat|cmd|command|exe|apk|jar|js|jsx|ts|tsx|php|pl|rb|go|rs|c|cc|cpp|h|hpp|class|dex|so)$' |
grep -Fv "$BASE" |
grep -Fv "ANDROID_SCRIPT_DOCTRINES_FOR_MAC_" |
sort -u > "$CANDIDATES"

while IFS= read -r SRC
do
    [ -f "$SRC" ] || continue

    HASH="$(sha256sum "$SRC" 2>>"$ERRORS" | awk '{print $1}')"
    [ -n "$HASH" ] || continue

    SIZE="$(stat -c '%s' "$SRC" 2>/dev/null || echo UNKNOWN)"
    NAME="$(basename "$SRC" | tr '/\r\n\t' '_____')"
    DEST="$DOCS/${HASH}_${NAME}"

    if [ ! -e "$DEST" ]; then
        if cp -p -- "$SRC" "$DEST" 2>>"$ERRORS"; then
            printf '%s\t%s\t%s\t%s\n' \
                "$HASH" "$SIZE" "$SRC" "$DEST" >> "$MANIFEST"
        fi
    fi
done < "$CANDIDATES"

CANDIDATE_COUNT="$(wc -l < "$CANDIDATES" | tr -d ' ')"
DOC_COUNT="$(find "$DOCS" -type f | wc -l | tr -d ' ')"
ERROR_COUNT="$(wc -l < "$ERRORS" | tr -d ' ')"

if [ "$DOC_COUNT" -eq 0 ]; then
    echo "CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT"
    echo "DOCTRINE_DOCUMENTS_PACKAGED=0"
    echo "FINAL_STATUS=BLOCKED_NO_DOCTRINE_DOCUMENTS_FOUND"
    exit 1
fi

cat > "$STATUS" <<EOF
ANDROID_SCRIPT_DOCTRINES_FOR_MAC
CREATED_AT=$(date -Iseconds 2>/dev/null || date)
HUMAN_GATE=Danijela_Djurovic_Keskin
PROTOKOL=888
SOURCE_DEVICE=ANDROID_TERMUX
TARGET_DEVICE=MACBOOK_AIR
CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT
DOCTRINE_DOCUMENTS_PACKAGED=$DOC_COUNT
ERROR_LOG_LINES=$ERROR_COUNT
SCRIPT_FILES_INCLUDED=NO
ORIGINALS_DELETED=NO
ORIGINALS_MOVED=NO
ORIGINALS_RENAMED=NO
EOF

if ! command -v zip >/dev/null 2>&1; then
    pkg install -y zip || {
        echo "FINAL_STATUS=BLOCKED_ZIP_INSTALL_FAILED"
        exit 1
    }
fi

cd "$HOME" || exit 1
zip -qr "$ZIP" "$(basename "$BASE")"

[ -f "$ZIP" ] || {
    echo "FINAL_STATUS=BLOCKED_ZIP_NOT_CREATED"
    exit 1
}

ZIP_HASH="$(sha256sum "$ZIP" | awk '{print $1}')"
ZIP_SIZE="$(stat -c '%s' "$ZIP")"

printf '%s  %s\n' "$ZIP_HASH" "$(basename "$ZIP")" > "$SHA_FILE"

echo
echo "CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT"
echo "DOCTRINE_DOCUMENTS_PACKAGED=$DOC_COUNT"
echo "ZIP_PATH=$ZIP"
echo "ZIP_SIZE_BYTES=$ZIP_SIZE"
echo "ZIP_SHA256=$ZIP_HASH"
echo

echo "Testing Mac connection: $MAC_HOST"

if ! ping -c 1 -W 3 "$MAC_HOST" >/dev/null 2>&1; then
    echo "FINAL_STATUS=PACKAGE_READY_BUT_MAC_NOT_REACHABLE"
    echo "NEXT_SAFE_ACTION=CONFIRM_MAC_AND_ANDROID_ARE_ON_SAME_WIFI"
    exit 1
fi

echo "MAC_REACHABLE=YES"
echo "SCP_TRANSFER_STARTING=YES"
echo "Mac may ask for the Mac login password."
echo

scp -p "$ZIP" "$SHA_FILE" \
    "${MAC_USER}@${MAC_HOST}:~/${MAC_DEST}/"

SCP_RC=$?

echo
if [ "$SCP_RC" -eq 0 ]; then
    echo "TRANSFER_TO_MAC=COMPLETED"
    echo "MAC_DESTINATION=~/$MAC_DEST"
    echo "SOURCE_FILES_PRESERVED=YES"
    echo "FINAL_STATUS=ANDROID_DOCTRINES_SENT_TO_MAC"
else
    echo "TRANSFER_TO_MAC=FAILED"
    echo "PACKAGE_REMAINS_ON_ANDROID=YES"
    echo "FINAL_STATUS=PACKAGE_READY_SCP_REVIEW_REQUIRED"
fi
