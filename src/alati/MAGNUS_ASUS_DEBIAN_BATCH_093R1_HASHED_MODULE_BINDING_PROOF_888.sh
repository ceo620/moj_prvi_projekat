#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 093R1"
echo " HASHED MODULE BINDING PROOF — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_093R1_$START_UTC"

AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=093R1"
echo "MODE=READ_ONLY_HASHED_MODULE_BINDING_PROOF"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/HASHED_ROLE_MATRIX.txt"
: > "$OUT/TASK_REGISTRY_REFERENCE_ANALYSIS.txt"
: > "$OUT/CONTENT_HASH_MATRIX.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== HASHED ROLE MATRIX ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$AGENT_ROOT" \
  "$OUT/HASHED_ROLE_MATRIX.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])

targets = {
    "agent_contract": {"AgentExecutionContract"},
    "agent_descriptor": {"AgentDescriptor"},
    "agent_registry": {"AgentRegistry", "AgentRegistryError"},
    "task_registry": {"TaskRegistry", "TaskRegistryError"},
}

rows = []

for path in sorted(root.glob("*.py")):
    try:
        tree = ast.parse(path.read_text(errors="replace"), filename=str(path))
    except Exception as exc:
        rows.append(f"FILE={path}")
        rows.append(f"PARSE_ERROR={type(exc).__name__}:{exc}")
        rows.append("")
        continue

    classes = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }

    funcs = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    matched = []

    for module, expected_classes in targets.items():
        if classes & expected_classes:
            matched.append(module)

    rows.append(f"FILE={path}")
    rows.append("CLASSES=" + ",".join(sorted(classes)))
    rows.append("FUNCTIONS=" + ",".join(sorted(funcs)))
    rows.append("ROLE_MATCH=" + ",".join(sorted(matched)))
    rows.append("")

out.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/HASHED_ROLE_MATRIX.txt"

echo
echo "===== TASK_REGISTRY REFERENCES ====="

grep -RInE \
  '(^|[^A-Za-z0-9_])task_registry([^A-Za-z0-9_]|$)|TaskRegistry' \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  2>/dev/null \
  | tee "$OUT/TASK_REGISTRY_REFERENCE_ANALYSIS.txt" || true

echo
echo "===== CONTENT HASH MATRIX ====="

for f in "$AGENT_ROOT"/*.py; do
    [[ -f "$f" ]] || continue

    HASH="$(sha256sum "$f" | awk '{print $1}')"
    BASE="$(basename "$f")"

    printf '%s\t%s\n' "$HASH" "$BASE" \
      | tee -a "$OUT/CONTENT_HASH_MATRIX.txt"
done

CONTRACT_BINDING_COUNT="$(
  grep -c 'ROLE_MATCH=.*agent_contract' "$OUT/HASHED_ROLE_MATRIX.txt" || true
)"

DESCRIPTOR_BINDING_COUNT="$(
  grep -c 'ROLE_MATCH=.*agent_descriptor' "$OUT/HASHED_ROLE_MATRIX.txt" || true
)"

REGISTRY_BINDING_COUNT="$(
  grep -c 'ROLE_MATCH=.*agent_registry' "$OUT/HASHED_ROLE_MATRIX.txt" || true
)"

TASK_REGISTRY_BINDING_COUNT="$(
  grep -c 'ROLE_MATCH=.*task_registry' "$OUT/HASHED_ROLE_MATRIX.txt" || true
)"

TASK_REGISTRY_REFERENCE_COUNT="$(
  wc -l < "$OUT/TASK_REGISTRY_REFERENCE_ANALYSIS.txt" | tr -d ' '
)"

if (( CONTRACT_BINDING_COUNT > 0 &&
      DESCRIPTOR_BINDING_COUNT > 0 &&
      REGISTRY_BINDING_COUNT > 0 )); then
    CORE_HASHED_BINDING_STATUS="PROVEN"
else
    CORE_HASHED_BINDING_STATUS="NOT_PROVEN"
fi

if (( TASK_REGISTRY_BINDING_COUNT > 0 )); then
    TASK_REGISTRY_STATUS="ACTIVE_IMPLEMENTATION_PROVEN"
elif (( TASK_REGISTRY_REFERENCE_COUNT > 0 )); then
    TASK_REGISTRY_STATUS="REFERENCED_BUT_IMPLEMENTATION_NOT_PROVEN"
else
    TASK_REGISTRY_STATUS="NOT_REFERENCED_IN_ACTIVE_SCOPE"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

HASHED_MODULE_BINDING_AUDIT=COMPLETE

AGENT_CONTRACT_BINDING_COUNT=$CONTRACT_BINDING_COUNT
AGENT_DESCRIPTOR_BINDING_COUNT=$DESCRIPTOR_BINDING_COUNT
AGENT_REGISTRY_BINDING_COUNT=$REGISTRY_BINDING_COUNT
TASK_REGISTRY_BINDING_COUNT=$TASK_REGISTRY_BINDING_COUNT
TASK_REGISTRY_REFERENCE_COUNT=$TASK_REGISTRY_REFERENCE_COUNT

CORE_HASHED_BINDING_STATUS=$CORE_HASHED_BINDING_STATUS
TASK_REGISTRY_STATUS=$TASK_REGISTRY_STATUS

QUARANTINE_IMPORT_ALLOWED=NO
PYTHONPATH_CHANGE_EXECUTED=NO
FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_RENAME_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$CORE_HASHED_BINDING_STATUS" != "PROVEN" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=CORE_HASHED_MODULE_BINDING_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R2_CORE_MODULE_DEEP_ANALYSIS"

elif [[ "$TASK_REGISTRY_STATUS" == "REFERENCED_BUT_IMPLEMENTATION_NOT_PROVEN" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=TASK_REGISTRY_IMPLEMENTATION_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R2_TASK_REGISTRY_SOURCE_PROOF"

else
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094_ISOLATED_IMPORT_CANARY_PREFLIGHT"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
