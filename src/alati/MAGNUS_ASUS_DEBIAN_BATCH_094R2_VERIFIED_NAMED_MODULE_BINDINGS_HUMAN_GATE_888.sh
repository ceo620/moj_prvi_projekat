#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 094R2"
echo " VERIFIED NAMED MODULE BINDINGS — HUMAN GATE"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_094R2_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=094R2"
echo "MODE=HUMAN_GATE_COPY_THREE_VERIFIED_NAMED_MODULE_BINDINGS_ONLY"
echo "START_UTC=$START_UTC"

echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_094R2_COPY_THREE_VERIFIED_NAMED_MODULE_BINDINGS_ONLY"

echo "ALLOW=COPY_THREE_VERIFIED_NAMED_MODULE_BINDINGS_ONLY"
echo "SOURCE_DELETE=DENY"
echo "SOURCE_MOVE=DENY"
echo "SOURCE_RENAME=DENY"
echo "TARGET_OVERWRITE=DENY"
echo "PYTHONPATH_CHANGE=DENY"
echo "AGENT_EXECUTION=DENY"
echo "PACKAGE_INSTALL=DENY"
echo "DELETE=DENY"
echo "FORMAT=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/PREFLIGHT.txt"
: > "$OUT/COPY_STATUS.txt"
: > "$OUT/POST_COPY_VALIDATION.txt"
: > "$OUT/FINAL_STATUS.txt"

declare -A SOURCES=(
  [agent_contract]="$AGENT_ROOT/240a4b0235a4_agent_contract.py"
  [agent_descriptor]="$AGENT_ROOT/6eb6f765f059_agent_descriptor.py"
  [agent_registry]="$AGENT_ROOT/b565dba4dad1_agent_registry.py"
)

declare -A EXPECTED_HASHES=(
  [agent_contract]="240a4b0235a451881b1f7b07e91e659259d32a0bc1df5dc6b928972be3028d85"
  [agent_descriptor]="6eb6f765f0596599d775e57f93f0b5fd23585c750d4b86eebe4eb5062aaa3687"
  [agent_registry]="b565dba4dad1f7cc1069caf397aae8111f02f52387dff684ea2b146f05e3e974"
)

declare -A REQUIRED_CLASSES=(
  [agent_contract]="AgentExecutionContract"
  [agent_descriptor]="AgentDescriptor"
  [agent_registry]="AgentRegistry"
)

echo "===== PREFLIGHT ====="

for module in agent_contract agent_descriptor agent_registry; do

    SRC="${SOURCES[$module]}"
    EXPECTED="${EXPECTED_HASHES[$module]}"
    TARGET="$AGENT_ROOT/${module}.py"

    if [[ ! -f "$SRC" ]]; then
        echo "RESULT=HOLD"
        echo "BLOCKER=SOURCE_MISSING_$module"
        echo "REPORT_DIR=$OUT"
        exit 0
    fi

    ACTUAL="$(sha256sum "$SRC" | awk '{print $1}')"

    {
      echo "MODULE=$module"
      echo "SOURCE=$SRC"
      echo "EXPECTED_HASH=$EXPECTED"
      echo "ACTUAL_HASH=$ACTUAL"
      echo "TARGET=$TARGET"
    } | tee -a "$OUT/PREFLIGHT.txt"

    if [[ "$ACTUAL" != "$EXPECTED" ]]; then
        echo "RESULT=HOLD"
        echo "BLOCKER=SOURCE_HASH_MISMATCH_$module"
        echo "REPORT_DIR=$OUT"
        exit 0
    fi

    if [[ -e "$TARGET" ]]; then

        if [[ -f "$TARGET" ]]; then
            EXISTING="$(sha256sum "$TARGET" | awk '{print $1}')"
        else
            EXISTING="NON_FILE_OBJECT"
        fi

        echo "TARGET_ALREADY_EXISTS=YES" \
          | tee -a "$OUT/PREFLIGHT.txt"
        echo "TARGET_EXISTING_HASH=$EXISTING" \
          | tee -a "$OUT/PREFLIGHT.txt"

        if [[ "$EXISTING" != "$EXPECTED" ]]; then
            echo "RESULT=HOLD"
            echo "BLOCKER=TARGET_EXISTS_OVERWRITE_DENIED_$module"
            echo "REPORT_DIR=$OUT"
            exit 0
        fi
    else
        echo "TARGET_ALREADY_EXISTS=NO" \
          | tee -a "$OUT/PREFLIGHT.txt"
    fi

    echo | tee -a "$OUT/PREFLIGHT.txt"
done

echo
echo "===== HUMAN GATE MUTATION ====="
echo "ACTION=COPY_THREE_VERIFIED_NAMED_MODULE_BINDINGS_ONLY"

COPY_FAIL_COUNT=0

for module in agent_contract agent_descriptor agent_registry; do

    SRC="${SOURCES[$module]}"
    EXPECTED="${EXPECTED_HASHES[$module]}"
    TARGET="$AGENT_ROOT/${module}.py"

    if [[ -f "$TARGET" ]]; then
        EXISTING="$(sha256sum "$TARGET" | awk '{print $1}')"

        if [[ "$EXISTING" == "$EXPECTED" ]]; then
            echo "MODULE=$module STATUS=ALREADY_PRESENT_IDENTICAL" \
              | tee -a "$OUT/COPY_STATUS.txt"
            continue
        fi
    fi

    set +e

    cp --no-clobber --preserve=mode,timestamps \
      "$SRC" "$TARGET" \
      2>&1 | tee -a "$OUT/COPY_STATUS.txt"

    RC=${PIPESTATUS[0]}

    set -e

    echo "MODULE=$module COPY_RC=$RC" \
      | tee -a "$OUT/COPY_STATUS.txt"

    if [[ "$RC" -ne 0 ]]; then
        COPY_FAIL_COUNT=$((COPY_FAIL_COUNT + 1))
    fi
done

echo
echo "===== POST COPY VALIDATION ====="

VALIDATED_COUNT=0
HASH_FAIL_COUNT=0
ROLE_FAIL_COUNT=0

for module in agent_contract agent_descriptor agent_registry; do

    TARGET="$AGENT_ROOT/${module}.py"
    EXPECTED="${EXPECTED_HASHES[$module]}"
    REQUIRED_CLASS="${REQUIRED_CLASSES[$module]}"

    if [[ -f "$TARGET" ]]; then
        TARGET_HASH="$(sha256sum "$TARGET" | awk '{print $1}')"
    else
        TARGET_HASH="MISSING"
    fi

    HASH_STATUS="FAIL"
    ROLE_STATUS="FAIL"

    if [[ "$TARGET_HASH" == "$EXPECTED" ]]; then
        HASH_STATUS="PASS"
    else
        HASH_FAIL_COUNT=$((HASH_FAIL_COUNT + 1))
    fi

    if [[ -f "$TARGET" ]]; then
        if PYTHONDONTWRITEBYTECODE=1 python3 - "$TARGET" "$REQUIRED_CLASS" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
required = sys.argv[2]

tree = ast.parse(path.read_text(errors="replace"), filename=str(path))

classes = {
    node.name
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
}

raise SystemExit(0 if required in classes else 2)
PY
        then
            ROLE_STATUS="PASS"
        else
            ROLE_FAIL_COUNT=$((ROLE_FAIL_COUNT + 1))
        fi
    else
        ROLE_FAIL_COUNT=$((ROLE_FAIL_COUNT + 1))
    fi

    if [[ "$HASH_STATUS" == "PASS" &&
          "$ROLE_STATUS" == "PASS" ]]; then
        VALIDATED_COUNT=$((VALIDATED_COUNT + 1))
    fi

    {
      echo "MODULE=$module"
      echo "TARGET=$TARGET"
      echo "TARGET_SHA256=$TARGET_HASH"
      echo "HASH_STATUS=$HASH_STATUS"
      echo "REQUIRED_CLASS=$REQUIRED_CLASS"
      echo "STATIC_ROLE_STATUS=$ROLE_STATUS"
      echo
    } | tee -a "$OUT/POST_COPY_VALIDATION.txt"
done

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

NAMED_MODULE_BINDING_MUTATION=COMPLETE

EXPECTED_BINDING_COUNT=3
VALIDATED_BINDING_COUNT=$VALIDATED_COUNT

COPY_FAIL_COUNT=$COPY_FAIL_COUNT
HASH_FAIL_COUNT=$HASH_FAIL_COUNT
ROLE_FAIL_COUNT=$ROLE_FAIL_COUNT

SOURCE_DELETE_EXECUTED=NO
SOURCE_MOVE_EXECUTED=NO
SOURCE_RENAME_EXECUTED=NO
TARGET_OVERWRITE_EXECUTED=NO

PYTHONPATH_CHANGE_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

DELETE_EXECUTED=NO
FORMAT_EXECUTED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if (( COPY_FAIL_COUNT > 0 )); then

    echo "RESULT=HOLD"
    echo "BLOCKER=NAMED_MODULE_COPY_FAILURE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R2R1_COPY_FAILURE_ANALYSIS"

elif (( HASH_FAIL_COUNT > 0 )); then

    echo "RESULT=HOLD"
    echo "BLOCKER=NAMED_MODULE_POST_COPY_HASH_FAILURE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R2R2_HASH_FAILURE_ANALYSIS"

elif (( ROLE_FAIL_COUNT > 0 )); then

    echo "RESULT=HOLD"
    echo "BLOCKER=NAMED_MODULE_STATIC_ROLE_FAILURE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R2R3_ROLE_FAILURE_ANALYSIS"

elif (( VALIDATED_COUNT != 3 )); then

    echo "RESULT=HOLD"
    echo "BLOCKER=NAMED_MODULE_BINDING_VALIDATION_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R2R4_BINDING_VALIDATION_ANALYSIS"

else

    echo "RESULT=PASS"
    echo "NAMED_MODULE_BINDINGS=COMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_095_ISOLATED_IMPORT_CANARY"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
