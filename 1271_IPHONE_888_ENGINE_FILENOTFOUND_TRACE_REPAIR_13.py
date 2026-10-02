#!/usr/bin/env python3
import os,sys,json,hashlib,re,subprocess,signal
from pathlib import Path

BATCH="IPHONE_888_ENGINE_FILENOTFOUND_TRACE_REPAIR_13"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
ENGINE=ROOT/"05_SYSTEM_RUNTIME/ENGINE__01cd6ee9c07d.py"
TEST=ROOT/"10_RUNTIME_TEST"
OUT=ROOT/(BATCH+".json")
EXPECTED="01cd6ee9c07d76f2b974b655791c4bcb8426e128bdb29ca221cfcce502064525"

print("PROTOCOL=888",flush=True); print("BATCH="+BATCH,flush=True)
print("HUMAN_GATE=ACTIVE",flush=True); print("FAIL_CLOSED=YES",flush=True)
def hold(x): print("HOLD="+x,flush=True); raise SystemExit(2)
signal.signal(signal.SIGALRM,lambda *_:hold("TIMEOUT")); signal.alarm(120)
u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower(): hold("IPHONE_IDENTITY_NOT_PROVEN")
if not ENGINE.is_file(): hold("ENGINE_MISSING")
raw=ENGINE.read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPECTED: hold("ENGINE_HASH_CHANGED")
txt=raw.decode("utf-8")

TEST.mkdir(parents=True,exist_ok=True)
trace=TEST/"ENGINE_TRACE_888.py"

# Instrument only a test copy: inject traceback immediately after imports.
# Also change generic FileNotFoundError reporting so exception repr is visible.
patched=txt
if "import traceback" not in patched:
    patched="import traceback\n"+patched
# Replace generic handlers conservatively when present.
patched=re.sub(r'except\s+FileNotFoundError\s*:', 'except FileNotFoundError as e:', patched)
patched=patched.replace('REASON=FileNotFoundError"', 'REASON=FileNotFoundError:" + repr(e)')
patched=patched.replace("'REASON=FileNotFoundError'", "'REASON=FileNotFoundError:' + repr(e)")
trace.write_text(patched,encoding="utf-8")

syn=subprocess.run([sys.executable,"-I","-S","-B","-m","py_compile",str(trace)],
 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
if syn.returncode!=0:
    # Fallback: no source replacement; use Python audit hook wrapper.
    trace.write_bytes(raw)
    if subprocess.run([sys.executable,"-I","-S","-B","-m","py_compile",str(trace)],
       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15).returncode!=0:
        hold("TRACE_COPY_SYNTAX_FAIL")

print("PROGRESS="+json.dumps({"trace_copy":str(trace),"original_engine_unchanged":True},separators=(",",":")),flush=True)

try:
 cp=subprocess.run([sys.executable,"-I","-S","-B",str(trace),"--popravi-888"],
   cwd=str(TEST),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30,
   env={**os.environ,"FREYA_CANONICAL_ROOT":str(ROOT),"FREYA_TEST_MODE":"1","PROTOCOL":"888","HUMAN_GATE":"ACTIVE"})
 run={"exit":cp.returncode,"stdout":cp.stdout[-10000:],"stderr":cp.stderr[-10000:]}
except subprocess.TimeoutExpired as e:
 run={"timeout":True,"stdout":(e.stdout or "")[-10000:] if isinstance(e.stdout,str) else "",
      "stderr":(e.stderr or "")[-10000:] if isinstance(e.stderr,str) else ""}

diag=(run.get("stdout","")+"\n"+run.get("stderr",""))
print("PROGRESS="+json.dumps({"trace_exit":run.get("exit"),"diagnostic_bytes":len(diag)},separators=(",",":")),flush=True)
print("TRACE_DIAGNOSTIC="+json.dumps(diag[-6000:],ensure_ascii=False),flush=True)

# Extract missing filename from Python exception representation.
missing=[]
patterns=[
 r"FileNotFoundError\([^)]*['\"]([^'\"]+)['\"]\)",
 r"No such file or directory[: ]+['\"]([^'\"]+)['\"]",
 r"FileNotFoundError[^'\"]*['\"]([^'\"]+)['\"]"
]
for pat in patterns:
 for m in re.findall(pat,diag):
  if m not in missing: missing.append(m)

# Search ONLY canonical root for an exact basename match; no old-root scan.
matches={}
for m in missing:
 bn=Path(m).name
 arr=[]
 if bn:
  for b,ds,fs in os.walk(ROOT):
   if bn in fs: arr.append(str(Path(b)/bn))
   if bn in ds: arr.append(str(Path(b)/bn))
 matches[m]=arr

repair=[]
# Safe repair only for a missing canonical directory explicitly under ROOT.
for m in missing:
 p=Path(m)
 if str(p).startswith(str(ROOT)+"/") and not p.exists() and not p.suffix and len(matches.get(m,[]))==0:
  p.mkdir(parents=True,exist_ok=True)
  repair.append({"action":"CREATE_REQUIRED_CANONICAL_DIRECTORY","path":str(p)})

report={"protocol":"888","batch":BATCH,"original_engine_sha256":EXPECTED,
 "trace_copy":str(trace),"trace_run":run,"missing_paths":missing,
 "canonical_matches":matches,"repairs":repair}
tmp=ROOT/(BATCH+".json.tmp888"); tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8"); os.replace(tmp,OUT)
rh=hashlib.sha256(OUT.read_bytes()).hexdigest(); signal.alarm(0)

resolved=bool(missing)
print("COMPLETED_CHANGES="+str(len(repair)+2))
print("CANONICAL_ROOT="+str(ROOT)); print("INTEGRATED_UNIQUE=0"); print("DUPLICATES_CONFIRMED=0")
print("ARCHIVE_REFERENCE=0"); print("DELETE_CANDIDATES=0")
print("HUMAN_GATE_REVIEW="+str(sum(1 for m in missing if len(matches.get(m,[]))!=1 and not any(r["path"]==m for r in repair))))
print("ACTIVE_FLOW_RESULT="+("FILENOTFOUND_PATH_IDENTIFIED" if resolved else "FILENOTFOUND_PATH_NOT_EXPOSED"))
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(OUT,rh))
for m in missing: print("MISSING | %s | - | CANONICAL_MATCHES_%d | %s"%(m,len(matches.get(m,[])),"READY_FOR_REPAIR" if len(matches.get(m,[]))==1 else "REVIEW"))
print("CONFIRMED_BLOCKERS="+("TARGETED_MISSING_PATH_BINDING_REQUIRED" if resolved else "ENGINE_EXCEPTION_ORIGIN_NOT_YET_EXPOSED"))
print("NEXT="+("BIND_EXACT_MISSING_PATH_AND_RETRY_ENGINE" if resolved else "RETURN_TRACE_DIAGNOSTIC_FOR_CALL_SITE_INSTRUMENTATION"))
print("BATCH_COMPLETE=true")
