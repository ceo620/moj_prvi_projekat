#!/data/data/com.termux/files/usr/bin/sh
# ANDROID_SCRIPT_HEALING_DOCTRINE_V3
# KEYWORD=VOLIM_TE
# ORIGINAL_IS_SACRED=YES
# REPAIR_ON_COPY_ONLY=YES
# SAFE_WRAPPER_ONLY=YES
# ID=H027
# ORIGINAL_NAME=export_dashboard_json.sh
# ORIGINAL_PATH=/data/data/com.termux/files/home/ANDROID_ARCHIVE_KNOWLEDGE_20260702_200007/02_REVIEW_ONLY_EXTRACTED/783fabe0565188ac24395e8187a74463182909526753f46ca6a7744ec09c6190_783fabe0565188ac24395e8187a74463182909526753f46ca6a7744ec09c6190_TITAN_FULL_MIGRATION_20260522_141658.tar.gz/TITAN_MIGRATION_20260522_141658/TITAN_ANDROID_EXECUTIVE_DB_V1_20260520_071216/03_EXPORTS/export_dashboard_json.sh
# ORIGINAL_SHA256=2daf7ce05922586d42ec6396f0a6fecad51f2e3aad68d520f3c52a5ead80c8f5
# HUMAN_GATE=ACTIVE

HUMAN_GATE="${HUMAN_GATE:-BLOCKED}"
if [ "$HUMAN_GATE" != "ALLOW_RUNTIME" ]; then
  echo "HUMAN_GATE_BLOCKED: Android V3 healed wrapper is static-only."
  exit 88
fi

echo "RUNTIME_NOT_IMPLEMENTED_YET: original payload preserved below for review."
exit 88

: <<'__ANDROID_VOLIM_TE_V3_PAYLOAD_H027_20260703_015331__'
#!/data/data/com.termux/files/usr/bin/bash

DB="/data/data/com.termux/files/home/TITAN_ANDROID_EXECUTIVE_DB_V1_20260520_071216/01_DB/titan_executive.db"
OUT="/data/data/com.termux/files/home/TITAN_ANDROID_EXECUTIVE_DB_V1_20260520_071216/05_DASHBOARD_BRIDGE/executive_db_dashboard_data.json"

tasks=$(sqlite3 "$DB" "SELECT count(*) FROM tasks WHERE status NOT LIKE 'DONE%';")
opps=$(sqlite3 "$DB" "SELECT count(*) FROM opportunities;")
strategies=$(sqlite3 "$DB" "SELECT count(*) FROM strategies;")
followups=$(sqlite3 "$DB" "SELECT count(*) FROM followups WHERE status NOT LIKE 'DONE%';")
notes=$(sqlite3 "$DB" "SELECT count(*) FROM notes;")
risks=$(sqlite3 "$DB" "SELECT count(*) FROM risks WHERE status NOT LIKE 'DONE%';")
gaps=$(sqlite3 "$DB" "SELECT count(*) FROM evidence_gaps WHERE status NOT LIKE 'DONE%';")
decisions=$(sqlite3 "$DB" "SELECT count(*) FROM decisions;")

cat > "$OUT" <<JSON
{
  "generated_at": "$(date '+%Y-%m-%d %H:%M:%S')",
  "mode": "LOCAL_ONLY_STATIC_ONLY_REPORT_ONLY",
  "db": "/data/data/com.termux/files/home/TITAN_ANDROID_EXECUTIVE_DB_V1_20260520_071216/01_DB/titan_executive.db",
  "open_tasks": "$tasks",
  "business_opportunities": "$opps",
  "strategy_candidates": "$strategies",
  "open_followups": "$followups",
  "notes": "$notes",
  "open_risks": "$risks",
  "evidence_gaps": "$gaps",
  "decisions": "$decisions"
}
JSON

echo "DB_DASHBOARD_JSON_CREATED=$OUT"
cat "$OUT"
__ANDROID_VOLIM_TE_V3_PAYLOAD_H027_20260703_015331__
