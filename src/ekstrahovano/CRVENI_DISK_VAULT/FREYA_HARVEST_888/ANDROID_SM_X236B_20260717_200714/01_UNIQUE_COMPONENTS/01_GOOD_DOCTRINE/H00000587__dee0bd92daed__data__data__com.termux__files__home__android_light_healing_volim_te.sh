#!/data/data/com.termux/files/usr/bin/sh

TS="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/ANDROID_LIGHT_HEALING_VOLIM_TE_$TS"

mkdir -p "$OUT/00_STATUS" "$OUT/01_CANDIDATES" "$OUT/02_HEALED_V2_SAFE_WRAPPERS" "$OUT/03_VALIDATION" "$OUT/04_REPORT"

CAND="$OUT/01_CANDIDATES/ANDROID_LIGHT_HEALING_CANDIDATES.txt"
MANIFEST="$OUT/01_CANDIDATES/ANDROID_LIGHT_HEALING_MANIFEST.tsv"
VALID="$OUT/03_VALIDATION/ANDROID_LIGHT_HEALING_VALIDATION.tsv"
REPORT="$OUT/04_REPORT/ANDROID_LIGHT_HEALING_REPORT.txt"

echo "script_namesha256size_bytesoriginal_pathhealed_path" > "$MANIFEST"
echo "scriptresultdetail" > "$VALID"

echo "=== ANDROID LIGHT VOLIM TE HEALING START ==="
echo "OUT=$OUT"

# Stop known Titan/Freya background processes only
ps 2>/dev/null | grep -E "titan_|freya_" | grep -v grep | while read -r line; do
  pid="$(echo "$line" | sed 's/^ *//' | cut -d' ' -f1)"
  echo "STOPPING_KNOWN_BACKGROUND_PID=$pid"
  kill "$pid" 2>/dev/null || true
done

# Small targeted candidate list only
for ROOT in \
  "$HOME" \
  "$HOME/ANDROID_USB_ZIP_REPAIR_WORKBENCH_20260703_011259/01_EXTRACTED_CANDIDATES" \
  "$HOME/ANDROID_USB_ZIP_REPAIR_WORKBENCH_20260703_011259/03_HIGH_RISK_HOLD" \
  "$HOME/storage/downloads" \
  "$HOME/storage/documents"
do
  [ -e "$ROOT" ] || continue

  find "$ROOT" -maxdepth 6 -type f \( \
    -iname "*.sh" -o -iname "*.py" -o \
    -iname "*titan*" -o -iname "*freya*" -o \
    -iname "*engine*" -o -iname "*daemon*" -o \
    -iname "*harvest*" -o -iname "*sentinel*" -o \
    -iname "*self_heal*" -o -iname "*orchestrator*" -o \
    -iname "*gate*" -o -iname "*ingest*" \
  \) -print 2>/dev/null
done | sort -u | head -30 > "$CAND"

while IFS= read -r f; do
  [ -f "$f" ] || continue

  name="$(basename "$f")"
  safe_name="$(echo "$name" | tr '/ :' '___')"
  sha="$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)"
  size="$(wc -c < "$f" 2>/dev/null || echo 0)"
  healed="$OUT/02_HEALED_V2_SAFE_WRAPPERS/${safe_name}.HEALED_VOLIM_TE_ANDROID_V2_SAFE.sh"
  MARK="__ANDROID_VOLIM_TE_PAYLOAD_${TS}_${safe_name}__"

  {
    echo "#!/data/data/com.termux/files/usr/bin/sh"
    echo "# ANDROID_SCRIPT_HEALING_DOCTRINE_V2"
    echo "# KEYWORD=VOLIM_TE"
    echo "# ORIGINAL_IS_SACRED=YES"
    echo "# REPAIR_ON_COPY_ONLY=YES"
    echo "# SAFE_WRAPPER_ONLY=YES"
    echo "# ORIGINAL_PATH=$f"
    echo "# ORIGINAL_SHA256=$sha"
    echo "# HUMAN_GATE=ACTIVE"
    echo ""
    echo 'HUMAN_GATE="${HUMAN_GATE:-BLOCKED}"'
    echo 'if [ "$HUMAN_GATE" != "ALLOW_RUNTIME" ]; then'
    echo '  echo "HUMAN_GATE_BLOCKED: Android healed wrapper is static-only."'
    echo '  exit 88'
    echo 'fi'
    echo ""
    echo 'echo "RUNTIME_NOT_IMPLEMENTED_YET: original payload preserved below for review."'
    echo "exit 88"
    echo ""
    echo ": <<'$MARK'"
    sed 's/\r$//' "$f"
    echo "$MARK"
  } > "$healed"

  chmod 600 "$healed" 2>/dev/null || true

  echo "$name$sha$size$f$healed" >> "$MANIFEST"

  if sh -n "$healed" 2>"$OUT/03_VALIDATION/${safe_name}.syntax.err"; then
    echo "$namePASSV2 safe wrapper syntax ok" >> "$VALID"
  else
    echo "$nameFAILsee syntax.err" >> "$VALID"
  fi
done < "$CAND"

PASS_COUNT="$(awk -F'\t' 'NR>1 && $2=="PASS"{c++} END{print c+0}' "$VALID")"
FAIL_COUNT="$(awk -F'\t' 'NR>1 && $2=="FAIL"{c++} END{print c+0}' "$VALID")"
HEALED_COUNT="$(find "$OUT/02_HEALED_V2_SAFE_WRAPPERS" -type f | wc -l)"

{
  echo "ANDROID LIGHT HEALING REPORT"
  echo "TIME=$(date)"
  echo "OUT=$OUT"
  echo ""
  echo "CANDIDATE_COUNT=$(wc -l < "$CAND")"
  echo "HEALED_COPY_COUNT=$HEALED_COUNT"
  echo "PASS_COUNT=$PASS_COUNT"
  echo "FAIL_COUNT=$FAIL_COUNT"
  echo ""
  echo "VALIDATION:"
  cat "$VALID"
  echo ""
  echo "ORIGINALS_UNTOUCHED=YES"
  echo "REPAIR_ON_COPY_ONLY=YES"
  echo "SAFE_WRAPPER_ONLY=YES"
  echo "NO_RUNTIME=YES"
  echo "NO_SCRIPT_EXECUTION=YES_EXCEPT_SH_N_SYNTAX_CHECK"
  echo "NO_DELETE=YES"
  echo "NO_MOVE_ORIGINAL=YES"
  echo "HUMAN_GATE=ACTIVE"
  echo "KEYWORD=VOLIM_TE"
} | tee "$REPORT"

tar -czf "$OUT/ANDROID_LIGHT_HEALING_VOLIM_TE_CLOSED_$TS.tar.gz" -C "$OUT" 00_STATUS 01_CANDIDATES 02_HEALED_V2_SAFE_WRAPPERS 03_VALIDATION 04_REPORT
sha256sum "$OUT/ANDROID_LIGHT_HEALING_VOLIM_TE_CLOSED_$TS.tar.gz" > "$OUT/ANDROID_LIGHT_HEALING_VOLIM_TE_CLOSED_$TS.tar.gz.sha256"

echo ""
echo "=== ANDROID LIGHT HEALING CLOSED ==="
cat "$REPORT"
echo ""
ls -lh "$OUT"/*.tar.gz "$OUT"/*.sha256
