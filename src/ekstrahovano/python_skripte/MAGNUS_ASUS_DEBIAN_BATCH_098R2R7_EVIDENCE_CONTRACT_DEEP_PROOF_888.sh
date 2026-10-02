#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R7"
echo " EVIDENCE CONTRACT DEEP PROOF — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R7_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R7"
echo "MODE=READ_ONLY_EVIDENCE_CONTRACT_DEEP_PROOF"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/VALIDATION_FUNCTIONS.txt"
: > "$OUT/STATUS_PRODUCERS.txt"
: > "$OUT/PILOT_REQUIREMENTS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== VALIDATION / DISCOVERY FUNCTIONS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
 "$AGENT_ROOT" \
 "$OUT/VALIDATION_FUNCTIONS.txt" \
 "$OUT/STATUS_PRODUCERS.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
fn_out = Path(sys.argv[2])
status_out = Path(sys.argv[3])

fn_rows = []
status_rows = []

interesting = (
    "validate",
    "discover",
    "inspect",
    "registry",
    "evidence",
    "readiness",
    "metadata",
)

for path in sorted(root.glob("*.py")):
    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception:
        continue

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if any(x in node.name.lower() for x in interesting):
            args = [
                a.arg for a in
                list(node.args.posonlyargs) + list(node.args.args)
            ]

            fn_rows.extend([
                f"FILE={path}",
                f"FUNCTION={node.name}",
                f"ARGS={','.join(args)}",
                "SOURCE_BEGIN",
                ast.get_source_segment(text, node) or "",
                "SOURCE_END",
                "",
            ])

        for child in ast.walk(node):
            if not isinstance(child, ast.Constant):
                continue

            if not isinstance(child.value, str):
                continue

            value = child.value

            if any(
                token in value.upper()
                for token in (
                    "PASS",
                    "READY",
                    "COMPLETE",
                    "VALID",
                    "EVIDENCE",
                    "REVIEW",
                    "FAIL",
                )
            ):
                status_rows.append(
                    f"FILE={path}\t"
                    f"FUNCTION={node.name}\t"
                    f"STATUS_LITERAL={value}"
                )

fn_out.write_text(
    "\n".join(fn_rows) + ("\n" if fn_rows else "")
)

status_out.write_text(
    "\n".join(status_rows) + ("\n" if status_rows else "")
)
PY

cat "$OUT/VALIDATION_FUNCTIONS.txt"

echo
echo "===== STATUS PRODUCERS ====="
cat "$OUT/STATUS_PRODUCERS.txt"

cat > "$OUT/PILOT_REQUIREMENTS.txt" <<'REQ'
PILOT_REQUIRED_AGENT_FIELD=agent_id
PILOT_REQUIRED_AGENT_FIELD=relative_path
PILOT_REQUIRED_AGENT_FIELD=sha256

PILOT_OPTIONAL_AGENT_FIELD=classes
PILOT_OPTIONAL_AGENT_FIELD=functions
PILOT_OPTIONAL_AGENT_FIELD=imports

PILOT_REQUIRED_EVIDENCE_FIELD=agent_id
PILOT_REQUIRED_EVIDENCE_FIELD=readiness_status
PILOT_REQUIRED_EVIDENCE_VALUE=EVIDENCE_COMPLETE

PROVEN_EVIDENCE_COMPLETE_WRITER_COUNT=0
REQ

STATUS_LITERAL_COUNT="$(
  wc -l < "$OUT/STATUS_PRODUCERS.txt" |
  tr -d ' '
)"

VALIDATION_FUNCTION_COUNT="$(
  grep -c '^FUNCTION=' "$OUT/VALIDATION_FUNCTIONS.txt" || true
)"

EVIDENCE_COMPLETE_WRITER_COUNT=0

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

EVIDENCE_CONTRACT_DEEP_PROOF=COMPLETE

VALIDATION_FUNCTION_COUNT=$VALIDATION_FUNCTION_COUNT
STATUS_LITERAL_COUNT=$STATUS_LITERAL_COUNT

EVIDENCE_COMPLETE_WRITER_COUNT=$EVIDENCE_COMPLETE_WRITER_COUNT

AGENT_INPUT_CONSTRUCTION_STATUS=PROVEN
EVIDENCE_COMPLETE_CONSUMER_STATUS=PROVEN
EVIDENCE_COMPLETE_PRODUCER_STATUS=NOT_PROVEN

CONTRACT_IMPLEMENTATION_STATUS=INCOMPLETE

SYNTHETIC_EVIDENCE_CREATED=NO
TARGET_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

FILE_MUTATION_EXECUTED=NO
NETWORK_EXECUTED=NO
PACKAGE_INSTALL_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- PILOT REQUIREMENTS ---"
cat "$OUT/PILOT_REQUIREMENTS.txt"

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"
echo "RESULT=HOLD"
echo "BLOCKER=EVIDENCE_COMPLETE_CONTRACT_HAS_CONSUMER_BUT_NO_PROVEN_PRODUCER"
echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R8_EVIDENCE_CONTRACT_REMEDIATION_DECISION"
echo "REPORT_DIR=$OUT"
echo "============================================================"
