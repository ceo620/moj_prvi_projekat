#!/data/data/com.termux/files/usr/bin/sh

TS="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/ANDROID_HEALING_VOLIM_TE_V3_$TS"

mkdir -p "$OUT/00_STATUS" "$OUT/01_CANDIDATES" "$OUT/02_HEALED_V3_SAFE_WRAPPERS" "$OUT/03_VALIDATION" "$OUT/04_REPORT"

CAND="$OUT/01_CANDIDATES/CANDIDATES_SCRIPTS_ONLY.txt"
MANIFEST="$OUT/01_CANDIDATES/MANIFEST.psv"
VALID="$OUT/03_VALIDATION/VALIDATION.psv"
REPORT="$OUT/04_REPORT/ANDROID_HEALING_V3_REPORT.txt"

printf "id|script_name|sha256|size_bytes|original_path|healed_path\n" > "$MANIFEST"
printf "id|script_name|result|detail\n" > "$VALID"

echo "=== ANDROID VOLIM TE V3 HEALING START ==="
echo "OUT=$OUT"

# Stop only known Titan/Freya background processes if any are active
ps 2>/dev/null | grep -E "titan_|freya_" | grep -v grep | while read -r line; do
  pid="$(echo "$line" | sed 's/^ *//' | cut -d' ' -f1)"
  echo "STOPPING_KNOWN_BACKGROUND_PID=$pid"
  kill "$pid" 2>/dev/null || true
done

# Scripts only. No txt/md/json in healing.
for ROOT in \
  "$HOME" \
  "$HOME/ANDROID_USB_ZIP_REPAIR_WORKBENCH_20260703_011259/01_EXTRACTED_CANDIDATES" \
  "$HOME/ANDROID_USB_ZIP_REPAIR_WORKBENCH_20260703_011259/03_HIGH_RISK_HOLD" \
  "$HOME/storage/downloads" \
  "$HOME/storage/documents"
do
  [ -e "$ROOT" ] || continue

  find "$ROOT" -maxdepth 7 -type f \( \
    -iname "*.sh" -o -iname "*.bash" -o -iname "*.py" \
  \) -print 2>/dev/null
done | sort -u | head -40 > "$CAND"

i=0
while IFS= read -r f; do
  [ -f "$f" ] || continue

  i=$((i + 1))
  id="$(printf "H%03d" "$i")"
  name="$(basename "$f")"
  sha="$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)"
  size="$(wc -c < "$f" 2>/dev/null || echo 0)"
  ext="${name##*.}"
  [ "$ext" = "$name" ] && ext="sh"

  healed="$OUT/02_HEALED_V3_SAFE_WRAPPERS/${id}.${ext}.HEALED_VOLIM_TE_V3_SAFE.sh"
  MARK="__ANDROID_VOLIM_TE_V3_PAYLOAD_${id}_${TS}__"

  {
    echo "#!/data/data/com.termux/files/usr/bin/sh"
    echo "# ANDROID_SCRIPT_HEALING_DOCTRINE_V3"
    echo "# KEYWORD=VOLIM_TE"
    echo "# ORIGINAL_IS_SACRED=YES"
    echo "# REPAIR_ON_COPY_ONLY=YES"
    echo "# SAFE_WRAPPER_ONLY=YES"
    echo "# ID=$id"
    echo "# ORIGINAL_NAME=$name"
    echo "# ORIGINAL_PATH=$f"
    echo "# ORIGINAL_SHA256=$sha"
    echo "# HUMAN_GATE=ACTIVE"
    echo ""
    echo 'HUMAN_GATE="${HUMAN_GATE:-BLOCKED}"'
    echo 'if [ "$HUMAN_GATE" != "ALLOW_RUNTIME" ]; then'
    echo '  echo "HUMAN_GATE_BLOCKED: Android V3 healed wrapper is static-only."'
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

  printf "%s|%s|%s|%s|%s|%s\n" "$id" "$name" "$sha" "$size" "$f" "$healed" >> "$MANIFEST"

  if sh -n "$healed" 2>"$OUT/03_VALIDATION/${id}.syntax.err"; then
    printf "%s|%s|PASS|V3 safe wrapper syntax ok\n" "$id" "$name" >> "$VALID"
  else
    printf "%s|%s|FAIL|see %s\n" "$id" "$name" "$OUT/03_VALIDATION/${id}.syntax.err" >> "$VALID"
  fi
done < "$CAND"

PASS_COUNT="$(awk -F'|' 'NR>1 && $3=="PASS"{c++} END{print c+0}' "$VALID")"
FAIL_COUNT="$(awk -F'|' 'NR>1 && $3=="FAIL"{c++} END{print c+0}' "$VALID")"
CANDIDATE_COUNT="$(wc -l < "$CAND")"
HEALED_COUNT="$(find "$OUT/02_HEALED_V3_SAFE_WRAPPERS" -type f | wc -l)"

{
  echo "ANDROID HEALING V3 REPORT"
  echo "TIME=$(date)"
  echo "OUT=$OUT"
  echo ""
  echo "CANDIDATE_COUNT=$CANDIDATE_COUNT"
  echo "HEALED_COPY_COUNT=$HEALED_COUNT"
  echo "PASS_COUNT=$PASS_COUNT"
  echo "FAIL_COUNT=$FAIL_COUNT"
  echo ""
  echo "VALIDATION:"
  cat "$VALID"
  echo ""
  echo "TOP_MANIFEST:"
  head -20 "$MANIFEST"
  echo ""
  echo "ORIGINALS_UNTOUCHED=YES"
  echo "REPAIR_ON_COPY_ONLY=YES"
  echo "SAFE_WRAPPER_ONLY=YES"
  echo "SHORT_HEALED_FILENAMES=YES"
  echo "NO_TXT_MD_JSON_HEALING=YES"
  echo "NO_RUNTIME=YES"
  echo "NO_SCRIPT_EXECUTION=YES_EXCEPT_SH_N_SYNTAX_CHECK"
  echo "NO_DELETE=YES"
  echo "NO_MOVE_ORIGINAL=YES"
  echo "HUMAN_GATE=ACTIVE"
  echo "KEYWORD=VOLIM_TE"
} | tee "$REPORT"

tar -czf "$OUT/ANDROID_HEALING_VOLIM_TE_V3_CLOSED_$TS.tar.gz" -C "$OUT" 00_STATUS 01_CANDIDATES 02_HEALED_V3_SAFE_WRAPPERS 03_VALIDATION 04_REPORT
sha256sum "$OUT/ANDROID_HEALING_VOLIM_TE_V3_CLOSED_$TS.tar.gz" > "$OUT/ANDROID_HEALING_VOLIM_TE_V3_CLOSED_$TS.tar.gz.sha256"

echo ""
echo "=== ANDROID HEALING V3 CLOSED ==="
cat "$REPORT"
echo ""
ls -lh "$OUT"/*.tar.gz "$OUT"/*.sha256
