#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="/data/data/com.termux/files/home/FREYA_ANDROID_TABLET_FORENSIC_REVIVAL_20260705_150231"
OUT="$ROOT/22_ANDROID_SAFE_REVIVAL_PLAN/MANIFEST_ONLY_EXPORT_PREVIEW/RUN_OUTPUT"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

MAN="$OUT/EXPORT_PREVIEW_MANIFEST_$TS.tsv"

echo "candidate_idsource_pathexists_nowtypefile_countarchive_allowed_nowcopy_allowed_nowhuman_gate_required" > "$MAN"

i=0
for p in \
"$ROOT/20_RUNTIME_STATIC_REVIEW_LOCK" \
"$ROOT/21_DRY_RUN_PATCH_DESIGNS" \
"$ROOT/22_ANDROID_SAFE_REVIVAL_PLAN" \
"$ROOT/08_HUMAN_GATE" \
"$ROOT/12_NON_RUNTIME_FREYA_SSOT_INDEX"
do
  i=$((i+1))
  if [ -d "$p" ]; then
    cnt="$(find "$p" -type f 2>/dev/null | wc -l)"
    printf "%s\t%s\tYES\tDIR\t%s\tNO\tNO\tYES\n" "$i" "$p" "$cnt" >> "$MAN"
  elif [ -f "$p" ]; then
    printf "%s\t%s\tYES\tFILE\t1\tNO\tNO\tYES\n" "$i" "$p" >> "$MAN"
  else
    printf "%s\t%s\tNO\tMISSING\t0\tNO\tNO\tYES\n" "$i" "$p" >> "$MAN"
  fi
done

sha256sum "$MAN" > "$MAN.sha256"

echo "===== MANIFEST ONLY EXPORT PREVIEW — PROTOKOL 889 ====="
echo "HUMAN_GATE=ACTIVE"
echo "MODE=MANIFEST_ONLY"
echo "ARCHIVE_CREATED=NO"
echo "COPY_DONE=NO"
echo "DELETE_DONE=NO"
echo "MOVE_DONE=NO"
echo "RENAME_DONE=NO"
echo "ORIGINALS_CHANGED=NO"
echo
column -t -s "$(printf '\t')" "$MAN" 2>/dev/null || cat "$MAN"
echo
echo "[MANIFEST_SHA256]"
cat "$MAN.sha256"
echo
echo "SCRIPT_EXECUTED=YES_MANIFEST_ONLY"
echo "DANGEROUS_RUNTIME_EXECUTED=NO"
echo "DAEMON_STARTED=NO"
echo "NEXT_SAFE_STEP=CREATE_ANDROID_RELEASE_GATE_CARD"
echo "===== END MANIFEST ONLY EXPORT PREVIEW ====="
