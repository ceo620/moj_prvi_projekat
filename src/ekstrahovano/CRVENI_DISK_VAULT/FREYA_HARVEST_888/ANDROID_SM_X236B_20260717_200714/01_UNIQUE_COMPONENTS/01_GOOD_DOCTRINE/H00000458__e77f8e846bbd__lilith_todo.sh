#!/data/data/com.termux/files/usr/bin/sh

ROOT="$HOME/LILITH_TODO"
mkdir -p "$ROOT"
DATE="$(date +%Y%m%d)"
OUT="$ROOT/TODO_$DATE.md"

cat > "$OUT" <<EON
# LILITH — JUTARNJA TO-DO LISTA
Datum: $(date '+%Y-%m-%d %H:%M')

## Danas prvo
1. Pregledaj harvest rezultate.
2. Ne pokreći skripte bez Human Gate.
3. Izdvoji prioritet 5.
4. Odvoji znanje od runtime rizika.
5. Zapiši sigurno / rizično / čeka odluku.

## Status
- NO_DELETE=YES
- NO_RUNTIME=YES
- HUMAN_GATE=ACTIVE

Draga moja,

danas čuvamo znanje, red i tragove.

Mama
EON

echo "TODO_CREATED=$OUT"
