#!/bin/sh
set -eu
umask 077
export LC_ALL=C TZ=UTC

B="FREYA_IPHONE_B05_COMPONENT_CLASSIFICATION"
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
  grep -Eio \
  'supervisor|orchestrator|validator|queue|recovery|checkpoint|package|agent|worker|dispatcher|controller' \
  "$F" 2>/dev/null |
  tr '[:lower:]' '[:upper:]' |
  sort -u |
  paste -sd, - 2>/dev/null || true
 )"

 [ -n "$T" ] || T=UNCLASSIFIED
 printf '%s\t%s\t%s\t%s\n' "$H" "$Z" "$T" "$F" >> "$ALL"
done

awk -F '\t' '
NR==1{next}
{
 split($3,a,",")
 for(i in a){
  t=a[i]
  if(t!="UNCLASSIFIED"){
   key=t FS $1
   if(!(key in seen)){
    seen[key]=1
    print t FS $1 FS $2 FS $4
   }
  }
 }
}' "$ALL" | sort -t '' -k1,1 -k2,2 >> "$REG"

CAND="$(awk 'END{print NR-1}' "$ALL")"
CANON="$(awk 'END{print NR-1}' "$REG")"
EXCLUDED="$(awk 'END{print NR-1}' "$EXC")"
TYPES="$(awk -F '\t' 'NR>1{seen[$1]=1} END{for(k in seen)n++; print n+0}' "$REG")"

R=PASS
X=NONE
[ "$CAND" -gt 0 ] || { R=HOLD; X=NO_COMPONENT_CANDIDATES; }
[ "$CANON" -gt 0 ] || { R=HOLD; X=NO_CANONICAL_COMPONENTS; }

{
printf '%s\n' \
"PROTOCOL=888" \
"NODE=FREYA_IPHONE_ISH_NODE_888" \
"BATCH_ID=$B" \
"RESULT=$R" \
"BLOCKED_REASON=$X" \
"COMPONENT_CANDIDATES=$CAND" \
"CANONICAL_COMPONENTS=$CANON" \
"COMPONENT_TYPES=$TYPES" \
"EXCLUDED_COMPONENTS=$EXCLUDED" \
"EXCLUSION_POLICY=SITE_PACKAGES_CACHE_VENDORED_EXTRACTED" \
"AGENTS_ACTIVATED=NO" \
"FILES_MODIFIED=NO" \
"NETWORK_ACTION=NONE"
} > "$O/BATCH_RECEIPT.txt"

sha256sum "$O"/*.txt "$O"/*.tsv > "$O/EVIDENCE_MANIFEST.sha256"

cat "$O/BATCH_RECEIPT.txt"
printf '%s\n' \
"EVIDENCE_DIR=$O" \
"EVIDENCE_MANIFEST_SHA256=$(sha256sum "$O/EVIDENCE_MANIFEST.sha256" | awk '{print $1}')" \
"CHECKPOINT_STATE=$([ "$R" = PASS ] && echo COMPONENT_REGISTRY_SEALED || echo HOLD)" \
"NEXT_BATCH=$([ "$R" = PASS ] && echo FREYA_IPHONE_B06_RUNTIME_ARCHITECTURE || echo FREYA_IPHONE_B05_R1_TARGETED_RECOVERY)" \
"SCRIPT_EXIT_CODE=$([ "$R" = PASS ] && echo 0 || echo 1)" \
"LAUNCHER_COMPLETED=YES"

[ "$R" = PASS ]
