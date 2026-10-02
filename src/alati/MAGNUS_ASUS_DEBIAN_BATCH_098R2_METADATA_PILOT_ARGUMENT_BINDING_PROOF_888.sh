#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2"
echo " METADATA PILOT ARGUMENT BINDING PROOF — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
AGENT_ROOT="$ROOT/03_AGENTS_ACTIVE/VALIDATED_PENDING_RUNTIME"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2"
echo "MODE=READ_ONLY_METADATA_PILOT_ARGUMENT_BINDING_PROOF"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/AGENT_RECORD_CANDIDATES.txt"
: > "$OUT/EVIDENCE_PACK_CANDIDATES.txt"
: > "$OUT/JOIN_CANDIDATES.txt"
: > "$OUT/FINAL_STATUS.txt"

echo "===== AGENT RECORD CANDIDATES ====="

grep -RIl \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  '"agent_id"\|agent_id' \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  2>/dev/null \
| sort -u \
| tee "$OUT/AGENT_RECORD_CANDIDATES.txt"

echo
echo "===== EVIDENCE PACK CANDIDATES ====="

grep -RIl \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  'EVIDENCE_COMPLETE' \
  "$ROOT/03_AGENTS_ACTIVE" \
  "$ROOT/09_EVIDENCE" \
  "$ROOT/20_CANONICAL_AGENT_CONTROL" \
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION" \
  2>/dev/null \
| sort -u \
| tee "$OUT/EVIDENCE_PACK_CANDIDATES.txt"

echo
echo "===== STRUCTURED JOIN ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$OUT/AGENT_RECORD_CANDIDATES.txt" \
  "$OUT/EVIDENCE_PACK_CANDIDATES.txt" \
  "$OUT/JOIN_CANDIDATES.txt" <<'PY'
import json
import sys
from pathlib import Path

agent_files = Path(sys.argv[1])
evidence_files = Path(sys.argv[2])
out = Path(sys.argv[3])

required_agent = {
    "agent_id",
    "relative_path",
    "sha256",
}

def load_json_objects(path):
    objs = []

    try:
        text = path.read_text(errors="replace")
    except Exception:
        return objs

    # Whole-file JSON.
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            objs.append(data)
        elif isinstance(data, list):
            objs.extend(x for x in data if isinstance(x, dict))
    except Exception:
        pass

    # JSONL fallback.
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue

        try:
            item = json.loads(line)
            if isinstance(item, dict):
                objs.append(item)
        except Exception:
            pass

    return objs

agents = []
evidence = []

for line in agent_files.read_text(errors="replace").splitlines():
    p = Path(line)

    for obj in load_json_objects(p):
        if required_agent.issubset(obj):
            agents.append((p, obj))

for line in evidence_files.read_text(errors="replace").splitlines():
    p = Path(line)

    for obj in load_json_objects(p):
        if (
            "agent_id" in obj
            and obj.get("readiness_status") == "EVIDENCE_COMPLETE"
        ):
            evidence.append((p, obj))

rows = []

for agent_path, agent in agents:
    aid = str(agent["agent_id"])

    for evidence_path, ev in evidence:
        if str(ev.get("agent_id")) != aid:
            continue

        rows.extend([
            f"AGENT_ID={aid}",
            f"AGENT_RECORD_FILE={agent_path}",
            f"EVIDENCE_FILE={evidence_path}",
            f"RELATIVE_PATH={agent.get('relative_path','')}",
            f"SHA256={agent.get('sha256','')}",
            f"CLASSES={agent.get('classes','')}",
            f"FUNCTIONS={agent.get('functions','')}",
            f"IMPORTS={agent.get('imports','')}",
            f"READINESS_STATUS={ev.get('readiness_status')}",
            "JOIN_STATUS=PASS",
            "",
        ])

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/JOIN_CANDIDATES.txt"

JOIN_COUNT="$(
  grep -c '^JOIN_STATUS=PASS$' \
    "$OUT/JOIN_CANDIDATES.txt" || true
)"

AGENT_FILE_COUNT="$(
  wc -l < "$OUT/AGENT_RECORD_CANDIDATES.txt" |
  tr -d ' '
)"

EVIDENCE_FILE_COUNT="$(
  wc -l < "$OUT/EVIDENCE_PACK_CANDIDATES.txt" |
  tr -d ' '
)"

if (( JOIN_COUNT > 0 )); then
    ARGUMENT_BINDING_STATUS="PROVEN"
else
    ARGUMENT_BINDING_STATUS="NOT_PROVEN"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

METADATA_PILOT_ARGUMENT_BINDING_AUDIT=COMPLETE

AGENT_RECORD_CANDIDATE_FILE_COUNT=$AGENT_FILE_COUNT
EVIDENCE_PACK_CANDIDATE_FILE_COUNT=$EVIDENCE_FILE_COUNT

VALID_AGENT_EVIDENCE_JOIN_COUNT=$JOIN_COUNT

ARGUMENT_1=agent
ARGUMENT_2=evidence_pack

ARGUMENT_BINDING_STATUS=$ARGUMENT_BINDING_STATUS

TARGET_FUNCTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO
NETWORK_EXECUTED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_DELETE_EXECUTED=NO

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
    echo "BLOCKER=VALID_METADATA_PILOT_ARGUMENT_BINDING_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R1_AGENT_EVIDENCE_SCHEMA_ANALYSIS"

fi

echo "REPORT_DIR=$OUT"
echo "============================================================"
