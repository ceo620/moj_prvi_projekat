#!/usr/bin/env python3
import os,json,hashlib,platform,re
from pathlib import Path
P=888;NODE="FREYA_IPHONE_ISH_NODE_888";B="IPHONE_888_BATCH_14R1_FINAL_SEAL_INCIDENT_FORENSICS_20260921";AUTH="DANIJELA_DJUROVIC_KESKIN"
EXPECTED_PATH="/root/IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env"
EXPECTED_HASH="13ee3ff93a6a9a23d178b8164a868609e06f613acccf6072c80095b9d31bd775"
SCRIPT="/root/IPHONE_888_BATCH_13_FINAL_LOCAL_PRODUCTION_SEAL_20260921.py"
SCRIPT_HASH="5bb671d62d796519bc647d8490459ae4f2c8c18e3603d210d8ed76b11fe517a8"
def out(**x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY_FORENSICS")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP");raise SystemExit(2)
ep=Path(EXPECTED_PATH)
out(event="EXPECTED_SEAL",path=EXPECTED_PATH,exists=ep.exists(),expected_sha256=EXPECTED_HASH)
# Locate exact hash or filename elsewhere under /root; bounded regular files only.
matches=[];namehits=[];refs=[];scanned=0
for dp,dn,fn in os.walk("/root",topdown=True,followlinks=False):
 dn[:]=[x for x in dn if x not in (".git","__pycache__")]
 for n in fn:
  scanned+=1;q=Path(dp)/n
  try:
   st=q.stat()
   if not q.is_file():continue
   if n=="IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env":namehits.append(str(q))
   if st.st_size<=2*1024*1024:
    # Search textual references first.
    if q.suffix.lower() in (".env",".txt",".log",".json",".jsonl",".md",".sh",".py",""):
     try:
      txt=q.read_text(errors="replace")
      if EXPECTED_HASH in txt or "IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env" in txt:
       refs.append(str(q))
     except OSError:pass
    # Hash plausible seal-sized files and exact-name hits.
    if n=="IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env" or (1000<=st.st_size<=2000 and "SEAL" in n.upper()):
     try:
      h=sha(q)
      if h==EXPECTED_HASH:matches.append(str(q))
     except OSError:pass
  except OSError:pass
out(event="SEAL_SEARCH",files_scanned=scanned,filename_hits=sorted(set(namehits)),exact_hash_hits=sorted(set(matches)),reference_files=sorted(set(refs))[:1000])
sp=Path(SCRIPT)
out(event="ORIGINAL_SEAL_SCRIPT",path=SCRIPT,exists=sp.is_file(),actual_sha256=sha(sp) if sp.is_file() else None,expected_sha256=SCRIPT_HASH)
# Shell histories, read only. Extract only lines relevant to seal/path/hash and rm/mv/unlink.
hist=[]
for q in [Path("/root/.ash_history"),Path("/root/.sh_history"),Path("/root/.bash_history")]:
 try:
  if q.is_file():
   lines=q.read_text(errors="replace").splitlines()
   rel=[x for x in lines if ("SEAL" in x.upper() or EXPECTED_HASH in x or re.search(r'(^|[;&| ])(rm|mv|unlink)([ ;&|]|$)',x))]
   hist.append({"path":str(q),"sha256":sha(q),"relevant_lines":rel[-500:]})
 except OSError:pass
out(event="SHELL_HISTORY",histories=hist)
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",STATUS="FINAL_SEAL_INCIDENT_FORENSICS_COMPLETE",
RECOVERY_SEAL_CREATED="NO",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
