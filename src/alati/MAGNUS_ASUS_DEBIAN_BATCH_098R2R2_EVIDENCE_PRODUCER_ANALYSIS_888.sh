#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R2"
echo " EVIDENCE PRODUCER ANALYSIS — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R2_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R2"
echo "MODE=READ_ONLY_EVIDENCE_PRODUCER_ANALYSIS"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/FUNCTION_MATRIX.txt"
: > "$OUT/RETURN_MATRIX.txt"
: > "$OUT/EVIDENCE_COMPLETE_PRODUCERS.txt"
: > "$OUT/AGENT_SCHEMA_PRODUCERS.txt"
: > "$OUT/DATAFLOW_SIGNALS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== STATIC PRODUCER ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
 "$AGENT_ROOT" \
 "$OUT/FUNCTION_MATRIX.txt" \
 "$OUT/RETURN_MATRIX.txt" \
 "$OUT/EVIDENCE_COMPLETE_PRODUCERS.txt" \
 "$OUT/AGENT_SCHEMA_PRODUCERS.txt" \
 "$OUT/DATAFLOW_SIGNALS.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])

function_out = Path(sys.argv[2])
return_out = Path(sys.argv[3])
evidence_out = Path(sys.argv[4])
agent_out = Path(sys.argv[5])
flow_out = Path(sys.argv[6])

function_rows = []
return_rows = []
evidence_rows = []
agent_rows = []
flow_rows = []

wanted_agent_keys = {
    "agent_id",
    "relative_path",
    "sha256",
}

for path in sorted(root.glob("*.py")):

    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception:
        continue

    for node in tree.body:

        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue

        args = [
            a.arg
            for a in (
                list(node.args.posonlyargs)
                + list(node.args.args)
            )
        ]

        function_rows.append(
            f"FILE={path}\t"
            f"FUNCTION={node.name}\t"
            f"ARGS={','.join(args)}"
        )

        source = ast.get_source_segment(text, node) or ""

        # Evidence-complete producer signals.
        if "EVIDENCE_COMPLETE" in source:
            evidence_rows.extend([
                f"FILE={path}",
                f"FUNCTION={node.name}",
                "EVIDENCE_COMPLETE_SIGNAL=YES",
                "",
            ])

        # Agent schema producer signals.
        present_keys = {
            key
            for key in wanted_agent_keys
            if repr(key) in source
            or f'"{key}"' in source
            or f"'{key}'" in source
        }

        if present_keys == wanted_agent_keys:
            agent_rows.extend([
                f"FILE={path}",
                f"FUNCTION={node.name}",
                "AGENT_SCHEMA_SIGNAL=YES",
                "KEYS=agent_id,relative_path,sha256",
                "",
            ])

        # Return expression analysis.
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                try:
                    expr = ast.unparse(child.value)
                except Exception:
                    expr = "UNKNOWN"

                return_rows.append(
                    f"FILE={path}\t"
                    f"FUNCTION={node.name}\t"
                    f"RETURN={expr}"
                )

        # Calls to relevant functions.
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue

            try:
                called = ast.unparse(child.func)
            except Exception:
                continue

            if any(
                signal in called
                for signal in (
                    "discover_agents",
                    "inspect_python_file",
                    "validate_descriptors",
                    "validate_registry",
                    "validate_dependency_map",
                    "build_metadata_registry",
                    "run_metadata_pilot",
                )
            ):
                try:
                    args_text = ",".join(
                        ast.unparse(a)
                        for a in child.args
                    )
                except Exception:
                    args_text = "UNKNOWN"

                flow_rows.append(
                    f"FILE={path}\t"
                    f"FUNCTION={node.name}\t"
                    f"CALL={called}\t"
                    f"ARGS={args_text}"
                )

function_out.write_text(
    "\n".join(function_rows)
    + ("\n" if function_rows else "")
)

return_out.write_text(
    "\n".join(return_rows)
    + ("\n" if return_rows else "")
)

evidence_out.write_text(
    "\n".join(evidence_rows)
    + ("\n" if evidence_rows else "")
)

agent_out.write_text(
    "\n".join(agent_rows)
    + ("\n" if agent_rows else "")
)

flow_out.write_text(
    "\n".join(flow_rows)
    + ("\n" if flow_rows else "")
)
PY

echo
echo "===== EVIDENCE_COMPLETE PRODUCERS ====="
cat "$OUT/EVIDENCE_COMPLETE_PRODUCERS.txt"

echo
echo "===== AGENT SCHEMA PRODUCERS ====="
cat "$OUT/AGENT_SCHEMA_PRODUCERS.txt"

echo
echo "===== DATAFLOW SIGNALS ====="
cat "$OUT/DATAFLOW_SIGNALS.txt"

echo
echo "===== RETURN MATRIX ====="
cat "$OUT/RETURN_MATRIX.txt"

EVIDENCE_PRODUCER_COUNT="$(
  grep -c '^EVIDENCE_COMPLETE_SIGNAL=YES$' \
    "$OUT/EVIDENCE_COMPLETE_PRODUCERS.txt" || true
)"

AGENT_PRODUCER_COUNT="$(
  grep -c '^AGENT_SCHEMA_SIGNAL=YES$' \
    "$OUT/AGENT_SCHEMA_PRODUCERS.txt" || true
)"

DATAFLOW_COUNT="$(
  wc -l < "$OUT/DATAFLOW_SIGNALS.txt" |
  tr -d ' '
)"

if (( EVIDENCE_PRODUCER_COUNT > 0 &&
      AGENT_PRODUCER_COUNT > 0 )); then

    PRODUCER_STATUS="PROVEN"

elif (( EVIDENCE_PRODUCER_COUNT > 0 ||
        AGENT_PRODUCER_COUNT > 0 )); then

    PRODUCER_STATUS="PARTIAL"

else

    PRODUCER_STATUS="NOT_PROVEN"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

EVIDENCE_PRODUCER_ANALYSIS=COMPLETE

EVIDENCE_COMPLETE_PRODUCER_COUNT=$EVIDENCE_PRODUCER_COUNT
AGENT_SCHEMA_PRODUCER_COUNT=$AGENT_PRODUCER_COUNT
DATAFLOW_SIGNAL_COUNT=$DATAFLOW_COUNT

PRODUCER_STATUS=$PRODUCER_STATUS

TARGET_FUNCTION_EXECUTED=NO
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

case "$PRODUCER_STATUS" in

  PROVEN)
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R3_CANARY_INPUT_CONSTRUCTION_PLAN"
    ;;

  PARTIAL)
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=METADATA_PILOT_PRODUCER_CHAIN_PARTIAL"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R3_CANARY_INPUT_CONSTRUCTION_PLAN"
    ;;

  *)
    echo "RESULT=HOLD"
    echo "BLOCKER=METADATA_PILOT_PRODUCER_CHAIN_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R3_FUNCTION_CONTRACT_DEEP_ANALYSIS"
    ;;
esac

echo "REPORT_DIR=$OUT"
echo "============================================================"
