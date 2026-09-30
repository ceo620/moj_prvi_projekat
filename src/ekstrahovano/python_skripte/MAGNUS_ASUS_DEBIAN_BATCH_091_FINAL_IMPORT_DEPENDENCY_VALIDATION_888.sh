#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 091"
echo " FINAL IMPORT DEPENDENCY VALIDATION — STATIC / NO EXECUTION"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_091_$START_UTC"

mkdir -p "$OUT"

CANONICAL_ROOT="$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=091"
echo "MODE=STATIC_IMPORT_DEPENDENCY_VALIDATION"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/PYTHON_FILES.txt"
: > "$OUT/IMPORTS_RAW.txt"
: > "$OUT/IMPORT_ROOTS.txt"
: > "$OUT/STDLIB_IMPORTS.txt"
: > "$OUT/AVAILABLE_IMPORTS.txt"
: > "$OUT/MISSING_IMPORTS.txt"
: > "$OUT/FINAL_STATUS.txt"

{
    find "$CANONICAL_ROOT" -type f -iname '*.py' 2>/dev/null
    find "$AGENT_ROOT" -maxdepth 2 -type f -iname '*.py' 2>/dev/null
} | sort -u > "$OUT/PYTHON_FILES.txt"

PYTHON_FILE_COUNT="$(wc -l < "$OUT/PYTHON_FILES.txt" | tr -d ' ')"

echo "===== STATIC IMPORT EXTRACTION ====="

PYTHONDONTWRITEBYTECODE=1 python3 - "$OUT/PYTHON_FILES.txt" "$OUT/IMPORTS_RAW.txt" <<'PY'
import ast
import sys
from pathlib import Path

source_list = Path(sys.argv[1])
output = Path(sys.argv[2])

rows = []

for line in source_list.read_text(errors="replace").splitlines():
    path = Path(line)
    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception as exc:
        rows.append(f"PARSE_ERROR\t{path}\t{type(exc).__name__}:{exc}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                rows.append(f"IMPORT\t{path}\t{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            rows.append(f"FROM\t{path}\t{module}")

output.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

awk -F '\t' '
$1=="IMPORT" || $1=="FROM" {
    n=$3
    sub(/\..*/, "", n)
    if (n != "") print n
}
' "$OUT/IMPORTS_RAW.txt" \
| sort -u > "$OUT/IMPORT_ROOTS.txt"

IMPORT_ROOT_COUNT="$(wc -l < "$OUT/IMPORT_ROOTS.txt" | tr -d ' ')"

echo "===== IMPORT CLASSIFICATION ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$OUT/IMPORT_ROOTS.txt" \
  "$OUT/STDLIB_IMPORTS.txt" \
  "$OUT/AVAILABLE_IMPORTS.txt" \
  "$OUT/MISSING_IMPORTS.txt" <<'PY'
import sys
import importlib.util
from pathlib import Path

roots = Path(sys.argv[1])
stdlib_out = Path(sys.argv[2])
available_out = Path(sys.argv[3])
missing_out = Path(sys.argv[4])

stdlib = set(getattr(sys, "stdlib_module_names", ()))

stdlib_found = []
available = []
missing = []

for name in roots.read_text(errors="replace").splitlines():
    name = name.strip()
    if not name:
        continue

    if name in stdlib:
        stdlib_found.append(name)
        continue

    try:
        spec = importlib.util.find_spec(name)
    except Exception:
        spec = None

    if spec is not None:
        available.append(name)
    else:
        missing.append(name)

stdlib_out.write_text("\n".join(stdlib_found) + ("\n" if stdlib_found else ""))
available_out.write_text("\n".join(available) + ("\n" if available else ""))
missing_out.write_text("\n".join(missing) + ("\n" if missing else ""))
PY

STDLIB_COUNT="$(wc -l < "$OUT/STDLIB_IMPORTS.txt" | tr -d ' ')"
AVAILABLE_COUNT="$(wc -l < "$OUT/AVAILABLE_IMPORTS.txt" | tr -d ' ')"
MISSING_COUNT="$(wc -l < "$OUT/MISSING_IMPORTS.txt" | tr -d ' ')"

if (( MISSING_COUNT == 0 )); then
    IMPORT_DEPENDENCY_STATUS="READY"
else
    IMPORT_DEPENDENCY_STATUS="REVIEW_REQUIRED"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

IMPORT_DEPENDENCY_AUDIT=COMPLETE

PYTHON_FILE_COUNT=$PYTHON_FILE_COUNT
IMPORT_ROOT_COUNT=$IMPORT_ROOT_COUNT

STDLIB_IMPORT_COUNT=$STDLIB_COUNT
AVAILABLE_NON_STDLIB_IMPORT_COUNT=$AVAILABLE_COUNT
MISSING_IMPORT_COUNT=$MISSING_COUNT

IMPORT_DEPENDENCY_STATUS=$IMPORT_DEPENDENCY_STATUS

PYTHON_EXECUTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
SERVICE_START_EXECUTED=NO
NETWORK_WRITE_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

PYTHONDONTWRITEBYTECODE=1

INSTALL_ALLOWED=NO
UPGRADE_ALLOWED=NO
AGENT_EXECUTION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO
NETWORK_WRITE_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- IMPORT ROOTS ---"
cat "$OUT/IMPORT_ROOTS.txt"

echo
echo "--- MISSING IMPORTS ---"
cat "$OUT/MISSING_IMPORTS.txt" || true

echo "============================================================"

if (( MISSING_COUNT > 0 )); then
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=MISSING_PYTHON_IMPORT_DEPENDENCIES"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_092_IMPORT_DEPENDENCY_CLASSIFICATION"
else
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_092_CONTROLLED_AGENT_CANARY_PREFLIGHT"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
