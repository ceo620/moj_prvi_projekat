#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R4"
echo " CONTROLLED METADATA PILOT CANARY — HUMAN GATE"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R4_$START_UTC"

TARGET="$AGENT_ROOT/05c0204f9c0a_agent_discovery.py"

EXPECTED_AGENT_ID="AGENT-dc77a383ab7dd347cc2d248d"
EXPECTED_RELATIVE_PATH="05c0204f9c0a_agent_discovery.py"
EXPECTED_SHA256="05c0204f9c0aba288d4dc8e74d171fe5ad78db39f743d0a53a78f4d5a581cc72"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R4"
echo "MODE=HUMAN_GATE_ONE_CONTROLLED_METADATA_PILOT_CANARY"
echo "START_UTC=$START_UTC"
echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_098R4_RUN_ONE_CONTROLLED_METADATA_PILOT_CANARY_ONLY"

echo "ALLOW=ONE_AGENT_ONE_METADATA_PILOT_CALL"
echo "NETWORK=DENY"
echo "FILE_WRITE=DENY"
echo "SERVICE_START=DENY"
echo "PACKAGE_INSTALL=DENY"
echo "EXTERNAL_SEND=DENY"
echo "DELETE=DENY"
echo "MOVE=DENY"
echo "RENAME=DENY"
echo "FORMAT=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/PREFLIGHT.txt"
: > "$OUT/CANARY_OUTPUT.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== PREFLIGHT ====="

if [[ ! -f "$TARGET" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=CANARY_TARGET_MISSING"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

ACTUAL_SHA256="$(sha256sum "$TARGET" | awk '{print $1}')"

{
echo "TARGET=$TARGET"
echo "EXPECTED_AGENT_ID=$EXPECTED_AGENT_ID"
echo "EXPECTED_RELATIVE_PATH=$EXPECTED_RELATIVE_PATH"
echo "EXPECTED_SHA256=$EXPECTED_SHA256"
echo "ACTUAL_SHA256=$ACTUAL_SHA256"
echo "PYTHON3=$(command -v python3)"
echo "PYTHON3_VERSION=$(python3 --version 2>&1)"
} | tee "$OUT/PREFLIGHT.txt"

if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=CANARY_TARGET_HASH_MISMATCH"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo
echo "===== CONTROLLED CANARY ====="

set +e

PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONPATH="$AGENT_ROOT" \
python3 - \
  "$TARGET" \
  "$EXPECTED_AGENT_ID" \
  "$EXPECTED_RELATIVE_PATH" \
  "$EXPECTED_SHA256" <<'PY' 2>&1 | tee "$OUT/CANARY_OUTPUT.txt"

import ast
import builtins
import hashlib
import os
import pathlib
import shutil
import socket
import sys

target = pathlib.Path(sys.argv[1])
expected_agent_id = sys.argv[2]
expected_relative_path = sys.argv[3]
expected_sha256 = sys.argv[4]

# ---------------------------------------------------------
# Establish target metadata before mutation guards.
# ---------------------------------------------------------

raw = target.read_bytes()
actual_sha256 = hashlib.sha256(raw).hexdigest()

if actual_sha256 != expected_sha256:
    raise SystemExit("TARGET_HASH_CHANGED")

tree = ast.parse(
    raw.decode("utf-8-sig"),
    filename=expected_relative_path,
)

classes = tuple(sorted(
    node.name
    for node in tree.body
    if isinstance(node, ast.ClassDef)
))

functions = tuple(sorted(
    node.name
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
))

imports = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.update(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module)

imports = tuple(sorted(imports))

# ---------------------------------------------------------
# Fail-closed guards.
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

def deny_mutation(*args, **kwargs):
    raise PermissionError(
        "PROTOCOL_888_CANARY_FILESYSTEM_MUTATION_DENIED"
    )

pathlib.Path.write_text = deny_mutation
pathlib.Path.write_bytes = deny_mutation
pathlib.Path.touch = deny_mutation
pathlib.Path.mkdir = deny_mutation
pathlib.Path.unlink = deny_mutation
pathlib.Path.rename = deny_mutation
pathlib.Path.replace = deny_mutation

os.remove = deny_mutation
os.unlink = deny_mutation
os.rename = deny_mutation
os.replace = deny_mutation
os.mkdir = deny_mutation
os.makedirs = deny_mutation

shutil.copy = deny_mutation
shutil.copy2 = deny_mutation
shutil.copyfile = deny_mutation
shutil.move = deny_mutation
shutil.rmtree = deny_mutation

class DeniedSocket:
    def __init__(self, *args, **kwargs):
        raise PermissionError(
            "PROTOCOL_888_CANARY_NETWORK_DENIED"
        )

socket.socket = DeniedSocket

# ---------------------------------------------------------
# Local imports only.
# ---------------------------------------------------------

from agent_descriptor import AgentDescriptor
from agent_registry import AgentRegistry

from evidence_complete_producer import (
    build_evidence_complete_record,
)

from ea4106a2d52a_metadata_agent_pilot import (
    run_metadata_pilot,
)

from importlib import import_module

validator = import_module(
    "4fae0850626f_agent_validation_engine"
)

validate_descriptors = validator.validate_descriptors
validate_registry = validator.validate_registry

print("CANARY_POLICY=FAIL_CLOSED")
print("NETWORK_GUARD=ACTIVE")
print("FILESYSTEM_WRITE_GUARD=ACTIVE")

# ---------------------------------------------------------
# One real descriptor.
# ---------------------------------------------------------

descriptor = AgentDescriptor(
    agent_id=expected_agent_id,
    relative_path=expected_relative_path,
    sha256=expected_sha256,
    bytes=len(raw),
    score=2,
    reasons=("CONTROLLED_METADATA_PILOT_CANARY",),
    classes=classes,
    functions=functions,
    imports=imports,
)

print("DESCRIPTOR_CONSTRUCTION=PASS")

validated_ids = validate_descriptors((descriptor,))

if tuple(validated_ids) != (expected_agent_id,):
    raise RuntimeError("DESCRIPTOR_VALIDATION_RESULT_MISMATCH")

print("DESCRIPTOR_VALIDATION=PASS")

registry = AgentRegistry()
registry.register(descriptor)

validate_registry(
    registry,
    (descriptor,),
)

print("REGISTRY_VALIDATION=PASS")

agent_mapping = {
    "agent_id": descriptor.agent_id,
    "relative_path": descriptor.relative_path,
    "sha256": descriptor.sha256,
    "classes": descriptor.classes,
    "functions": descriptor.functions,
    "imports": descriptor.imports,
    "parse_status": descriptor.parse_status,
}

evidence_pack = build_evidence_complete_record(
    agent_mapping,
    descriptor_validation_pass=True,
    registry_validation_pass=True,
)

if evidence_pack != {
    "agent_id": expected_agent_id,
    "readiness_status": "EVIDENCE_COMPLETE",
}:
    raise RuntimeError("EVIDENCE_PACK_CONTRACT_MISMATCH")

print("EVIDENCE_PRODUCER=PASS")
print("EVIDENCE_READINESS=EVIDENCE_COMPLETE")

# ---------------------------------------------------------
# Exactly one metadata pilot call.
# ---------------------------------------------------------

result = run_metadata_pilot(
    agent_mapping,
    evidence_pack,
)

print("METADATA_PILOT_CALL=PASS")
print("METADATA_PILOT_CALL_COUNT=1")
print("RESULT_TYPE=" + type(result).__name__)

result_agent_id = getattr(result, "agent_id", None)
result_status = getattr(result, "status", None)
result_source_sha256 = getattr(result, "source_sha256", None)

print("RESULT_AGENT_ID=" + str(result_agent_id))
print("RESULT_STATUS=" + str(result_status))
print("RESULT_SOURCE_SHA256=" + str(result_source_sha256))

if result_agent_id != expected_agent_id:
    raise RuntimeError("RESULT_AGENT_ID_MISMATCH")

if result_source_sha256 != expected_sha256:
    raise RuntimeError("RESULT_SOURCE_SHA256_MISMATCH")

if result_status != "PASS_METADATA_CONTROL_PLANE":
    raise RuntimeError("RESULT_STATUS_MISMATCH")

print("RESULT_CONTRACT_VALIDATION=PASS")
print("CANARY_COMPLETED=YES")
PY

CANARY_RC=${PIPESTATUS[0]}

set -e

PILOT_PASS_COUNT="$(
  grep -c '^METADATA_PILOT_CALL=PASS$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

COMPLETED_COUNT="$(
  grep -c '^CANARY_COMPLETED=YES$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

RESULT_CONTRACT_PASS_COUNT="$(
  grep -c '^RESULT_CONTRACT_VALIDATION=PASS$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

DESCRIPTOR_PASS_COUNT="$(
  grep -c '^DESCRIPTOR_VALIDATION=PASS$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

REGISTRY_PASS_COUNT="$(
  grep -c '^REGISTRY_VALIDATION=PASS$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

PRODUCER_PASS_COUNT="$(
  grep -c '^EVIDENCE_PRODUCER=PASS$' \
    "$OUT/CANARY_OUTPUT.txt" || true
)"

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CONTROLLED_METADATA_PILOT_CANARY=COMPLETE

CANARY_RC=$CANARY_RC

DESCRIPTOR_VALIDATION_PASS_COUNT=$DESCRIPTOR_PASS_COUNT
REGISTRY_VALIDATION_PASS_COUNT=$REGISTRY_PASS_COUNT
EVIDENCE_PRODUCER_PASS_COUNT=$PRODUCER_PASS_COUNT

METADATA_PILOT_CALL_PASS_COUNT=$PILOT_PASS_COUNT
METADATA_PILOT_CALL_COUNT=$PILOT_PASS_COUNT

RESULT_CONTRACT_PASS_COUNT=$RESULT_CONTRACT_PASS_COUNT
CANARY_COMPLETED_COUNT=$COMPLETED_COUNT

TARGET_AGENT_ID=$EXPECTED_AGENT_ID
TARGET_RELATIVE_PATH=$EXPECTED_RELATIVE_PATH
TARGET_SHA256=$EXPECTED_SHA256

NETWORK_PERMISSION=DENY
FILESYSTEM_WRITE_PERMISSION=DENY

PACKAGE_INSTALL_EXECUTED=NO
SERVICE_START_EXECUTED=NO
EXTERNAL_SEND_EXECUTED=NO
DELETE_EXECUTED=NO
MOVE_EXECUTED=NO
RENAME_EXECUTED=NO
FORMAT_EXECUTED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$CANARY_RC" -ne 0 ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=CONTROLLED_METADATA_PILOT_CANARY_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R4R1_CANARY_FAILURE_ANALYSIS"

elif [[ "$DESCRIPTOR_PASS_COUNT" -ne 1 ||
        "$REGISTRY_PASS_COUNT" -ne 1 ||
        "$PRODUCER_PASS_COUNT" -ne 1 ||
        "$PILOT_PASS_COUNT" -ne 1 ||
        "$RESULT_CONTRACT_PASS_COUNT" -ne 1 ||
        "$COMPLETED_COUNT" -ne 1 ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=CONTROLLED_METADATA_PILOT_CANARY_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R4R1_CANARY_FAILURE_ANALYSIS"

else
    echo "RESULT=PASS"
    echo "BATCH_098_CONTROLLED_METADATA_PILOT_CANARY=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_099_POST_CANARY_FINAL_QUALIFICATION"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
