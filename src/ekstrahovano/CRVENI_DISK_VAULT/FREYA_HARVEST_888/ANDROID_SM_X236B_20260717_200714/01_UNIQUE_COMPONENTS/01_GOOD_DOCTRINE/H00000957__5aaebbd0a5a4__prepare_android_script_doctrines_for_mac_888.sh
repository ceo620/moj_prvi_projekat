#!/data/data/com.termux/files/usr/bin/bash

set -u

RUN_ID="$(date +%Y%m%d_%H%M%S)"
BASE="$HOME/ANDROID_SCRIPT_DOCTRINES_FOR_MAC_$RUN_ID"
CONTROL="$BASE/00_CONTROL"
DOCS="$BASE/01_DOCTRINE_DOCUMENTS"
ZIP="$HOME/ANDROID_SCRIPT_DOCTRINES_FOR_MAC_$RUN_ID.zip"
ZIP_SHA="$ZIP.sha256"

mkdir -p "$CONTROL" "$DOCS"

MANIFEST="$CONTROL/01_DOCTRINE_MANIFEST.tsv"
ERRORS="$CONTROL/02_ERRORS.log"
CANDIDATES="$CONTROL/03_CANDIDATE_PATHS.txt"
STATUS="$CONTROL/04_STATUS.txt"

printf 'SHA256\tSIZE_BYTES\tSOURCE_PATH\tPACKAGE_PATH\n' > "$MANIFEST"
: > "$ERRORS"
: > "$CANDIDATES"

echo "============================================================"
echo "ANDROID TERMUX — SCRIPT DOCTRINE PACKAGE FOR MAC"
echo "============================================================"
echo "HUMAN_GATE=Danijela_Djurovic_Keskin"
echo "PROTOKOL=888"
echo "ACTION=FIND_COPY_PACKAGE_DOCTRINE_DOCUMENTS"
echo "SCRIPT_FILES_INCLUDED=NO"
echo "DELETE=NO"
echo "MOVE_ORIGINALS=NO"
echo "RENAME_ORIGINALS=NO"
echo "EXECUTE_DISCOVERED_CONTENT=NO"
echo "TRANSFER_TO_MAC=NOT_STARTED"
echo

ROOTS=("$HOME")

[ -d "/storage/emulated/0" ] && ROOTS+=("/storage/emulated/0")
[ -d "/storage/2983-487E" ] && ROOTS+=("/storage/2983-487E")
[ -d "/storage/DADB-D2A1" ] && ROOTS+=("/storage/DADB-D2A1")

find "${ROOTS[@]}" -type f 2>>"$ERRORS" |
awk -v base="$BASE" -v zip="$ZIP" '
BEGIN { IGNORECASE=1 }
{
    path=$0
    name=path
    sub(/^.*\//, "", name)

    if (index(path, base)==1 || path==zip || path==zip ".sha256") next

    if (name ~ /\.(sh|bash|zsh|fish|py|pyc|ps1|bat|cmd|command|exe|apk|jar|js|jsx|ts|tsx|php|pl|rb|go|rs|c|cc|cpp|h|hpp|class|dex|so)$/) next

    if (
        path ~ /(doctrine|doctrines|doktrina|doktrine|governance|human[_ -]?gate|protocol|protokol|ssot|evidence[_ -]?first|script[_ -]?governance|daemon[_ -]?orchestrator)/ &&
        path ~ /(android|termux|freya|titan|script|skript|daemon|relay|mobile|tablet)/
    ) print path
}' |
sort -u > "$CANDIDATES"

while IFS= read -r SRC
do
    [ -f "$SRC" ] || continue

    HASH="$(sha256sum "$SRC" 2>>"$ERRORS" | awk '{print $1}')"
    [ -n "$HASH" ] || continue

    SIZE="$(stat -c '%s' "$SRC" 2>/dev/null || wc -c < "$SRC" 2>/dev/null || echo UNKNOWN)"
    NAME="$(basename "$SRC" | tr '/\r\n\t' '_____')"
    DEST="$DOCS/${HASH}_${NAME}"

    if [ ! -e "$DEST" ]; then
        if cp -p -- "$SRC" "$DEST" 2>>"$ERRORS"; then
            printf '%s\t%s\t%s\t%s\n' \
                "$HASH" "$SIZE" "$SRC" "$DEST" >> "$MANIFEST"
        fi
    fi
done < "$CANDIDATES"

DOC_COUNT="$(find "$DOCS" -type f 2>/dev/null | wc -l | tr -d ' ')"
CANDIDATE_COUNT="$(wc -l < "$CANDIDATES" 2>/dev/null | tr -d ' ')"
ERROR_COUNT="$(wc -l < "$ERRORS" 2>/dev/null | tr -d ' ')"

cat > "$STATUS" <<EOF
============================================================
ANDROID SCRIPT DOCTRINES — PACKAGE STATUS
============================================================
CREATED_AT=$(date -Iseconds 2>/dev/null || date)
HUMAN_GATE=Danijela_Djurovic_Keskin
PROTOKOL=888

SOURCE_DEVICE=ANDROID_TERMUX
TARGET_DEVICE=MACBOOK_AIR

SEARCH_ROOTS=${ROOTS[*]}
CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT
DOCTRINE_DOCUMENTS_PACKAGED=$DOC_COUNT
ERROR_LOG_LINES=$ERROR_COUNT

SCRIPT_FILES_INCLUDED=NO
ORIGINALS_DELETED=NO
ORIGINALS_MOVED=NO
ORIGINALS_RENAMED=NO
DISCOVERED_CONTENT_EXECUTED=NO
TRANSFER_TO_MAC=NOT_STARTED
EOF

if ! command -v zip >/dev/null 2>&1; then
    echo "ZIP_COMMAND_FOUND=NO"
    echo "FINAL_STATUS=BLOCKED_ZIP_PACKAGE_NOT_INSTALLED"
    echo "NEXT_SAFE_ACTION=RUN_pkg_install_zip"
    exit 1
fi

cd "$HOME" || exit 1
zip -qr "$ZIP" "$(basename "$BASE")"

if [ ! -f "$ZIP" ]; then
    echo "FINAL_STATUS=BLOCKED_ZIP_NOT_CREATED"
    exit 1
fi

ZIP_HASH="$(sha256sum "$ZIP" | awk '{print $1}')"
ZIP_SIZE="$(stat -c '%s' "$ZIP" 2>/dev/null || wc -c < "$ZIP")"

printf '%s  %s\n' "$ZIP_HASH" "$(basename "$ZIP")" > "$ZIP_SHA"

cat >> "$STATUS" <<EOF

ZIP_PATH=$ZIP
ZIP_SIZE_BYTES=$ZIP_SIZE
ZIP_SHA256=$ZIP_HASH
SHA256_FILE=$ZIP_SHA
FINAL_STATUS=ANDROID_SCRIPT_DOCTRINES_READY_FOR_MAC_WIFI_TRANSFER
EOF

echo
echo "CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT"
echo "DOCTRINE_DOCUMENTS_PACKAGED=$DOC_COUNT"
echo "ERROR_LOG_LINES=$ERROR_COUNT"
echo "ZIP_PATH=$ZIP"
echo "ZIP_SIZE_BYTES=$ZIP_SIZE"
echo "ZIP_SHA256=$ZIP_HASH"
echo "SHA256_FILE=$ZIP_SHA"
echo "SCRIPT_FILES_INCLUDED=NO"
echo "ORIGINALS_CHANGED=NO"
echo "TRANSFER_TO_MAC=NOT_STARTED"
echo "FINAL_STATUS=ANDROID_SCRIPT_DOCTRINES_READY_FOR_MAC_WIFI_TRANSFER"
