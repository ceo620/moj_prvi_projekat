#!/data/data/com.termux/files/usr/bin/bash
set -u

TS="$(date +%Y%m%d_%H%M%S)"
OUT="/sdcard/Download/ARCHIVE_DO_NOT_RUN_PREP_MANIFEST_$TS.txt"
HASH="/sdcard/Download/ARCHIVE_DO_NOT_RUN_PREP_MANIFEST_$TS.sha256"

CANONICAL_MEMORY="/sdcard/delta_v4_memory.json"

write_candidate() {
  LABEL="$1"
  PATHX="$2"
  CLASSIFICATION="$3"
  REASON="$4"
  ARCHIVE_DECISION="$5"

  echo "" >> "$OUT"
  echo "[$LABEL]" >> "$OUT"
  echo "Path: $PATHX" >> "$OUT"
  echo "Classification: $CLASSIFICATION" >> "$OUT"
  echo "Reason: $REASON" >> "$OUT"
  echo "Archive decision: $ARCHIVE_DECISION" >> "$OUT"

  if [ -f "$PATHX" ]; then
    echo "Exists: YES" >> "$OUT"
    echo "File metadata:" >> "$OUT"
    ls -lah "$PATHX" >> "$OUT" 2>&1
    echo "SHA256:" >> "$OUT"
    sha256sum "$PATHX" >> "$OUT"
  else
    echo "Exists: NO" >> "$OUT"
    echo "SHA256: MISSING" >> "$OUT"
  fi
}

{
  echo "ARCHIVE_DO_NOT_RUN_PREP_MANIFEST"
  echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "Mode:"
  echo "STATIC_ARCHIVE_PREP_ONLY"
  echo ""
  echo "Controls:"
  echo "NO DELETE"
  echo "NO MOVE"
  echo "NO RENAME"
  echo "NO OVERWRITE"
  echo "NO SCRIPT EXECUTION"
  echo "NO OLD LOOP"
  echo "NO delta_v2 runtime"
  echo "NO DELTA_ORACLE runtime"
  echo "NO nexus_mobile runtime"
  echo ""
  echo "Purpose:"
  echo "Prepare legacy Delta scripts for later ARCHIVE_DO_NOT_RUN phase after final human review."
  echo ""
  echo "Canonical active core:"
  echo "/data/data/com.termux/files/home/delta_v4_5.py"
  echo ""
  echo "Canonical active memory:"
  echo "$CANONICAL_MEMORY"
  echo ""
  echo "Canonical memory proof:"
  if [ -f "$CANONICAL_MEMORY" ]; then
    ls -lah "$CANONICAL_MEMORY"
    sha256sum "$CANONICAL_MEMORY"
  else
    echo "MISSING"
  fi
  echo ""
  echo "Approved active files — not archive candidates:"
  echo "/data/data/com.termux/files/home/delta_v4_5.py"
  echo "/data/data/com.termux/files/home/ANDROID_CONTROL_CENTER.sh"
  echo "/data/data/com.termux/files/home/delta_legacy_compat_adapter.py"
  echo "/data/data/com.termux/files/home/delta_oracle_oneshot_adapter.py"
  echo "/data/data/com.termux/files/home/nexus_operator_adapter.py"
} > "$OUT"

write_candidate \
  "ARCHIVE_CANDIDATE_001_DELTA_V2" \
  "$HOME/delta_v2.py" \
  "BLOCK_FROM_RUNTIME_SPLIT_BRAIN_RISK" \
  "Uses /sdcard/delta_memory.json instead of canonical /sdcard/delta_v4_memory.json." \
  "ARCHIVE_DO_NOT_RUN_CANDIDATE_AFTER_FINAL_REVIEW"

write_candidate \
  "ARCHIVE_CANDIDATE_002_DELTA_V3" \
  "$HOME/delta_v3.py" \
  "LEGACY_SAME_MEMORY_MODULE" \
  "Older Delta module superseded by DeltaV45; uses same canonical memory but should not be active core." \
  "ARCHIVE_DO_NOT_RUN_CANDIDATE_AFTER_COMPATIBILITY_CONFIRMATION"

write_candidate \
  "ARCHIVE_CANDIDATE_003_DELTA_V4" \
  "$HOME/delta_v4.py" \
  "LEGACY_SAME_MEMORY_MODULE" \
  "Older Delta module superseded by DeltaV45; uses same canonical memory but should not be active core." \
  "ARCHIVE_DO_NOT_RUN_CANDIDATE_AFTER_COMPATIBILITY_CONFIRMATION"

write_candidate \
  "ARCHIVE_CANDIDATE_004_DELTA_ORACLE" \
  "$HOME/DELTA_ORACLE.py" \
  "BLOCK_FROM_RUNTIME_LOOP_RISK" \
  "Contains while True / sleep loop behavior; replaced by delta_oracle_oneshot_adapter.py." \
  "ARCHIVE_DO_NOT_RUN_CANDIDATE_AFTER_ADAPTER_FINAL_TEST"

write_candidate \
  "ARCHIVE_CANDIDATE_005_NEXUS_MOBILE" \
  "$HOME/nexus_mobile.py" \
  "BLOCK_FROM_RUNTIME_LOOP_RISK" \
  "Contains uncontrolled loop behavior; replaced by nexus_operator_adapter.py." \
  "ARCHIVE_DO_NOT_RUN_CANDIDATE_AFTER_ADAPTER_FINAL_TEST"

{
  echo ""
  echo "Adapter files that must remain active or available:"
  for f in \
    "$HOME/delta_v4_5.py" \
    "$HOME/ANDROID_CONTROL_CENTER.sh" \
    "$HOME/delta_legacy_compat_adapter.py" \
    "$HOME/delta_oracle_oneshot_adapter.py" \
    "$HOME/nexus_operator_adapter.py"
  do
    echo ""
    echo "File: $f"
    if [ -f "$f" ]; then
      ls -lah "$f"
      sha256sum "$f"
    else
      echo "MISSING"
    fi
  done

  echo ""
  echo "Reference decisions:"
  for f in \
    /sdcard/Download/DELTA_LEARNING_MODULE_CONSISTENCY_DECISION_20260514.txt \
    /sdcard/Download/DELTA_LEGACY_SCRIPT_RETIREMENT_REGISTER_20260514.txt \
    /sdcard/Download/DELTA_LEGACY_SCRIPT_HASH_BASELINE_20260514.txt \
    /sdcard/Download/DELTA_ADAPTER_TEST_REGISTER_20260514.txt \
    /sdcard/Download/DELTA_ADAPTER_RETIREMENT_LOCK_MANIFEST_20260514_222043.txt
  do
    echo ""
    echo "Reference: $f"
    if [ -f "$f" ]; then
      sha256sum "$f"
    else
      echo "MISSING"
    fi
  done

  echo ""
  echo "Final prep decision:"
  echo "Archive preparation manifest is created."
  echo "No file has been deleted."
  echo "No file has been moved."
  echo "No legacy file has been renamed."
  echo "Archive execution remains NOT AUTHORIZED."
  echo ""
  echo "Next allowed phase:"
  echo "ARCHIVE_DO_NOT_RUN_EXECUTION_MANIFEST_DRAFT"
  echo ""
  echo "Execution condition for future archive phase:"
  echo "Only after final human confirmation, preserve SHA256, copy to archive folder, verify copy hash, then optionally disable runtime references."
} >> "$OUT"

sha256sum "$OUT" > "$HASH"

echo "ARCHIVE_DO_NOT_RUN_PREP_MANIFEST CREATED"
echo "MANIFEST: $OUT"
echo "MANIFEST SHA256:"
cat "$HASH"
