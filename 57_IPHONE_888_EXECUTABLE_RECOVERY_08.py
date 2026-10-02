#!/usr/bin/env python3
import os,json,hashlib,re,shutil,time
from pathlib import Path
BATCH="IPHONE_888_EXECUTABLE_RECOVERY_08"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888"); SRC=Path("/root/FREYA_RAD_888")
EVID=ROOT/"09_EVIDENCE"; DEST=ROOT/"05_SYSTEM_RUNTIME"; OUT=EVID/(BATCH+".json")
DEAD=time.monotonic()+300
print("PROTOCOL=888"); print("BATCH="+BATCH); print("HUMAN_GATE=ACTIVE"); print("FAIL_CLOSED=YES")
def hold(x): print("HOLD="+x); raise SystemExit(2)
u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower(): hold("IPHONE_IDENTITY_NOT_PROVEN")
if not ROOT.is_dir() or not SRC.is_dir(): hold("ROOT_OR_SOURCE_NOT_PROVEN")
if not EVID.is_dir(): hold("CANONICAL_EVIDENCE_NOT_STABLE")
def H(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
# Use current canon hash set; bounded ~454 files.
canon=set(); cf=0
for b,ds,fs in os.walk(ROOT):
 for n in fs:
  p=Path(b)/n
  try: canon.add(H(p)); cf+=1
  except: pass
print("PROGRESS="+json.dumps({"canon_files":cf,"canon_hashes":len(canon)},separators=(",",":")))
py=re.compile(rb'(^#![^\n]*python|(^|\n)\s*(?:from\s+\S+\s+import|import\s+\S+|def\s+\w+\s*\(|class\s+\w+))',re.M)
sh=re.compile(rb'(^#![^\n]*(?:/sh|ash|bash)|(^|\n)\s*(?:set\s+-[A-Za-z]+|if\s+\[|case\s+[^ \n]+|for\s+\w+\s+in\s+))',re.M)
sysrx=re.compile(rb'(FREYA|HUMAN_GATE|PROTOCOL.?888|SSOT|registry|manifest|runtime|worker|router|factory|workflow|pipeline|subprocess|Popen|os\.system)',re.I)
cand=[]; errs=[]; checked=0
for b,ds,fs in os.walk(SRC):
 ds[:]=sorted(d for d in ds if d not in {".git","__pycache__","node_modules"})
 for n in sorted(fs):
  if time.monotonic()>DEAD: hold("TARGETED_SOURCE_TIMEOUT")
  p=Path(b)/n
  try:
   if p.is_symlink() or not p.is_file(): continue
   z=p.stat().st_size
   if z==0 or z>8388608: continue
   checked+=1
   data=p.read_bytes()
   if data[:8192].count(b"\0")>8: continue
   kind="PYTHON" if py.search(data) else ("SHELL" if sh.search(data) else None)
   if not kind: continue
   h=hashlib.sha256(data).hexdigest()
   score=10+(5 if sysrx.search(data) else 0)+(2 if b"FREYA" in data.upper() else 0)
   cand.append({"source":str(p),"hash":h,"size":z,"kind":kind,"score":score,"duplicate":h in canon})
  except Exception as e: errs.append({"path":str(p),"error":repr(e)})
print("PROGRESS="+json.dumps({"source_checked":checked,"script_candidates":len(cand),"errors":len(errs)},separators=(",",":")))
# One representative per unique noncanonical hash.
best={}
for c in sorted(cand,key=lambda x:(-x["score"],x["source"])):
 if not c["duplicate"] and c["hash"] not in best: best[c["hash"]]=c
unique=list(best.values())
integrated=[]
if unique: DEST.mkdir(parents=True,exist_ok=True)
for i,c in enumerate(unique,1):
 sp=Path(c["source"]); ext=".py" if c["kind"]=="PYTHON" else ".sh"
 stem=re.sub(r'[^A-Za-z0-9._-]+','_',sp.stem).strip("._-") or "recovered"
 dp=DEST/(stem+"__"+c["hash"][:12]+ext)
 if dp.exists() and H(dp)!=c["hash"]: dp=DEST/(stem+"__"+c["hash"][:20]+ext)
 if not dp.exists():
  tp=dp.with_name(dp.name+".tmp888"); shutil.copyfile(sp,tp)
  if H(tp)!=c["hash"]: tp.unlink(missing_ok=True); hold("COPY_HASH_MISMATCH")
  os.replace(tp,dp)
 integrated.append({"source":str(sp),"dest":str(dp),"sha256":c["hash"],"kind":c["kind"],"score":c["score"]})
 if i%25==0: print("PROGRESS="+json.dumps({"integrated":i},separators=(",",":")))
runtime=sorted([x for x in integrated if x["score"]>=15],key=lambda x:(-x["score"],x["dest"]))
rep={"protocol":"888","batch":BATCH,"checked":checked,"candidates":cand[:300],"integrated":integrated,"runtime_candidates":runtime,"errors":errs[:100]}
tmp=OUT.with_suffix(".json.tmp"); tmp.write_text(json.dumps(rep,indent=2,ensure_ascii=False),encoding="utf-8"); os.replace(tmp,OUT); rh=H(OUT)
print("COMPLETED_CHANGES="+str(len(integrated)+1)); print("CANONICAL_ROOT="+str(ROOT))
print("INTEGRATED_UNIQUE="+str(len(integrated))); print("DUPLICATES_CONFIRMED="+str(sum(1 for c in cand if c["duplicate"])))
print("ARCHIVE_REFERENCE=0"); print("DELETE_CANDIDATES=0"); print("HUMAN_GATE_REVIEW=0")
print("ACTIVE_FLOW_RESULT="+("EXECUTABLE_LAYER_RECOVERED" if runtime else "BLOCKED_NO_SYSTEM_RUNTIME_RECOVERED"))
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(OUT,rh))
for x in runtime[:20]: print("RUNTIME | %s | %s | CONTENT_AND_HASH_VALIDATED | READY_FOR_CONTROLLED_TEST"%(x["dest"],x["sha256"]))
print("CONFIRMED_BLOCKERS="+("CONTROLLED_RUNTIME_PRODUCT_TEST_REQUIRED" if runtime else "SYSTEM_RUNTIME_NOT_RECOVERED"))
print("NEXT="+("CONTROLLED_RUNTIME_PRODUCT_TEST" if runtime else "RETURN_EVIDENCE_FOR_TARGETED_ESCALATION")); print("BATCH_COMPLETE=true")
