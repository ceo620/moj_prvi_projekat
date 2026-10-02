#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R3"
echo " CONTROLLED METADATA PILOT CANARY PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R3_$START_UTC"

DISCOVERY="$AGENT_ROOT/05c0204f9c0a_agent_discovery.py"
DESCRIPTOR="$AGENT_ROOT/agent_descriptor.py"
REGISTRY="$AGENT_ROOT/agent_registry.py"
VALIDATOR="$AGENT_ROOT/4fae0850626f_agent_validation_engine.py"
PRODUCER="$AGENT_ROOT/evidence_complete_producer.py"
PILOT="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R3"
echo "MODE=READ_ONLY_CONTROLLED_METADATA_PILOT_CANARY_PLAN"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/COMPONENT_STATUS.txt"
: > "$OUT/CANARY_TARGET_ANALYSIS.txt"
: > "$OUT/CANARY_INPUT_PLAN.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== COMPONENT STATUS ====="

COMPONENT_FAIL_COUNT=0

for f in \
  "$DISCOVERY" \
  "$DESCRIPTOR" \
  "$REGISTRY" \
  "$VALIDATOR" \
  "$PRODUCER" \
  "$PILOT"
do
    if [[ -f "$f" ]]; then
        H="$(sha256sum "$f" | awk '{print $1}')"
        echo "FILE=$f" | tee -a "$OUT/COMPONENT_STATUS.txt"
        echo "STATUS=PRESENT" | tee -a "$OUT/COMPONENT_STATUS.txt"
        echo "SHA256=$H" | tee -a "$OUT/COMPONENT_STATUS.txt"
        echo | tee -a "$OUT/COMPONENT_STATUS.txt"
    else
        echo "FILE=$f" | tee -a "$OUT/COMPONENT_STATUS.txt"
        echo "STATUS=MISSING" | tee -a "$OUT/COMPONENT_STATUS.txt"
        echo | tee -a "$OUT/COMPONENT_STATUS.txt"
        COMPONENT_FAIL_COUNT=$((COMPONENT_FAIL_COUNT + 1))
    fi
done

echo
echo "===== CANARY TARGET ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$AGENT_ROOT" \
  "$OUT/CANARY_TARGET_ANALYSIS.txt" <<'PY'
import ast
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])

excluded_names = {
    "agent_contract.py",
    "agent_descriptor.py",
    "agent_registry.py",
    "task_registry.py",
    "evidence_complete_producer.py",
    "ea4106a2d52a_metadata_agent_pilot.py",
}

rows = []

for path in sorted(root.glob("*.py")):
    if path.name in excluded_names:
        continue

    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception:
        continue

    classes = sorted(
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    )

    functions = sorted(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )

    imports = sorted({
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    })

    rel = path.name
    agent_id = "AGENT-" + hashlib.sha256(
        rel.encode("utf-8")
    ).hexdigest()[:24]

    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    rows.extend([
        f"FILE={path}",
        f"AGENT_ID={agent_id}",
        f"RELATIVE_PATH={rel}",
        f"SHA256={sha256}",
        f"CLASSES={','.join(classes)}",
        f"FUNCTIONS={','.join(functions)}",
        f"IMPORTS={','.join(imports)}",
        "PARSE_STATUS=PASS",
        "",
    ])

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/CANARY_TARGET_ANALYSIS.txt"

CANDIDATE_COUNT="$(
  grep -c '^AGENT_ID=' "$OUT/CANARY_TARGET_ANALYSIS.txt" || true
)"

SELECTED_AGENT_ID="$(
  awk -F= '$1=="AGENT_ID"{print $2; exit}' \
    "$OUT/CANARY_TARGET_ANALYSIS.txt"
)"

SELECTED_RELATIVE_PATH="$(
  awk -F= '$1=="RELATIVE_PATH"{print $2; exit}' \
    "$OUT/CANARY_TARGET_ANALYSIS.txt"
)"

SELECTED_SHA256="$(
  awk -F= '$1=="SHA256"{print $2; exit}' \
    "$OUT/CANARY_TARGET_ANALYSIS.txt"
)"

if [[ -n "$SELECTED_AGENT_ID" ]]; then
    SELECTION_STATUS="PROVEN"
else
    SELECTION_STATUS="NOT_PROVEN"
fi

cat > "$OUT/CANARY_INPUT_PLAN.txt" <<PLAN
CANARY_INPUT_SOURCE=STATIC_VERIFIED_LOCAL_AGENT

SELECTED_AGENT_ID=${SELECTED_AGENT_ID:-NONE}
SELECTED_RELATIVE_PATH=${SELECTED_RELATIVE_PATH:-NONE}
SELECTED_SHA256=${SELECTED_SHA256:-NONE}

DESCRIPTOR_VALIDATION_REQUIRED=YES
REGISTRY_VALIDATION_REQUIRED=YES
DEPENDENCY_VALIDATION_REQUIRED=OPTIONAL

EVIDENCE_PRODUCER=build_evidence_complete_record
PILOT_FUNCTION=run_metadata_pilot

CANARY_EXECUTION_SCOPE=ONE_AGENT_ONE_FUNCTION

NETWORK_ALLOWED=NO
FILE_WRITE_ALLOWED=NO
SERVICE_START_ALLOWED=NO
PACKAGE_INSTALL_ALLOWED=NO
EXTERNAL_SEND_ALLOWED=NO

DELETE_ALLOWED=NO
MOVE_ALLOWED=NO
RENAME_ALLOWED=NO
FORMAT_ALLOWED=NO

HUMAN_GATE_REQUIRED_BEFORE_EXECUTION=YES
PLAN

if (( COMPONENT_FAIL_COUNT == 0 )) &&
   (( CANDIDATE_COUNT > 0 )) &&
   [[ "$SELECTION_STATUS" == "PROVEN" ]]; then
    PLAN_STATUS="READY_FOR_HUMAN_GATE"
else
    PLAN_STATUS="HOLD"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CONTROLLED_METADATA_PILOT_CANARY_PLAN=COMPLETE

COMPONENT_FAIL_COUNT=$COMPONENT_FAIL_COUNT
CANARY_CANDIDATE_COUNT=$CANDIDATE_COUNT

SELECTION_STATUS=$SELECTION_STATUS
SELECTED_AGENT_ID=${SELECTED_AGENT_ID:-NONE}
SELECTED_RELATIVE_PATH=${SELECTED_RELATIVE_PATH:-NONE}
SELECTED_SHA256=${SELECTED_SHA256:-NONE}

PLAN_STATUS=$PLAN_STATUS

TARGET_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
EVIDENCE_RECORD_CREATED=NO

FILE_MUTATION_EXECUTED=NO
NETWORK_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

HUMAN_GATE_REQUIRED=YES
MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- CANARY INPUT PLAN ---"
cat "$OUT/CANARY_INPUT_PLAN.txt"

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$PLAN_STATUS" == "READY_FOR_HUMAN_GATE" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=HUMAN_GATE_APPROVAL_REQUIRED_FOR_REAL_METADATA_PILOT_CANARY"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R4_CONTROLLED_METADATA_PILOT_CANARY_HUMAN_GATE"
else
    echo "RESULT=HOLD"
    echo "BLOCKER=CONTROLLED_METADATA_PILOT_CANARY_PLAN_NOT_READY"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R3R1_CANARY_SELECTION_ANALYSIS"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
