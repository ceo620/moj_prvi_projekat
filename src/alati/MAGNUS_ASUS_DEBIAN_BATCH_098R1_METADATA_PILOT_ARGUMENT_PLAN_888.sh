#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R1"
echo " METADATA PILOT ARGUMENT PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
PILOT_FILE="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R1"
echo "MODE=READ_ONLY_METADATA_PILOT_ARGUMENT_PLAN"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/FUNCTION_SIGNATURE.txt"
: > "$OUT/FUNCTION_SOURCE.txt"
: > "$OUT/CALL_SITES.txt"
: > "$OUT/ARGUMENT_USAGE.txt"
: > "$OUT/FINAL_STATUS.txt"

if [[ ! -f "$PILOT_FILE" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=METADATA_PILOT_FILE_NOT_FOUND"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo "===== STATIC FUNCTION ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$PILOT_FILE" \
  "$OUT/FUNCTION_SIGNATURE.txt" \
  "$OUT/FUNCTION_SOURCE.txt" \
  "$OUT/ARGUMENT_USAGE.txt" <<'PY'
import ast
import sys
from pathlib import Path

src = Path(sys.argv[1])
sig_out = Path(sys.argv[2])
source_out = Path(sys.argv[3])
usage_out = Path(sys.argv[4])

text = src.read_text(errors="replace")
tree = ast.parse(text, filename=str(src))

target = None

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "run_metadata_pilot":
            target = node
            break

if target is None:
    sig_out.write_text("FUNCTION_FOUND=NO\n")
    raise SystemExit(0)

args = list(target.args.posonlyargs) + list(target.args.args)
defaults = list(target.args.defaults)

required_count = len(args) - len(defaults)

rows = [
    "FUNCTION_FOUND=YES",
    f"FUNCTION_NAME={target.name}",
    f"ARGUMENT_COUNT={len(args)}",
    f"REQUIRED_ARGUMENT_COUNT={required_count}",
]

for index, arg in enumerate(args, start=1):
    annotation = ast.unparse(arg.annotation) if arg.annotation else "NONE"
    required = "YES" if index <= required_count else "NO"

    rows.extend([
        f"ARG_{index}_NAME={arg.arg}",
        f"ARG_{index}_ANNOTATION={annotation}",
        f"ARG_{index}_REQUIRED={required}",
    ])

sig_out.write_text("\n".join(rows) + "\n")

segment = ast.get_source_segment(text, target) or ""
source_out.write_text(segment + "\n")

usage = []

arg_names = {a.arg for a in args}

for node in ast.walk(target):
    if isinstance(node, ast.Name) and node.id in arg_names:
        usage.append(
            f"ARG={node.id}\t"
            f"LINENO={getattr(node, 'lineno', 'UNKNOWN')}\t"
            f"CTX={type(node.ctx).__name__}"
        )

usage_out.write_text(
    "\n".join(sorted(set(usage))) +
    ("\n" if usage else "")
)
PY

cat "$OUT/FUNCTION_SIGNATURE.txt"

echo
echo "===== FUNCTION SOURCE ====="
cat "$OUT/FUNCTION_SOURCE.txt"

echo
echo "===== ARGUMENT USAGE ====="
cat "$OUT/ARGUMENT_USAGE.txt"

echo
echo "===== CALL SITE SEARCH ====="

grep -RInE \
  'run_metadata_pilot[[:space:]]*\(' \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  2>/dev/null \
  | grep -v "$PILOT_FILE" \
  | tee "$OUT/CALL_SITES.txt" || true

CALL_SITE_COUNT="$(
  wc -l < "$OUT/CALL_SITES.txt" |
  tr -d ' '
)"

ARG1="$(
  awk -F= '$1=="ARG_1_NAME"{print $2}' \
    "$OUT/FUNCTION_SIGNATURE.txt"
)"

ARG2="$(
  awk -F= '$1=="ARG_2_NAME"{print $2}' \
    "$OUT/FUNCTION_SIGNATURE.txt"
)"

ARG1_ANNOTATION="$(
  awk -F= '$1=="ARG_1_ANNOTATION"{print $2}' \
    "$OUT/FUNCTION_SIGNATURE.txt"
)"

ARG2_ANNOTATION="$(
  awk -F= '$1=="ARG_2_ANNOTATION"{print $2}' \
    "$OUT/FUNCTION_SIGNATURE.txt"
)"

if (( CALL_SITE_COUNT > 0 )); then
    ARGUMENT_SOURCE_STATUS="CALL_SITE_EVIDENCE_FOUND"
else
    ARGUMENT_SOURCE_STATUS="NO_CALL_SITE_EVIDENCE"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

METADATA_PILOT_ARGUMENT_ANALYSIS=COMPLETE

ARGUMENT_1_NAME=${ARG1:-UNKNOWN}
ARGUMENT_1_ANNOTATION=${ARG1_ANNOTATION:-UNKNOWN}

ARGUMENT_2_NAME=${ARG2:-UNKNOWN}
ARGUMENT_2_ANNOTATION=${ARG2_ANNOTATION:-UNKNOWN}

CALL_SITE_COUNT=$CALL_SITE_COUNT
ARGUMENT_SOURCE_STATUS=$ARGUMENT_SOURCE_STATUS

TARGET_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
NETWORK_EXECUTED=NO
SERVICE_START_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_DELETE_EXECUTED=NO
PERSISTENT_PYTHONPATH_CHANGE_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- CALL SITES ---"
cat "$OUT/CALL_SITES.txt" || true

echo "============================================================"

if (( CALL_SITE_COUNT > 0 )); then
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2_METADATA_PILOT_ARGUMENT_BINDING_PROOF"
else
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=NO_EXISTING_METADATA_PILOT_CALL_SITE_FOUND"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2_METADATA_PILOT_ARGUMENT_SEMANTIC_ANALYSIS"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
