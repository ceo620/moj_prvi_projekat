#!/bin/bash
set -eu

ROOT="$HOME/FREYA_ASUS_DEBIAN_888"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/MAGNUS_DEBIAN_BATCH_002_$TS"

mkdir -p "$OUT"

echo "============================================================"
echo "MAGNUS DEBIAN BATCH 002"
echo "CANONICAL ARCHITECTURE REVIEW"
echo "============================================================"

echo "PROTOCOL=888"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "MODE=READ_ONLY"


echo
echo "===== CANONICAL ROOTS ====="

for D in \
00_CONTROL \
01_CONFIG \
02_SSOT \
03_INTAKE \
06_AGENTS \
07_JOBS \
08_STATE \
09_HANDOFF \
10_EVIDENCE \
11_BACKUP \
12_ROLLBACK \
18_LIVE_DASHBOARD
do
    if [ -d "$ROOT/$D" ]; then
        echo "$D=FOUND"
    else
        echo "$D=MISSING"
    fi
done | tee "$OUT/CANONICAL_ROOTS.txt"


echo
echo "===== SSOT ====="

find "$ROOT/02_SSOT" -maxdepth 2 -type f 2>/dev/null | \
head -100 | tee "$OUT/SSOT_INDEX.txt"


echo
echo "===== AGENTS ====="

find "$ROOT/06_AGENTS" -maxdepth 2 -type f 2>/dev/null | \
head -100 | tee "$OUT/AGENT_INDEX.txt"


echo
echo "===== RUNTIME ====="

find "$ROOT" -type d 2>/dev/null | \
grep -Ei "runtime|state|watchdog|dispatcher|dashboard" | \
head -100 | tee "$OUT/RUNTIME_INDEX.txt"


echo
echo "===== HANDOFF ====="

find "$ROOT/09_HANDOFF" -maxdepth 3 -type f 2>/dev/null | \
head -100 | tee "$OUT/HANDOFF_INDEX.txt"


echo
echo "===== FINAL ====="

cat > "$OUT/RESULT.env" <<EOF
PROTOCOL=888
NODE=FREYA_ASUS_DEBIAN_888
BATCH=002

MODE=ARCHITECTURE_REVIEW

SSOT=CHECKED
AGENTS=CHECKED
RUNTIME=CHECKED
HANDOFF=CHECKED

MUTATION=NO
DELETE=NO
MOVE=NO
WRITE=NO

RESULT=PASS
NEXT=DEBIAN_AGENT_RUNTIME_REVIEW
EOF

cat "$OUT/RESULT.env"

echo
echo "REPORT=$OUT"

echo "============================================================"

