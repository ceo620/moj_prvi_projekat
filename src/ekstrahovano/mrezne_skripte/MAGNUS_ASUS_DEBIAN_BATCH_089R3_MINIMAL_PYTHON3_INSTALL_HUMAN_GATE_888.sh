#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 089R3"
echo " HUMAN GATE — MINIMAL PYTHON3 INSTALL ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_089R3_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=089R3"
echo "MODE=HUMAN_GATE_INSTALL_PYTHON3_ONLY"
echo "START_UTC=$START_UTC"
echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_089R3_INSTALL_PYTHON3_ONLY"

echo "ALLOW=INSTALL_PYTHON3_ONLY"
echo "APT_UPDATE=DENY"
echo "UPGRADE=DENY"
echo "DIST_UPGRADE=DENY"
echo "PIP_INSTALL=DENY"
echo "VENV_INSTALL=DENY"
echo "AGENT_EXECUTION=DENY"
echo "SERVICE_START=DENY"
echo "DELETE=DENY"
echo "FORMAT=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/PREFLIGHT.txt"
: > "$OUT/INSTALL_OUTPUT.txt"
: > "$OUT/POST_INSTALL_STATUS.txt"

echo "===== PREFLIGHT ====="

PYTHON3_BEFORE="$(
  command -v python3 >/dev/null 2>&1 \
  && python3 --version 2>&1 \
  || echo MISSING
)"

PYTHON3_CANDIDATE="$(
  apt-cache policy python3 2>/dev/null |
  awk '/Candidate:/ {print $2; exit}'
)"

PYTHON3_CANDIDATE="${PYTHON3_CANDIDATE:-NONE}"

{
echo "USER=$(id -un)"
echo "UID=$(id -u)"
echo "APT_GET=$(command -v apt-get || echo NOT_FOUND)"
echo "SUDO_STATUS=$(command -v sudo >/dev/null 2>&1 && echo AVAILABLE || echo MISSING)"
echo "PYTHON3_BEFORE=$PYTHON3_BEFORE"
echo "PYTHON3_CANDIDATE=$PYTHON3_CANDIDATE"
} | tee "$OUT/PREFLIGHT.txt"

if [[ "$PYTHON3_CANDIDATE" == "NONE" || "$PYTHON3_CANDIDATE" == "(none)" ]]; then
  echo "RESULT=HOLD"
  echo "BLOCKER=PYTHON3_PACKAGE_CANDIDATE_NOT_AVAILABLE"
  echo "REPORT_DIR=$OUT"
  exit 0
fi

echo
echo "===== HUMAN GATE MUTATION ====="
echo "ACTION=INSTALL_PYTHON3_ONLY"

set +e

if [[ "$(id -u)" -eq 0 ]]; then
  apt-get install -y --no-install-recommends python3 \
    2>&1 | tee "$OUT/INSTALL_OUTPUT.txt"
  INSTALL_RC=${PIPESTATUS[0]}
elif command -v sudo >/dev/null 2>&1; then
  sudo apt-get install -y --no-install-recommends python3 \
    2>&1 | tee "$OUT/INSTALL_OUTPUT.txt"
  INSTALL_RC=${PIPESTATUS[0]}
else
  echo "ERROR=SUDO_NOT_AVAILABLE_AND_NOT_ROOT" \
    | tee "$OUT/INSTALL_OUTPUT.txt"
  INSTALL_RC=126
fi

set -e

echo
echo "===== POST INSTALL VALIDATION ====="

PYTHON3_PATH="$(command -v python3 2>/dev/null || true)"
PYTHON3_VERSION="$(
  python3 --version 2>&1 || true
)"

DPKG_PYTHON3_STATUS="$(
  dpkg-query -W \
    -f='${Status} ${Version}\n' \
    python3 2>/dev/null || true
)"

if [[ -n "$PYTHON3_PATH" ]]; then
  PYTHON3_STATUS="AVAILABLE"
else
  PYTHON3_STATUS="MISSING"
fi

{
echo "INSTALL_RC=$INSTALL_RC"
echo "PYTHON3_STATUS=$PYTHON3_STATUS"
echo "PYTHON3_PATH=${PYTHON3_PATH:-NONE}"
echo "PYTHON3_VERSION=${PYTHON3_VERSION:-NONE}"
echo "DPKG_PYTHON3_STATUS=${DPKG_PYTHON3_STATUS:-NONE}"

echo "APT_UPDATE_EXECUTED=NO"
echo "UPGRADE_EXECUTED=NO"
echo "DIST_UPGRADE_EXECUTED=NO"
echo "PIP_INSTALL_EXECUTED=NO"
echo "VENV_INSTALL_EXECUTED=NO"
echo "AGENT_EXECUTION_EXECUTED=NO"
echo "SERVICE_START_EXECUTED=NO"
} | tee "$OUT/POST_INSTALL_STATUS.txt"

echo "============================================================"

if [[ "$INSTALL_RC" -ne 0 ]]; then

  echo "RESULT=HOLD"
  echo "BLOCKER=PYTHON3_INSTALL_FAILED"
  echo "REPORT_DIR=$OUT"
  echo "NEXT_RECOMMENDED_BATCH=BATCH_089R3R1_PYTHON3_INSTALL_FAILURE_ANALYSIS"

elif [[ "$PYTHON3_STATUS" != "AVAILABLE" ]]; then

  echo "RESULT=HOLD"
  echo "BLOCKER=PYTHON3_NOT_AVAILABLE_AFTER_INSTALL"
  echo "REPORT_DIR=$OUT"
  echo "NEXT_RECOMMENDED_BATCH=BATCH_089R3R2_POST_INSTALL_PATH_ANALYSIS"

else

  echo "RESULT=PASS"
  echo "REPORT_DIR=$OUT"
  echo "NEXT_RECOMMENDED_BATCH=BATCH_090_POST_PYTHON_RUNTIME_VALIDATION"

fi

echo "============================================================"
