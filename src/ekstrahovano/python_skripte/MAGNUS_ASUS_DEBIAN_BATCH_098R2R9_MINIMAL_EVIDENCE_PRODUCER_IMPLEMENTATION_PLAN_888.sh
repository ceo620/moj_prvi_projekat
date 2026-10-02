#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R9"
echo " MINIMAL EVIDENCE PRODUCER IMPLEMENTATION PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R9_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R9"
echo "MODE=READ_ONLY_MINIMAL_EVIDENCE_PRODUCER_IMPLEMENTATION_PLAN"
echo "START_UTC=$START_UTC"
echo "HUMAN_GATE_APPROVAL=HUMAN_GATE_APPROVE_OPTION_A_BATCH_098R2R9_MINIMAL_EVIDENCE_PRODUCER_PLAN"
} > "$OUT/BATCH.env"

: > "$OUT/PRODUCER_CONTRACT.txt"
: > "$OUT/VALIDATION_BINDINGS.txt"
: > "$OUT/PROPOSED_IMPLEMENTATION.txt"
: > "$OUT/TARGET_PREFLIGHT.txt"
: > "$OUT/FINAL_STATUS.txt"

DESCRIPTOR="$AGENT_ROOT/agent_descriptor.py"
REGISTRY="$AGENT_ROOT/agent_registry.py"
VALIDATOR="$AGENT_ROOT/4fae0850626f_agent_validation_engine.py"
PILOT="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

TARGET="$AGENT_ROOT/evidence_complete_producer.py"

echo "===== TARGET PREFLIGHT ====="

if [[ -e "$TARGET" ]]; then
    TARGET_EXISTS="YES"
    if [[ -f "$TARGET" ]]; then
        TARGET_HASH="$(sha256sum "$TARGET" | awk '{print $1}')"
    else
        TARGET_HASH="NON_FILE_OBJECT"
    fi
else
    TARGET_EXISTS="NO"
    TARGET_HASH="NONE"
fi

{
echo "TARGET=$TARGET"
echo "TARGET_EXISTS=$TARGET_EXISTS"
echo "TARGET_HASH=$TARGET_HASH"
} | tee "$OUT/TARGET_PREFLIGHT.txt"

echo
echo "===== VALIDATION BINDING PROOF ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$VALIDATOR" \
  "$OUT/VALIDATION_BINDINGS.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

text = path.read_text(errors="replace")
tree = ast.parse(text, filename=str(path))

wanted = {
    "validate_descriptors",
    "validate_registry",
    "validate_dependency_map",
}

rows = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted:
        rows.append(f"FUNCTION={node.name}")
        rows.append("SOURCE_BEGIN")
        rows.append(ast.get_source_segment(text, node) or "")
        rows.append("SOURCE_END")
        rows.append("")

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/VALIDATION_BINDINGS.txt"

cat > "$OUT/PRODUCER_CONTRACT.txt" <<'CONTRACT'
COMPONENT=evidence_complete_producer

PURPOSE=CREATE_MINIMAL_LOCAL_EVIDENCE_MAPPING_FOR_METADATA_PILOT

INPUT=VERIFIED_AGENT_MAPPING_OR_AGENT_DESCRIPTOR

REQUIRED_INPUT_FIELD=agent_id
REQUIRED_INPUT_FIELD=relative_path
REQUIRED_INPUT_FIELD=sha256

REQUIRED_PRECONDITION=parse_status:PASS
REQUIRED_PRECONDITION=descriptor_validation:PASS
REQUIRED_PRECONDITION=registry_validation:PASS

OPTIONAL_PRECONDITION=dependency_validation:PASS

OUTPUT_FIELD=agent_id
OUTPUT_FIELD=readiness_status

OUTPUT_VALUE=readiness_status:EVIDENCE_COMPLETE

OUTPUT_MUST_NOT_INCLUDE=execution_permission
OUTPUT_MUST_NOT_START_AGENT=YES
OUTPUT_MUST_NOT_WRITE_NETWORK=YES
OUTPUT_MUST_NOT_START_SERVICE=YES

NETWORK_REQUIRED=NO
PACKAGE_INSTALL_REQUIRED=NO
SERVICE_REQUIRED=NO

ORIGINAL_AGENT_MUTATION_REQUIRED=NO
SOURCE_DELETE_REQUIRED=NO
SOURCE_MOVE_REQUIRED=NO

FAIL_CLOSED=YES
CONTRACT

cat > "$OUT/PROPOSED_IMPLEMENTATION.txt" <<'PLAN'
PROPOSED_FILENAME=evidence_complete_producer.py

PROPOSED_FUNCTION=build_evidence_complete_record

PROPOSED_SIGNATURE=
build_evidence_complete_record(
    agent,
    descriptor_validation_pass,
    registry_validation_pass,
    dependency_validation_pass=None
)

PROPOSED_LOGIC=

1. REQUIRE agent_id
2. REQUIRE relative_path
3. REQUIRE sha256

4. REQUIRE descriptor_validation_pass == True
5. REQUIRE registry_validation_pass == True

6. IF dependency_validation_pass is provided:
      REQUIRE dependency_validation_pass == True

7. IF agent has parse_status:
      REQUIRE parse_status == "PASS"

8. RETURN ONLY:
   {
     "agent_id": str(agent["agent_id"]),
     "readiness_status": "EVIDENCE_COMPLETE"
   }

9. NO FILE WRITE
10. NO NETWORK
11. NO AGENT EXECUTION
12. NO SERVICE START
13. NO PACKAGE INSTALL
14. NO SOURCE MUTATION
15. FAIL CLOSED ON ANY MISSING OR FAILED PRECONDITION

IMPLEMENTATION_EXECUTED=NO
PLAN

VALIDATOR_FUNCTION_COUNT="$(
  grep -c '^FUNCTION=' "$OUT/VALIDATION_BINDINGS.txt" || true
)"

if [[ "$TARGET_EXISTS" == "NO" ]]; then
    TARGET_STATUS="AVAILABLE"
else
    TARGET_STATUS="CONFLICT_OR_ALREADY_PRESENT"
fi

if (( VALIDATOR_FUNCTION_COUNT >= 2 )) &&
   [[ "$TARGET_STATUS" == "AVAILABLE" ]]; then
    PLAN_STATUS="READY_FOR_HUMAN_GATE"
else
    PLAN_STATUS="HOLD"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

MINIMAL_EVIDENCE_PRODUCER_IMPLEMENTATION_PLAN=COMPLETE

VALIDATOR_FUNCTION_COUNT=$VALIDATOR_FUNCTION_COUNT

TARGET_PATH=$TARGET
TARGET_STATUS=$TARGET_STATUS

PLAN_STATUS=$PLAN_STATUS

PROPOSED_COMPONENT=evidence_complete_producer
PROPOSED_FUNCTION=build_evidence_complete_record

IMPLEMENTATION_EXECUTED=NO
FILE_CREATION_EXECUTED=NO
FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_DELETE_EXECUTED=NO
FILE_OVERWRITE_EXECUTED=NO

AGENT_EXECUTION_EXECUTED=NO
NETWORK_EXECUTED=NO
SERVICE_START_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

HUMAN_GATE_REQUIRED=YES
MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- PRODUCER CONTRACT ---"
cat "$OUT/PRODUCER_CONTRACT.txt"

echo
echo "--- PROPOSED IMPLEMENTATION ---"
cat "$OUT/PROPOSED_IMPLEMENTATION.txt"

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$PLAN_STATUS" == "READY_FOR_HUMAN_GATE" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=HUMAN_GATE_APPROVAL_REQUIRED_FOR_MINIMAL_EVIDENCE_PRODUCER_IMPLEMENTATION"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R10_MINIMAL_EVIDENCE_PRODUCER_IMPLEMENTATION_HUMAN_GATE"
else
    echo "RESULT=HOLD"
    echo "BLOCKER=MINIMAL_EVIDENCE_PRODUCER_PLAN_NOT_READY"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R9R1_PLAN_CONFLICT_ANALYSIS"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
