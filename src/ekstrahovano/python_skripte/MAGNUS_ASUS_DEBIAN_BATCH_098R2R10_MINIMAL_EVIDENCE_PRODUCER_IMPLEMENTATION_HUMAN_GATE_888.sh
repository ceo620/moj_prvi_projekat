#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R10"
echo " MINIMAL EVIDENCE PRODUCER IMPLEMENTATION — HUMAN GATE"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R10_$START_UTC"

TARGET="$AGENT_ROOT/evidence_complete_producer.py"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R10"
echo "MODE=HUMAN_GATE_CREATE_MINIMAL_EVIDENCE_PRODUCER_ONLY"
echo "START_UTC=$START_UTC"
echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_BATCH_098R2R10_CREATE_MINIMAL_EVIDENCE_PRODUCER_ONLY"

echo "ALLOW=CREATE_ONE_NEW_FILE_ONLY"
echo "TARGET=$TARGET"
echo "OVERWRITE=DENY"
echo "DELETE=DENY"
echo "MOVE=DENY"
echo "RENAME=DENY"
echo "NETWORK=DENY"
echo "PACKAGE_INSTALL=DENY"
echo "SERVICE_START=DENY"
echo "AGENT_EXECUTION=DENY"
} > "$OUT/BATCH.env"

: > "$OUT/PREFLIGHT.txt"
: > "$OUT/CREATION_STATUS.txt"
: > "$OUT/STATIC_VALIDATION.txt"
: > "$OUT/CONTRACT_VALIDATION.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== PREFLIGHT ====="

{
echo "TARGET=$TARGET"
echo "AGENT_ROOT=$AGENT_ROOT"
echo "PYTHON3=$(command -v python3 || true)"
echo "PYTHON3_VERSION=$(python3 --version 2>&1 || true)"
} | tee "$OUT/PREFLIGHT.txt"

if [[ -e "$TARGET" ]]; then
    EXISTING_HASH="NON_FILE_OBJECT"

    if [[ -f "$TARGET" ]]; then
        EXISTING_HASH="$(sha256sum "$TARGET" | awk '{print $1}')"
    fi

    echo "TARGET_EXISTS=YES" | tee -a "$OUT/PREFLIGHT.txt"
    echo "TARGET_EXISTING_HASH=$EXISTING_HASH" | tee -a "$OUT/PREFLIGHT.txt"

    echo "RESULT=HOLD"
    echo "BLOCKER=TARGET_ALREADY_EXISTS_OVERWRITE_DENIED"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo "TARGET_EXISTS=NO" | tee -a "$OUT/PREFLIGHT.txt"

echo
echo "===== HUMAN GATE MUTATION ====="
echo "ACTION=CREATE_MINIMAL_EVIDENCE_PRODUCER_ONLY"

TMP="$OUT/evidence_complete_producer.py.new"

cat > "$TMP" <<'PY'
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional


class EvidenceContractError(ValueError):
    pass


def build_evidence_complete_record(
    agent: Mapping[str, object],
    descriptor_validation_pass: bool,
    registry_validation_pass: bool,
    dependency_validation_pass: Optional[bool] = None,
) -> Dict[str, str]:
    required_fields = (
        "agent_id",
        "relative_path",
        "sha256",
    )

    for field in required_fields:
        value = agent.get(field)

        if value is None or str(value) == "":
            raise EvidenceContractError(
                f"MISSING_REQUIRED_AGENT_FIELD:{field}"
            )

    if descriptor_validation_pass is not True:
        raise EvidenceContractError(
            "DESCRIPTOR_VALIDATION_NOT_PROVEN"
        )

    if registry_validation_pass is not True:
        raise EvidenceContractError(
            "REGISTRY_VALIDATION_NOT_PROVEN"
        )

    if (
        dependency_validation_pass is not None
        and dependency_validation_pass is not True
    ):
        raise EvidenceContractError(
            "DEPENDENCY_VALIDATION_NOT_PROVEN"
        )

    parse_status: Any = agent.get("parse_status")

    if (
        parse_status is not None
        and str(parse_status) != "PASS"
    ):
        raise EvidenceContractError(
            f"AGENT_PARSE_STATUS_NOT_PASS:{parse_status}"
        )

    return {
        "agent_id": str(agent["agent_id"]),
        "readiness_status": "EVIDENCE_COMPLETE",
    }
PY

TMP_HASH="$(sha256sum "$TMP" | awk '{print $1}')"

echo "TMP_FILE=$TMP" | tee "$OUT/CREATION_STATUS.txt"
echo "TMP_SHA256=$TMP_HASH" | tee -a "$OUT/CREATION_STATUS.txt"

echo
echo "===== PRE-CREATE STATIC VALIDATION ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$TMP" \
  "$OUT/STATIC_VALIDATION.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

text = path.read_text(errors="strict")
tree = ast.parse(text, filename=str(path))

functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

classes = {
    node.name
    for node in tree.body
    if isinstance(node, ast.ClassDef)
}

target = functions.get("build_evidence_complete_record")

rows = [
    "PARSE_STATUS=PASS",
    f"EVIDENCE_CONTRACT_ERROR_CLASS={'PASS' if 'EvidenceContractError' in classes else 'FAIL'}",
    f"PRODUCER_FUNCTION={'PASS' if target is not None else 'FAIL'}",
]

if target is not None:
    source = ast.get_source_segment(text, target) or ""

    rows.extend([
        f"AGENT_ID_SIGNAL={'PASS' if 'agent_id' in source else 'FAIL'}",
        f"RELATIVE_PATH_SIGNAL={'PASS' if 'relative_path' in source else 'FAIL'}",
        f"SHA256_SIGNAL={'PASS' if 'sha256' in source else 'FAIL'}",
        f"EVIDENCE_COMPLETE_SIGNAL={'PASS' if 'EVIDENCE_COMPLETE' in source else 'FAIL'}",
        f"DESCRIPTOR_GATE_SIGNAL={'PASS' if 'descriptor_validation_pass' in source else 'FAIL'}",
        f"REGISTRY_GATE_SIGNAL={'PASS' if 'registry_validation_pass' in source else 'FAIL'}",
        f"DEPENDENCY_GATE_SIGNAL={'PASS' if 'dependency_validation_pass' in source else 'FAIL'}",
        f"PARSE_STATUS_GATE_SIGNAL={'PASS' if 'parse_status' in source else 'FAIL'}",
    ])

out.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/STATIC_VALIDATION.txt"

STATIC_FAIL_COUNT="$(
  grep -c '=FAIL$' "$OUT/STATIC_VALIDATION.txt" || true
)"

if (( STATIC_FAIL_COUNT > 0 )); then
    echo "RESULT=HOLD"
    echo "BLOCKER=PRODUCER_STATIC_VALIDATION_FAILED"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo
echo "===== CREATE TARGET ====="

set +e
cp --no-clobber "$TMP" "$TARGET"
COPY_RC=$?
set -e

echo "CREATE_RC=$COPY_RC" | tee -a "$OUT/CREATION_STATUS.txt"

if [[ "$COPY_RC" -ne 0 ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=TARGET_CREATION_FAILED"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

if [[ ! -f "$TARGET" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=TARGET_NOT_FOUND_AFTER_CREATION"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

TARGET_HASH="$(sha256sum "$TARGET" | awk '{print $1}')"

echo "TARGET_SHA256=$TARGET_HASH" | tee -a "$OUT/CREATION_STATUS.txt"

if [[ "$TARGET_HASH" != "$TMP_HASH" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=POST_CREATE_HASH_MISMATCH"
    echo "REPORT_DIR=$OUT"
    exit 0
fi

echo
echo "===== CONTRACT VALIDATION ====="

PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONPATH="$AGENT_ROOT" \
python3 - <<'PY' | tee "$OUT/CONTRACT_VALIDATION.txt"
from evidence_complete_producer import (
    EvidenceContractError,
    build_evidence_complete_record,
)

valid_agent = {
    "agent_id": "AGENT-CANARY-CONTRACT-ONLY",
    "relative_path": "contract/proof.py",
    "sha256": "0" * 64,
    "parse_status": "PASS",
}

record = build_evidence_complete_record(
    valid_agent,
    descriptor_validation_pass=True,
    registry_validation_pass=True,
    dependency_validation_pass=True,
)

assert record == {
    "agent_id": "AGENT-CANARY-CONTRACT-ONLY",
    "readiness_status": "EVIDENCE_COMPLETE",
}

print("VALID_CONTRACT_TEST=PASS")

failure_tests = 0

tests = [
    (
        {},
        True,
        True,
        True,
    ),
    (
        valid_agent,
        False,
        True,
        True,
    ),
    (
        valid_agent,
        True,
        False,
        True,
    ),
    (
        valid_agent,
        True,
        True,
        False,
    ),
    (
        {
            **valid_agent,
            "parse_status": "REVIEW",
        },
        True,
        True,
        True,
    ),
]

for args in tests:
    try:
        build_evidence_complete_record(
            args[0],
            descriptor_validation_pass=args[1],
            registry_validation_pass=args[2],
            dependency_validation_pass=args[3],
        )
    except EvidenceContractError:
        failure_tests += 1
    else:
        raise SystemExit(
            "FAIL_CLOSED_TEST_FAILED"
        )

print(f"FAIL_CLOSED_TEST_PASS_COUNT={failure_tests}")
print("EXPECTED_FAIL_CLOSED_TEST_COUNT=5")
print("NETWORK_ACTION_EXECUTED=NO")
print("AGENT_TASK_EXECUTED=NO")
print("SERVICE_START_EXECUTED=NO")
print("FILE_WRITE_BY_PRODUCER_EXECUTED=NO")
PY

VALID_CONTRACT_COUNT="$(
  grep -c '^VALID_CONTRACT_TEST=PASS$' \
    "$OUT/CONTRACT_VALIDATION.txt" || true
)"

FAIL_CLOSED_COUNT="$(
  awk -F= '$1=="FAIL_CLOSED_TEST_PASS_COUNT"{print $2}' \
    "$OUT/CONTRACT_VALIDATION.txt"
)"

FAIL_CLOSED_COUNT="${FAIL_CLOSED_COUNT:-0}"

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

MINIMAL_EVIDENCE_PRODUCER_IMPLEMENTATION=COMPLETE

TARGET=$TARGET
TARGET_SHA256=$TARGET_HASH

STATIC_VALIDATION_FAIL_COUNT=$STATIC_FAIL_COUNT

VALID_CONTRACT_TEST_PASS_COUNT=$VALID_CONTRACT_COUNT
FAIL_CLOSED_TEST_PASS_COUNT=$FAIL_CLOSED_COUNT
EXPECTED_FAIL_CLOSED_TEST_COUNT=5

PRODUCER_FUNCTION=build_evidence_complete_record
PRODUCER_OUTPUT_STATUS=EVIDENCE_COMPLETE

TARGET_OVERWRITE_EXECUTED=NO
SOURCE_DELETE_EXECUTED=NO
SOURCE_MOVE_EXECUTED=NO
SOURCE_RENAME_EXECUTED=NO

AGENT_TASK_EXECUTION_EXECUTED=NO
NETWORK_EXECUTED=NO
SERVICE_START_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$VALID_CONTRACT_COUNT" -ne 1 ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=VALID_PRODUCER_CONTRACT_TEST_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R10R1_PRODUCER_IMPLEMENTATION_ANALYSIS"

elif [[ "$FAIL_CLOSED_COUNT" -ne 5 ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=PRODUCER_FAIL_CLOSED_VALIDATION_FAILED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R10R1_PRODUCER_IMPLEMENTATION_ANALYSIS"

else
    echo "RESULT=PASS"
    echo "EVIDENCE_COMPLETE_PRODUCER_STATUS=IMPLEMENTED_AND_VALIDATED"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R3_CONTROLLED_METADATA_PILOT_CANARY_PLAN"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
