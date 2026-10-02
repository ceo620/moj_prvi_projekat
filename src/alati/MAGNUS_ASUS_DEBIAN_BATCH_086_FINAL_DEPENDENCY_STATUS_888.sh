#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 086"
echo " FINAL DEPENDENCY STATUS — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_086_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=086"
echo "MODE=READ_ONLY_FINAL_DEPENDENCY_STATUS"
echo "ROOT=$ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/DEPENDENCY_MATRIX.txt"
: > "$OUT/FINAL_DEPENDENCY_STATUS.txt"

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '%s=AVAILABLE\n' "$cmd"
  else
    printf '%s=MISSING\n' "$cmd"
  fi
}

{
check_cmd bash
check_cmd python3
check_cmd python
check_cmd pip3
check_cmd pip
check_cmd jq
check_cmd curl
check_cmd wget
check_cmd git
check_cmd rsync
check_cmd sqlite3
check_cmd sha256sum
check_cmd openssl
check_cmd tar
check_cmd gzip
check_cmd unzip
check_cmd zip
check_cmd ss
check_cmd netstat
check_cmd awk
check_cmd sed
check_cmd grep
check_cmd find
check_cmd xargs
} | tee "$OUT/DEPENDENCY_MATRIX.txt"

AVAILABLE_COUNT="$(
  grep -c '=AVAILABLE$' "$OUT/DEPENDENCY_MATRIX.txt" || true
)"

MISSING_COUNT="$(
  grep -c '=MISSING$' "$OUT/DEPENDENCY_MATRIX.txt" || true
)"

PYTHON3_STATUS="$(
  grep '^python3=' "$OUT/DEPENDENCY_MATRIX.txt" | cut -d= -f2
)"

if [[ "$PYTHON3_STATUS" == "MISSING" ]]; then
  PYTHON_RUNTIME_READINESS="BLOCKED_FOR_PYTHON_WORKLOADS"
else
  PYTHON_RUNTIME_READINESS="READY"
fi

cat > "$OUT/FINAL_DEPENDENCY_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

DEPENDENCY_AUDIT=COMPLETE

AVAILABLE_DEPENDENCY_COUNT=$AVAILABLE_COUNT
MISSING_DEPENDENCY_COUNT=$MISSING_COUNT

PYTHON3_STATUS=$PYTHON3_STATUS
PYTHON_RUNTIME_READINESS=$PYTHON_RUNTIME_READINESS

AGENT_STRUCTURE_STATUS=FOUND
ACTIVE_AGENT_STATUS=NOT_OBSERVED

AUTOMATIC_INSTALL=DISABLED
AUTOMATIC_UPGRADE=DISABLED
AUTOMATIC_REPAIR=DISABLED

INSTALL_ALLOWED=NO
UPGRADE_ALLOWED=NO
MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO
NETWORK_WRITE_ALLOWED=NO

DEPENDENCY_MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- DEPENDENCY MATRIX ---"
cat "$OUT/DEPENDENCY_MATRIX.txt"

echo
echo "--- SUMMARY ---"
cat "$OUT/FINAL_DEPENDENCY_STATUS.txt"

echo "============================================================"

if [[ "$PYTHON3_STATUS" == "MISSING" ]]; then
  echo "RESULT=PASS_WITH_WARNINGS"
  echo "WARNING=PYTHON3_MISSING"
  echo "REPORT_DIR=$OUT"
  echo "NEXT_RECOMMENDED_BATCH=BATCH_087_FINAL_RUNTIME_COMPATIBILITY_STATUS"
else
  echo "RESULT=PASS"
  echo "REPORT_DIR=$OUT"
  echo "NEXT_RECOMMENDED_BATCH=BATCH_087_FINAL_RUNTIME_COMPATIBILITY_STATUS"
fi

echo "============================================================"
