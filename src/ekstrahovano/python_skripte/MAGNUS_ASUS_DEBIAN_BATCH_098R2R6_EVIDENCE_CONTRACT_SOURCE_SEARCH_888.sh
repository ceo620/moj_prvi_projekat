#!/usr/bin/env bash
set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 098R2R6"
echo " EVIDENCE CONTRACT SOURCE SEARCH — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

ROOT="/mnt/c/FREYA_ASUS_NODE_888"
REPORT_ROOT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS"
OUT="$REPORT_ROOT/BATCH_098R2R6_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=098R2R6"
echo "MODE=READ_ONLY_EVIDENCE_CONTRACT_SOURCE_SEARCH"
echo "START_UTC=$START_UTC"
} > "$OUT/BATCH.env"

: > "$OUT/EVIDENCE_COMPLETE_FILES.txt"
: > "$OUT/READINESS_STATUS_FILES.txt"
: > "$OUT/AGENT_ID_FILES.txt"
: > "$OUT/COMBINED_CANDIDATES.txt"
: > "$OUT/STATIC_WRITER_ANALYSIS.txt"
: > "$OUT/FINAL_STATUS.txt"

SEARCH_ROOTS=(
  "$ROOT/00_CONTROL"
  "$ROOT/02_REGISTRY"
  "$ROOT/03_AGENTS_ACTIVE"
  "$ROOT/05_RUNTIME_UNION"
  "$ROOT/06_ASUS_INGEST"
  "$ROOT/09_EVIDENCE"
  "$ROOT/20_CANONICAL_AGENT_CONTROL"
  "$ROOT/21_CANONICAL_INTAKE_CONTROL"
  "$ROOT/22_CANONICAL_FACTORY_BINDING"
  "$ROOT/23_CANONICAL_BUILDER_IMPLEMENTATIONS"
  "$ROOT/24_CONTROLLED_FACTORY_CANARY"
  "$ROOT/25_CANONICAL_AGENT_IMPLEMENTATION"
)

echo "===== EVIDENCE_COMPLETE SEARCH ====="

grep -RIl \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  --include='*.py' \
  --include='*.json' \
  --include='*.jsonl' \
  --include='*.csv' \
  --include='*.txt' \
  --include='*.env' \
  --include='*.ps1' \
  'EVIDENCE_COMPLETE' \
  "${SEARCH_ROOTS[@]}" \
  2>/dev/null \
| sort -u \
| tee "$OUT/EVIDENCE_COMPLETE_FILES.txt" || true

echo
echo "===== READINESS_STATUS SEARCH ====="

grep -RIl \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  --include='*.py' \
  --include='*.json' \
  --include='*.jsonl' \
  --include='*.csv' \
  --include='*.txt' \
  --include='*.env' \
  --include='*.ps1' \
  'readiness_status' \
  "${SEARCH_ROOTS[@]}" \
  2>/dev/null \
| sort -u \
| tee "$OUT/READINESS_STATUS_FILES.txt" || true

echo
echo "===== AGENT_ID SEARCH ====="

grep -RIl \
  --exclude-dir='90_QUARANTINE' \
  --exclude-dir='08_ARCHIVES' \
  --exclude-dir='11_BACKUP' \
  --exclude-dir='99_ARCHIVE' \
  --include='*.py' \
  --include='*.json' \
  --include='*.jsonl' \
  --include='*.csv' \
  --include='*.txt' \
  --include='*.env' \
  --include='*.ps1' \
  'agent_id' \
  "${SEARCH_ROOTS[@]}" \
  2>/dev/null \
| sort -u \
| tee "$OUT/AGENT_ID_FILES.txt" || true

cat \
  "$OUT/EVIDENCE_COMPLETE_FILES.txt" \
  "$OUT/READINESS_STATUS_FILES.txt" \
  "$OUT/AGENT_ID_FILES.txt" \
| sort \
| uniq -c \
| awk '$1 >= 2 {$1=""; sub(/^ /,""); print}' \
> "$OUT/COMBINED_CANDIDATES.txt"

echo
echo "===== COMBINED CANDIDATES ====="
cat "$OUT/COMBINED_CANDIDATES.txt"

echo
echo "===== STATIC PYTHON WRITER ANALYSIS ====="

PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$OUT/COMBINED_CANDIDATES.txt" \
  "$OUT/STATIC_WRITER_ANALYSIS.txt" <<'PY'
import ast
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])

rows = []

for line in src.read_text(errors="replace").splitlines():
    p = Path(line)

    if p.suffix.lower() != ".py":
        continue

    try:
        text = p.read_text(errors="replace")
        tree = ast.parse(text, filename=str(p))
    except Exception as exc:
        rows.extend([
            f"FILE={p}",
            f"PARSE=FAIL:{type(exc).__name__}:{exc}",
            ""
        ])
        continue

    for fn in [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]:
        fn_source = ast.get_source_segment(text, fn) or ""

        has_agent_id = "agent_id" in fn_source
        has_readiness = "readiness_status" in fn_source
        has_complete = "EVIDENCE_COMPLETE" in fn_source

        writer_signal = False

        for node in ast.walk(fn):
            if isinstance(node, ast.Dict):
                pairs = {}
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        key = k.value
                        try:
                            val = ast.literal_eval(v)
                        except Exception:
                            try:
                                val = ast.unparse(v)
                            except Exception:
                                val = "UNKNOWN"
                        pairs[key] = val

                if (
                    pairs.get("readiness_status") == "EVIDENCE_COMPLETE"
                    and "agent_id" in pairs
                ):
                    writer_signal = True

            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if not isinstance(target, ast.Subscript):
                        continue

                    try:
                        key = ast.literal_eval(target.slice)
                    except Exception:
                        key = None

                    if key == "readiness_status":
                        try:
                            val = ast.literal_eval(node.value)
                        except Exception:
                            val = None

                        if val == "EVIDENCE_COMPLETE":
                            writer_signal = True

        if has_agent_id or has_readiness or has_complete:
            rows.extend([
                f"FILE={p}",
                f"FUNCTION={fn.name}",
                f"AGENT_ID_SIGNAL={'YES' if has_agent_id else 'NO'}",
                f"READINESS_STATUS_SIGNAL={'YES' if has_readiness else 'NO'}",
                f"EVIDENCE_COMPLETE_SIGNAL={'YES' if has_complete else 'NO'}",
                f"WRITER_SIGNAL={'YES' if writer_signal else 'NO'}",
                ""
            ])

out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY

cat "$OUT/STATIC_WRITER_ANALYSIS.txt"

EVIDENCE_COMPLETE_FILE_COUNT="$(
  wc -l < "$OUT/EVIDENCE_COMPLETE_FILES.txt" | tr -d ' '
)"

READINESS_STATUS_FILE_COUNT="$(
  wc -l < "$OUT/READINESS_STATUS_FILES.txt" | tr -d ' '
)"

AGENT_ID_FILE_COUNT="$(
  wc -l < "$OUT/AGENT_ID_FILES.txt" | tr -d ' '
)"

COMBINED_CANDIDATE_COUNT="$(
  wc -l < "$OUT/COMBINED_CANDIDATES.txt" | tr -d ' '
)"

WRITER_COUNT="$(
  grep -c '^WRITER_SIGNAL=YES$' \
    "$OUT/STATIC_WRITER_ANALYSIS.txt" || true
)"

if (( WRITER_COUNT > 0 )); then
    EVIDENCE_CONTRACT_SOURCE_STATUS="PROVEN"
elif (( COMBINED_CANDIDATE_COUNT > 0 )); then
    EVIDENCE_CONTRACT_SOURCE_STATUS="PARTIAL"
else
    EVIDENCE_CONTRACT_SOURCE_STATUS="NOT_FOUND"
fi

cat > "$OUT/FINAL_STATUS.txt" <<STATUS
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888

EVIDENCE_CONTRACT_SOURCE_SEARCH=COMPLETE

EVIDENCE_COMPLETE_FILE_COUNT=$EVIDENCE_COMPLETE_FILE_COUNT
READINESS_STATUS_FILE_COUNT=$READINESS_STATUS_FILE_COUNT
AGENT_ID_FILE_COUNT=$AGENT_ID_FILE_COUNT

COMBINED_CANDIDATE_COUNT=$COMBINED_CANDIDATE_COUNT
TRUE_WRITER_COUNT=$WRITER_COUNT

EVIDENCE_CONTRACT_SOURCE_STATUS=$EVIDENCE_CONTRACT_SOURCE_STATUS

PYTHON_EXECUTION_EXECUTED=NO
AGENT_EXECUTION_EXECUTED=NO

FILE_COPY_EXECUTED=NO
FILE_MOVE_EXECUTED=NO
FILE_DELETE_EXECUTED=NO
FILE_RENAME_EXECUTED=NO

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

case "$EVIDENCE_CONTRACT_SOURCE_STATUS" in

  PROVEN)
    echo "RESULT=PASS"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R7_EVIDENCE_PRODUCER_BINDING_PLAN"
    ;;

  PARTIAL)
    echo "RESULT=PASS_WITH_WARNINGS"
    echo "WARNING=EVIDENCE_CONTRACT_REFERENCES_FOUND_BUT_WRITER_NOT_PROVEN"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R7_EVIDENCE_CONTRACT_DEEP_PROOF"
    ;;

  *)
    echo "RESULT=HOLD"
    echo "BLOCKER=EVIDENCE_COMPLETE_SOURCE_NOT_FOUND"
    echo "NEXT_RECOMMENDED_BATCH=BATCH_098R2R7_METADATA_PILOT_CONTRACT_DECISION"
    ;;
esac

echo "REPORT_DIR=$OUT"
echo "============================================================"
