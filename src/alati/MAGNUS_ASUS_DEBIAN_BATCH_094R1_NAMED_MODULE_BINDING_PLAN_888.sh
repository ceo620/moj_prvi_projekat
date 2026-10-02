#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 094R1"
echo " NAMED MODULE BINDING PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_094R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=094R1"
echo "MODE=READ_ONLY_NAMED_MODULE_BINDING_PLAN"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/BINDING_MATRIX.txt"
: > "$OUT/STATIC_ROLE_PROOF.txt"
: > "$OUT/TARGET_PREFLIGHT.txt"
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

SOURCE_PROVEN_COUNT=0
ROLE_PROVEN_COUNT=0
TARGET_AVAILABLE_COUNT=0
CONFLICT_COUNT=0

for module in agent_contract agent_descriptor agent_registry; do

    SRC="${SOURCES[$module]}"
    EXPECTED_HASH="${EXPECTED_HASHES[$module]}"
    TARGET="$AGENT_ROOT/${module}.py"
    REQUIRED_CLASS="${REQUIRED_CLASSES[$module]}"

    echo "===== MODULE=$module =====" | tee -a "$OUT/BINDING_MATRIX.txt"

    if [[ -f "$SRC" ]]; then
        ACTUAL_HASH="$(sha256sum "$SRC" | awk '{print $1}')"
        SOURCE_EXISTS="YES"
    else
        ACTUAL_HASH="MISSING"
        SOURCE_EXISTS="NO"
    fi

    if [[ "$ACTUAL_HASH" == "$EXPECTED_HASH" ]]; then
        SOURCE_HASH_STATUS="PASS"
        SOURCE_PROVEN_COUNT=$((SOURCE_PROVEN_COUNT + 1))
    else
        SOURCE_HASH_STATUS="FAIL"
    fi

    {
      echo "SOURCE=$SRC"
      echo "SOURCE_EXISTS=$SOURCE_EXISTS"
      echo "EXPECTED_HASH=$EXPECTED_HASH"
      echo "ACTUAL_HASH=$ACTUAL_HASH"
      echo "SOURCE_HASH_STATUS=$SOURCE_HASH_STATUS"
    } | tee -a "$OUT/BINDING_MATRIX.txt"

    ROLE_STATUS="FAIL"

    if [[ -f "$SRC" ]]; then
        if PYTHONDONTWRITEBYTECODE=1 python3 - "$SRC" "$REQUIRED_CLASS" <<'PY'
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
            ROLE_PROVEN_COUNT=$((ROLE_PROVEN_COUNT + 1))
        fi
    fi

    {
      echo "REQUIRED_CLASS=$REQUIRED_CLASS"
      echo "STATIC_ROLE_STATUS=$ROLE_STATUS"
    } | tee -a "$OUT/STATIC_ROLE_PROOF.txt"

    if [[ -e "$TARGET" ]]; then
        TARGET_EXISTS="YES"

        if [[ -f "$TARGET" ]]; then
            TARGET_HASH="$(sha256sum "$TARGET" | awk '{print $1}')"
        else
            TARGET_HASH="NON_FILE_OBJECT"
        fi

        if [[ "$TARGET_HASH" == "$EXPECTED_HASH" ]]; then
            TARGET_STATUS="ALREADY_PRESENT_IDENTICAL"
            TARGET_AVAILABLE_COUNT=$((TARGET_AVAILABLE_COUNT + 1))
        else
            TARGET_STATUS="CONFLICT"
            CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
        fi

    else
        TARGET_EXISTS="NO"
        TARGET_HASH="NONE"
        TARGET_STATUS="AVAILABLE"
        TARGET_AVAILABLE_COUNT=$((TARGET_AVAILABLE_COUNT + 1))
    fi

    {
      echo "MODULE=$module"
      echo "TARGET=$TARGET"
      echo "TARGET_EXISTS=$TARGET_EXISTS"
      echo "TARGET_HASH=$TARGET_HASH"
      echo "TARGET_STATUS=$TARGET_STATUS"
      echo
    } | tee -a "$OUT/TARGET_PREFLIGHT.txt"

    echo | tee -a "$OUT/BINDING_MATRIX.txt"
done

if (( SOURCE_PROVEN_COUNT == 3 &&
      ROLE_PROVEN_COUNT == 3 &&
      TARGET_AVAILABLE_COUNT == 3 &&
      CONFLICT_COUNT == 0 )); then

    PLAN_STATUS="READY_FOR_HUMAN_GATE"
else
    PLAN_STATUS="HOLD"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

NAMED_MODULE_BINDING_PLAN=COMPLETE

SOURCE_PROVEN_COUNT=$SOURCE_PROVEN_COUNT
ROLE_PROVEN_COUNT=$ROLE_PROVEN_COUNT
TARGET_AVAILABLE_COUNT=$TARGET_AVAILABLE_COUNT
CONFLICT_COUNT=$CONFLICT_COUNT

PLAN_STATUS=$PLAN_STATUS

PROPOSED_BINDINGS=3

PROPOSED_TARGET_1=$AGENT_ROOT/agent_contract.py
PROPOSED_TARGET_2=$AGENT_ROOT/agent_descriptor.py
PROPOSED_TARGET_3=$AGENT_ROOT/agent_registry.py

SOURCE_DELETE_ALLOWED=NO
SOURCE_MOVE_ALLOWED=NO
SOURCE_RENAME_ALLOWED=NO
TARGET_OVERWRITE_ALLOWED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_RENAME_EXECUTED=NO
FILE_DELETE_EXECUTED=NO

PYTHONPATH_CHANGE_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

MUTATION_ALLOWED=NO

HUMAN_GATE_REQUIRED=YES
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- BINDING MATRIX ---"
cat "$OUT/BINDING_MATRIX.txt"

echo
echo "--- STATIC ROLE PROOF ---"
cat "$OUT/STATIC_ROLE_PROOF.txt"

echo
echo "--- TARGET PREFLIGHT ---"
cat "$OUT/TARGET_PREFLIGHT.txt"

echo "============================================================"

if [[ "$PLAN_STATUS" == "READY_FOR_HUMAN_GATE" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=HUMAN_GATE_APPROVAL_REQUIRED_FOR_THREE_NAMED_MODULE_BINDINGS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R2_VERIFIED_NAMED_MODULE_BINDINGS_HUMAN_GATE"

else

    echo "RESULT=HOLD"
    echo "BLOCKER=NAMED_MODULE_BINDING_PREFLIGHT_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R1R1_BINDING_CONFLICT_ANALYSIS"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
