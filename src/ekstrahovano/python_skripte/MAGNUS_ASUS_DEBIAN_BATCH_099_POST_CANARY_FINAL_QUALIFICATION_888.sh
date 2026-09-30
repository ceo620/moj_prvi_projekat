#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 099"
echo " POST CANARY FINAL QUALIFICATION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_PARENT="$ROOT/03_AGENTS_ACTIVE"
PACKAGE="VALIDATED_PENDING_RUNTIME"
AGENT_ROOT="$AGENT_PARENT/$PACKAGE"

REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_099_$START_UTC"

TARGET="$AGENT_ROOT/05c0204f9c0a_agent_discovery.py"
PRODUCER="$AGENT_ROOT/evidence_complete_producer.py"
PILOT="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

EXPECTED_TARGET_SHA256="05c0204f9c0aba288d4dc8e74d171fe5ad78db39f743d0a53a78f4d5a581cc72"
EXPECTED_PRODUCER_SHA256="6faf1b71a902d314b3e8e24d99eb965d227738a30709e55a1198b4b551d84c0c"
EXPECTED_PILOT_SHA256="ea4106a2d52a1d3002cefad7396ee21d320eed2b56925610acbcf42ee4c829e9"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=099"
echo "MODE=READ_ONLY_POST_CANARY_FINAL_QUALIFICATION"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/RUNTIME_STATUS.txt"
: > "$OUT/HASH_STATUS.txt"
: > "$OUT/PACKAGE_IMPORT_STATUS.txt"
: > "$OUT/CANARY_EVIDENCE_STATUS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== RUNTIME STATUS ====="

{
echo "PYTHON3_PATH=$(command -v python3 || true)"
echo "PYTHON3_VERSION=$(python3 --version 2>&1 || true)"
echo "PACKAGE=$PACKAGE"
echo "AGENT_PARENT=$AGENT_PARENT"
} | tee "$OUT/RUNTIME_STATUS.txt"

echo
echo "===== HASH STATUS ====="

HASH_FAIL_COUNT=0

check_hash() {
    local label="$1"
    local file="$2"
    local expected="$3"

    if [[ ! -f "$file" ]]; then
        echo "${label}_STATUS=MISSING"
        HASH_FAIL_COUNT=$((HASH_FAIL_COUNT + 1))
        return
    fi

    local actual
    actual="$(sha256sum "$file" | awk '{print $1}')"

    echo "${label}_PATH=$file"
    echo "${label}_EXPECTED_SHA256=$expected"
    echo "${label}_ACTUAL_SHA256=$actual"

    if [[ "$actual" == "$expected" ]]; then
        echo "${label}_HASH_STATUS=PASS"
    else
        echo "${label}_HASH_STATUS=FAIL"
        HASH_FAIL_COUNT=$((HASH_FAIL_COUNT + 1))
    fi

    echo
}

{
check_hash TARGET "$TARGET" "$EXPECTED_TARGET_SHA256"
check_hash PRODUCER "$PRODUCER" "$EXPECTED_PRODUCER_SHA256"
check_hash PILOT "$PILOT" "$EXPECTED_PILOT_SHA256"
} | tee "$OUT/HASH_STATUS.txt"

echo
echo "===== PACKAGE IMPORT QUALIFICATION ====="

set +e

PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONPATH="$AGENT_PARENT" \
python3 - "$PACKAGE" <<'PY' 2>&1 | tee "$OUT/PACKAGE_IMPORT_STATUS.txt"
import importlib
import sys

package = sys.argv[1]

modules = [
    f"{package}.agent_descriptor",
    f"{package}.agent_registry",
    f"{package}.evidence_complete_producer",
    f"{package}.ea4106a2d52a_metadata_agent_pilot",
    f"{package}.4fae0850626f_agent_validation_engine",
]

failures = 0

for name in modules:
    try:
        module = importlib.import_module(name)
        print(f"IMPORT_PASS={name}")
        print(f"MODULE_FILE={getattr(module, '__file__', 'NONE')}")
    except Exception as exc:
        failures += 1
        print(f"IMPORT_FAIL={name}")
        print(f"ERROR={type(exc).__name__}:{exc}")

print(f"IMPORT_FAILURE_COUNT={failures}")

raise SystemExit(0 if failures == 0 else 20)
PY

IMPORT_RC=${PIPESTATUS[0]}

set -e

IMPORT_PASS_COUNT="$(
  grep -c '^IMPORT_PASS=' "$OUT/PACKAGE_IMPORT_STATUS.txt" || true
)"

IMPORT_FAIL_COUNT="$(
  grep -c '^IMPORT_FAIL=' "$OUT/PACKAGE_IMPORT_STATUS.txt" || true
)"

echo
echo "===== CANARY EVIDENCE QUALIFICATION ====="

LATEST_CANARY="$(
  find "$REPORT_ROOT" \
    -maxdepth 1 \
    -type d \
    -name 'BATCH_098R4R3_*' \
    2>/dev/null |
  sort |
  tail -n1
)"

CANARY_EVIDENCE_STATUS="NOT_FOUND"
CANARY_RESULT_PASS_COUNT=0
CANARY_COMPLETED_COUNT=0
CANARY_PILOT_PASS_COUNT=0

if [[ -n "$LATEST_CANARY" &&
      -f "$LATEST_CANARY/FINAL_STATUS.txt" ]]; then

    CANARY_EVIDENCE_STATUS="FOUND"

    CANARY_COMPLETED_COUNT="$(
      grep -c '^CANARY_COMPLETED_COUNT=1$' \
        "$LATEST_CANARY/FINAL_STATUS.txt" || true
    )"

    CANARY_PILOT_PASS_COUNT="$(
      grep -c '^METADATA_PILOT_CALL_PASS_COUNT=1$' \
        "$LATEST_CANARY/FINAL_STATUS.txt" || true
    )"

    if [[ -f "$LATEST_CANARY/CANARY_OUTPUT.txt" ]]; then
        CANARY_RESULT_PASS_COUNT="$(
          grep -c '^RESULT_STATUS=PASS_METADATA_CONTROL_PLANE$' \
            "$LATEST_CANARY/CANARY_OUTPUT.txt" || true
        )"
    fi
fi

{
echo "LATEST_CANARY=${LATEST_CANARY:-NONE}"
echo "CANARY_EVIDENCE_STATUS=$CANARY_EVIDENCE_STATUS"
echo "CANARY_COMPLETED_PROOF_COUNT=$CANARY_COMPLETED_COUNT"
echo "CANARY_PILOT_PASS_PROOF_COUNT=$CANARY_PILOT_PASS_COUNT"
echo "CANARY_RESULT_STATUS_PROOF_COUNT=$CANARY_RESULT_PASS_COUNT"
} | tee "$OUT/CANARY_EVIDENCE_STATUS.txt"

QUALIFICATION_FAIL_COUNT=0

[[ "$HASH_FAIL_COUNT" -eq 0 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$IMPORT_RC" -eq 0 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$IMPORT_PASS_COUNT" -eq 5 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$IMPORT_FAIL_COUNT" -eq 0 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$CANARY_EVIDENCE_STATUS" == "FOUND" ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$CANARY_COMPLETED_COUNT" -eq 1 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$CANARY_PILOT_PASS_COUNT" -eq 1 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))
[[ "$CANARY_RESULT_PASS_COUNT" -eq 1 ]] || QUALIFICATION_FAIL_COUNT=$((QUALIFICATION_FAIL_COUNT + 1))

if [[ "$QUALIFICATION_FAIL_COUNT" -eq 0 ]]; then
    FINAL_QUALIFICATION_STATUS="PASS"
else
    FINAL_QUALIFICATION_STATUS="HOLD"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

POST_CANARY_FINAL_QUALIFICATION=COMPLETE

PYTHON3_STATUS=$(command -v python3 >/dev/null 2>&1 && echo AVAILABLE || echo MISSING)

HASH_FAIL_COUNT=$HASH_FAIL_COUNT

PACKAGE_IMPORT_RC=$IMPORT_RC
PACKAGE_IMPORT_PASS_COUNT=$IMPORT_PASS_COUNT
PACKAGE_IMPORT_FAIL_COUNT=$IMPORT_FAIL_COUNT

CANARY_EVIDENCE_STATUS=$CANARY_EVIDENCE_STATUS
CANARY_COMPLETED_PROOF_COUNT=$CANARY_COMPLETED_COUNT
CANARY_PILOT_PASS_PROOF_COUNT=$CANARY_PILOT_PASS_COUNT
CANARY_RESULT_STATUS_PROOF_COUNT=$CANARY_RESULT_PASS_COUNT

QUALIFICATION_FAIL_COUNT=$QUALIFICATION_FAIL_COUNT
FINAL_QUALIFICATION_STATUS=$FINAL_QUALIFICATION_STATUS

TARGET_FUNCTION_EXECUTED=NO
METADATA_PILOT_EXECUTED=NO
AGENT_TASK_EXECUTED=NO

FILE_MUTATION_EXECUTED=NO
NETWORK_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO
SERVICE_START_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$FINAL_QUALIFICATION_STATUS" == "PASS" ]]; then
    echo "RESULT=PASS"
    echo "BATCH_099_POST_CANARY_FINAL_QUALIFICATION=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_100_FINAL_CLOSURE_AND_SEAL"
else
    echo "RESULT=HOLD"
    echo "BLOCKER=POST_CANARY_FINAL_QUALIFICATION_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_099R1_FINAL_QUALIFICATION_FAILURE_ANALYSIS"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
