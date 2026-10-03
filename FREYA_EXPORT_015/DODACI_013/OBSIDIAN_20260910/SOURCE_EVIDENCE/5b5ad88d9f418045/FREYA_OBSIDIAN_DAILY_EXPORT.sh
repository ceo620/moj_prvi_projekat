#!/bin/sh
R=/root/FREYA_IPHONE_ISH_NODE_888
C="$R/17_PERSONAL_CONTROL_TOWER"
O="$R/19_APP_BRIDGES/OBSIDIAN_EXPORT"
A="$C/REGISTERS/ACTION_REGISTER.tsv"
K="$C/REGISTERS/CONTACT_ACTION_REGISTER.tsv"
S="$C/REGISTERS/CONTENT_CALENDAR.tsv"
B="$C/REGISTERS/DEVELOPMENT_BACKLOG.tsv"
D="$(date +%F)"
F="$O/FREYA_DAILY_MATRIX_${D}.md"
T="$(printf '\t')"

{
  printf '# FREYA Daily Matrix — %s\n\n' "$D"
  printf '## Hitno i danas\n\n'
  awk -F "$T" -v d="$D" 'NR>1&&$7!="DONE"&&($5=="CRITICAL"||$6==d){printf "- [ ] **%s** — %s | Status: %s | Next: %s\n",$2,$3,$7,$8}' "$A"
  printf '\n## Kome se javiti\n\n'
  awk -F "$T" -v d="$D" 'NR>1&&$11!="DONE"&&$8!=""&&$8<=d{printf "- **%s / %s** — %s | Projekat: %s | Predlog: %s\n",$2,$4,$5,$6,$9}' "$K"
  printf '\n## Objave\n\n'
  awk -F "$T" -v d="$D" 'NR>1&&$9!="POSTED_MANUALLY"&&$8!=""&&$8<=d{printf "- **%s / %s** — %s | Status: %s\n",$2,$3,$4,$9}' "$S"
  printf '\n## Razvoj iPhone čvora\n\n'
  awk -F "$T" 'NR>1&&$6!="DONE"{printf "- [ ] **%s** — %s | Prioritet: %s | Next: %s\n",$1,$4,$5,$8}' "$B"
  printf '\n## Human Gate\n\n'
  printf -- '- Auto email: NO\n- Auto post: NO\n- Auto signature: NO\n- Network action: NONE\n'
} >"$F"

printf 'RESULT=PASS\nOBSIDIAN_MARKDOWN=%s\nNETWORK_ACTION=NONE\nAUTO_POST=NO\nAUTO_SEND=NO\n' "$F"
