#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 089R2R1"
echo " APT METADATA + PYTHON CANDIDATE — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_089R2R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=089R2R1"
echo "MODE=READ_ONLY_APT_METADATA_AND_PYTHON_CANDIDATE"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/APT_SOURCE_FILES.txt"
: > "$OUT/APT_SOURCE_CONTENT.txt"
: > "$OUT/APT_METADATA_STATUS.txt"
: > "$OUT/PYTHON_POLICY.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== APT SOURCE FILES ====="

{
    [[ -f /etc/apt/sources.list ]] && printf '%s\n' /etc/apt/sources.list

    find /etc/apt/sources.list.d \
        -maxdepth 1 \
        -type f \
        \( -name '*.list' -o -name '*.sources' \) \
        -print 2>/dev/null || true
} | sort -u | tee "$OUT/APT_SOURCE_FILES.txt"

while IFS= read -r f; do
    [[ -f "$f" ]] || continue

    {
        echo "===== $f ====="
        cat "$f"
        echo
    } >> "$OUT/APT_SOURCE_CONTENT.txt"
done < "$OUT/APT_SOURCE_FILES.txt"

cat "$OUT/APT_SOURCE_CONTENT.txt"

SOURCE_FILE_COUNT="$(
    wc -l < "$OUT/APT_SOURCE_FILES.txt" | tr -d ' '
)"

SOURCE_SIGNAL_COUNT="$(
    grep -E \
        '^[[:space:]]*(deb[[:space:]]|Types:[[:space:]]*deb)' \
        "$OUT/APT_SOURCE_CONTENT.txt" \
        2>/dev/null |
    wc -l |
    tr -d ' '
)"

APT_LIST_FILE_COUNT="$(
    find /var/lib/apt/lists \
        -maxdepth 1 \
        -type f \
        2>/dev/null |
    wc -l |
    tr -d ' '
)"

APT_LIST_TOTAL_COUNT="$(
    find /var/lib/apt/lists \
        -mindepth 1 \
        -maxdepth 1 \
        2>/dev/null |
    wc -l |
    tr -d ' '
)"

{
echo "APT_SOURCE_FILE_COUNT=$SOURCE_FILE_COUNT"
echo "APT_SOURCE_SIGNAL_COUNT=$SOURCE_SIGNAL_COUNT"
echo "APT_LIST_FILE_COUNT=$APT_LIST_FILE_COUNT"
echo "APT_LIST_TOTAL_COUNT=$APT_LIST_TOTAL_COUNT"
} | tee "$OUT/APT_METADATA_STATUS.txt"

echo
echo "===== PYTHON PACKAGE POLICY ====="

for pkg in python3 python3-minimal python3-venv python3-pip; do
    echo "----- $pkg -----" | tee -a "$OUT/PYTHON_POLICY.txt"
    apt-cache policy "$pkg" 2>&1 \
        | tee -a "$OUT/PYTHON_POLICY.txt" || true
done

PYTHON3_CANDIDATE="$(
    apt-cache policy python3 2>/dev/null |
    awk '/Candidate:/ {print $2; exit}'
)"

PYTHON3_INSTALLED="$(
    apt-cache policy python3 2>/dev/null |
    awk '/Installed:/ {print $2; exit}'
)"

PYTHON3_CANDIDATE="${PYTHON3_CANDIDATE:-NONE}"
PYTHON3_INSTALLED="${PYTHON3_INSTALLED:-NONE}"

if [[ "$PYTHON3_CANDIDATE" != "NONE" &&
      "$PYTHON3_CANDIDATE" != "(none)" ]]; then

    PACKAGE_METADATA_READINESS="READY"
    BLOCKER="HUMAN_GATE_APPROVAL_REQUIRED_FOR_PYTHON3_INSTALL"

else
    PACKAGE_METADATA_READINESS="NOT_READY"
    BLOCKER="APT_METADATA_NOT_READY"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

KNOWN_BLOCKER=PYTHON3_REQUIRED_BY_ACTIVE_ASUS_PATH

CANONICAL_PYTHON_COUNT=16
ACTIVE_AGENT_PYTHON_COUNT=18

APT_SOURCE_FILE_COUNT=$SOURCE_FILE_COUNT
APT_SOURCE_SIGNAL_COUNT=$SOURCE_SIGNAL_COUNT
APT_LIST_FILE_COUNT=$APT_LIST_FILE_COUNT
APT_LIST_TOTAL_COUNT=$APT_LIST_TOTAL_COUNT

PYTHON3_INSTALLED=$PYTHON3_INSTALLED
PYTHON3_CANDIDATE=$PYTHON3_CANDIDATE

PACKAGE_METADATA_READINESS=$PACKAGE_METADATA_READINESS

TARGET_PACKAGE=python3
PYTHON3_VENV=DEFER
PYTHON3_PIP=DEFER

APT_UPDATE_EXECUTED=NO
INSTALL_EXECUTED=NO
UPGRADE_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

AUTOMATIC_INSTALL=DISABLED
AUTOMATIC_UPGRADE=DISABLED
AUTOMATIC_EXECUTION=DISABLED

INSTALL_ALLOWED=NO
NETWORK_WRITE_ALLOWED=NO
MUTATION_ALLOWED=NO

HUMAN_GATE_REQUIRED=YES
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"
echo "RESULT=HOLD"
echo "BLOCKER=$BLOCKER"
echo "REPORT_DIR=$OUT"

if [[ "$PACKAGE_METADATA_READINESS" == "READY" ]]; then
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R3_MINIMAL_PYTHON3_INSTALL_HUMAN_GATE"
else
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R2R2_APT_METADATA_REFRESH_DECISION"
fi

echo "============================================================"
