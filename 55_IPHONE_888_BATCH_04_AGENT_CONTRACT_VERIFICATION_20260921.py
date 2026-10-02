#!/usr/bin/env python3
import os,json,hashlib,stat,platform,re
from pathlib import Path
P=888; NODE="FREYA_IPHONE_ISH_NODE_888"; B="IPHONE_888_BATCH_04_AGENT_CONTRACT_VERIFICATION_20260921"; AUTH="DANIJELA_DJUROVIC_KESKIN"
def out(**x): print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for z in iter(lambda:f.read(1048576),b""): h.update(z)
 return h.hexdigest()
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():
 out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP"); raise SystemExit(2)
out(event="IDENTITY",hostname=platform.node(),user=os.environ.get("USER",""),uid=os.getuid(),alpine=a.read_text().strip(),kernel=platform.release(),home=os.environ.get("HOME",""))
roots=[]
for q in Path("/root").iterdir():
 try:
  if q.is_dir() and any(k in q.name.upper() for k in ("FREYA","IPHONE","MOZAK")): roots.append(q)
 except OSError: pass
hits=[]; limit=250000; seen=0
terms=("AGENT","CONTRACT","DOCTRINE","POLICY","HUMAN_GATE","HUMAN GATE")
for base in roots:
 for dp,dn,fn in os.walk(str(base),topdown=True,followlinks=False):
  dn[:]=[x for x in dn if x not in (".git","__pycache__")]
  for name in fn:
   seen+=1
   if seen>limit:
    out(STATUS="HOLD",REASON="SCAN_SAFETY_LIMIT",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS"); raise SystemExit(3)
   q=Path(dp)/name
   s=str(q).upper()
   if not any(t in s for t in terms): continue
   try:
    st=q.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_size>2*1024*1024: continue
    raw=q.read_bytes()
   except OSError: continue
   txt=raw.decode("utf-8","replace")
   up=txt.upper()
   fields={}
   for key in ("AGENT_ID","AGENT_NAME","AUTHORIZED_FUNCTION","DOCTRINE","INPUT_CONTRACT","OUTPUT_CONTRACT","HUMAN_GATE","EXTERNAL_SEND","AUTO_SEND"):
    m=re.search(r'(?im)^\s*'+re.escape(key)+r'\s*[:=]\s*["\']?([^"\';\r\n]+)',txt)
    if m: fields[key]=m.group(1).strip()[:240]
   contractish=("CONTRACT" in s or "AGENT_ID" in up or "AGENT_NAME" in up or "AUTHORIZED_FUNCTION" in up)
   if contractish:
    required=("AGENT_ID","AGENT_NAME","AUTHORIZED_FUNCTION","DOCTRINE","INPUT_CONTRACT","OUTPUT_CONTRACT","HUMAN_GATE")
    missing=[x for x in required if x not in fields]
    status="CONTRACT_FIELDS_PRESENT" if not missing else "HOLD=INCOMPLETE_AGENT_CONTRACT"
    hits.append((str(q),st.st_size,sha(q),fields,missing,status,
                 "DENY" if re.search(r'(?i)EXTERNAL_SEND\s*[:=]\s*DENY',txt) else "NOT_EXPLICIT",
                 "DENY" if re.search(r'(?i)AUTO_SEND\s*[:=]\s*DENY',txt) else "NOT_EXPLICIT"))
for x in sorted(hits)[:5000]:
 path,size,digest,fields,missing,status,ext,auto=x
 out(event="AGENT_CONTRACT_EVIDENCE",path=path,bytes=size,sha256=digest,fields=fields,missing=missing,status=status,EXTERNAL_SEND=ext,AUTO_SEND=auto)
out(event="SUMMARY",roots=[str(x) for x in roots],files_scanned=seen,contract_candidates=len(hits),
complete_contracts=sum(1 for x in hits if not x[4]),incomplete_contracts=sum(1 for x in hits if x[4]))
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",STATUS="AGENT_CONTRACT_VERIFICATION_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
