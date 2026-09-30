#!/data/data/com.termux/files/usr/bin/bash

set -u

RUN_ID="$(date +%Y%m%d_%H%M%S)"
BASE="$HOME/ANDROID_DOCTRINES_FOR_MAC_$RUN_ID"
CONTROL="$BASE/00_CONTROL"
DOCTRINES="$BASE/01_ANDROID_DOCTRINES"

ZIP="$HOME/ANDROID_DOCTRINES_FOR_MAC_$RUN_ID.zip"
ZIP_SHA="$ZIP.sha256"

CANDIDATES="$CONTROL/01_CANDIDATE_PATHS.txt"
MANIFEST="$CONTROL/02_DOCTRINE_MANIFEST.tsv"
ERRORS="$CONTROL/03_ERRORS.log"
STATUS="$CONTROL/04_STATUS.txt"

mkdir -p "$CONTROL" "$DOCTRINES"

: > "$CANDIDATES"
: > "$ERRORS"
printf 'SHA256\tSIZE_BYTES\tSOURCE_PATH\tPACKAGE_PATH\n' > "$MANIFEST"

echo "============================================================"
echo "ANDROID TERMUX — PREPARE DOCTRINES FOR MAC"
echo "============================================================"
echo "HUMAN_GATE=Danijela_Djurovic_Keskin"
echo "PROTOKOL=888"
echo "SOURCE_DEVICE=ANDROID_TERMUX"
echo "TARGET_DEVICE=MACBOOK_AIR"
echo "ACTION=DISCOVER_COPY_PACKAGE_ONLY"
echo "DELETE=NO"
echo "MOVE_ORIGINALS=NO"
echo "RENAME_ORIGINALS=NO"
echo "EXECUTE_DISCOVERED_CONTENT=NO"
echo "SCRIPT_FILES_INCLUDED=NO"
echo "DAEMON_START=NO"
echo "AUTO_INTERNET=NO"
echo "TRANSFER_TO_MAC=NOT_STARTED"
echo

ROOTS=("$HOME")

[ -d "/storage/emulated/0" ] && ROOTS+=("/storage/emulated/0")
[ -d "/storage/2983-487E" ] && ROOTS+=("/storage/2983-487E")
[ -d "/storage/DADB-D2A1" ] && ROOTS+=("/storage/DADB-D2A1")

is_script_file() {
    case "${1,,}" in
        *.sh|*.bash|*.zsh|*.fish|*.py|*.pyc|*.ps1|*.bat|*.cmd|*.command|\
        *.exe|*.apk|*.jar|*.js|*.jsx|*.ts|*.tsx|*.php|*.pl|*.rb|*.go|\
        *.rs|*.c|*.cc|*.cpp|*.h|*.hpp|*.class|*.dex|*.so)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

is_doctrine_path() {
    local lower="${1,,}"

    case "$lower" in
        *doctrine*|*doctrines*|*doktrina*|*doktrine*|\
        *governance*|*human_gate*|*"human gate"*|*human-gate*|\
        *protocol*|*protokol*|*ssot*|\
        *evidence_first*|*"evidence first"*|*evidence-first*|\
        *script_governance*|*"script governance"*|*script-governance*|\
        *daemon_orchestrator*|*"daemon orchestrator"*|*daemon-orchestrator*|\
        *freya_titan_doctrine*|*"freya titan doctrine"*|\
        *android_doctrine*|*"android doctrine"*|\
        *termux_doctrine*|*"termux doctrine"*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

for ROOT in "${ROOTS[@]}"
do
    [ -d "$ROOT" ] || continue

    find "$ROOT" -type f -print0 2>>"$ERRORS" |
    while IFS= read -r -d '' SRC
    do
        case "$SRC" in
            "$BASE"/*|"$ZIP"|"$ZIP_SHA"|\
            "$HOME"/ANDROID_DOCTRINES_FOR_MAC_*.zip|\
            "$HOME"/ANDROID_DOCTRINES_FOR_MAC_*.zip.sha256)
                continue
                ;;
        esac

        is_script_file "$SRC" && continue
        is_doctrine_path "$SRC" || continue

        printf '%s\n' "$SRC"
    done
done | sort -u > "$CANDIDATES"

while IFS= read -r SRC
do
    [ -f "$SRC" ] || continue

    HASH="$(sha256sum "$SRC" 2>>"$ERRORS" | awk '{print $1}')"
    [ -n "$HASH" ] || continue

    SIZE="$(stat -c '%s' "$SRC" 2>/dev/null || wc -c < "$SRC" 2>/dev/null || echo UNKNOWN)"
    NAME="$(basename "$SRC" | tr '/\r\n\t' '_____')"
    DEST="$DOCTRINES/${HASH}_${NAME}"

    if [ ! -e "$DEST" ]; then
        if cp -p -- "$SRC" "$DEST" 2>>"$ERRORS"; then
            printf '%s\t%s\t%s\t%s\n' \
                "$HASH" "$SIZE" "$SRC" "$DEST" >> "$MANIFEST"
        fi
    fi
done < "$CANDIDATES"

CANDIDATE_COUNT="$(wc -l < "$CANDIDATES" | tr -d ' ')"
DOCUMENT_COUNT="$(find "$DOCTRINES" -type f 2>/dev/null | wc -l | tr -d ' ')"
ERROR_COUNT="$(wc -l < "$ERRORS" | tr -d ' ')"

cat > "$STATUS" <<EOF
============================================================
ANDROID DOCTRINES FOR MAC — STATUS
============================================================
CREATED_AT=$(date -Iseconds 2>/dev/null || date)
HUMAN_GATE=Danijela_Djurovic_Keskin
PROTOKOL=888

SOURCE_DEVICE=ANDROID_TERMUX
TARGET_DEVICE=MACBOOK_AIR
SEARCH_ROOTS=${ROOTS[*]}

CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT
DOCTRINE_DOCUMENTS_PACKAGED=$DOCUMENT_COUNT
ERROR_LOG_LINES=$ERROR_COUNT

SCRIPT_FILES_INCLUDED=NO
ORIGINALS_DELETED=NO
ORIGINALS_MOVED=NO
ORIGINALS_RENAMED=NO
DISCOVERED_CONTENT_EXECUTED=NO
DAEMON_STARTED=NO
TRANSFER_TO_MAC=NOT_STARTED
EOF

echo "CANDIDATE_PATHS_FOUND=$CANDIDATE_COUNT"
echo "DOCTRINE_DOCUMENTS_PACKAGED=$DOCUMENT_COUNT"
echo "ERROR_LOG_LINES=$ERROR_COUNT"

if [ "$DOCUMENT_COUNT" -eq 0 ]; then
    echo "STATUS_FILE=$STATUS"
    echo "FINAL_STATUS=BLOCKED_NO_ANDROID_DOCTRINES_FOUND"
    exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
    echo "ZIP_COMMAND_FOUND=NO"
    echo "AUTO_INSTALL_ATTEMPTED=NO"
    echo "FINAL_STATUS=BLOCKED_ZIP_COMMAND_NOT_INSTALLED"
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
FINAL_STATUS=ANDROID_DOCTRINES_READY_FOR_MAC_TRANSFER
EOF

echo
echo "ZIP_PATH=$ZIP"
echo "ZIP_SIZE_BYTES=$ZIP_SIZE"
echo "ZIP_SHA256=$ZIP_HASH"
echo "SHA256_FILE=$ZIP_SHA"
echo "SCRIPT_FILES_INCLUDED=NO"
echo "ORIGINALS_CHANGED=NO"
echo "TRANSFER_TO_MAC=NOT_STARTED"
echo "FINAL_STATUS=ANDROID_DOCTRINES_READY_FOR_MAC_TRANSFER"
echo "============================================================"
