#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R4R1"
echo " CANARY FAILURE ANALYSIS — PACKAGE IMPORT PROOF"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_PARENT="$ROOT/03_AGENTS_ACTIVE"
PACKAGE="VALIDATED_PENDING_RUNTIME"
AGENT_ROOT="$AGENT_PARENT/$PACKAGE"

REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R4R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R4R1"
echo "MODE=READ_ONLY_CANARY_FAILURE_ANALYSIS"
echo "START_UTC=$START_UTC"
echo "AGENT_PARENT=$AGENT_PARENT"
echo "PACKAGE=$PACKAGE"
} > "$OUT/BATCH.env"

: > "$OUT/RELATIVE_IMPORT_PROOF.txt"
: > "$OUT/PACKAGE_IMPORT_PROOF.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== RELATIVE IMPORT PROOF ====="

grep -nE \
  '^[[:space:]]*from[[:space:]]+\.' \
  "$AGENT_ROOT/agent_registry.py" \
  "$AGENT_ROOT/4fae0850626f_agent_validation_engine.py" \
  "$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py" \
  2>/dev/null \
| tee "$OUT/RELATIVE_IMPORT_PROOF.txt" || true

echo
echo "===== PACKAGE IMPORT PROOF ====="

set +e

PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONPATH="$AGENT_PARENT" \
python3 - "$PACKAGE" <<'PY' 2>&1 | tee "$OUT/PACKAGE_IMPORT_PROOF.txt"
import importlib
import sys

package = sys.argv[1]

targets = [
    f"{package}.agent_descriptor",
    f"{package}.agent_registry",
    f"{package}.evidence_complete_producer",
    f"{package}.ea4106a2d52a_metadata_agent_pilot",
    f"{package}.4fae0850626f_agent_validation_engine",
]

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

raise SystemExit(0 if failures == 0 else 20)
PY

IMPORT_RC=${PIPESTATUS[0]}

set -e

IMPORT_PASS_COUNT="$(
  grep -c '^IMPORT_PASS=' "$OUT/PACKAGE_IMPORT_PROOF.txt" || true
)"

IMPORT_FAIL_COUNT="$(
  grep -c '^IMPORT_FAIL=' "$OUT/PACKAGE_IMPORT_PROOF.txt" || true
)"

RELATIVE_IMPORT_SIGNAL_COUNT="$(
  wc -l < "$OUT/RELATIVE_IMPORT_PROOF.txt" |
  tr -d ' '
)"

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CANARY_FAILURE_ANALYSIS=COMPLETE

ROOT_CAUSE=TOP_LEVEL_IMPORT_USED_FOR_PACKAGE_RELATIVE_MODULES

AGENT_PARENT=$AGENT_PARENT
PACKAGE=$PACKAGE

RELATIVE_IMPORT_SIGNAL_COUNT=$RELATIVE_IMPORT_SIGNAL_COUNT

PACKAGE_IMPORT_RC=$IMPORT_RC
PACKAGE_IMPORT_PASS_COUNT=$IMPORT_PASS_COUNT
PACKAGE_IMPORT_FAIL_COUNT=$IMPORT_FAIL_COUNT
EXPECTED_PACKAGE_IMPORT_COUNT=5

SOURCE_REPAIR_REQUIRED=NO
MODULE_CONTENT_CHANGE_REQUIRED=NO
PYTHONPATH_PERSISTENT_CHANGE_REQUIRED=NO

PROPOSED_FIX=CANARY_USE_PACKAGE_AWARE_IMPORTS
PROPOSED_RUNTIME_PYTHONPATH=$AGENT_PARENT

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

if [[ "$IMPORT_RC" -eq 0 &&
      "$IMPORT_PASS_COUNT" -eq 5 &&
      "$IMPORT_FAIL_COUNT" -eq 0 ]]; then

    echo "RESULT=PASS"
    echo "ROOT_CAUSE_CONFIRMED=YES"
    echo "PACKAGE_IMPORT_MODEL=PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R4R2_CORRECTED_METADATA_PILOT_CANARY_PLAN"

else

    echo "RESULT=HOLD"
    echo "BLOCKER=PACKAGE_IMPORT_MODEL_NOT_FULLY_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R4R1R1_IMPORT_BINDING_DEEP_ANALYSIS"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
