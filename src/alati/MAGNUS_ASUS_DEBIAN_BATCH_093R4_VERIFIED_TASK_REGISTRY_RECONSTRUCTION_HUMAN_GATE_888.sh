#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 093R4"
echo " VERIFIED TASK REGISTRY RECONSTRUCTION — HUMAN GATE"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_093R4_$START_UTC"

EXPECTED_HASH="c719113415d0937e8298ae9dc82040065320d751862f4ccc281c36c1127495f8"
TARGET="$AGENT_ROOT/task_registry.py"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=093R4"
echo "MODE=HUMAN_GATE_COPY_VERIFIED_TASK_REGISTRY_ONLY"
echo "START_UTC=$START_UTC"

echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_093R4_COPY_VERIFIED_TASK_REGISTRY_ONLY"

echo "ALLOW=COPY_VERIFIED_TASK_REGISTRY_ONLY"
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

: > "$OUT/SOURCE_PREFLIGHT.txt"
: > "$OUT/COPY_STATUS.txt"
: > "$OUT/POST_COPY_VALIDATION.txt"

echo "===== SOURCE PREFLIGHT ====="

mapfile -t SOURCES < <(
  find "$ROOT/90_QUARANTINE" \
    -type f \
    -name 'task_registry.py' \
    2>/dev/null |
  sort
)

VALID_SOURCES=()

for src in "${SOURCES[@]}"; do
    H="$(sha256sum "$src" | awk '{print $1}')"

    printf 'SOURCE=%s\nSHA256=%s\n\n' "$src" "$H" \
      | tee -a "$OUT/SOURCE_PREFLIGHT.txt"

    if [[ "$H" == "$EXPECTED_HASH" ]]; then
        VALID_SOURCES+=("$src")
    fi
done

VALID_SOURCE_COUNT="${#VALID_SOURCES[@]}"

echo "VALID_SOURCE_COUNT=$VALID_SOURCE_COUNT" \
  | tee -a "$OUT/SOURCE_PREFLIGHT.txt"

if (( VALID_SOURCE_COUNT < 1 )); then
    echo "RESULT=HOLD"
    echo "BLOCKER=NO_VERIFIED_TASK_REGISTRY_SOURCE"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

SOURCE="${VALID_SOURCES[0]}"
SOURCE_HASH="$(sha256sum "$SOURCE" | awk '{print $1}')"

echo
echo "===== TARGET PREFLIGHT ====="

if [[ -e "$TARGET" ]]; then

    EXISTING_HASH="$(
      [[ -f "$TARGET" ]] \
      && sha256sum "$TARGET" | awk '{print $1}' \
      || echo NON_FILE_OBJECT
    )"

    echo "TARGET_ALREADY_EXISTS=YES"
    echo "TARGET_EXISTING_HASH=$EXISTING_HASH"

    if [[ "$EXISTING_HASH" == "$EXPECTED_HASH" ]]; then
        echo "RESULT=PASS"
        echo "STATUS=TARGET_ALREADY_PRESENT_IDENTICAL"
        echo "REPORT_DIR=$OUT"
        echo "NEXT_RECOMMENDED_BATCH=BATCH_094_ISOLATED_IMPORT_CANARY_PREFLIGHT"
        exit 0
    fi

    echo "RESULT=HOLD"
    echo "BLOCKER=TARGET_EXISTS_OVERWRITE_DENIED"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo "TARGET_ALREADY_EXISTS=NO"

echo
echo "===== HUMAN GATE MUTATION ====="
echo "ACTION=COPY_VERIFIED_TASK_REGISTRY_ONLY"
echo "SOURCE=$SOURCE"
echo "TARGET=$TARGET"
echo "SOURCE_SHA256=$SOURCE_HASH"

if [[ "$SOURCE_HASH" != "$EXPECTED_HASH" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=SOURCE_HASH_CHANGED_BEFORE_COPY"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

set +e

cp --no-clobber --preserve=mode,timestamps \
   "$SOURCE" "$TARGET" 2>&1 \
   | tee "$OUT/COPY_STATUS.txt"

COPY_RC=${PIPESTATUS[0]}

set -e

echo
echo "===== POST COPY VALIDATION ====="

if [[ -f "$TARGET" ]]; then
    TARGET_HASH="$(sha256sum "$TARGET" | awk '{print $1}')"
    TARGET_SIZE="$(stat -c '%s' "$TARGET" 2>/dev/null || echo UNKNOWN)"
else
    TARGET_HASH="MISSING"
    TARGET_SIZE="MISSING"
fi

PARSE_STATUS="FAIL"

if [[ -f "$TARGET" ]]; then
    if PYTHONDONTWRITEBYTECODE=1 python3 - "$TARGET" <<'PY'
import ast
import sys
from pathlib import Path

p = Path(sys.argv[1])
tree = ast.parse(p.read_text(errors="replace"), filename=str(p))

classes = {
    n.name for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
}

required = {"TaskRegistry", "TaskSpec"}

if not required.issubset(classes):
    raise SystemExit(2)
PY
    then
        PARSE_STATUS="PASS"
    fi
fi

{
echo "COPY_RC=$COPY_RC"
echo "SOURCE_SHA256=$SOURCE_HASH"
echo "TARGET_SHA256=$TARGET_HASH"
echo "TARGET_SIZE=$TARGET_SIZE"
echo "STATIC_PARSE_AND_CLASS_STATUS=$PARSE_STATUS"

echo "SOURCE_DELETE_EXECUTED=NO"
echo "SOURCE_MOVE_EXECUTED=NO"
echo "SOURCE_RENAME_EXECUTED=NO"

echo "TARGET_OVERWRITE_EXECUTED=NO"

echo "PYTHONPATH_CHANGE_EXECUTED=NO"
echo "AGENT_EXECUTION_EXECUTED=NO"
echo "PACKAGE_INSTALL_EXECUTED=NO"
echo "DELETE_EXECUTED=NO"
echo "FORMAT_EXECUTED=NO"
} | tee "$OUT/POST_COPY_VALIDATION.txt"

echo "============================================================"

if [[ "$COPY_RC" -ne 0 ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=TASK_REGISTRY_COPY_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R4R1_COPY_FAILURE_ANALYSIS"

elif [[ "$TARGET_HASH" != "$EXPECTED_HASH" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=POST_COPY_HASH_MISMATCH"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R4R2_HASH_MISMATCH_ANALYSIS"

elif [[ "$PARSE_STATUS" != "PASS" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=TASK_REGISTRY_STATIC_VALIDATION_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R4R3_STATIC_VALIDATION_ANALYSIS"

else

    echo "RESULT=PASS"
    echo "TASK_REGISTRY_RECONSTRUCTION=COMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_094_ISOLATED_IMPORT_CANARY_PREFLIGHT"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
