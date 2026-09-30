#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 095"
echo " ISOLATED LOCAL IMPORT CANARY — HUMAN GATE"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_PARENT="$ROOT/03_AGENTS_ACTIVE"
PACKAGE_DIR="$AGENT_PARENT/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_095_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=095"
echo "MODE=HUMAN_GATE_ISOLATED_LOCAL_IMPORT_CANARY_ONLY"
echo "START_UTC=$START_UTC"
echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_095_ISOLATED_LOCAL_IMPORT_CANARY_ONLY"

echo "ALLOW=ISOLATED_LOCAL_IMPORT_CANARY_ONLY"
echo "NETWORK=DENY"
echo "PACKAGE_INSTALL=DENY"
echo "FILE_WRITE_BY_CANARY=DENY"
echo "AGENT_TASK_EXECUTION=DENY"
echo "SERVICE_START=DENY"
echo "EXTERNAL_SEND=DENY"
echo "DELETE=DENY"
echo "MOVE=DENY"
echo "RENAME=DENY"
echo "FORMAT=DENY"
echo "PYTHONPATH_PERSISTENT_CHANGE=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/IMPORT_CANARY_OUTPUT.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== PREFLIGHT ====="

for f in \
  "$PACKAGE_DIR/agent_contract.py" \
  "$PACKAGE_DIR/agent_descriptor.py" \
  "$PACKAGE_DIR/agent_registry.py" \
  "$PACKAGE_DIR/task_registry.py"
do
    if [[ ! -f "$f" ]]; then
        echo "RESULT=HOLD"
        echo "BLOCKER=REQUIRED_NAMED_MODULE_MISSING"
        echo "MISSING_FILE=$f"
        echo "REPORT_DIR=$OUT"
        exit 0
    fi
done

echo "PYTHON3=$(command -v python3)"
echo "PYTHON3_VERSION=$(python3 --version 2>&1)"
echo "PACKAGE_DIR=$PACKAGE_DIR"
echo "AGENT_PARENT=$AGENT_PARENT"

echo
echo "===== ISOLATED IMPORT CANARY ====="

set +e

PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONPATH="$AGENT_PARENT" \
python3 - <<'PY' 2>&1 | tee "$OUT/IMPORT_CANARY_OUTPUT.txt"
import importlib
import os
import sys

package = "VALIDATED_PENDING_RUNTIME"

targets = [
    f"{package}.agent_contract",
    f"{package}.agent_descriptor",
    f"{package}.agent_registry",
    f"{package}.task_registry",
]

print("PYTHON_EXECUTABLE=" + sys.executable)
print("PYTHON_VERSION=" + sys.version.split()[0])
print("PYTHONDONTWRITEBYTECODE=" + os.environ.get("PYTHONDONTWRITEBYTECODE", ""))
print("PYTHONNOUSERSITE=" + os.environ.get("PYTHONNOUSERSITE", ""))

failures = 0

for name in targets:
    try:
        module = importlib.import_module(name)
        print(f"IMPORT_PASS={name}")
        print(f"MODULE_FILE={getattr(module, '__file__', 'NONE')}")
    except Exception as exc:
        failures += 1
        print(f"IMPORT_FAIL={name}")
        print(f"ERROR={type(exc).__name__}:{exc}")

print(f"IMPORT_FAILURE_COUNT={failures}")

if failures:
    raise SystemExit(20)
PY

CANARY_RC=${PIPESTATUS[0]}

set -e

IMPORT_PASS_COUNT="$(
  grep -c '^IMPORT_PASS=' "$OUT/IMPORT_CANARY_OUTPUT.txt" || true
)"

IMPORT_FAIL_COUNT="$(
  grep -c '^IMPORT_FAIL=' "$OUT/IMPORT_CANARY_OUTPUT.txt" || true
)"

BYTECODE_COUNT="$(
  find "$PACKAGE_DIR" \
    -type f \
    \( -name '*.pyc' -o -path '*/__pycache__/*' \) \
    2>/dev/null |
  wc -l |
  tr -d ' '
)"

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

ISOLATED_IMPORT_CANARY=COMPLETE

CANARY_RC=$CANARY_RC
IMPORT_PASS_COUNT=$IMPORT_PASS_COUNT
IMPORT_FAIL_COUNT=$IMPORT_FAIL_COUNT

EXPECTED_IMPORT_COUNT=4

BYTECODE_ARTIFACT_COUNT=$BYTECODE_COUNT

NETWORK_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO
AGENT_TASK_EXECUTION_EXECUTED=NO
SERVICE_START_EXECUTED=NO
EXTERNAL_SEND_EXECUTED=NO

PERSISTENT_PYTHONPATH_CHANGE_EXECUTED=NO
DELETE_EXECUTED=NO
MOVE_EXECUTED=NO
RENAME_EXECUTED=NO
FORMAT_EXECUTED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$CANARY_RC" -ne 0 || "$IMPORT_FAIL_COUNT" -gt 0 ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=ISOLATED_LOCAL_IMPORT_CANARY_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_095R1_IMPORT_FAILURE_ANALYSIS"
elif [[ "$IMPORT_PASS_COUNT" -ne 4 ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=IMPORT_CANARY_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_095R1_IMPORT_FAILURE_ANALYSIS"
else
    echo "RESULT=PASS"
    echo "IMPORT_CANARY_STATUS=READY"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_096_CONTROLLED_AGENT_RUNTIME_PREFLIGHT"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
