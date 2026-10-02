#!/usr/bin/env python3
import os,json,hashlib,stat,platform,re
from pathlib import Path
P=888;NODE="FREYA_IPHONE_ISH_NODE_888";B="IPHONE_888_BATCH_04R1_CONTRACT_SET_RECONCILIATION_20260921";AUTH="DANIJELA_DJUROVIC_KESKIN"
BASE=Path("/root/FREYA_SEGMENTS_014_d_20s9r2/PAYLOAD/AGENT_CONTRACTS/PAYLOAD/AGENT_CONTRACTS")
def out(**x): print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def parse(q):
 t=q.read_text(errors="replace"); d={}
 for line in t.splitlines():
  m=re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$',line)
  if m:d[m.group(1).upper()]=m.group(2).strip().strip('"').strip("'")
 return d
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():
 out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP");raise SystemExit(2)
out(event="IDENTITY",hostname=platform.node(),uid=os.getuid(),alpine=a.read_text().strip(),kernel=platform.release())
if not BASE.is_dir():
 out(STATUS="HOLD",REASON="AGENT_CONTRACT_SET_ROOT_MISSING",path=str(BASE),NEXT="STOP");raise SystemExit(3)
agents=[]
for d in sorted((x for x in BASE.iterdir() if x.is_dir()),key=lambda x:x.name):
 parts={}; hashes={}
 for name in ("DOCTRINE.env","INPUT_CONTRACT.env","OUTPUT_CONTRACT.env"):
  q=d/name
  if q.is_file():
   parts[name]=parse(q);hashes[name]=sha(q)
 merged={}
 for x in parts.values(): merged.update(x)
 aid=merged.get("AGENT_ID",d.name); an=merged.get("AGENT_NAME","")
 # Contract semantics may be distributed across the three files.
 authfun=merged.get("AUTHORIZED_FUNCTION") or merged.get("FUNCTION") or merged.get("AUTHORIZED_SCOPE") or merged.get("ROLE")
 doctrine=merged.get("DOCTRINE") or merged.get("DOCTRINE_ID") or merged.get("DOCTRINE_VERSION")
 inp=merged.get("INPUT_CONTRACT") or ("PRESENT_FILE" if "INPUT_CONTRACT.env" in parts else None)
 oup=merged.get("OUTPUT_CONTRACT") or ("PRESENT_FILE" if "OUTPUT_CONTRACT.env" in parts else None)
 hg=merged.get("HUMAN_GATE")
 ext=merged.get("EXTERNAL_SEND")
 auto=merged.get("AUTO_SEND")
 missing=[]
 for k,v in (("AGENT_NAME",an),("AUTHORIZED_FUNCTION",authfun),("DOCTRINE",doctrine),("INPUT_CONTRACT",inp),("OUTPUT_CONTRACT",oup),("HUMAN_GATE",hg)):
  if not v:missing.append(k)
 status="CONTRACT_SET_COMPLETE" if not missing else "HOLD=INCOMPLETE_AGENT_CONTRACT_SET"
 out(event="AGENT_CONTRACT_SET",agent_id=aid,agent_name=an,path=str(d),files=sorted(parts),sha256=hashes,
     authorized_function=authfun,doctrine=doctrine,input_contract=inp,output_contract=oup,human_gate=hg,
     EXTERNAL_SEND=ext or "NOT_EXPLICIT",AUTO_SEND=auto or "NOT_EXPLICIT",missing=missing,status=status)
 agents.append((aid,missing,ext,auto))
out(event="SUMMARY",agent_directories=len(agents),complete_contract_sets=sum(not x[1] for x in agents),
 incomplete_contract_sets=sum(bool(x[1]) for x in agents),
 external_send_deny=sum((x[2] or "").upper()=="DENY" for x in agents),
 auto_send_deny=sum((x[3] or "").upper()=="DENY" for x in agents))
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",STATUS="CONTRACT_SET_RECONCILIATION_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
