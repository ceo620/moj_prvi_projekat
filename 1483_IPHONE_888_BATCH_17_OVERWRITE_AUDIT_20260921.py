#!/usr/bin/env python3
import os,re,json,hashlib,stat
from pathlib import Path
P=888; N="FREYA_IPHONE_ISH_NODE_888"; B="IPHONE_888_BATCH_17_OVERWRITE_AUDIT_20260921"; A="DANIJELA_DJUROVIC_KESKIN"
S=Path("/root/IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env"); H="13ee3ff93a6a9a23d178b8164a868609e06f613acccf6072c80095b9d31bd775"
def out(**x): print(json.dumps(x,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for z in iter(lambda:f.read(1048576),b""): h.update(z)
 return h.hexdigest()
out(PROTOCOL=P,NODE=N,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=A,HUMAN_GATE_APPROVAL="BATCH_17_READ_ONLY_OVERWRITE_AUDIT",DEFAULT_MODE="DENY",FAIL_CLOSED="YES",READ_ONLY="YES",WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0)
if os.getuid()!=0 or not Path("/etc/alpine-release").is_file(): out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP"); raise SystemExit(2)
if not S.is_file(): out(STATUS="HOLD",REASON="FINAL_SEAL_GATE",detail="SEAL_MISSING",NEXT="STOP"); raise SystemExit(3)
a=sha(S); out(event="FINAL_SEAL_VERIFY",path=str(S),expected_sha256=H,actual_sha256=a,match=a==H)
if a!=H: out(STATUS="HOLD",REASON="FINAL_SEAL_GATE",detail="SEAL_HASH_CHANGED",NEXT="STOP"); raise SystemExit(4)
rx={
"PYTHON_OVERWRITE":[r"\.write_text\s*\(",r"\.write_bytes\s*\(",r"\bos\.replace\s*\(",r"\bos\.rename\s*\(",r"\bshutil\.copy(?:2|file)?\s*\(",r"\bshutil\.move\s*\(",r"\bopen\s*\([^\n]{0,300},\s*['\"]w"],
"SHELL_OVERWRITE":[r"(^|[;&|()\s])cp\s+",r"(^|[;&|()\s])mv\s+",r"(?<!>)>(?!>)\s*[^\s]",r"\btee\s+(?!-a(?:\s|$))"]}
rx={k:[re.compile(v,re.I|re.M) for v in vs] for k,vs in rx.items()}
c=[]; scanned=0; errors=0
for q in Path("/root").iterdir():
 try:
  if q.is_dir() or q.suffix.lower() not in (".py",".sh"): continue
  st=q.stat()
  if not stat.S_ISREG(st.st_mode) or st.st_size>2097152: continue
  scanned+=1; t=q.read_text(errors="replace"); m=[k for k,rs in rx.items() if any(r.search(t) for r in rs)]
  if m: c.append({"path":str(q),"bytes":st.st_size,"sha256":sha(q),"overwrite_capability_markers":m})
 except OSError: errors+=1
out(event="OVERWRITE_STATIC_AUDIT",scope="LIVE_ROOT_EXECUTABLE_SURFACES_ONLY",files_scanned=scanned,scan_errors=errors,overwrite_capability_candidate_count=len(c),candidates=c,note="CAPABILITY_IS_NOT_EXECUTION_EVIDENCE")
out(PROTOCOL=P,NODE=N,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=A,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",READ_ONLY="YES",WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",FINAL_SEAL_SHA256=a,OVERWRITE_ACTIONS_PERFORMED_BY_THIS_BATCH=0,STATUS="OVERWRITE_AUDIT_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
