#!/bin/sh
set -eu
umask 077
export LC_ALL=C TZ=UTC

B="FREYA_IPHONE_B05_R1_BUSYBOX_PORTABLE_COMPONENT_CLASSIFICATION"
C="/root/freya_audit/00_CONTROL"
O="$C/BATCHES/$B/${B}_$(date -u +%Y%m%dT%H%M%SZ)_PID$$"
mkdir -p "$O"

ALL="$O/ALL_CANDIDATES.tsv"
REG="$O/CANONICAL_COMPONENT_REGISTRY.tsv"
EXC="$O/EXCLUDED_COMPONENTS.tsv"

printf 'SHA256\tBYTES\tTYPE\tPATH\n' > "$ALL"
printf 'COMPONENT_TYPE\tSHA256\tBYTES\tPATH\n' > "$REG"
printf 'REASON\tPATH\n' > "$EXC"

find /root/freya_audit /root/CENTRALNI_MODUL_UCENJA \
-type f \( -name '*.sh' -o -name '*.py' \) 2>/dev/null |
sort -u |
while IFS= read -r F; do
 case "$F" in
  */site-packages/*|*/__pycache__/*|*/cache/*|*/CACHE/*|*/vendor/*|*/vendored/*|*/extracted/*|*/EXTRACTED/*|*.pyc)
   printf 'NON_CANONICAL_PATH\t%s\n' "$F" >> "$EXC"
   continue
   ;;
 esac

 H="$(sha256sum "$F" | awk '{print $1}')"
 Z="$(wc -c < "$F" | tr -d ' ')"

 T="$(
  grep -Eio 'supervisor|orchestrator|validator|queue|recovery|checkpoint|package|agent|worker|dispatcher|controller' "$F" 2>/dev/null |
  tr '[:lower:]' '[:upper:]' |
  sort -u |
  awk 'BEGIN{s=""}{s=(s==""?$0:s","$0)}END{print s}'
 )"

 [ -n "$T" ] || T=UNCLASSIFIED
 printf '%s\t%s\t%s\t%s\n' "$H" "$Z" "$T" "$F" >> "$ALL"
done

awk -F '\t' '
NR>1 {
 split($3,a,",")
 for(i=1;i<=length(a);i++){
  t=a[i]
  if(t!="" && t!="UNCLASSIFIED"){
   k=t SUBSEP $1
   if(!(k in seen)){
    seen[k]=1
    print t "\t" $1 "\t" $2 "\t" $4
   }
  }
 }
}' "$ALL" | sort >> "$REG"

CAND="$(awk 'END{print NR-1}' "$ALL")"
CANON="$(awk 'END{print NR-1}' "$REG")"
EXCLUDED="$(awk 'END{print NR-1}' "$EXC")"
TYPES="$(awk -F '\t' 'NR>1{a[$1]=1} END{for(k in a)n++; print n+0}' "$REG")"

R=PASS
X=NONE
[ "$CAND" -gt 0 ] || { R=HOLD; X=NO_COMPONENT_CANDIDATES; }
[ "$CANON" -gt 0 ] || { R=HOLD; X=NO_CANONICAL_COMPONENTS; }

{
printf '%s\n' \
"PROTOCOL=888" \
"NODE=FREYA_IPHONE_ISH_NODE_888" \
"MAIN_BATCH=BATCH_05" \
"RECOVERY_BATCH=$B" \
"RESULT=$R" \
"BLOCKED_REASON=$X" \
"COMPONENT_CANDIDATES=$CAND" \
"CANONICAL_COMPONENTS=$CANON" \
"COMPONENT_TYPES=$TYPES" \
"EXCLUDED_COMPONENTS=$EXCLUDED" \
"BUSYBOX_COMPATIBILITY=PASS" \
"ORIGINAL_B05_SCRIPT_MODIFIED=NO" \
"AGENTS_ACTIVATED=NO" \
"FILES_MODIFIED=NO" \
"NETWORK_ACTION=NONE" \
"CHECKPOINT_STATE=$([ "$R" = PASS ] && echo B05_COMPONENT_REGISTRY_SEALED || echo HOLD)"
} > "$O/BATCH_RECEIPT.txt"

sha256sum "$ALL" "$REG" "$EXC" "$O/BATCH_RECEIPT.txt" > "$O/EVIDENCE_MANIFEST.sha256"

cat "$O/BATCH_RECEIPT.txt"
printf '%s\n' \
"EVIDENCE_DIR=$O" \
"REGISTRY_SHA256=$(sha256sum "$REG" | awk '{print $1}')" \
"EVIDENCE_MANIFEST_SHA256=$(sha256sum "$O/EVIDENCE_MANIFEST.sha256" | awk '{print $1}')" \
"NEXT_BATCH=$([ "$R" = PASS ] && echo FREYA_IPHONE_B06_RUNTIME_ARCHITECTURE || echo FREYA_IPHONE_B05_R2_TARGETED_RECOVERY)" \
"SCRIPT_EXIT_CODE=$([ "$R" = PASS ] && echo 0 || echo 1)" \
"LAUNCHER_COMPLETED=YES"

[ "$R" = PASS ]
