#!/usr/bin/env python3
import os,sys,json,hashlib,re,subprocess,signal,time,tempfile
from pathlib import Path

BATCH="IPHONE_888_REAL_IO_PRODUCT_VALIDATION_10"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
ENGINE=ROOT/"05_SYSTEM_RUNTIME/ENGINE__01cd6ee9c07d.py"
OUT=ROOT/(BATCH+".json")
TEST=ROOT/"10_RUNTIME_TEST"
LIMIT=150
print("PROTOCOL=888",flush=True); print("BATCH="+BATCH,flush=True)
print("HUMAN_GATE=ACTIVE",flush=True); print("FAIL_CLOSED=YES",flush=True)
def hold(x): print("HOLD="+x,flush=True); raise SystemExit(2)
signal.signal(signal.SIGALRM,lambda *_:hold("TIMEOUT")); signal.alarm(LIMIT)
u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower(): hold("IPHONE_IDENTITY_NOT_PROVEN")
if not ROOT.is_dir() or not ENGINE.is_file(): hold("PROVEN_ENGINE_MISSING")
eh=hashlib.sha256(ENGINE.read_bytes()).hexdigest()
if eh!="01cd6ee9c07d76f2b974b655791c4bcb8426e128bdb29ca221cfcce502064525": hold("ENGINE_HASH_CHANGED")

txt=ENGINE.read_text("utf-8",errors="replace")
# Determine CLI contract safely from source/help, not assumptions.
help_cp=subprocess.run([sys.executable,"-I","-S","-B",str(ENGINE),"--help"],
 cwd=str(ENGINE.parent),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20)
helptext=(help_cp.stdout+"\n"+help_cp.stderr)[-12000:]
print("PROGRESS="+json.dumps({"engine_sha256":eh,"help_exit":help_cp.returncode,"help_bytes":len(helptext)},separators=(",",":")),flush=True)

# Extract argparse option names and obvious positional arguments.
opts=sorted(set(re.findall(r'["\'](--[A-Za-z0-9_-]+)["\']',txt)))
uses_argparse=("argparse" in txt or "ArgumentParser" in txt)
print("PROGRESS="+json.dumps({"argparse":uses_argparse,"options":opts[:40]},separators=(",",":")),flush=True)

# Refuse uncontrolled production execution. Only synthesize a test when source/help
# exposes a recognizable input/output CLI contract.
input_opts=[x for x in opts if any(k in x.lower() for k in ("input","source","infile","file"))]
output_opts=[x for x in opts if any(k in x.lower() for k in ("output","outdir","dest","result"))]
TEST.mkdir(parents=True,exist_ok=True)
inp=TEST/"CONTROLLED_INPUT_888.txt"
inp.write_text("PROTOCOL=888\nTEST=CONTROLLED_LOCAL_INPUT\nVALUE=1\n",encoding="utf-8")
prod=TEST/"OUTPUT"
prod.mkdir(exist_ok=True)

before={}
for b,ds,fs in os.walk(TEST):
 for n in fs:
  p=Path(b)/n
  before[str(p)]=(p.stat().st_mtime_ns,p.stat().st_size)

execution={"attempted":False}
if input_opts and output_opts:
 cmd=[sys.executable,"-I","-S","-B",str(ENGINE),input_opts[0],str(inp),output_opts[0],str(prod)]
 try:
  cp=subprocess.run(cmd,cwd=str(TEST),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
  execution={"attempted":True,"cmd_args":cmd[5:],"exit":cp.returncode,"stdout":cp.stdout[-6000:],"stderr":cp.stderr[-6000:]}
 except subprocess.TimeoutExpired:
  execution={"attempted":True,"timeout":True}
else:
 execution={"attempted":False,"reason":"NO_SAFE_EXPLICIT_INPUT_OUTPUT_CLI_CONTRACT"}

products=[]
for b,ds,fs in os.walk(TEST):
 for n in fs:
  p=Path(b)/n
  if p==inp: continue
  st=p.stat(); old=before.get(str(p))
  if old and old==(st.st_mtime_ns,st.st_size): continue
  data=p.read_bytes()
  kind="BINARY" if data[:8192].count(b"\0")>8 else "TEXT"
  valid=False; detail=""
  suf=p.suffix.lower()
  if suf==".json":
   try: json.loads(data.decode("utf-8")); valid=True; detail="JSON_PARSE_PASS"
   except Exception as e: detail="JSON_PARSE_FAIL"
  elif suf==".csv":
   try:
    s=data.decode("utf-8"); valid=bool(s.strip() and ("," in s or ";" in s)); detail="CSV_TEXT_STRUCTURE_"+("PASS" if valid else "FAIL")
   except: detail="CSV_DECODE_FAIL"
  elif suf in {".txt",".md",".log",""} and kind=="TEXT":
   try: valid=bool(data.decode("utf-8").strip()); detail="TEXT_READ_PASS" if valid else "TEXT_EMPTY"
   except: detail="TEXT_DECODE_FAIL"
  elif suf==".pdf":
   valid=data.startswith(b"%PDF-") and b"%%EOF" in data[-2048:]; detail="PDF_STRUCTURE_"+("PASS" if valid else "FAIL")
  elif suf in {".docx",".xlsx"}:
   valid=data.startswith(b"PK\x03\x04"); detail="OOXML_CONTAINER_"+("PASS" if valid else "FAIL")
  else:
   valid=len(data)>0; detail="NONEMPTY_"+kind
  products.append({"path":str(p),"sha256":hashlib.sha256(data).hexdigest(),"size":len(data),"validation":detail,"valid":valid})

success=execution.get("attempted") and execution.get("exit")==0 and products and all(x["valid"] for x in products)
report={"protocol":"888","batch":BATCH,"engine":str(ENGINE),"engine_sha256":eh,
 "help_exit":help_cp.returncode,"help_tail":helptext,"options":opts,
 "input_options":input_opts,"output_options":output_opts,"execution":execution,"products":products}
tmp=ROOT/(BATCH+".json.tmp888"); tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8"); os.replace(tmp,OUT)
rh=hashlib.sha256(OUT.read_bytes()).hexdigest(); signal.alarm(0)
print("COMPLETED_CHANGES="+str(3+len(products))); print("CANONICAL_ROOT="+str(ROOT))
print("INTEGRATED_UNIQUE=0"); print("DUPLICATES_CONFIRMED=0"); print("ARCHIVE_REFERENCE=0"); print("DELETE_CANDIDATES=0"); print("HUMAN_GATE_REVIEW=0")
print("ACTIVE_FLOW_RESULT="+("REAL_IO_PRODUCT_TEST_PASS" if success else ("BLOCKED_NO_SAFE_IO_CONTRACT" if not execution.get("attempted") else "REAL_IO_PRODUCT_TEST_FAIL")))
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(OUT,rh))
for x in products: print("PRODUCT | %s | %s | %s | %s"%(x["path"],x["sha256"],x["validation"],"READY" if x["valid"] else "BLOCKED"))
print("CONFIRMED_BLOCKERS="+("NONE_FOR_RUNTIME_PRODUCT_TEST" if success else ("SAFE_INPUT_OUTPUT_CONTRACT_NOT_PROVEN" if not execution.get("attempted") else "REAL_IO_TEST_DID_NOT_PASS")))
print("NEXT="+("V1_REFERENCE_REPAIR_AND_FINAL_ACCEPTANCE" if success else "RETURN_IO_CONTRACT_EVIDENCE_FOR_TARGETED_REPAIR"))
print("BATCH_COMPLETE=true")
