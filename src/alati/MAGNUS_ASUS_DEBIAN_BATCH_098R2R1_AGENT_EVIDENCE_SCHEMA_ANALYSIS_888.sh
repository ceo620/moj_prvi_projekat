#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R1"
echo " AGENT + EVIDENCE SCHEMA ANALYSIS — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R1_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R1"
echo "MODE=READ_ONLY_AGENT_EVIDENCE_SCHEMA_ANALYSIS"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/JSON_FILES.txt"
: > "$OUT/STRUCTURED_RECORDS.txt"
: > "$OUT/AGENT_RECORDS.txt"
: > "$OUT/EVIDENCE_RECORDS.txt"
: > "$OUT/JOIN_PROOF.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== STRUCTURED FILE DISCOVERY ====="

find \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/09_EVIDENCE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  -type f \
  \( -iname '*.json' -o -iname '*.jsonl' \) \
  2>/dev/null \
| grep -Ev '/(90_QUARANTINE|08_ARCHIVES|11_BACKUP|99_ARCHIVE)/' \
| sort -u \
| tee "$OUT/JSON_FILES.txt"

JSON_FILE_COUNT="$(wc -l < "$OUT/JSON_FILES.txt" | tr -d ' ')"

echo
echo "===== STATIC JSON SCHEMA ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
 "$OUT/JSON_FILES.txt" \
 "$OUT/STRUCTURED_RECORDS.txt" \
 "$OUT/AGENT_RECORDS.txt" \
 "$OUT/EVIDENCE_RECORDS.txt" \
 "$OUT/JOIN_PROOF.txt" <<'PY'
import json
import sys
from pathlib import Path

file_list = Path(sys.argv[1])
structured_out = Path(sys.argv[2])
agent_out = Path(sys.argv[3])
evidence_out = Path(sys.argv[4])
join_out = Path(sys.argv[5])

structured = []
agents = []
evidence = []

def walk(value, source, pointer="$"):
    if isinstance(value, dict):
        keys = sorted(map(str, value.keys()))

        aid = value.get("agent_id")
        readiness = value.get("readiness_status")

        structured.append(
            f"FILE={source}\tPOINTER={pointer}\t"
            f"AGENT_ID={aid if aid is not None else 'NONE'}\t"
            f"READINESS_STATUS={readiness if readiness is not None else 'NONE'}\t"
            f"KEYS={','.join(keys)}"
        )

        required_agent = {
            "agent_id",
            "relative_path",
            "sha256",
        }

        if required_agent.issubset(value.keys()):
            agents.append((source, pointer, value))

        if (
            aid is not None
            and readiness == "EVIDENCE_COMPLETE"
        ):
            evidence.append((source, pointer, value))

        for k, v in value.items():
            walk(v, source, f"{pointer}.{k}")

    elif isinstance(value, list):
        for i, v in enumerate(value):
            walk(v, source, f"{pointer}[{i}]")

for line in file_list.read_text(errors="replace").splitlines():
    path = Path(line)

    try:
        text = path.read_text(errors="replace")
    except Exception:
        continue

    parsed = False

    try:
        value = json.loads(text)
        walk(value, path)
        parsed = True
    except Exception:
        pass

    if not parsed:
        for lineno, raw in enumerate(text.splitlines(), start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except Exception:
                continue
            walk(value, path, f"$LINE[{lineno}]")

agent_rows = []
for source, pointer, obj in agents:
    agent_rows.extend([
        f"AGENT_ID={obj.get('agent_id')}",
        f"SOURCE={source}",
        f"POINTER={pointer}",
        f"RELATIVE_PATH={obj.get('relative_path')}",
        f"SHA256={obj.get('sha256')}",
        f"CLASSES={obj.get('classes','')}",
        f"FUNCTIONS={obj.get('functions','')}",
        f"IMPORTS={obj.get('imports','')}",
        "",
    ])

evidence_rows = []
for source, pointer, obj in evidence:
    evidence_rows.extend([
        f"AGENT_ID={obj.get('agent_id')}",
        f"SOURCE={source}",
        f"POINTER={pointer}",
        "READINESS_STATUS=EVIDENCE_COMPLETE",
        "",
    ])

join_rows = []

for asrc, aptr, agent in agents:
    aid = str(agent.get("agent_id"))

    for esrc, eptr, ev in evidence:
        if str(ev.get("agent_id")) != aid:
            continue

        join_rows.extend([
            f"AGENT_ID={aid}",
            f"AGENT_SOURCE={asrc}",
            f"AGENT_POINTER={aptr}",
            f"EVIDENCE_SOURCE={esrc}",
            f"EVIDENCE_POINTER={eptr}",
            f"RELATIVE_PATH={agent.get('relative_path')}",
            f"SHA256={agent.get('sha256')}",
            "READINESS_STATUS=EVIDENCE_COMPLETE",
            "JOIN_STATUS=PASS",
            "",
        ])

structured_out.write_text(
    "\n".join(structured) + ("\n" if structured else "")
)
agent_out.write_text(
    "\n".join(agent_rows) + ("\n" if agent_rows else "")
)
evidence_out.write_text(
    "\n".join(evidence_rows) + ("\n" if evidence_rows else "")
)
join_out.write_text(
    "\n".join(join_rows) + ("\n" if join_rows else "")
)
PY

AGENT_RECORD_COUNT="$(
  grep -c '^AGENT_ID=' "$OUT/AGENT_RECORDS.txt" || true
)"

EVIDENCE_RECORD_COUNT="$(
  grep -c '^READINESS_STATUS=EVIDENCE_COMPLETE$' \
    "$OUT/EVIDENCE_RECORDS.txt" || true
)"

JOIN_COUNT="$(
  grep -c '^JOIN_STATUS=PASS$' "$OUT/JOIN_PROOF.txt" || true
)"

echo
echo "===== AGENT RECORDS ====="
cat "$OUT/AGENT_RECORDS.txt"

echo
echo "===== EVIDENCE RECORDS ====="
cat "$OUT/EVIDENCE_RECORDS.txt"

echo
echo "===== JOIN PROOF ====="
cat "$OUT/JOIN_PROOF.txt"

if (( JOIN_COUNT > 0 )); then
    BINDING_STATUS="PROVEN"
elif (( AGENT_RECORD_COUNT > 0 && EVIDENCE_RECORD_COUNT == 0 )); then
    BINDING_STATUS="EVIDENCE_SCHEMA_NOT_FOUND"
elif (( AGENT_RECORD_COUNT == 0 )); then
    BINDING_STATUS="AGENT_SCHEMA_NOT_FOUND"
else
    BINDING_STATUS="JOIN_NOT_PROVEN"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

AGENT_EVIDENCE_SCHEMA_ANALYSIS=COMPLETE

JSON_FILE_COUNT=$JSON_FILE_COUNT
VALID_AGENT_RECORD_COUNT=$AGENT_RECORD_COUNT
EVIDENCE_COMPLETE_RECORD_COUNT=$EVIDENCE_RECORD_COUNT
VALID_AGENT_EVIDENCE_JOIN_COUNT=$JOIN_COUNT

ARGUMENT_BINDING_STATUS=$BINDING_STATUS

TARGET_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
NETWORK_EXECUTED=NO
FILE_MUTATION_EXECUTED=NO

MUTATION_ALLOWED=NO
DELETE_ALLOWED=NO
REPAIR_ALLOWED=NO

MODE=HUMAN_GATE_CONTROLLED
STATUS

echo
echo "--- FINAL STATUS ---"
cat "$OUT/FINAL_STATUS.txt"

echo "============================================================"

if (( JOIN_COUNT > 0 )); then
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R3_CONTROLLED_METADATA_PILOT_CANARY_PLAN"
else
    echo "RESULT=HOLD"
    echo "BLOCKER=METADATA_PILOT_ARGUMENT_SCHEMA_BINDING_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R2_EVIDENCE_PRODUCER_ANALYSIS"
fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
