#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 096"
echo " CONTROLLED AGENT RUNTIME PREFLIGHT — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
CANONICAL_ROOT="$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION"

REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_096_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=096"
echo "MODE=READ_ONLY_CONTROLLED_AGENT_RUNTIME_PREFLIGHT"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/PYTHON_FILE_MATRIX.txt"
: > "$OUT/ENTRYPOINT_MATRIX.txt"
: > "$OUT/TOP_LEVEL_RISK_MATRIX.txt"
: > "$OUT/CALLABLE_MATRIX.txt"
: > "$OUT/FINAL_STATUS.txt"

{
    find "$AGENT_ROOT" -maxdepth 1 -type f -iname '*.py' 2>/dev/null
    find "$CANONICAL_ROOT" -type f -iname '*.py' 2>/dev/null
} | sort -u > "$OUT/PYTHON_FILE_MATRIX.txt"

PYTHON_FILE_COUNT="$(
    wc -l < "$OUT/PYTHON_FILE_MATRIX.txt" |
    tr -d ' '
)"

echo "===== STATIC RUNTIME ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$OUT/PYTHON_FILE_MATRIX.txt" \
  "$OUT/ENTRYPOINT_MATRIX.txt" \
  "$OUT/TOP_LEVEL_RISK_MATRIX.txt" \
  "$OUT/CALLABLE_MATRIX.txt" <<'PY'
import ast
import sys
from pathlib import Path

source_list = Path(sys.argv[1])
entry_out = Path(sys.argv[2])
risk_out = Path(sys.argv[3])
callable_out = Path(sys.argv[4])

entry_rows = []
risk_rows = []
callable_rows = []

RISK_CALLS = {
    "open",
    "exec",
    "eval",
    "compile",
    "__import__",
}

NETWORK_HINTS = {
    "socket",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "smtplib",
    "subprocess",
}

for line in source_list.read_text(errors="replace").splitlines():
    path = Path(line)

    try:
        tree = ast.parse(
            path.read_text(errors="replace"),
            filename=str(path)
        )
    except Exception as exc:
        risk_rows.append(
            f"FILE={path}\tPARSE=FAIL\tERROR={type(exc).__name__}:{exc}"
        )
        continue

    funcs = []
    classes = []
    main_guard = False
    top_level_calls = []
    imports = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node.name)

        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

        elif isinstance(node, ast.If):
            try:
                if (
                    isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"
                    and len(node.test.comparators) == 1
                    and isinstance(node.test.comparators[0], ast.Constant)
                    and node.test.comparators[0].value == "__main__"
                ):
                    main_guard = True
            except Exception:
                pass

        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            top_level_calls.append(ast.unparse(node.value.func))

        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            top_level_calls.append(ast.unparse(node.value.func))

        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            top_level_calls.append(ast.unparse(node.value.func))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    callable_rows.append(
        f"FILE={path}\t"
        f"FUNCTIONS={','.join(sorted(set(funcs)))}\t"
        f"CLASSES={','.join(sorted(set(classes)))}"
    )

    entry_rows.append(
        f"FILE={path}\tMAIN_GUARD={'YES' if main_guard else 'NO'}"
    )

    suspicious_call_count = 0

    for call in top_level_calls:
        root = call.split(".")[0]
        if root in RISK_CALLS:
            suspicious_call_count += 1

    network_signal = any(
        imp.split(".")[0] in NETWORK_HINTS
        for imp in imports
    )

    risk_rows.append(
        f"FILE={path}\t"
        f"TOP_LEVEL_CALL_COUNT={len(top_level_calls)}\t"
        f"SUSPICIOUS_TOP_LEVEL_CALL_COUNT={suspicious_call_count}\t"
        f"NETWORK_OR_SUBPROCESS_IMPORT_SIGNAL={'YES' if network_signal else 'NO'}\t"
        f"TOP_LEVEL_CALLS={','.join(top_level_calls)}"
    )

entry_out.write_text(
    "\n".join(entry_rows) + ("\n" if entry_rows else "")
)

risk_out.write_text(
    "\n".join(risk_rows) + ("\n" if risk_rows else "")
)

callable_out.write_text(
    "\n".join(callable_rows) + ("\n" if callable_rows else "")
)
PY

MAIN_GUARD_COUNT="$(
    grep -c 'MAIN_GUARD=YES' "$OUT/ENTRYPOINT_MATRIX.txt" || true
)"

SUSPICIOUS_TOP_LEVEL_FILE_COUNT="$(
    awk -F '\t' '
    {
      for(i=1;i<=NF;i++){
        if($i ~ /^SUSPICIOUS_TOP_LEVEL_CALL_COUNT=/){
          split($i,a,"=")
          if(a[2]+0 > 0) c++
        }
      }
    }
    END {print c+0}
    ' "$OUT/TOP_LEVEL_RISK_MATRIX.txt"
)"

NETWORK_SIGNAL_FILE_COUNT="$(
    grep -c 'NETWORK_OR_SUBPROCESS_IMPORT_SIGNAL=YES' \
      "$OUT/TOP_LEVEL_RISK_MATRIX.txt" || true
)"

FUNCTION_BEARING_FILE_COUNT="$(
    awk -F '\t' '
      {
        for(i=1;i<=NF;i++){
          if($i ~ /^FUNCTIONS=/ && $i != "FUNCTIONS=") {
            c++
            break
          }
        }
      }
      END {print c+0}
    ' "$OUT/CALLABLE_MATRIX.txt"
)"

CLASS_BEARING_FILE_COUNT="$(
    awk -F '\t' '
      {
        for(i=1;i<=NF;i++){
          if($i ~ /^CLASSES=/ && $i != "CLASSES=") {
            c++
            break
          }
        }
      }
      END {print c+0}
    ' "$OUT/CALLABLE_MATRIX.txt"
)"

if (( SUSPICIOUS_TOP_LEVEL_FILE_COUNT == 0 )); then
    STATIC_RUNTIME_RISK="LOW"
else
    STATIC_RUNTIME_RISK="REVIEW_REQUIRED"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CONTROLLED_RUNTIME_PREFLIGHT=COMPLETE

PYTHON_FILE_COUNT=$PYTHON_FILE_COUNT

MAIN_GUARD_FILE_COUNT=$MAIN_GUARD_COUNT
FUNCTION_BEARING_FILE_COUNT=$FUNCTION_BEARING_FILE_COUNT
CLASS_BEARING_FILE_COUNT=$CLASS_BEARING_FILE_COUNT

SUSPICIOUS_TOP_LEVEL_FILE_COUNT=$SUSPICIOUS_TOP_LEVEL_FILE_COUNT
NETWORK_OR_SUBPROCESS_SIGNAL_FILE_COUNT=$NETWORK_SIGNAL_FILE_COUNT

STATIC_RUNTIME_RISK=$STATIC_RUNTIME_RISK

PYTHON_MODULE_EXECUTION_EXECUTED=NO
AGENT_TASK_EXECUTION_EXECUTED=NO
SERVICE_START_EXECUTED=NO
NETWORK_EXECUTED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_DELETE_EXECUTED=NO

PACKAGE_INSTALL_EXECUTED=NO
PYTHONPATH_PERSISTENT_CHANGE_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- ENTRYPOINT MATRIX ---"
cat "$OUT/ENTRYPOINT_MATRIX.txt"

echo
echo "--- TOP LEVEL RISK MATRIX ---"
cat "$OUT/TOP_LEVEL_RISK_MATRIX.txt"

echo "============================================================"

if (( SUSPICIOUS_TOP_LEVEL_FILE_COUNT > 0 )); then

    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=TOP_LEVEL_RUNTIME_SIDE_EFFECT_SIGNALS_REQUIRE_CLASSIFICATION"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_096R1_RUNTIME_SIDE_EFFECT_CLASSIFICATION"

else

    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_097_CONTROLLED_AGENT_CANARY_PLAN"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
