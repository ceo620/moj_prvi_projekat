#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 093R2R2"
echo " TASK REGISTRY PROVENANCE ANALYSIS — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_093R2R2_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=093R2R2"
echo "MODE=READ_ONLY_TASK_REGISTRY_PROVENANCE_ANALYSIS"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/ALL_TASK_REGISTRY_FILES.txt"
: > "$OUT/HASH_MATRIX.txt"
: > "$OUT/HASH_REFERENCE_MATCHES.txt"
: > "$OUT/QUARANTINE_STATIC_ANALYSIS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== ALL PHYSICAL TASK_REGISTRY FILES ====="

find "$ROOT" \
  -type f \
  -name 'task_registry.py' \
  2>/dev/null \
  | sort \
  | tee "$OUT/ALL_TASK_REGISTRY_FILES.txt"

PHYSICAL_COUNT="$(
  wc -l < "$OUT/ALL_TASK_REGISTRY_FILES.txt" | tr -d ' '
)"

echo
echo "===== HASH MATRIX ====="

while IFS= read -r f; do
    [[ -f "$f" ]] || continue

    H="$(sha256sum "$f" | awk '{print $1}')"
    SIZE="$(stat -c '%s' "$f" 2>/dev/null || echo UNKNOWN)"

    printf '%s\t%s\t%s\n' "$H" "$SIZE" "$f" \
      | tee -a "$OUT/HASH_MATRIX.txt"

done < "$OUT/ALL_TASK_REGISTRY_FILES.txt"

UNIQUE_HASH_COUNT="$(
  cut -f1 "$OUT/HASH_MATRIX.txt" |
  sort -u |
  wc -l |
  tr -d ' '
)"

echo
echo "===== STATIC IMPLEMENTATION ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$OUT/ALL_TASK_REGISTRY_FILES.txt" \
  "$OUT/QUARANTINE_STATIC_ANALYSIS.txt" <<'PY'
import ast
import hashlib
import sys
from pathlib import Path

source = Path(sys.argv[1])
output = Path(sys.argv[2])

rows = []

for line in source.read_text(errors="replace").splitlines():
    path = Path(line)

    try:
        data = path.read_bytes()
        tree = ast.parse(data.decode(errors="replace"), filename=str(path))
    except Exception as exc:
        rows.extend([
            f"FILE={path}",
            f"PARSE_STATUS=FAIL:{type(exc).__name__}:{exc}",
            ""
        ])
        continue

    classes = sorted({
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
    })

    funcs = sorted({
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    })

    imports = []

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports.extend(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module or "")

    rows.extend([
        f"FILE={path}",
        "SHA256=" + hashlib.sha256(data).hexdigest(),
        "PARSE_STATUS=PASS",
        "CLASSES=" + ",".join(classes),
        "FUNCTIONS=" + ",".join(funcs),
        "IMPORTS=" + ",".join(sorted(set(imports))),
        ""
    ])

output.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/QUARANTINE_STATIC_ANALYSIS.txt"

TASKREGISTRY_CLASS_COUNT="$(
  grep -cE '^CLASSES=.*(^|,)TaskRegistry(,|$)' \
    "$OUT/QUARANTINE_STATIC_ANALYSIS.txt" || true
)"

TASKSPEC_CLASS_COUNT="$(
  grep -cE '^CLASSES=.*(^|,)TaskSpec(,|$)' \
    "$OUT/QUARANTINE_STATIC_ANALYSIS.txt" || true
)"

PARSE_PASS_COUNT="$(
  grep -c '^PARSE_STATUS=PASS$' \
    "$OUT/QUARANTINE_STATIC_ANALYSIS.txt" || true
)"

echo
echo "===== HASH REFERENCES OUTSIDE QUARANTINE ====="

while IFS=$'\t' read -r hash size path; do

    [[ -n "$hash" ]] || continue

    grep -RIl \
      --exclude='task_registry.py' \
      --exclude-dir='90_QUARANTINE' \
      --exclude-dir='08_ARCHIVES' \
      --exclude-dir='11_BACKUP' \
      --exclude-dir='99_ARCHIVE' \
      "$hash" \
      "$ROOT" \
      2>/dev/null \
      | while IFS= read -r ref; do
          printf '%s\t%s\n' "$hash" "$ref"
        done

done < "$OUT/HASH_MATRIX.txt" \
| sort -u \
| tee "$OUT/HASH_REFERENCE_MATCHES.txt"

HASH_REFERENCE_COUNT="$(
  wc -l < "$OUT/HASH_REFERENCE_MATCHES.txt" | tr -d ' '
)"

if (( PHYSICAL_COUNT > 0 &&
      UNIQUE_HASH_COUNT == 1 &&
      PARSE_PASS_COUNT == PHYSICAL_COUNT &&
      TASKREGISTRY_CLASS_COUNT == PHYSICAL_COUNT &&
      TASKSPEC_CLASS_COUNT == PHYSICAL_COUNT )); then

    CONTENT_CONSISTENCY="PROVEN"

else
    CONTENT_CONSISTENCY="NOT_PROVEN"
fi

if (( HASH_REFERENCE_COUNT > 0 )); then
    EXTERNAL_PROVENANCE_SIGNAL="FOUND"
else
    EXTERNAL_PROVENANCE_SIGNAL="NOT_FOUND"
fi

if [[ "$CONTENT_CONSISTENCY" == "PROVEN" &&
      "$EXTERNAL_PROVENANCE_SIGNAL" == "FOUND" ]]; then

    PROVENANCE_STATUS="STRONG_PROOF"

elif [[ "$CONTENT_CONSISTENCY" == "PROVEN" ]]; then

    PROVENANCE_STATUS="CONTENT_PROVEN_PROVENANCE_INCOMPLETE"

else
    PROVENANCE_STATUS="NOT_PROVEN"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

TASK_REGISTRY_PROVENANCE_AUDIT=COMPLETE

PHYSICAL_TASK_REGISTRY_COUNT=$PHYSICAL_COUNT
UNIQUE_CONTENT_HASH_COUNT=$UNIQUE_HASH_COUNT
PARSE_PASS_COUNT=$PARSE_PASS_COUNT

TASKREGISTRY_IMPLEMENTATION_COUNT=$TASKREGISTRY_CLASS_COUNT
TASKSPEC_IMPLEMENTATION_COUNT=$TASKSPEC_CLASS_COUNT

CONTENT_CONSISTENCY=$CONTENT_CONSISTENCY

NONQUARANTINE_HASH_REFERENCE_COUNT=$HASH_REFERENCE_COUNT
EXTERNAL_PROVENANCE_SIGNAL=$EXTERNAL_PROVENANCE_SIGNAL

PROVENANCE_STATUS=$PROVENANCE_STATUS

QUARANTINE_IMPORT_ALLOWED=NO
QUARANTINE_EXECUTION_ALLOWED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_RENAME_EXECUTED=NO
FILE_EXTRACTION_EXECUTED=NO

PYTHONPATH_CHANGE_EXECUTED=NO
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

echo
echo "--- HASH REFERENCES ---"
cat "$OUT/HASH_REFERENCE_MATCHES.txt" || true

echo "============================================================"

case "$PROVENANCE_STATUS" in

  STRONG_PROOF)
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R3_TASK_REGISTRY_RECONSTRUCTION_PLAN"
    ;;

  CONTENT_PROVEN_PROVENANCE_INCOMPLETE)
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=TASK_REGISTRY_CONTENT_VALID_BUT_PROVENANCE_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R3_TASK_REGISTRY_RECONSTRUCTION_PLAN"
    ;;

  *)
    echo "RESULT=HOLD"
    echo "BLOCKER=TASK_REGISTRY_PROVENANCE_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_093R2R3_TASK_REGISTRY_EVIDENCE_CHAIN_ANALYSIS"
    ;;
esac

echo "REPORT_DIR=$OUT"
echo "============================================================"
