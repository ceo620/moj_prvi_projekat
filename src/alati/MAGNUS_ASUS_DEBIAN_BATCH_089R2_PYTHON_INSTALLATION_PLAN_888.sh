#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 089R2"
echo " PYTHON INSTALLATION PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_089R2_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=089R2"
echo "MODE=READ_ONLY_PYTHON_INSTALLATION_PLAN"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/APT_SOURCE_STATUS.txt"
: > "$OUT/APT_METADATA_STATUS.txt"
: > "$OUT/PYTHON_PACKAGE_STATUS.txt"
: > "$OUT/INSTALLATION_PLAN.txt"

echo "===== APT SOURCES =====" | tee "$OUT/APT_SOURCE_STATUS.txt"

if [[ -f /etc/apt/sources.list ]]; then
    cat /etc/apt/sources.list | tee -a "$OUT/APT_SOURCE_STATUS.txt"
fi

if [[ -d /etc/apt/sources.list.d ]]; then
    find /etc/apt/sources.list.d \
      -maxdepth 1 \
      -type f \
      -print \
      -exec sh -c 'echo "--- $1 ---"; cat "$1"' _ {} \; \
      2>/dev/null | tee -a "$OUT/APT_SOURCE_STATUS.txt"
fi

SOURCE_SIGNAL_COUNT="$(
    grep -Ehc '^[[:space:]]*(deb |Types: deb)' \
      /etc/apt/sources.list \
      /etc/apt/sources.list.d/* \
      2>/dev/null |
    awk '{s+=$1} END {print s+0}'
)"

APT_LIST_FILE_COUNT="$(
    find /var/lib/apt/lists \
      -maxdepth 1 \
      -type f \
      2>/dev/null |
    wc -l |
    tr -d ' '
)"

{
echo "SOURCE_SIGNAL_COUNT=$SOURCE_SIGNAL_COUNT"
echo "APT_LIST_FILE_COUNT=$APT_LIST_FILE_COUNT"
} | tee "$OUT/APT_METADATA_STATUS.txt"

echo "===== PYTHON PACKAGE POLICY =====" | tee "$OUT/PYTHON_PACKAGE_STATUS.txt"

for pkg in python3 python3-minimal python3-venv python3-pip; do
    echo "--- $pkg ---" | tee -a "$OUT/PYTHON_PACKAGE_STATUS.txt"
    apt-cache policy "$pkg" 2>/dev/null \
      | tee -a "$OUT/PYTHON_PACKAGE_STATUS.txt" || true
done

PYTHON3_CANDIDATE="$(
    apt-cache policy python3 2>/dev/null |
    awk '/Candidate:/ {print $2; exit}'
)"

PYTHON3_CANDIDATE="${PYTHON3_CANDIDATE:-NONE}"

if [[ "$PYTHON3_CANDIDATE" != "NONE" && "$PYTHON3_CANDIDATE" != "(none)" ]]; then
    PACKAGE_METADATA_READINESS="READY"
    PROPOSED_ACTION="HUMAN_GATE_INSTALL_PYTHON3_ONLY"
else
    PACKAGE_METADATA_READINESS="NOT_READY"
    PROPOSED_ACTION="APT_METADATA_REFRESH_REQUIRES_SEPARATE_HUMAN_GATE"
fi

cat > "$OUT/INSTALLATION_PLAN.txt" <<PLAN
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

KNOWN_BLOCKER=PYTHON3_REQUIRED_BY_ACTIVE_ASUS_PATH

CANONICAL_PYTHON_COUNT=16
ACTIVE_AGENT_PYTHON_COUNT=18

APT_SOURCE_SIGNAL_COUNT=$SOURCE_SIGNAL_COUNT
APT_LIST_FILE_COUNT=$APT_LIST_FILE_COUNT

PYTHON3_CANDIDATE=$PYTHON3_CANDIDATE
PACKAGE_METADATA_READINESS=$PACKAGE_METADATA_READINESS

PROPOSED_ACTION=$PROPOSED_ACTION

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

NETWORK_WRITE_ALLOWED=NO
INSTALL_ALLOWED=NO
MUTATION_ALLOWED=NO

HUMAN_GATE_REQUIRED=YES
PLAN

echo
echo "--- INSTALLATION PLAN ---"
cat "$OUT/INSTALLATION_PLAN.txt"

echo "============================================================"

if [[ "$PACKAGE_METADATA_READINESS" == "READY" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=HUMAN_APPROVAL_REQUIRED_FOR_MINIMAL_PYTHON3_INSTALL"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R3_MINIMAL_PYTHON3_INSTALL_HUMAN_GATE"
else
    echo "RESULT=HOLD"
    echo "BLOCKER=APT_METADATA_NOT_READY"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_089R2R1_APT_METADATA_REMEDIATION_PLAN"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
