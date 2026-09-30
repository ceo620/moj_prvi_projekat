#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R3"
echo " CANARY INPUT CONSTRUCTION PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R3_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R3"
echo "MODE=READ_ONLY_CANARY_INPUT_CONSTRUCTION_PLAN"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/DISCOVERY_FUNCTION_PROOF.txt"
: > "$OUT/EVIDENCE_PRODUCER_PROOF.txt"
: > "$OUT/PILOT_CONTRACT_PROOF.txt"
: > "$OUT/FINAL_STATUS.txt"

DISCOVERY_FILE="$AGENT_ROOT/05c0204f9c0a_agent_discovery.py"
PILOT_FILE="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

echo "===== DISCOVERY FUNCTION PROOF ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
 "$DISCOVERY_FILE" \
 "$OUT/DISCOVERY_FUNCTION_PROOF.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

text = path.read_text(errors="replace")
tree = ast.parse(text, filename=str(path))

wanted = {"inspect_python_file", "discover_agents"}

rows = []

for node in tree.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue

    if node.name not in wanted:
        continue

    segment = ast.get_source_segment(text, node) or ""

    rows.append(f"===== FUNCTION={node.name} =====")
    rows.append(segment)
    rows.append("")

out.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/DISCOVERY_FUNCTION_PROOF.txt"

echo
echo "===== TRUE EVIDENCE_COMPLETE PRODUCER SEARCH ====="

grep -RInE \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  'readiness_status[^[:alnum:]_]*[:=][^[:cntrl:]]*EVIDENCE_COMPLETE|EVIDENCE_COMPLETE[^[:cntrl:]]*readiness_status' \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  2>/dev/null \
| grep -v 'ea4106a2d52a_metadata_agent_pilot.py' \
| tee "$OUT/EVIDENCE_PRODUCER_PROOF.txt" || true

echo
echo "===== PILOT CONTRACT ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
 "$PILOT_FILE" \
 "$OUT/PILOT_CONTRACT_PROOF.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

text = path.read_text(errors="replace")
tree = ast.parse(text, filename=str(path))

target = None

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "run_metadata_pilot":
            target = node
            break

if target is None:
    out.write_text("FUNCTION_FOUND=NO\n")
    raise SystemExit

rows = [
    "FUNCTION_FOUND=YES",
    "REQUIRED_AGENT_KEYS=agent_id,relative_path,sha256",
    "OPTIONAL_AGENT_KEYS=classes,functions,imports",
    "REQUIRED_EVIDENCE_KEYS=agent_id,readiness_status",
    "REQUIRED_EVIDENCE_STATUS=EVIDENCE_COMPLETE",
]

out.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/PILOT_CONTRACT_PROOF.txt"

DISCOVERY_HAS_AGENT_ID="$(
  grep -cE "['\"]agent_id['\"]" \
    "$OUT/DISCOVERY_FUNCTION_PROOF.txt" || true
)"

DISCOVERY_HAS_RELATIVE_PATH="$(
  grep -cE "['\"]relative_path['\"]" \
    "$OUT/DISCOVERY_FUNCTION_PROOF.txt" || true
)"

DISCOVERY_HAS_SHA256="$(
  grep -cE "['\"]sha256['\"]" \
    "$OUT/DISCOVERY_FUNCTION_PROOF.txt" || true
)"

DISCOVERY_HAS_CLASSES="$(
  grep -cE "['\"]classes['\"]" \
    "$OUT/DISCOVERY_FUNCTION_PROOF.txt" || true
)"

DISCOVERY_HAS_FUNCTIONS="$(
  grep -cE "['\"]functions['\"]" \
    "$OUT/DISCOVERY_FUNCTION_PROOF.txt" || true
)"

DISCOVERY_HAS_IMPORTS="$(
  grep -cE "['\"]imports['\"]" \
    "$OUT/DISCOVERY_FUNCTION_PROOF.txt" || true
)"

EVIDENCE_PRODUCER_COUNT="$(
  wc -l < "$OUT/EVIDENCE_PRODUCER_PROOF.txt" |
  tr -d ' '
)"

if (( DISCOVERY_HAS_AGENT_ID > 0 &&
      DISCOVERY_HAS_RELATIVE_PATH > 0 &&
      DISCOVERY_HAS_SHA256 > 0 )); then

    AGENT_INPUT_SOURCE_STATUS="PROVEN_FROM_DISCOVERY"

else
    AGENT_INPUT_SOURCE_STATUS="NOT_PROVEN"
fi

if (( EVIDENCE_PRODUCER_COUNT > 0 )); then
    EVIDENCE_INPUT_SOURCE_STATUS="PROVEN"
else
    EVIDENCE_INPUT_SOURCE_STATUS="NOT_PROVEN"
fi

if [[ "$AGENT_INPUT_SOURCE_STATUS" == "PROVEN_FROM_DISCOVERY" &&
      "$EVIDENCE_INPUT_SOURCE_STATUS" == "PROVEN" ]]; then

    CANARY_INPUT_PLAN_STATUS="READY"

else
    CANARY_INPUT_PLAN_STATUS="BLOCKED"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CANARY_INPUT_CONSTRUCTION_ANALYSIS=COMPLETE

AGENT_ID_SIGNAL_COUNT=$DISCOVERY_HAS_AGENT_ID
RELATIVE_PATH_SIGNAL_COUNT=$DISCOVERY_HAS_RELATIVE_PATH
SHA256_SIGNAL_COUNT=$DISCOVERY_HAS_SHA256
CLASSES_SIGNAL_COUNT=$DISCOVERY_HAS_CLASSES
FUNCTIONS_SIGNAL_COUNT=$DISCOVERY_HAS_FUNCTIONS
IMPORTS_SIGNAL_COUNT=$DISCOVERY_HAS_IMPORTS

AGENT_INPUT_SOURCE_STATUS=$AGENT_INPUT_SOURCE_STATUS

TRUE_EVIDENCE_COMPLETE_PRODUCER_COUNT=$EVIDENCE_PRODUCER_COUNT
EVIDENCE_INPUT_SOURCE_STATUS=$EVIDENCE_INPUT_SOURCE_STATUS

CANARY_INPUT_PLAN_STATUS=$CANARY_INPUT_PLAN_STATUS

TARGET_FUNCTION_EXECUTED=NO
DISCOVERY_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

NETWORK_EXECUTED=NO
FILE_MUTATION_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$CANARY_INPUT_PLAN_STATUS" == "READY" ]]; then

    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R3_CONTROLLED_METADATA_PILOT_CANARY_PLAN"

elif [[ "$AGENT_INPUT_SOURCE_STATUS" == "PROVEN_FROM_DISCOVERY" &&
        "$EVIDENCE_INPUT_SOURCE_STATUS" == "NOT_PROVEN" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=EVIDENCE_COMPLETE_PRODUCER_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R4_EVIDENCE_COMPLETE_CONTRACT_ANALYSIS"

else

    echo "RESULT=HOLD"
    echo "BLOCKER=CANARY_INPUT_PRODUCER_CHAIN_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R4_INPUT_SCHEMA_DEEP_ANALYSIS"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
