#!/usr/bin/env python3
import os,hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
R=Path("/root/FREYA_RAD_888"); AF=R/"05_SISTEM/AGENT_FACTORY"; AP=AF/"AUTOPILOT"
WR=AP/"IPHONE_888_AUTOPILOT.sh"; CR=Path("/etc/crontabs/root")
OLD=Path("/root/IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env")
OUT=Path("/root/IPHONE_888_AUTOPILOT_FINAL_SEAL_20260922.env")
EXP_WR="d3d409532b346c81e54727a1df2f0631eb90d551287c132757cacb76d64c8935"
EXP_CR="857ab32f8bcbd84c117ebc5abc3ce9164b56cf63d6bd8e9fdcf9c723b1f80915"
EXP_OLD="13ee3ff93a6a9a23d178b8164a868609e06f613acccf6072c80095b9d31bd775"
MARK="# PROTOCOL888_IPHONE_AUTOPILOT"
def emit(e,**k):print(json.dumps({"event":e,**k},ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with open(q,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def hold(r,**k):emit("HOLD",reason=r,**k);raise SystemExit(2)
emit("BEGIN",PROTOCOL=888,BATCH="IPHONE_888_AUTOPILOT_BATCH_06_FINAL_SEAL_20260922",
 HUMAN_GATE="ACTIVE",DEFAULT_MODE="DENY",FAIL_CLOSED="YES",SSOT="SOVEREIGN",
 EVIDENCE_FIRST="YES",SCOPE_BOUND="YES",NETWORK="DENY",DELETE="DENY",ZIP_CREATE="DENY")
for q,e,n in [(WR,EXP_WR,"WRAPPER"),(CR,EXP_CR,"CRON"),(OLD,EXP_OLD,"PRIOR_SEAL")]:
 if not q.is_file() or q.is_symlink():hold("PIN_TYPE",component=n)
 a=sha(q);emit("PIN",component=n,expected=e,actual=a,match=a==e)
 if a!=e:hold("PIN_HASH",component=n)
if CR.read_text(errors="replace").count(MARK)!=1:hold("CRON_MARKER")
ps=subprocess.run(["ps","aux"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout
crond=[x for x in ps.splitlines() if "/usr/sbin/crond" in x]
if not crond:hold("CROND_NOT_RUNNING")
# Final runtime canary and source stability
inp=R/"00_ULAZ"; before={q.name:sha(q) for q in inp.iterdir() if q.is_file() and not q.is_symlink()}
cp=subprocess.run([str(WR)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
if cp.returncode!=0:hold("FINAL_CANARY",rc=cp.returncode,stdout=cp.stdout[-4000:])
after={q.name:sha(q) for q in inp.iterdir() if q.is_file() and not q.is_symlink()}
if before!=after:hold("SOURCE_HASH_CHANGED")
if OUT.exists():hold("FINAL_SEAL_ALREADY_EXISTS_NO_OVERWRITE",path=str(OUT),sha256=sha(OUT) if OUT.is_file() else None)
lines=[
"PROTOCOL=888",
"NODE=FREYA_IPHONE_ISH_NODE_888",
"DEVICE=IPHONE",
"ENVIRONMENT=ISH_ALPINE",
"HUMAN_GATE=ACTIVE",
"HUMAN_GATE_AUTHORITY=DANIJELA_DJUROVIC_KESKIN",
"DEFAULT_MODE=DENY",
"FAIL_CLOSED=YES",
"SSOT=SOVEREIGN",
"SSOT_PATH=/root/FREYA_RAD_888",
"CANONICAL_INPUT=/root/FREYA_RAD_888/00_ULAZ",
"CANONICAL_OUTPUT=/root/FREYA_RAD_888/01_PROIZVODI",
"AUTOPILOT=ACTIVE",
"AUTOPILOT_SCOPE=LOCAL_ONLY_WHILE_ISH_RUNTIME_AVAILABLE",
"SCHEDULER=ALPINE_CROND",
"SCHEDULE=EVERY_15_MINUTES",
"CROND_PROOF=PASS",
"WRAPPER_STABILITY=PASS",
"CANARY=PASS",
"SOURCE_HASH_STABLE=YES",
"WRAPPER_SHA256="+EXP_WR,
"CRON_SHA256="+EXP_CR,
"PRIOR_LOCAL_PRODUCTION_SEAL_SHA256="+EXP_OLD,
"NETWORK_ACTIONS=DENY",
"AUTO_EXTERNAL_SEND=DENY",
"AUTO_SIGN=DENY",
"ASUS_HANDOFF=HUMAN_GATE_REQUIRED",
"NEW_AGENTS=0",
"ZIP_CREATION=DENY",
"DELETIONS_BY_AUTOPILOT=DENY",
"CLEANUP=SEPARATE_HUMAN_GATE",
"IOS_BACKGROUND_LIMITATION=AUTOPILOT_NOT_GUARANTEED_WHEN_IOS_SUSPENDS_ISH",
"FINAL_STATUS=PASS",
"REOPEN_WITHOUT_NEW_INCIDENT=DENY",
"SEALED_UTC="+datetime.now(timezone.utc).isoformat(),
"NEXT=STOP"
]
data=("\n".join(lines)+"\n").encode()
fd=os.open(str(OUT),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
rb=OUT.read_bytes()
if rb!=data:hold("SEAL_READBACK")
h=hashlib.sha256(rb).hexdigest()
emit("FINAL_SEAL_CREATED",path=str(OUT),bytes=len(rb),sha256=h,readback="PASS")
emit("END",RESULT="PASS_FINAL_SEAL",AUTOPILOT="ACTIVE_LOCAL_WHILE_ISH_RUNTIME_AVAILABLE",
 FINAL_SEAL_PATH=str(OUT),FINAL_SEAL_SHA256=h,DELETIONS=0,NETWORK_ACTIONS=0,ZIP_CREATED=0,NEXT="STOP")
