#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 097"
echo " CONTROLLED AGENT CANARY PLAN — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_097_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=097"
echo "MODE=READ_ONLY_CONTROLLED_AGENT_CANARY_PLAN"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/CANARY_CANDIDATES.txt"
: > "$OUT/SELECTED_CANARY.txt"
: > "$OUT/CANARY_POLICY.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== CANARY CANDIDATE ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$AGENT_ROOT" \
  "$OUT/CANARY_CANDIDATES.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])

rows = []

for path in sorted(root.glob("*.py")):
    try:
        tree = ast.parse(
            path.read_text(errors="replace"),
            filename=str(path)
        )
    except Exception:
        continue

    functions = []
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    risky = bool(
        imports & {
            "socket",
            "requests",
            "urllib",
            "http",
            "subprocess",
            "smtplib",
            "ftplib",
        }
    )

    for fn in sorted(set(functions)):
        rows.append(
            f"FILE={path}\tFUNCTION={fn}\t"
            f"NETWORK_SUBPROCESS_SIGNAL={'YES' if risky else 'NO'}"
        )

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/CANARY_CANDIDATES.txt"

# Prefer the already identified metadata pilot if available.
PILOT="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

if [[ -f "$PILOT" ]] &&
   grep -q 'FUNCTION=run_metadata_pilot' "$OUT/CANARY_CANDIDATES.txt"; then

    SELECTED_FILE="$PILOT"
    SELECTED_FUNCTION="run_metadata_pilot"
    SELECTION_STATUS="PROVEN_CANDIDATE"

else

    SELECTED_FILE="NONE"
    SELECTED_FUNCTION="NONE"
    SELECTION_STATUS="NO_SAFE_CANDIDATE_PROVEN"
fi

{
echo "SELECTED_FILE=$SELECTED_FILE"
echo "SELECTED_FUNCTION=$SELECTED_FUNCTION"
echo "SELECTION_STATUS=$SELECTION_STATUS"
} | tee "$OUT/SELECTED_CANARY.txt"

cat > "$OUT/CANARY_POLICY.txt" <<POLICY
CANARY_EXECUTION_SCOPE=ONE_FUNCTION_ONLY

NETWORK_ALLOWED=NO
EXTERNAL_SEND_ALLOWED=NO
SERVICE_START_ALLOWED=NO
PACKAGE_INSTALL_ALLOWED=NO

DELETE_ALLOWED=NO
MOVE_ALLOWED=NO
RENAME_ALLOWED=NO
FORMAT_ALLOWED=NO

PERSISTENT_PYTHONPATH_CHANGE_ALLOWED=NO

ORIGINAL_FILE_MUTATION_ALLOWED=NO

PYTHONDONTWRITEBYTECODE=1
PYTHONNOUSERSITE=1

HUMAN_GATE_REQUIRED_BEFORE_EXECUTION=YES
POLICY

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

CONTROLLED_AGENT_CANARY_PLAN=COMPLETE

SELECTED_FILE=$SELECTED_FILE
SELECTED_FUNCTION=$SELECTED_FUNCTION
SELECTION_STATUS=$SELECTION_STATUS

AGENT_EXECUTION_EXECUTED=NO
NETWORK_EXECUTED=NO
SERVICE_START_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

FILE_MUTATION_EXECUTED=NO
DELETE_EXECUTED=NO

HUMAN_GATE_REQUIRED=YES
MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo
echo "--- CANARY POLICY ---"
cat "$OUT/CANARY_POLICY.txt"

echo "============================================================"

if [[ "$SELECTION_STATUS" == "PROVEN_CANDIDATE" ]]; then
    echo "RESULT=HOLD"
    echo "BLOCKER=HUMAN_GATE_APPROVAL_REQUIRED_FOR_CONTROLLED_AGENT_CANARY"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098_CONTROLLED_AGENT_CANARY_HUMAN_GATE"
else
    echo "RESULT=HOLD"
    echo "BLOCKER=SAFE_AGENT_CANARY_CANDIDATE_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_097R1_CANARY_CANDIDATE_DEEP_ANALYSIS"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
