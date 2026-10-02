#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 089R2R3"
echo " HUMAN GATE — APT UPDATE ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_089R2R3_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=089R2R3"
echo "MODE=HUMAN_GATE_APT_UPDATE_ONLY"
echo "START_UTC=$START_UTC"

echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_089R2R3_APT_UPDATE_ONLY"

echo "ALLOW=APT_GET_UPDATE_ONLY"
echo "INSTALL=DENY"
echo "UPGRADE=DENY"
echo "DIST_UPGRADE=DENY"
echo "PYTHON_INSTALL=DENY"
echo "AGENT_EXECUTION=DENY"
echo "DELETE=DENY"
echo "FORMAT=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/PREFLIGHT.txt"
: > "$OUT/APT_UPDATE_OUTPUT.txt"
: > "$OUT/POST_UPDATE_STATUS.txt"

echo "===== PREFLIGHT ====="

APT_GET="$(command -v apt-get || true)"

if [[ -z "$APT_GET" ]]; then
    echo "APT_GET=NOT_FOUND" | tee "$OUT/PREFLIGHT.txt"
    echo "RESULT=HOLD"
    echo "BLOCKER=APT_GET_NOT_FOUND"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

{
echo "APT_GET=$APT_GET"
echo "USER=$(id -un)"
echo "UID=$(id -u)"
echo "SUDO_STATUS=$(command -v sudo >/dev/null 2>&1 && echo AVAILABLE || echo MISSING)"
echo "PYTHON3_BEFORE=$(command -v python3 >/dev/null 2>&1 && python3 --version 2>&1 || echo MISSING)"
} | tee "$OUT/PREFLIGHT.txt"

echo
echo "===== HUMAN GATE MUTATION ====="
echo "ACTION=APT_GET_UPDATE_ONLY"

set +e

if [[ "$(id -u)" -eq 0 ]]; then
    apt-get update 2>&1 | tee "$OUT/APT_UPDATE_OUTPUT.txt"
    UPDATE_RC=${PIPESTATUS[0]}
elif command -v sudo >/dev/null 2>&1; then
    sudo apt-get update 2>&1 | tee "$OUT/APT_UPDATE_OUTPUT.txt"
    UPDATE_RC=${PIPESTATUS[0]}
else
    echo "ERROR=SUDO_NOT_AVAILABLE_AND_NOT_ROOT" | tee "$OUT/APT_UPDATE_OUTPUT.txt"
    UPDATE_RC=126
fi

set -e

echo
echo "===== POST UPDATE VALIDATION ====="

PYTHON3_CANDIDATE="$(
    apt-cache policy python3 2>/dev/null |
    awk '/Candidate:/ {print $2; exit}'
)"

PYTHON3_INSTALLED="$(
    apt-cache policy python3 2>/dev/null |
    awk '/Installed:/ {print $2; exit}'
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

PYTHON3_CANDIDATE="${PYTHON3_CANDIDATE:-NONE}"
PYTHON3_INSTALLED="${PYTHON3_INSTALLED:-NONE}"

{
echo "APT_UPDATE_RC=$UPDATE_RC"
echo "APT_LIST_FILE_COUNT=$APT_LIST_FILE_COUNT"
echo "APT_LIST_TOTAL_COUNT=$APT_LIST_TOTAL_COUNT"

echo "PYTHON3_INSTALLED=$PYTHON3_INSTALLED"
echo "PYTHON3_CANDIDATE=$PYTHON3_CANDIDATE"

echo "INSTALL_EXECUTED=NO"
echo "UPGRADE_EXECUTED=NO"
echo "DIST_UPGRADE_EXECUTED=NO"
echo "PYTHON_INSTALL_EXECUTED=NO"
echo "AGENT_EXECUTION_EXECUTED=NO"
} | tee "$OUT/POST_UPDATE_STATUS.txt"

echo "============================================================"

if [[ "$UPDATE_RC" -ne 0 ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=APT_UPDATE_FAILED"
    echo "REPORT_DIR=$OUT"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R2R3R1_APT_UPDATE_FAILURE_ANALYSIS"

elif [[ "$PYTHON3_CANDIDATE" == "NONE" || "$PYTHON3_CANDIDATE" == "(none)" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=PYTHON3_CANDIDATE_STILL_NOT_AVAILABLE"
    echo "REPORT_DIR=$OUT"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R2R3R2_PACKAGE_INDEX_ANALYSIS"

else

    echo "RESULT=PASS"
    echo "REPORT_DIR=$OUT"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R3_MINIMAL_PYTHON3_INSTALL_HUMAN_GATE"

fi

echo "============================================================"
