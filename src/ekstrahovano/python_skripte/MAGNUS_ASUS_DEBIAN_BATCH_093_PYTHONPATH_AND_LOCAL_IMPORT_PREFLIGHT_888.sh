#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 093"
echo " PYTHONPATH + LOCAL IMPORT PREFLIGHT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_093_$START_UTC"

AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
CANONICAL_ROOT="$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=093"
echo "MODE=READ_ONLY_PYTHONPATH_LOCAL_IMPORT_PREFLIGHT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/ACTIVE_AGENT_MODULE_ANALYSIS.txt"
: > "$OUT/QUARANTINE_MODULE_STATUS.txt"
: > "$OUT/CANONICAL_MODULE_STATUS.txt"
: > "$OUT/FINAL_STATUS.txt"

MODULES=(
  agent_contract
  agent_descriptor
  agent_registry
  task_registry
)

echo "===== ACTIVE AGENT STATIC MODULE ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$AGENT_ROOT" \
  "$OUT/ACTIVE_AGENT_MODULE_ANALYSIS.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])

rows = []

for path in sorted(root.glob("*.py")):
    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception as exc:
        rows.append(f"FILE={path}")
        rows.append(f"PARSE_ERROR={type(exc).__name__}:{exc}")
        rows.append("")
        continue

    classes = []
    funcs = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    rows.append(f"FILE={path}")
    rows.append("CLASSES=" + ",".join(sorted(set(classes))))
    rows.append("FUNCTIONS=" + ",".join(sorted(set(funcs))))
    rows.append("IMPORTS=" + ",".join(sorted(set(imports))))
    rows.append("")

out.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/ACTIVE_AGENT_MODULE_ANALYSIS.txt"

echo
echo "===== CANONICAL/NON-QUARANTINE MODULE SEARCH ====="

NONQUARANTINE_FOUND=0

for module in "${MODULES[@]}"; do
    echo "MODULE=$module" | tee -a "$OUT/CANONICAL_MODULE_STATUS.txt"

    MATCHES="$(
      find "$ROOT" \
        -type f \
        -name "${module}.py" \
        2>/dev/null \
      | grep -Ev '/(90_QUARANTINE|08_ARCHIVES|11_BACKUP|99_ARCHIVE)/' \
      || true
    )"

    if [[ -n "$MATCHES" ]]; then
        printf '%s\n' "$MATCHES" | tee -a "$OUT/CANONICAL_MODULE_STATUS.txt"
        NONQUARANTINE_FOUND=$((NONQUARANTINE_FOUND + 1))
    else
        echo "NONQUARANTINE_NAMED_MODULE=NOT_FOUND" \
          | tee -a "$OUT/CANONICAL_MODULE_STATUS.txt"
    fi

    echo >> "$OUT/CANONICAL_MODULE_STATUS.txt"
done

echo
echo "===== QUARANTINE MODULE STATUS ====="

QUARANTINE_ONLY_COUNT=0

for module in "${MODULES[@]}"; do
    QCOUNT="$(
      find "$ROOT/90_QUARANTINE" \
        -type f \
        -name "${module}.py" \
        2>/dev/null |
      wc -l |
      tr -d ' '
    )"

    echo "${module}_QUARANTINE_COUNT=$QCOUNT" \
      | tee -a "$OUT/QUARANTINE_MODULE_STATUS.txt"

    if (( QCOUNT > 0 )); then
        QUARANTINE_ONLY_COUNT=$((QUARANTINE_ONLY_COUNT + 1))
    fi
done

ASUS_CORE_COUNT="$(
  find "$CANONICAL_ROOT" \
    -type f \
    -name 'asus_agent_core_888.py' \
    2>/dev/null |
  wc -l |
  tr -d ' '
)"

ACTIVE_HASHED_AGENT_COUNT="$(
  find "$AGENT_ROOT" \
    -maxdepth 1 \
    -type f \
    -iname '*.py' \
    2>/dev/null |
  wc -l |
  tr -d ' '
)"

# Role-name signals in active hashed filenames.
CONTRACT_SIGNAL_COUNT="$(
  find "$AGENT_ROOT" -maxdepth 1 -type f -iname '*agent_contract*.py' 2>/dev/null |
  wc -l | tr -d ' '
)"

DESCRIPTOR_SIGNAL_COUNT="$(
  find "$AGENT_ROOT" -maxdepth 1 -type f -iname '*agent_descriptor*.py' 2>/dev/null |
  wc -l | tr -d ' '
)"

REGISTRY_SIGNAL_COUNT="$(
  find "$AGENT_ROOT" -maxdepth 1 -type f -iname '*agent_registry*.py' 2>/dev/null |
  wc -l | tr -d ' '
)"

TASK_REGISTRY_SIGNAL_COUNT="$(
  find "$AGENT_ROOT" -maxdepth 1 -type f -iname '*task_registry*.py' 2>/dev/null |
  wc -l | tr -d ' '
)"

if (( QUARANTINE_ONLY_COUNT > 0 )); then
    QUARANTINE_PYTHONPATH_ALLOWED="NO"
else
    QUARANTINE_PYTHONPATH_ALLOWED="NOT_APPLICABLE"
fi

if (( NONQUARANTINE_FOUND == 4 )); then
    LOCAL_IMPORT_STATUS="NAMED_ACTIVE_MODULES_FOUND"
elif (( CONTRACT_SIGNAL_COUNT > 0 ||
        DESCRIPTOR_SIGNAL_COUNT > 0 ||
        REGISTRY_SIGNAL_COUNT > 0 ||
        TASK_REGISTRY_SIGNAL_COUNT > 0 )); then
    LOCAL_IMPORT_STATUS="ACTIVE_HASHED_IMPLEMENTATIONS_REQUIRE_BINDING_PROOF"
else
    LOCAL_IMPORT_STATUS="ACTIVE_IMPORT_BINDING_NOT_PROVEN"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

LOCAL_IMPORT_PREFLIGHT=COMPLETE

ACTIVE_HASHED_AGENT_COUNT=$ACTIVE_HASHED_AGENT_COUNT
CANONICAL_ASUS_AGENT_CORE_COUNT=$ASUS_CORE_COUNT

NONQUARANTINE_NAMED_MODULE_COUNT=$NONQUARANTINE_FOUND
QUARANTINE_MODULE_CLASS_COUNT=$QUARANTINE_ONLY_COUNT

ACTIVE_CONTRACT_FILENAME_SIGNAL_COUNT=$CONTRACT_SIGNAL_COUNT
ACTIVE_DESCRIPTOR_FILENAME_SIGNAL_COUNT=$DESCRIPTOR_SIGNAL_COUNT
ACTIVE_REGISTRY_FILENAME_SIGNAL_COUNT=$REGISTRY_SIGNAL_COUNT
ACTIVE_TASK_REGISTRY_FILENAME_SIGNAL_COUNT=$TASK_REGISTRY_SIGNAL_COUNT

LOCAL_IMPORT_STATUS=$LOCAL_IMPORT_STATUS

QUARANTINE_PYTHONPATH_ALLOWED=$QUARANTINE_PYTHONPATH_ALLOWED
PYTHONPATH_CHANGE_EXECUTED=NO
FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_RENAME_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- NON-QUARANTINE MODULE STATUS ---"
cat "$OUT/CANONICAL_MODULE_STATUS.txt"

echo
echo "--- QUARANTINE STATUS ---"
cat "$OUT/QUARANTINE_MODULE_STATUS.txt"

echo "============================================================"

case "$LOCAL_IMPORT_STATUS" in

  NAMED_ACTIVE_MODULES_FOUND)
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094_ISOLATED_IMPORT_CANARY"
    ;;

  ACTIVE_HASHED_IMPLEMENTATIONS_REQUIRE_BINDING_PROOF)
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=HASHED_ACTIVE_MODULE_BINDING_NOT_YET_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R1_HASHED_MODULE_BINDING_PROOF"
    ;;

  *)
    echo "RESULT=HOLD"
    echo "BLOCKER=ACTIVE_LOCAL_IMPORT_BINDING_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R1_HASHED_MODULE_BINDING_PROOF"
    ;;
esac

echo "REPORT_DIR=$OUT"
echo "============================================================"
