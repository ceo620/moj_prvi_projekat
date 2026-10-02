#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 089R1"
echo " HUMAN GATE PYTHON REMEDIATION DECISION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_089R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=089R1"
echo "MODE=READ_ONLY_HUMAN_GATE_PYTHON_REMEDIATION_DECISION"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/PLATFORM_STATUS.txt"
: > "$OUT/PACKAGE_MANAGER_STATUS.txt"
: > "$OUT/PYTHON_PACKAGE_CANDIDATES.txt"
: > "$OUT/HUMAN_GATE_DECISION.txt"

{
echo "===== PLATFORM ====="
cat /etc/os-release 2>/dev/null || true
echo
echo "KERNEL=$(uname -srmo 2>/dev/null || true)"
echo "USER=$(id -un)"
echo "UID=$(id -u)"
} | tee "$OUT/PLATFORM_STATUS.txt"

APT_STATUS="MISSING"
command -v apt-get >/dev/null 2>&1 && APT_STATUS="AVAILABLE"

DPKG_STATUS="MISSING"
command -v dpkg >/dev/null 2>&1 && DPKG_STATUS="AVAILABLE"

PYTHON3_STATUS="MISSING"
command -v python3 >/dev/null 2>&1 && PYTHON3_STATUS="AVAILABLE"

{
echo "APT_GET_STATUS=$APT_STATUS"
echo "DPKG_STATUS=$DPKG_STATUS"
echo "PYTHON3_STATUS=$PYTHON3_STATUS"
} | tee "$OUT/PACKAGE_MANAGER_STATUS.txt"

if command -v apt-cache >/dev/null 2>&1; then
  {
    echo "===== python3 ====="
    apt-cache policy python3 2>/dev/null || true

    echo
    echo "===== python3-minimal ====="
    apt-cache policy python3-minimal 2>/dev/null || true

    echo
    echo "===== python3-venv ====="
    apt-cache policy python3-venv 2>/dev/null || true

    echo
    echo "===== python3-pip ====="
    apt-cache policy python3-pip 2>/dev/null || true
  } > "$OUT/PYTHON_PACKAGE_CANDIDATES.txt"
else
  echo "APT_CACHE=NOT_AVAILABLE" > "$OUT/PYTHON_PACKAGE_CANDIDATES.txt"
fi

if command -v dpkg >/dev/null 2>&1; then
  {
    echo
    echo "===== INSTALLED PYTHON-RELATED PACKAGES ====="
    dpkg -l 2>/dev/null | grep -Ei '^ii[[:space:]]+python|^ii[[:space:]]+libpython' || true
  } >> "$OUT/PYTHON_PACKAGE_CANDIDATES.txt"
fi

cat > "$OUT/HUMAN_GATE_DECISION.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

PYTHON_REMEDIATION_DECISION_STATUS=PREPARED

KNOWN_BLOCKER=PYTHON3_REQUIRED_BY_ACTIVE_ASUS_PATH

CANONICAL_PYTHON_COUNT=16
ACTIVE_AGENT_PYTHON_COUNT=18

PYTHON3_STATUS=$PYTHON3_STATUS
APT_GET_STATUS=$APT_STATUS
DPKG_STATUS=$DPKG_STATUS

PROPOSED_MINIMUM_REMEDIATION=INSTALL_PYTHON3_ONLY
OPTIONAL_FUTURE_COMPONENTS=PYTHON3_VENV_AND_PIP_ONLY_IF_LATER_PROVEN_REQUIRED

INSTALL_EXECUTED=NO
APT_UPDATE_EXECUTED=NO
UPGRADE_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

AUTOMATIC_INSTALL=DISABLED
AUTOMATIC_UPGRADE=DISABLED
AUTOMATIC_EXECUTION=DISABLED

INSTALL_ALLOWED=NO
UPGRADE_ALLOWED=NO
MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO
NETWORK_WRITE_ALLOWED=NO

HUMAN_GATE_DECISION=REQUIRED
STATUS

echo
echo "--- HUMAN GATE DECISION ---"
cat "$OUT/HUMAN_GATE_DECISION.txt"

echo
echo "--- PACKAGE CANDIDATES ---"
cat "$OUT/PYTHON_PACKAGE_CANDIDATES.txt"

echo "============================================================"
echo "RESULT=HOLD"
echo "BLOCKER=HUMAN_GATE_APPROVAL_REQUIRED_FOR_PYTHON3_INSTALLATION"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_089R2_PYTHON_INSTALLATION_PLAN"
echo "============================================================"
