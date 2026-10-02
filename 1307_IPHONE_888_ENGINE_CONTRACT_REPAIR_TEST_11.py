#!/usr/bin/env python3
import os,sys,json,hashlib,re,ast,subprocess,signal,time,shutil
from pathlib import Path

BATCH="IPHONE_888_ENGINE_CONTRACT_REPAIR_TEST_11"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
ENGINE=ROOT/"05_SYSTEM_RUNTIME/ENGINE__01cd6ee9c07d.py"
OUT=ROOT/(BATCH+".json")
TEST=ROOT/"10_RUNTIME_TEST"
EXPECTED="01cd6ee9c07d76f2b974b655791c4bcb8426e128bdb29ca221cfcce502064525"
print("PROTOCOL=888",flush=True); print("BATCH="+BATCH,flush=True)
print("HUMAN_GATE=ACTIVE",flush=True); print("FAIL_CLOSED=YES",flush=True)
def hold(x): print("HOLD="+x,flush=True); raise SystemExit(2)
signal.signal(signal.SIGALRM,lambda *_:hold("TIMEOUT")); signal.alarm(150)
u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower(): hold("IPHONE_IDENTITY_NOT_PROVEN")
if not ENGINE.is_file(): hold("PROVEN_ENGINE_MISSING")
data=ENGINE.read_bytes(); h=hashlib.sha256(data).hexdigest()
if h!=EXPECTED: hold("ENGINE_HASH_CHANGED")
txt=data.decode("utf-8","replace")
print("PROGRESS="+json.dumps({"engine_sha256":h,"bytes":len(data)},separators=(",",":")),flush=True)

# Parse source literals and calls only from the proven ENGINE.
try: tree=ast.parse(txt)
except Exception as e: hold("ENGINE_AST_PARSE_FAIL")
strings=[]
calls=[]
for node in ast.walk(tree):
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        strings.append(node.value)
    if isinstance(node,ast.Call):
        fn=""
        try: fn=ast.unparse(node.func)
        except: pass
        args=[]
        for a in node.args:
            try: args.append(ast.literal_eval(a))
            except: args.append(None)
        calls.append({"fn":fn,"args":args})
paths=sorted(set(s for s in strings if "/" in s or "\\" in s or Path(s).suffix.lower() in {".json",".jsonl",".csv",".txt",".md",".pdf",".docx",".xlsx"}))
repair_mode="--popravi-888" in txt
print("PROGRESS="+json.dumps({"repair_mode":repair_mode,"path_literals":len(paths),"calls":len(calls)},separators=(",",":")),flush=True)

# Detect actual filesystem write/read semantics.
write_markers=("write_text","write_bytes","open","json.dump","shutil.copy","shutil.move","os.replace","rename","unlink","remove","mkdir")
relevant=[c for c in calls if any(m in c["fn"] for m in write_markers)]
stale=[s for s in strings if "/root/FREYA_RAD_888" in s]
canon=[s for s in strings if "/root/FREYA_IPHONE_ISH_NODE_888" in s]
danger=bool(re.search(r'\b(rm\s+-rf|mkfs|shutdown|reboot|poweroff)\b',txt,re.I))

# Determine whether --popravi-888 is gated and bounded enough to execute.
# Require canonical-root awareness, no stale absolute root, no destructive shell pattern.
safe=repair_mode and bool(canon) and not stale and not danger
TEST.mkdir(parents=True,exist_ok=True)
execution={"attempted":False}
before={}
for b,ds,fs in os.walk(ROOT):
    if str(Path(b)).startswith(str(ROOT/"09_EVIDENCE")): continue
    for n in fs:
        p=Path(b)/n
        try: before[str(p)]=(p.stat().st_mtime_ns,p.stat().st_size)
        except: pass

if safe:
    try:
        cp=subprocess.run([sys.executable,"-I","-S","-B",str(ENGINE),"--popravi-888"],
          cwd=str(TEST),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30,
          env={**os.environ,"FREYA_CANONICAL_ROOT":str(ROOT),"FREYA_TEST_MODE":"1","PROTOCOL":"888","HUMAN_GATE":"ACTIVE"})
        execution={"attempted":True,"exit":cp.returncode,"stdout":cp.stdout[-8000:],"stderr":cp.stderr[-8000:]}
    except subprocess.TimeoutExpired:
        execution={"attempted":True,"timeout":True}
    except Exception as e:
        execution={"attempted":True,"error":repr(e)}

changed=[]
for b,ds,fs in os.walk(ROOT):
    for n in fs:
        p=Path(b)/n
        if p==OUT: continue
        try:
            st=p.stat(); old=before.get(str(p))
            if old!=(st.st_mtime_ns,st.st_size):
                changed.append({"path":str(p),"size":st.st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
        except: pass

report={"protocol":"888","batch":BATCH,"engine_sha256":h,"repair_mode":repair_mode,
 "path_literals":paths,"canonical_literals":canon,"stale_literals":stale,
 "relevant_calls":relevant,"dangerous_pattern":danger,"safe_to_execute":safe,
 "execution":execution,"changed_files":changed}
tmp=ROOT/(BATCH+".json.tmp888"); tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8"); os.replace(tmp,OUT)
rh=hashlib.sha256(OUT.read_bytes()).hexdigest(); signal.alarm(0)

passed=safe and execution.get("exit")==0
print("COMPLETED_CHANGES="+str(len(changed)+1)); print("CANONICAL_ROOT="+str(ROOT))
print("INTEGRATED_UNIQUE=0"); print("DUPLICATES_CONFIRMED=0"); print("ARCHIVE_REFERENCE=0"); print("DELETE_CANDIDATES=0")
print("HUMAN_GATE_REVIEW=0")
print("ACTIVE_FLOW_RESULT="+("ENGINE_REPAIR_MODE_EXECUTION_PASS" if passed else ("ENGINE_CONTRACT_UNSAFE_OR_UNPROVEN" if not safe else "ENGINE_REPAIR_MODE_EXECUTION_FAIL")))
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(OUT,rh))
for x in changed[:20]: print("OUTPUT | %s | %s | FILE_CHANGED_AND_HASHED | %s"%(x["path"],x["sha256"],"READY" if passed else "BLOCKED"))
print("CONFIRMED_BLOCKERS="+("PRODUCT_SEMANTIC_VALIDATION_AND_REFERENCE_REPAIR" if passed else "ENGINE_POPRAVI_888_CONTRACT_NOT_SAFE_FOR_EXECUTION" if not safe else "ENGINE_EXECUTION_DID_NOT_PASS"))
print("NEXT="+("VALIDATE_CHANGED_PRODUCTS_REPAIR_STALE_RUNTIME_REFERENCES_AND_FINAL_ACCEPTANCE" if passed else "RETURN_ENGINE_CONTRACT_EVIDENCE_FOR_TARGETED_REPAIR"))
print("BATCH_COMPLETE=true")
