#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R5"
echo " EVIDENCE CONTRACT RESOLUTION — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R5_$START_UTC"

EXPECTED_HASH="a8829c1348311af73c49f7dd566fc4ce1c5e48e6124ea73eaea5c76786be33a1"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R5"
echo "MODE=READ_ONLY_EVIDENCE_CONTRACT_RESOLUTION"
echo "START_UTC=$START_UTC"
echo "EXPECTED_HASH=$EXPECTED_HASH"
} > "$OUT/BATCH.env"

: > "$OUT/SOURCE_CANDIDATES.txt"
: > "$OUT/HASH_PROOF.txt"
: > "$OUT/STATIC_ANALYSIS.txt"
: > "$OUT/CONTRACT_SIGNALS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== SOURCE CANDIDATES ====="

find "$ROOT/90_QUARANTINE" \
  -type f \
  -name 'approval_evidence_pack.py' \
  2>/dev/null \
| sort \
| tee "$OUT/SOURCE_CANDIDATES.txt"

SOURCE_COUNT="$(
  wc -l < "$OUT/SOURCE_CANDIDATES.txt" |
  tr -d ' '
)"

VALID_SOURCE_COUNT=0

while IFS= read -r f; do
    [[ -f "$f" ]] || continue

    H="$(sha256sum "$f" | awk '{print $1}')"

    {
      echo "FILE=$f"
      echo "SHA256=$H"
      echo
    } >> "$OUT/HASH_PROOF.txt"

    if [[ "$H" == "$EXPECTED_HASH" ]]; then
        VALID_SOURCE_COUNT=$((VALID_SOURCE_COUNT + 1))
    fi

done < "$OUT/SOURCE_CANDIDATES.txt"

cat "$OUT/HASH_PROOF.txt"

echo
echo "===== STATIC AST ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$OUT/SOURCE_CANDIDATES.txt" \
  "$OUT/STATIC_ANALYSIS.txt" \
  "$OUT/CONTRACT_SIGNALS.txt" <<'PY'
import ast
import sys
from pathlib import Path

source_list = Path(sys.argv[1])
analysis_out = Path(sys.argv[2])
contract_out = Path(sys.argv[3])

analysis = []
contracts = []

for line in source_list.read_text(errors="replace").splitlines():
    path = Path(line)

    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception as exc:
        analysis.extend([
            f"FILE={path}",
            f"PARSE_STATUS=FAIL:{type(exc).__name__}:{exc}",
            ""
        ])
        continue

    classes = sorted({
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
    })

    functions = sorted({
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    })

    imports = []

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports.extend(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module or "")

    analysis.extend([
        f"FILE={path}",
        "PARSE_STATUS=PASS",
        "CLASSES=" + ",".join(classes),
        "FUNCTIONS=" + ",".join(functions),
        "IMPORTS=" + ",".join(sorted(set(imports))),
        ""
    ])

    for node in ast.walk(tree):

        # Dict literal with readiness_status.
        if isinstance(node, ast.Dict):
            pairs = {}

            for k, v in zip(node.keys, node.values):
                if (
                    isinstance(k, ast.Constant)
                    and isinstance(k.value, str)
                ):
                    key = k.value

                    try:
                        value = ast.literal_eval(v)
                    except Exception:
                        try:
                            value = ast.unparse(v)
                        except Exception:
                            value = "UNKNOWN"

                    pairs[key] = value

            if "readiness_status" in pairs:
                contracts.extend([
                    f"FILE={path}",
                    f"LINENO={getattr(node,'lineno','UNKNOWN')}",
                    "SIGNAL=READINESS_STATUS_DICT",
                    f"READINESS_VALUE={pairs.get('readiness_status')}",
                    f"AGENT_ID_PRESENT={'YES' if 'agent_id' in pairs else 'NO'}",
                    ""
                ])

        # Assignment x["readiness_status"] = ...
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Subscript):
                    continue

                try:
                    key = ast.literal_eval(target.slice)
                except Exception:
                    key = None

                if key != "readiness_status":
                    continue

                try:
                    value = ast.literal_eval(node.value)
                except Exception:
                    try:
                        value = ast.unparse(node.value)
                    except Exception:
                        value = "UNKNOWN"

                contracts.extend([
                    f"FILE={path}",
                    f"LINENO={getattr(node,'lineno','UNKNOWN')}",
                    "SIGNAL=READINESS_STATUS_ASSIGN",
                    f"READINESS_VALUE={value}",
                    ""
                ])

analysis_out.write_text(
    "\n".join(analysis) + ("\n" if analysis else "")
)

contract_out.write_text(
    "\n".join(contracts) + ("\n" if contracts else "")
)
PY

cat "$OUT/STATIC_ANALYSIS.txt"

echo
echo "===== CONTRACT SIGNALS ====="
cat "$OUT/CONTRACT_SIGNALS.txt"

PARSE_PASS_COUNT="$(
  grep -c '^PARSE_STATUS=PASS$' \
    "$OUT/STATIC_ANALYSIS.txt" || true
)"

EVIDENCE_COMPLETE_SIGNAL_COUNT="$(
  grep -c '^READINESS_VALUE=EVIDENCE_COMPLETE$' \
    "$OUT/CONTRACT_SIGNALS.txt" || true
)"

AGENT_ID_COLOCATED_COUNT="$(
  grep -c '^AGENT_ID_PRESENT=YES$' \
    "$OUT/CONTRACT_SIGNALS.txt" || true
)"

if (( SOURCE_COUNT > 0 &&
      VALID_SOURCE_COUNT == SOURCE_COUNT &&
      PARSE_PASS_COUNT == SOURCE_COUNT )); then

    SOURCE_PROOF_STATUS="PROVEN"
else
    SOURCE_PROOF_STATUS="NOT_PROVEN"
fi

if (( EVIDENCE_COMPLETE_SIGNAL_COUNT > 0 )); then
    EVIDENCE_COMPLETE_CONTRACT_STATUS="PROVEN"
else
    EVIDENCE_COMPLETE_CONTRACT_STATUS="NOT_PROVEN"
fi

if (( AGENT_ID_COLOCATED_COUNT > 0 )); then
    AGENT_JOIN_CONTRACT_STATUS="PROVEN"
else
    AGENT_JOIN_CONTRACT_STATUS="NOT_PROVEN"
fi

if [[ "$SOURCE_PROOF_STATUS" == "PROVEN" &&
      "$EVIDENCE_COMPLETE_CONTRACT_STATUS" == "PROVEN" &&
      "$AGENT_JOIN_CONTRACT_STATUS" == "PROVEN" ]]; then

    EVIDENCE_PRODUCER_STATUS="PROVEN"

elif [[ "$SOURCE_PROOF_STATUS" == "PROVEN" &&
        "$EVIDENCE_COMPLETE_CONTRACT_STATUS" == "PROVEN" ]]; then

    EVIDENCE_PRODUCER_STATUS="PARTIAL"

else
    EVIDENCE_PRODUCER_STATUS="NOT_PROVEN"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

EVIDENCE_CONTRACT_RESOLUTION=COMPLETE

SOURCE_COUNT=$SOURCE_COUNT
VALID_SOURCE_COUNT=$VALID_SOURCE_COUNT
PARSE_PASS_COUNT=$PARSE_PASS_COUNT

SOURCE_PROOF_STATUS=$SOURCE_PROOF_STATUS

EVIDENCE_COMPLETE_SIGNAL_COUNT=$EVIDENCE_COMPLETE_SIGNAL_COUNT
AGENT_ID_COLOCATED_COUNT=$AGENT_ID_COLOCATED_COUNT

EVIDENCE_COMPLETE_CONTRACT_STATUS=$EVIDENCE_COMPLETE_CONTRACT_STATUS
AGENT_JOIN_CONTRACT_STATUS=$AGENT_JOIN_CONTRACT_STATUS

EVIDENCE_PRODUCER_STATUS=$EVIDENCE_PRODUCER_STATUS

QUARANTINE_IMPORT_ALLOWED=NO
QUARANTINE_EXECUTION_ALLOWED=NO

TARGET_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_DELETE_EXECUTED=NO

NETWORK_EXECUTED=NO
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

case "$EVIDENCE_PRODUCER_STATUS" in

  PROVEN)
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R6_EVIDENCE_PRODUCER_PROVENANCE_AND_BINDING_PLAN"
    ;;

  PARTIAL)
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=EVIDENCE_COMPLETE_CONTRACT_PROVEN_BUT_AGENT_JOIN_INCOMPLETE"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R6_EVIDENCE_PRODUCER_DEEP_CONTRACT_ANALYSIS"
    ;;

  *)
    echo "RESULT=HOLD"
    echo "BLOCKER=APPROVAL_EVIDENCE_PACK_NOT_PROVEN_AS_METADATA_PILOT_PRODUCER"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R6_EVIDENCE_CONTRACT_SOURCE_SEARCH"
    ;;
esac

echo "REPORT_DIR=$OUT"
echo "============================================================"
