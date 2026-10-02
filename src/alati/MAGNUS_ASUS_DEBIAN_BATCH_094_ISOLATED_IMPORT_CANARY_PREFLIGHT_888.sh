#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 094"
echo " ISOLATED IMPORT CANARY PREFLIGHT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_094_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=094"
echo "MODE=READ_ONLY_ISOLATED_IMPORT_CANARY_PREFLIGHT"
echo "AGENT_ROOT=$AGENT_ROOT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/EXPECTED_MODULE_MATRIX.txt"
: > "$OUT/HASHED_IMPLEMENTATION_MATRIX.txt"
: > "$OUT/PACKAGE_STATUS.txt"
: > "$OUT/RELATIVE_IMPORTS.txt"
: > "$OUT/FINAL_STATUS.txt"

MODULES=(
  agent_contract
  agent_descriptor
  agent_registry
  task_registry
)

echo "===== EXPECTED NAMED MODULES ====="

NAMED_PRESENT_COUNT=0
NAMED_MISSING_COUNT=0

for module in "${MODULES[@]}"; do

    TARGET="$AGENT_ROOT/${module}.py"

    if [[ -f "$TARGET" ]]; then

        H="$(sha256sum "$TARGET" | awk '{print $1}')"

        echo "MODULE=$module" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"
        echo "STATUS=PRESENT" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"
        echo "PATH=$TARGET" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"
        echo "SHA256=$H" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"

        NAMED_PRESENT_COUNT=$((NAMED_PRESENT_COUNT + 1))

    else

        echo "MODULE=$module" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"
        echo "STATUS=MISSING" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"
        echo "PATH=$TARGET" \
          | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"

        NAMED_MISSING_COUNT=$((NAMED_MISSING_COUNT + 1))
    fi

    echo | tee -a "$OUT/EXPECTED_MODULE_MATRIX.txt"
done

echo
echo "===== HASHED IMPLEMENTATION CANDIDATES ====="

declare -A PATTERNS=(
  [agent_contract]='*agent_contract.py'
  [agent_descriptor]='*agent_descriptor.py'
  [agent_registry]='*agent_registry.py'
  [task_registry]='*task_registry.py'
)

HASHED_BINDING_CANDIDATE_COUNT=0

for module in "${MODULES[@]}"; do

    echo "MODULE=$module" \
      | tee -a "$OUT/HASHED_IMPLEMENTATION_MATRIX.txt"

    while IFS= read -r f; do

        [[ -f "$f" ]] || continue

        BASE="$(basename "$f")"

        if [[ "$BASE" == "${module}.py" ]]; then
            continue
        fi

        H="$(sha256sum "$f" | awk '{print $1}')"

        echo "HASHED_CANDIDATE=$f" \
          | tee -a "$OUT/HASHED_IMPLEMENTATION_MATRIX.txt"
        echo "SHA256=$H" \
          | tee -a "$OUT/HASHED_IMPLEMENTATION_MATRIX.txt"

        HASHED_BINDING_CANDIDATE_COUNT=$((HASHED_BINDING_CANDIDATE_COUNT + 1))

    done < <(
        find "$AGENT_ROOT" \
          -maxdepth 1 \
          -type f \
          -name "${PATTERNS[$module]}" \
          2>/dev/null |
        sort
    )

    echo | tee -a "$OUT/HASHED_IMPLEMENTATION_MATRIX.txt"
done

echo
echo "===== PACKAGE STATUS ====="

if [[ -f "$AGENT_ROOT/__init__.py" ]]; then
    PACKAGE_INIT_STATUS="PRESENT"
else
    PACKAGE_INIT_STATUS="MISSING"
fi

PARENT_DIR="$(dirname "$AGENT_ROOT")"
PACKAGE_DIR_NAME="$(basename "$AGENT_ROOT")"

{
echo "AGENT_ROOT=$AGENT_ROOT"
echo "PARENT_DIR=$PARENT_DIR"
echo "PACKAGE_DIR_NAME=$PACKAGE_DIR_NAME"
echo "PACKAGE_INIT_STATUS=$PACKAGE_INIT_STATUS"
} | tee "$OUT/PACKAGE_STATUS.txt"

echo
echo "===== RELATIVE IMPORTS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$AGENT_ROOT" \
  "$OUT/RELATIVE_IMPORTS.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])

rows = []

for path in sorted(root.glob("*.py")):
    try:
        tree = ast.parse(
            path.read_text(errors="replace"),
            filename=str(path)
        )
    except Exception as exc:
        rows.append(
            f"PARSE_ERROR\t{path}\t{type(exc).__name__}:{exc}"
        )
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            names = ",".join(a.name for a in node.names)
            module = node.module or ""
            rows.append(
                f"{path}\tLEVEL={node.level}\tMODULE={module}\tNAMES={names}"
            )

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/RELATIVE_IMPORTS.txt"

RELATIVE_IMPORT_COUNT="$(
  wc -l < "$OUT/RELATIVE_IMPORTS.txt" |
  tr -d ' '
)"

TASK_REGISTRY_HASH="$(
  [[ -f "$AGENT_ROOT/task_registry.py" ]] \
  && sha256sum "$AGENT_ROOT/task_registry.py" | awk '{print $1}' \
  || echo NONE
)"

EXPECTED_TASK_REGISTRY_HASH="c719113415d0937e8298ae9dc82040065320d751862f4ccc281c36c1127495f8"

if [[ "$TASK_REGISTRY_HASH" == "$EXPECTED_TASK_REGISTRY_HASH" ]]; then
    TASK_REGISTRY_STATUS="PROVEN"
else
    TASK_REGISTRY_STATUS="NOT_PROVEN"
fi

if (( NAMED_MISSING_COUNT == 0 )); then
    NAMED_MODULE_STATUS="READY"
else
    NAMED_MODULE_STATUS="INCOMPLETE"
fi

if [[ "$PACKAGE_INIT_STATUS" == "PRESENT" ]]; then
    PACKAGE_STRUCTURE_STATUS="PACKAGE_MARKER_PRESENT"
else
    PACKAGE_STRUCTURE_STATUS="PACKAGE_MARKER_MISSING"
fi

if [[ "$NAMED_MODULE_STATUS" == "READY" &&
      "$TASK_REGISTRY_STATUS" == "PROVEN" ]]; then

    IMPORT_CANARY_READINESS="READY"

else

    IMPORT_CANARY_READINESS="BLOCKED"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

IMPORT_CANARY_PREFLIGHT=COMPLETE

NAMED_MODULE_PRESENT_COUNT=$NAMED_PRESENT_COUNT
NAMED_MODULE_MISSING_COUNT=$NAMED_MISSING_COUNT

HASHED_BINDING_CANDIDATE_COUNT=$HASHED_BINDING_CANDIDATE_COUNT

RELATIVE_IMPORT_COUNT=$RELATIVE_IMPORT_COUNT

PACKAGE_INIT_STATUS=$PACKAGE_INIT_STATUS
PACKAGE_STRUCTURE_STATUS=$PACKAGE_STRUCTURE_STATUS

TASK_REGISTRY_STATUS=$TASK_REGISTRY_STATUS

NAMED_MODULE_STATUS=$NAMED_MODULE_STATUS
IMPORT_CANARY_READINESS=$IMPORT_CANARY_READINESS

PYTHON_IMPORT_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
PYTHONPATH_CHANGE_EXECUTED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_RENAME_EXECUTED=NO
FILE_DELETE_EXECUTED=NO

PACKAGE_INSTALL_EXECUTED=NO
NETWORK_WRITE_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- EXPECTED MODULE MATRIX ---"
cat "$OUT/EXPECTED_MODULE_MATRIX.txt"

echo
echo "--- HASHED IMPLEMENTATION MATRIX ---"
cat "$OUT/HASHED_IMPLEMENTATION_MATRIX.txt"

echo "============================================================"

if [[ "$TASK_REGISTRY_STATUS" != "PROVEN" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=TASK_REGISTRY_POST_RECONSTRUCTION_PROOF_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R1_TASK_REGISTRY_POST_COPY_ANALYSIS"

elif (( NAMED_MISSING_COUNT > 0 )); then

    echo "RESULT=HOLD"
    echo "BLOCKER=NAMED_LOCAL_MODULE_BINDINGS_MISSING"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094R1_NAMED_MODULE_BINDING_PLAN"

else

    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_095_ISOLATED_IMPORT_CANARY"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
