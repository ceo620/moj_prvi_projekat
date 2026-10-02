#!/usr/bin/env python3
import os,hashlib,json,subprocess
from pathlib import Path
R=Path("/root/FREYA_RAD_888"); AF=R/"05_SISTEM/AGENT_FACTORY"; AP=AF/"AUTOPILOT"; WR=AP/"IPHONE_888_AUTOPILOT.sh"; STATE=AP/"STATE"; CRON=Path("/etc/crontabs/root")
MARK="# PROTOCOL888_IPHONE_AUTOPILOT"
LINE="*/15\t*\t*\t*\t*\t/root/FREYA_RAD_888/05_SISTEM/AGENT_FACTORY/AUTOPILOT/IPHONE_888_AUTOPILOT.sh "+MARK
pins={
AF/"RUNTIME/integrated_runtime_00_ulaz.sh":"96d8ddba473c6a808a30cdbb46a73e79dbcc8b05eca36496190fe6e1b0274a67",
AF/"ROUTER/queue_binder.sh":"45a742625b793b0b827e0928bfabc6bc025f89de299b540199862c51cdc5fc8c",
AF/"RUNTIME/document_processor.py":"8236c31e63747752248df5c70c13e7d3786dd53336387bb115a63fef5cc8f64d",
AF/"CONTRACTS/execution_allowlist.tsv":"7468c027470d8eeb33059367240cfadfbf134783d793056f9b1741e920a13550",
AF/"CONTRACTS/AGENT_ID":"36c34970bdc66ef019444bd967faef656585ab94fb11a47ecf7fcd7bdd8e01e6",
Path("/root/IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env"):"13ee3ff93a6a9a23d178b8164a868609e06f613acccf6072c80095b9d31bd775"}
def emit(e,**k): print(json.dumps({"event":e,**k},ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with open(q,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def hold(r,**k): emit("HOLD",reason=r,**k); raise SystemExit(2)
emit("BEGIN",PROTOCOL=888,BATCH="IPHONE_888_AUTOPILOT_BATCH_04_SCOPED_ACTIVATION_20260922",HUMAN_GATE="APPROVED",DEFAULT_MODE="DENY",FAIL_CLOSED="YES",SSOT="SOVEREIGN",NETWORK="DENY",ZIP_CREATION="DENY",DELETION="DENY",NEW_AGENTS=0)
if os.getuid()!=0 or not R.is_dir(): hold("IDENTITY_OR_SSOT_GATE")
for q,e in pins.items():
 if not q.is_file() or q.is_symlink(): hold("PIN_FILE_GATE",path=str(q))
 a=sha(q); emit("PIN",path=str(q),expected=e,actual=a,match=a==e)
 if a!=e: hold("PIN_HASH_MISMATCH",path=str(q))
inp=R/"00_ULAZ"; before={q.name:sha(q) for q in inp.iterdir() if q.is_file() and not q.is_symlink()}
if len(before)!=14: hold("INPUT_COUNT_CHANGED",count=len(before))
lock=R/"RUN.lock"
if not lock.is_file() or lock.stat().st_size!=0: hold("RUN_LOCK_UNEXPECTED")
old=CRON.read_text(errors="replace")
if MARK in old or WR.exists(): hold("AUTOPILOT_ALREADY_PRESENT")
AP.mkdir(mode=0o700); STATE.mkdir(mode=0o700)
wrapper="""#!/bin/sh
set -eu
R=/root/FREYA_RAD_888
AF="$R/05_SISTEM/AGENT_FACTORY"
S="$AF/AUTOPILOT/STATE"
exec 9>"$S/runtime.lock"
flock -n 9 || exit 0
printf '%s  %s\\n' \\
'96d8ddba473c6a808a30cdbb46a73e79dbcc8b05eca36496190fe6e1b0274a67' "$AF/RUNTIME/integrated_runtime_00_ulaz.sh" \\
'45a742625b793b0b827e0928bfabc6bc025f89de299b540199862c51cdc5fc8c' "$AF/ROUTER/queue_binder.sh" \\
'8236c31e63747752248df5c70c13e7d3786dd53336387bb115a63fef5cc8f64d' "$AF/RUNTIME/document_processor.py" \\
'7468c027470d8eeb33059367240cfadfbf134783d793056f9b1741e920a13550' "$AF/CONTRACTS/execution_allowlist.tsv" \\
'36c34970bdc66ef019444bd967faef656585ab94fb11a47ecf7fcd7bdd8e01e6' "$AF/CONTRACTS/AGENT_ID" \\
'13ee3ff93a6a9a23d178b8164a868609e06f613acccf6072c80095b9d31bd775' "/root/IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env" | sha256sum -c - >/dev/null 2>&1 || { echo RESULT=HOLD_PIN_MISMATCH >"$S/LAST_RUN.log"; exit 20; }
A="$(cat "$AF/CONTRACTS/AGENT_ID")"
[ "$A" = DAILY_PRIORITY ] || { echo RESULT=HOLD_AGENT_ID >"$S/LAST_RUN.log"; exit 21; }
RUN="$S/RUN_$(date -u +%Y%m%dT%H%M%SZ)_$$"
mkdir -p "$RUN"
set +e
sh "$AF/RUNTIME/integrated_runtime_00_ulaz.sh" "$R/00_ULAZ" "$AF/RUNTIME/document_processor.py" "$AF/ROUTER/queue_binder.sh" "$AF/CONTRACTS/execution_allowlist.tsv" "$A" "$RUN" >"$S/.last.$$" 2>&1
rc=$?
set -e
if [ "$rc" -eq 4 ]; then echo RESULT=PASS_IDLE_NO_NEW_INPUT >"$S/LAST_RUN.log"; rm -f "$S/.last.$$"; exit 0; fi
cat "$S/.last.$$" >"$S/LAST_RUN.log"; rm -f "$S/.last.$$"
exit "$rc"
"""
WR.write_text(wrapper,encoding="utf-8",newline="\n"); os.chmod(WR,0o700)
emit("WRAPPER_CREATED",path=str(WR),bytes=WR.stat().st_size,sha256=sha(WR))
new=old+("" if old.endswith("\n") else "\n")+LINE+"\n"
tmp=CRON.with_name("root.protocol888.tmp")
fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,"w") as f: f.write(new); f.flush(); os.fsync(f.fileno())
os.replace(tmp,CRON)
emit("CRON_ACTIVATED",sha256=sha(CRON),line=LINE)
if subprocess.run(["sh","-c","pgrep -x crond >/dev/null 2>&1"]).returncode!=0: subprocess.run(["/usr/sbin/crond"],check=True)
emit("CROND",running=subprocess.run(["sh","-c","pgrep -x crond >/dev/null 2>&1"]).returncode==0)
cp=subprocess.run([str(WR)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
emit("CANARY",rc=cp.returncode,stdout=cp.stdout[-12000:])
if cp.returncode!=0: hold("CANARY_FAILED",rc=cp.returncode)
after={q.name:sha(q) for q in inp.iterdir() if q.is_file() and not q.is_symlink()}
if before!=after: hold("SOURCE_HASH_CHANGED")
log=STATE/"LAST_RUN.log"; emit("LAST_RUN",content=log.read_text(errors="replace")[:12000] if log.is_file() else None)
emit("END",RESULT="PASS_SCOPED_AUTOPILOT_ACTIVATED",AUTOPILOT="ACTIVE_LOCAL_WHILE_ISH_RUNTIME_AVAILABLE",SCHEDULE="EVERY_15_MINUTES_VIA_ALPINE_CRON",SOURCE_HASH_STABLE="YES",NETWORK_ACTIONS=0,DELETIONS=0,ZIP_CREATED=0,AUTO_SIGN="DENY",AUTO_EXTERNAL_SEND="DENY",ASUS_HANDOFF="HUMAN_GATE_REQUIRED",NEXT="RETURN_COMPLETE_OUTPUT_FOR_BATCH_05_STABILITY_AND_FINAL_SEAL")
