#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098"
echo " CONTROLLED METADATA PILOT CANARY — HUMAN GATE"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_PARENT="$ROOT/03_AGENTS_ACTIVE"
PACKAGE_DIR="$AGENT_PARENT/VALIDATED_PENDING_RUNTIME"
PILOT_FILE="$PACKAGE_DIR/ea4106a2d52a_metadata_agent_pilot.py"

REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098"
echo "MODE=HUMAN_GATE_CONTROLLED_METADATA_PILOT_CANARY_ONLY"
echo "START_UTC=$START_UTC"
echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_098_CONTROLLED_METADATA_PILOT_CANARY_ONLY"

echo "ALLOW=RUN_METADATA_PILOT_ONE_FUNCTION_ONLY"
echo "NETWORK=DENY"
echo "FILE_WRITE=DENY"
echo "DELETE=DENY"
echo "MOVE=DENY"
echo "RENAME=DENY"
echo "FORMAT=DENY"
echo "PACKAGE_INSTALL=DENY"
echo "SERVICE_START=DENY"
echo "EXTERNAL_SEND=DENY"
echo "PERSISTENT_PYTHONPATH_CHANGE=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/SIGNATURE_PROOF.txt"
: > "$OUT/CANARY_OUTPUT.txt"
: > "$OUT/POST_CANARY_STATUS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== PREFLIGHT ====="

if [[ ! -f "$PILOT_FILE" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=METADATA_PILOT_FILE_NOT_FOUND"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo "PILOT_FILE=$PILOT_FILE"
echo "PILOT_SHA256=$(sha256sum "$PILOT_FILE" | awk '{print $1}')"
echo "PYTHON3=$(command -v python3)"
echo "PYTHON3_VERSION=$(python3 --version 2>&1)"

echo
echo "===== STATIC SIGNATURE PROOF ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$PILOT_FILE" \
  "$OUT/SIGNATURE_PROOF.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

tree = ast.parse(
    path.read_text(errors="replace"),
    filename=str(path)
)

target = None

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "run_metadata_pilot":
            target = node
            break

if target is None:
    out.write_text(
        "FUNCTION_FOUND=NO\n"
        "REQUIRED_POSITIONAL_COUNT=-1\n"
    )
    raise SystemExit(0)

args = target.args

positional = list(args.posonlyargs) + list(args.args)
defaults = list(args.defaults)

required_positional = max(
    0,
    len(positional) - len(defaults)
)

required_kwonly = sum(
    1
    for default in args.kw_defaults
    if default is None
)

out.write_text(
    "FUNCTION_FOUND=YES\n"
    f"FUNCTION_NAME={target.name}\n"
    f"POSITIONAL_ARG_COUNT={len(positional)}\n"
    f"REQUIRED_POSITIONAL_COUNT={required_positional}\n"
    f"KEYWORD_ONLY_ARG_COUNT={len(args.kwonlyargs)}\n"
    f"REQUIRED_KEYWORD_ONLY_COUNT={required_kwonly}\n"
    f"VARARG={'YES' if args.vararg else 'NO'}\n"
    f"KWARG={'YES' if args.kwarg else 'NO'}\n"
)
PY

cat "$OUT/SIGNATURE_PROOF.txt"

FUNCTION_FOUND="$(
  awk -F= '$1=="FUNCTION_FOUND"{print $2}' \
    "$OUT/SIGNATURE_PROOF.txt"
)"

REQUIRED_POSITIONAL_COUNT="$(
  awk -F= '$1=="REQUIRED_POSITIONAL_COUNT"{print $2}' \
    "$OUT/SIGNATURE_PROOF.txt"
)"

REQUIRED_KEYWORD_ONLY_COUNT="$(
  awk -F= '$1=="REQUIRED_KEYWORD_ONLY_COUNT"{print $2}' \
    "$OUT/SIGNATURE_PROOF.txt"
)"

REQUIRED_POSITIONAL_COUNT="${REQUIRED_POSITIONAL_COUNT:--1}"
REQUIRED_KEYWORD_ONLY_COUNT="${REQUIRED_KEYWORD_ONLY_COUNT:--1}"

if [[ "$FUNCTION_FOUND" != "YES" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=RUN_METADATA_PILOT_FUNCTION_NOT_FOUND"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R1_METADATA_PILOT_SIGNATURE_ANALYSIS"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

if (( REQUIRED_POSITIONAL_COUNT > 0 ||
      REQUIRED_KEYWORD_ONLY_COUNT > 0 )); then

    echo "RESULT=HOLD"
    echo "BLOCKER=RUN_METADATA_PILOT_REQUIRES_ARGUMENTS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R1_METADATA_PILOT_ARGUMENT_PLAN"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo
echo "===== HUMAN GATE CANARY ====="
echo "ACTION=RUN_METADATA_PILOT_ONE_FUNCTION_ONLY"

set +e

PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONPATH="$AGENT_PARENT" \
python3 - <<'PY' 2>&1 | tee "$OUT/CANARY_OUTPUT.txt"
import builtins
import importlib
import os
import pathlib
import shutil
import socket
import sys

# ---------------------------------------------------------
# Fail-closed write/network guards.
# Reads remain permitted.
# ---------------------------------------------------------

_real_open = builtins.open

def guarded_open(file, mode="r", *args, **kwargs):
    mode = str(mode)
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        raise PermissionError(
            "PROTOCOL_888_CANARY_FILE_WRITE_DENIED"
        )
    return _real_open(file, mode, *args, **kwargs)

builtins.open = guarded_open

def deny_write(*args, **kwargs):
    raise PermissionError(
        "PROTOCOL_888_CANARY_FILESYSTEM_MUTATION_DENIED"
    )

pathlib.Path.write_text = deny_write
pathlib.Path.write_bytes = deny_write
pathlib.Path.touch = deny_write
pathlib.Path.mkdir = deny_write
pathlib.Path.unlink = deny_write
pathlib.Path.rename = deny_write
pathlib.Path.replace = deny_write

os.remove = deny_write
os.unlink = deny_write
os.rename = deny_write
os.replace = deny_write
os.mkdir = deny_write
os.makedirs = deny_write

shutil.copy = deny_write
shutil.copy2 = deny_write
shutil.copyfile = deny_write
shutil.move = deny_write
shutil.rmtree = deny_write

class DeniedSocket:
    def __init__(self, *args, **kwargs):
        raise PermissionError(
            "PROTOCOL_888_CANARY_NETWORK_DENIED"
        )

socket.socket = DeniedSocket

print("CANARY_POLICY=FAIL_CLOSED")
print("NETWORK_GUARD=ACTIVE")
print("FILESYSTEM_WRITE_GUARD=ACTIVE")
print("PYTHONDONTWRITEBYTECODE=" +
      os.environ.get("PYTHONDONTWRITEBYTECODE", ""))
print("PYTHONNOUSERSITE=" +
      os.environ.get("PYTHONNOUSERSITE", ""))

module_name = (
    "VALIDATED_PENDING_RUNTIME."
    "ea4106a2d52a_metadata_agent_pilot"
)

module = importlib.import_module(module_name)

fn = getattr(module, "run_metadata_pilot")

print("MODULE_IMPORT=PASS")
print("FUNCTION_RESOLUTION=PASS")

result = fn()

print("FUNCTION_CALL=PASS")
print("RESULT_TYPE=" + type(result).__name__)

if hasattr(result, "to_dict") and callable(result.to_dict):
    try:
        data = result.to_dict()
        print("RESULT_TO_DICT=PASS")
        print("RESULT_KEYS=" +
              ",".join(sorted(map(str, data.keys()))))
    except Exception as exc:
        print(
            "RESULT_TO_DICT=FAIL:"
            + type(exc).__name__
            + ":"
            + str(exc)
        )

print("CANARY_COMPLETED=YES")
PY

CANARY_RC=${PIPESTATUS[0]}

set -e

FUNCTION_CALL_PASS_COUNT="$(
  grep -c '^FUNCTION_CALL=PASS$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

CANARY_COMPLETED_COUNT="$(
  grep -c '^CANARY_COMPLETED=YES$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

WRITE_DENIAL_COUNT="$(
  grep -c 'PROTOCOL_888_CANARY_.*WRITE_DENIED\|PROTOCOL_888_CANARY_FILESYSTEM_MUTATION_DENIED' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

NETWORK_DENIAL_COUNT="$(
  grep -c 'PROTOCOL_888_CANARY_NETWORK_DENIED' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

BYTECODE_COUNT="$(
  find "$PACKAGE_DIR" \
    -type f \
    \( -name '*.pyc' -o -path '*/__pycache__/*' \) \
    2>/dev/null |
  wc -l |
  tr -d ' '
)"

cat > "$OUT/POST_CANARY_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CONTROLLED_METADATA_PILOT_CANARY=COMPLETE

CANARY_RC=$CANARY_RC

FUNCTION_CALL_PASS_COUNT=$FUNCTION_CALL_PASS_COUNT
CANARY_COMPLETED_COUNT=$CANARY_COMPLETED_COUNT

FILESYSTEM_WRITE_DENIAL_COUNT=$WRITE_DENIAL_COUNT
NETWORK_DENIAL_COUNT=$NETWORK_DENIAL_COUNT

BYTECODE_ARTIFACT_COUNT=$BYTECODE_COUNT

NETWORK_PERMISSION=DENY
FILESYSTEM_WRITE_PERMISSION=DENY
DELETE_PERMISSION=DENY
MOVE_PERMISSION=DENY
RENAME_PERMISSION=DENY

PACKAGE_INSTALL_EXECUTED=NO
SERVICE_START_EXECUTED=NO
EXTERNAL_SEND_EXECUTED=NO
PERSISTENT_PYTHONPATH_CHANGE_EXECUTED=NO

TARGET_FUNCTION_EXECUTED=run_metadata_pilot
EXECUTED_FUNCTION_COUNT=1

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- POST CANARY STATUS ---"
cat "$OUT/POST_CANARY_STATUS.txt"

echo "============================================================"

if [[ "$CANARY_RC" -ne 0 ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=CONTROLLED_METADATA_PILOT_CANARY_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R1_CANARY_FAILURE_ANALYSIS"

elif [[ "$FUNCTION_CALL_PASS_COUNT" -ne 1 ||
        "$CANARY_COMPLETED_COUNT" -ne 1 ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=CONTROLLED_METADATA_PILOT_CANARY_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R1_CANARY_FAILURE_ANALYSIS"

else

    echo "RESULT=PASS"
    echo "CONTROLLED_METADATA_PILOT_CANARY=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_099_POST_CANARY_FINAL_QUALIFICATION"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
