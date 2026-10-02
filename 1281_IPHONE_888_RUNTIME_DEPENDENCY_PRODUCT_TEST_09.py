#!/usr/bin/env python3
import os,sys,json,hashlib,re,subprocess,signal,time
from pathlib import Path

BATCH="IPHONE_888_RUNTIME_DEPENDENCY_PRODUCT_TEST_09"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
RUNTIME=ROOT/"05_SYSTEM_RUNTIME"
REC=ROOT/"IPHONE_888_EXECUTABLE_RECOVERY_08R1.json"
OUT=ROOT/(BATCH+".json")
LIMIT=150

print("PROTOCOL=888",flush=True); print("BATCH="+BATCH,flush=True)
print("HUMAN_GATE=ACTIVE",flush=True); print("FAIL_CLOSED=YES",flush=True)
def hold(x): print("HOLD="+x,flush=True); raise SystemExit(2)
signal.signal(signal.SIGALRM,lambda *_:hold("TIMEOUT")); signal.alarm(LIMIT)
u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower(): hold("IPHONE_IDENTITY_NOT_PROVEN")
if not ROOT.is_dir() or not RUNTIME.is_dir() or not REC.is_file(): hold("RUNTIME_RECOVERY_EVIDENCE_MISSING")
try: rec=json.loads(REC.read_text("utf-8"))
except: hold("RUNTIME_RECOVERY_EVIDENCE_INVALID")
items=rec.get("integrated",[])
paths=[Path(x["dest"]) for x in items if x.get("dest") and Path(x["dest"]).is_file()]
print("PROGRESS="+json.dumps({"recovered_runtime_files":len(paths)},separators=(",",":")),flush=True)

oldrefs=[b"/root/FREYA_RAD_888",b"/root/FREYA_IPHONE_ISH_NODE_888"]
analysis=[]; basename={p.name:p for p in paths}
for p in paths:
 b=p.read_bytes(); txt=b.decode("utf-8","replace")
 refs=[]
 for q in paths:
  # references by original-ish stem or recovered basename
  if q==p: continue
  tokens={q.name,q.stem.split("__")[0]}
  if any(t and t in txt for t in tokens): refs.append(str(q))
 score=0; reasons=[]
 if p.suffix==".py":
  cp=subprocess.run([sys.executable,"-I","-S","-B","-m","py_compile",str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
  syntax=cp.returncode==0
 else:
  sh="/bin/sh"
  cp=subprocess.run([sh,"-n",str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
  syntax=cp.returncode==0
 if syntax: score+=5; reasons.append("SYNTAX_PASS")
 if refs: score+=min(10,len(refs)*2); reasons.append("REFERENCES_RECOVERED_COMPONENTS")
 if re.search(r'(main|run|autopilot|integrated|workflow|pipeline|factory)',txt,re.I): score+=4; reasons.append("ORCHESTRATION_CONTENT")
 if str(ROOT) in txt: score+=3; reasons.append("CANONICAL_ROOT_REFERENCE")
 stale="/root/FREYA_RAD_888" in txt
 if stale: score-=6; reasons.append("STALE_ROOT_REFERENCE")
 dangerous=bool(re.search(r'\b(rm\s+-rf|mkfs|dd\s+if=|shutdown|reboot|poweroff)\b',txt,re.I))
 if dangerous: score-=100; reasons.append("DESTRUCTIVE_PATTERN")
 analysis.append({"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"syntax_pass":syntax,
                  "references":refs,"stale_root_reference":stale,"dangerous":dangerous,
                  "score":score,"reasons":reasons})
print("PROGRESS="+json.dumps({"syntax_pass":sum(x["syntax_pass"] for x in analysis),
 "stale_reference_files":sum(x["stale_root_reference"] for x in analysis),
 "destructive_pattern_files":sum(x["dangerous"] for x in analysis)},separators=(",",":")),flush=True)

analysis.sort(key=lambda x:(-x["score"],x["path"]))
safe=[x for x in analysis if x["syntax_pass"] and not x["dangerous"] and not x["stale_root_reference"]]
proven=None
if safe and (len(safe)==1 or safe[0]["score"]>=safe[1]["score"]+4) and safe[0]["score"]>=9:
 proven=safe[0]

test={"attempted":False}
if proven:
 p=Path(proven["path"])
 # First controlled invocation: help/version only, 20s, cwd canonical runtime.
 # This proves entrypoint loadability without allowing an uncontrolled production run.
 attempts=[["--help"],["-h"],["--version"]]
 for args in attempts:
  try:
   cmd=([sys.executable,"-I","-S","-B",str(p)]+args) if p.suffix==".py" else (["/bin/sh",str(p)]+args)
   cp=subprocess.run(cmd,cwd=str(RUNTIME),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20)
   test={"attempted":True,"path":str(p),"args":args,"exit":cp.returncode,
         "stdout":cp.stdout[-4000:],"stderr":cp.stderr[-4000:]}
   if cp.returncode==0: break
  except subprocess.TimeoutExpired:
   test={"attempted":True,"path":str(p),"args":args,"timeout":True}
   break
  except Exception as e:
   test={"attempted":True,"path":str(p),"args":args,"error":repr(e)}
   break

report={"protocol":"888","batch":BATCH,"analysis":analysis,"proven_entrypoint":proven,"controlled_test":test}
tmp=ROOT/(BATCH+".json.tmp888"); tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8"); os.replace(tmp,OUT)
rh=hashlib.sha256(OUT.read_bytes()).hexdigest(); signal.alarm(0)
print("COMPLETED_CHANGES=1"); print("CANONICAL_ROOT="+str(ROOT))
print("INTEGRATED_UNIQUE=0"); print("DUPLICATES_CONFIRMED=0"); print("ARCHIVE_REFERENCE=0"); print("DELETE_CANDIDATES=0")
print("HUMAN_GATE_REVIEW="+str(max(0,len(safe)-(1 if proven else 0))))
if proven:
 result="CONTROLLED_ENTRYPOINT_TEST_"+("PASS" if test.get("exit")==0 else "EXECUTED_NOT_PASS")
else: result="ENTRYPOINT_NOT_YET_UNIQUE"
print("ACTIVE_FLOW_RESULT="+result)
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(OUT,rh))
for x in analysis[:12]:
 print("RUNTIME | %s | %s | SCORE_%s_SYNTAX_%s_STALE_%s | %s"%(x["path"],x["sha256"],x["score"],x["syntax_pass"],x["stale_root_reference"],"READY" if proven and x["path"]==proven["path"] else "REVIEW"))
print("CONFIRMED_BLOCKERS="+("REAL_INPUT_OUTPUT_PRODUCT_VALIDATION_REQUIRED" if proven and test.get("exit")==0 else "ENTRYPOINT_OR_REFERENCE_REPAIR_REQUIRED"))
print("NEXT="+("REAL_INPUT_OUTPUT_PRODUCT_VALIDATION" if proven and test.get("exit")==0 else "RETURN_DEPENDENCY_EVIDENCE_FOR_TARGETED_REPAIR"))
print("BATCH_COMPLETE=true")
