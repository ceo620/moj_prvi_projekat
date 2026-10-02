#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R4"
echo " INPUT SCHEMA DEEP ANALYSIS — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R4_$START_UTC"

DESCRIPTOR_FILE="$AGENT_ROOT/6eb6f765f059_agent_descriptor.py"
DISCOVERY_FILE="$AGENT_ROOT/05c0204f9c0a_agent_discovery.py"
PILOT_FILE="$AGENT_ROOT/ea4106a2d52a_metadata_agent_pilot.py"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R4"
echo "MODE=READ_ONLY_INPUT_SCHEMA_DEEP_ANALYSIS"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/DESCRIPTOR_SCHEMA.txt"
: > "$OUT/DISCOVERY_BINDING.txt"
: > "$OUT/EVIDENCE_CONTRACT_REFERENCES.txt"
: > "$OUT/EVIDENCE_STATUS_WRITERS.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== AGENT DESCRIPTOR SCHEMA ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$DESCRIPTOR_FILE" \
  "$OUT/DESCRIPTOR_SCHEMA.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

text = path.read_text(errors="replace")
tree = ast.parse(text, filename=str(path))

rows = []

for node in tree.body:
    if not isinstance(node, ast.ClassDef):
        continue

    if node.name != "AgentDescriptor":
        continue

    rows.append("CLASS_FOUND=YES")
    rows.append("CLASS_NAME=AgentDescriptor")

    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            annotation = ast.unparse(stmt.annotation)
            rows.append(
                f"FIELD={name}\tANNOTATION={annotation}"
            )

        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append(f"METHOD={stmt.name}")

            if stmt.name in {
                "to_dict",
                "as_dict",
                "serialize",
            }:
                segment = ast.get_source_segment(text, stmt) or ""
                rows.append("SERIALIZER_SOURCE_BEGIN")
                rows.append(segment)
                rows.append("SERIALIZER_SOURCE_END")

out.write_text("\n".join(rows) + "\n")
PY

cat "$OUT/DESCRIPTOR_SCHEMA.txt"

echo
echo "===== DISCOVERY -> DESCRIPTOR BINDING ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$DISCOVERY_FILE" \
  "$OUT/DISCOVERY_BINDING.txt" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
out = Path(sys.argv[2])

text = path.read_text(errors="replace")
tree = ast.parse(text, filename=str(path))

rows = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue

    try:
        name = ast.unparse(node.func)
    except Exception:
        continue

    if name != "AgentDescriptor":
        continue

    rows.append("AGENT_DESCRIPTOR_CONSTRUCTION=FOUND")

    for kw in node.keywords:
        if kw.arg is None:
            continue

        try:
            value = ast.unparse(kw.value)
        except Exception:
            value = "UNKNOWN"

        rows.append(
            f"FIELD={kw.arg}\tSOURCE_EXPR={value}"
        )

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/DISCOVERY_BINDING.txt"

echo
echo "===== EVIDENCE CONTRACT REFERENCES ====="

grep -RInE \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  'readiness_status|EVIDENCE_COMPLETE|evidence_pack' \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/09_EVIDENCE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  2>/dev/null \
| sort -u \
| tee "$OUT/EVIDENCE_CONTRACT_REFERENCES.txt" || true

echo
echo "===== TRUE READINESS STATUS WRITER ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$AGENT_ROOT" \
  "$OUT/EVIDENCE_STATUS_WRITERS.txt" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])

rows = []

for path in sorted(root.rglob("*.py")):
    try:
        text = path.read_text(errors="replace")
        tree = ast.parse(text, filename=str(path))
    except Exception:
        continue

    for node in ast.walk(tree):

        # dict literal:
        # {"readiness_status": "EVIDENCE_COMPLETE"}
        if isinstance(node, ast.Dict):
            pairs = {}

            for k, v in zip(node.keys, node.values):
                if (
                    isinstance(k, ast.Constant)
                    and isinstance(k.value, str)
                ):
                    try:
                        pairs[k.value] = ast.literal_eval(v)
                    except Exception:
                        pass

            if pairs.get("readiness_status") == "EVIDENCE_COMPLETE":
                rows.append(
                    f"FILE={path}\t"
                    f"LINENO={getattr(node,'lineno','UNKNOWN')}\t"
                    "WRITER_TYPE=DICT_LITERAL"
                )

        # x["readiness_status"] = "EVIDENCE_COMPLETE"
        if isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Subscript)
                and isinstance(node.value, ast.Constant)
                and node.value.value == "EVIDENCE_COMPLETE"
            ):
                target = node.targets[0]

                try:
                    key = ast.literal_eval(target.slice)
                except Exception:
                    key = None

                if key == "readiness_status":
                    rows.append(
                        f"FILE={path}\t"
                        f"LINENO={getattr(node,'lineno','UNKNOWN')}\t"
                        "WRITER_TYPE=SUBSCRIPT_ASSIGN"
                    )

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/EVIDENCE_STATUS_WRITERS.txt"

DESCRIPTOR_CONSTRUCTION_COUNT="$(
  grep -c '^AGENT_DESCRIPTOR_CONSTRUCTION=FOUND$' \
    "$OUT/DISCOVERY_BINDING.txt" || true
)"

AGENT_ID_BINDING_COUNT="$(
  grep -c '^FIELD=agent_id' \
    "$OUT/DISCOVERY_BINDING.txt" || true
)"

RELATIVE_PATH_BINDING_COUNT="$(
  grep -c '^FIELD=relative_path' \
    "$OUT/DISCOVERY_BINDING.txt" || true
)"

SHA256_BINDING_COUNT="$(
  grep -c '^FIELD=sha256' \
    "$OUT/DISCOVERY_BINDING.txt" || true
)"

EVIDENCE_WRITER_COUNT="$(
  wc -l < "$OUT/EVIDENCE_STATUS_WRITERS.txt" |
  tr -d ' '
)"

EVIDENCE_REFERENCE_COUNT="$(
  wc -l < "$OUT/EVIDENCE_CONTRACT_REFERENCES.txt" |
  tr -d ' '
)"

if (( DESCRIPTOR_CONSTRUCTION_COUNT > 0 &&
      AGENT_ID_BINDING_COUNT > 0 &&
      RELATIVE_PATH_BINDING_COUNT > 0 &&
      SHA256_BINDING_COUNT > 0 )); then

    AGENT_INPUT_CONSTRUCTION_STATUS="PROVEN"

else
    AGENT_INPUT_CONSTRUCTION_STATUS="NOT_PROVEN"
fi

if (( EVIDENCE_WRITER_COUNT > 0 )); then
    EVIDENCE_PRODUCER_STATUS="PROVEN"
else
    EVIDENCE_PRODUCER_STATUS="NOT_PROVEN"
fi

if [[ "$AGENT_INPUT_CONSTRUCTION_STATUS" == "PROVEN" &&
      "$EVIDENCE_PRODUCER_STATUS" == "PROVEN" ]]; then

    PILOT_INPUT_CHAIN_STATUS="PROVEN"

else
    PILOT_INPUT_CHAIN_STATUS="INCOMPLETE"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

INPUT_SCHEMA_DEEP_ANALYSIS=COMPLETE

DESCRIPTOR_CONSTRUCTION_COUNT=$DESCRIPTOR_CONSTRUCTION_COUNT

AGENT_ID_BINDING_COUNT=$AGENT_ID_BINDING_COUNT
RELATIVE_PATH_BINDING_COUNT=$RELATIVE_PATH_BINDING_COUNT
SHA256_BINDING_COUNT=$SHA256_BINDING_COUNT

AGENT_INPUT_CONSTRUCTION_STATUS=$AGENT_INPUT_CONSTRUCTION_STATUS

EVIDENCE_CONTRACT_REFERENCE_COUNT=$EVIDENCE_REFERENCE_COUNT
TRUE_EVIDENCE_COMPLETE_WRITER_COUNT=$EVIDENCE_WRITER_COUNT
EVIDENCE_PRODUCER_STATUS=$EVIDENCE_PRODUCER_STATUS

PILOT_INPUT_CHAIN_STATUS=$PILOT_INPUT_CHAIN_STATUS

TARGET_FUNCTION_EXECUTED=NO
DISCOVERY_FUNCTION_EXECUTED=NO
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
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if [[ "$PILOT_INPUT_CHAIN_STATUS" == "PROVEN" ]]; then

    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R3_CONTROLLED_METADATA_PILOT_CANARY_PLAN"

elif [[ "$AGENT_INPUT_CONSTRUCTION_STATUS" == "PROVEN" &&
        "$EVIDENCE_PRODUCER_STATUS" == "NOT_PROVEN" ]]; then

    echo "RESULT=HOLD"
    echo "BLOCKER=EVIDENCE_COMPLETE_PRODUCER_NOT_IMPLEMENTED_OR_NOT_FOUND"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R5_EVIDENCE_CONTRACT_RESOLUTION"

else

    echo "RESULT=HOLD"
    echo "BLOCKER=METADATA_PILOT_INPUT_CHAIN_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R5_INPUT_BINDING_ANALYSIS"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
