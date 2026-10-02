#!/usr/bin/env python3
# PROTOCOL 888 — repair scheduler truth before final seal.
import os,hashlib,json,subprocess,time
from pathlib import Path
R=Path("/root/FREYA_RAD_888"); AF=R/"05_SISTEM/AGENT_FACTORY"; AP=AF/"AUTOPILOT"
WR=AP/"IPHONE_888_AUTOPILOT.sh"; ST=AP/"STATE"; CR=Path("/etc/crontabs/root")
MARK="# PROTOCOL888_IPHONE_AUTOPILOT"
EXPECTED_WR="d3d409532b346c81e54727a1df2f0631eb90d551287c132757cacb76d64c8935"
EXPECTED_CR="857ab32f8bcbd84c117ebc5abc3ce9164b56cf63d6bd8e9fdcf9c723b1f80915"
def emit(e,**k): print(json.dumps({"event":e,**k},sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with open(q,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def hold(r,**k):emit("HOLD",reason=r,**k);raise SystemExit(2)
emit("BEGIN",PROTOCOL=888,BATCH="IPHONE_888_AUTOPILOT_BATCH_05_SCHEDULER_REPAIR_STABILITY_20260922",HUMAN_GATE="ACTIVE",DEFAULT_MODE="DENY",FAIL_CLOSED="YES",NETWORK="DENY",DELETION="DENY",ZIP="DENY")
if not WR.is_file() or sha(WR)!=EXPECTED_WR:hold("WRAPPER_PIN")
if not CR.is_file() or sha(CR)!=EXPECTED_CR:hold("CRON_PIN")
if CR.read_text(errors="replace").count(MARK)!=1:hold("CRON_MARKER_COUNT")
# iSH may not retain crond as a background daemon. Prove behavior rather than assume it.
def procs():
 cp=subprocess.run(["ps","aux"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return [x for x in cp.stdout.splitlines() if "crond" in x and "grep" not in x]
before=procs(); emit("CROND_BEFORE",matches=before)
start=subprocess.run(["/usr/sbin/crond"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
time.sleep(1)
after=procs(); emit("CROND_START_ATTEMPT",rc=start.returncode,stdout=start.stdout,matches_after=after)
# Direct scheduler-equivalent proof: wrapper itself must remain healthy and source-stable.
inp=R/"00_ULAZ"; bh={q.name:sha(q) for q in inp.iterdir() if q.is_file() and not q.is_symlink()}
runs=[]
for i in range(2):
 cp=subprocess.run([str(WR)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
 log=(ST/"LAST_RUN.log").read_text(errors="replace") if (ST/"LAST_RUN.log").is_file() else ""
 runs.append({"sample":i+1,"rc":cp.returncode,"stdout":cp.stdout[-4000:],"last_run":log[:4000]})
 if cp.returncode!=0:hold("WRAPPER_STABILITY_FAIL",sample=i+1,rc=cp.returncode)
emit("WRAPPER_STABILITY",samples=runs)
ah={q.name:sha(q) for q in inp.iterdir() if q.is_file() and not q.is_symlink()}
if bh!=ah:hold("SOURCE_HASH_CHANGED")
persistent=bool(after)
# Truthful scheduler classification.
if persistent:
 status="PASS_CRON_DAEMON_AND_WRAPPER_STABLE"; mode="CRON_EVERY_15_MIN_WHILE_ISH_AVAILABLE"
else:
 status="PASS_WRAPPER_STABLE_CROND_NOT_PERSISTENT"; mode="ENTRYPOINT_READY_IOS_TRIGGER_REQUIRED"
emit("SCHEDULER_DECISION",crond_persistent=persistent,status=status,autopilot_mode=mode,
 cron_config_preserved=True,wrapper_sha256=sha(WR),cron_sha256=sha(CR))
emit("END",RESULT=status,SOURCE_HASH_STABLE="YES",NETWORK_ACTIONS=0,DELETIONS=0,ZIP_CREATED=0,
 FINAL_SEAL="NOT_YET_ISSUED",NEXT="RETURN_COMPLETE_OUTPUT_FOR_BATCH_06_FINAL_SEAL")
