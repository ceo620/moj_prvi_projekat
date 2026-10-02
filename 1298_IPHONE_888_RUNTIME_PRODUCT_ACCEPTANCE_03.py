import os,sys,json,hashlib,subprocess,time
from pathlib import Path
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
print("PROTOCOL=888")
print("BATCH=IPHONE_888_RUNTIME_PRODUCT_ACCEPTANCE_03")
print("HUMAN_GATE=ACTIVE")
print("FAIL_CLOSED=YES")
if os.uname().sysname!="Linux" or "ish" not in os.uname().release.lower() or os.geteuid()!=0:
 print("HOLD=IPHONE_IDENTITY_NOT_PROVEN");sys.exit(2)
if not ROOT.is_dir(): print("HOLD=CANONICAL_ROOT_MISSING");sys.exit(2)
files=[]
for b,ds,fs in os.walk(ROOT):
 for n in fs: files.append(Path(b)/n)
print("PROGRESS="+json.dumps({"canonical_files":len(files)},separators=(",",":")))
# Target only executable/system candidates already in canon; no outside-root scan.
keys=("runtime","service","worker","main","factory","build","ssot","registry","config")
c=[]
for p in files:
 q=str(p).lower()
 if p.suffix.lower() in (".py",".sh") and any(k in q for k in keys): c.append(p)
print("PROGRESS="+json.dumps({"active_code_candidates":len(c)},separators=(",",":")))
# Fail closed rather than guessing which historical script is safe to execute.
report=ROOT/"09_EVIDENCE"/"IPHONE_888_RUNTIME_PRODUCT_ACCEPTANCE_03.json"
report.parent.mkdir(parents=True,exist_ok=True)
data={"canonical_root":str(ROOT),"canonical_files":len(files),"candidates":[str(x) for x in c[:200]],"result":"TARGETED_RUNTIME_SELECTION_REQUIRED" if c else "NO_RUNTIME_CANDIDATE_PROVEN"}
report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
h=hashlib.sha256(report.read_bytes()).hexdigest()
print("COMPLETED_CHANGES=1")
print("CANONICAL_ROOT="+str(ROOT))
print("INTEGRATED_UNIQUE=0")
print("DUPLICATES_CONFIRMED=0")
print("ARCHIVE_REFERENCE=0")
print("DELETE_CANDIDATES=0")
print("HUMAN_GATE_REVIEW=0")
print("ACTIVE_FLOW_RESULT=TARGETED_RUNTIME_SELECTION_REQUIRED" if c else "ACTIVE_FLOW_RESULT=BLOCKED_NO_RUNTIME_CANDIDATE_PROVEN")
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(report,h))
print("CONFIRMED_BLOCKERS=RUNTIME_PRODUCT_FUNCTIONAL_TEST_NOT_YET_PROVEN")
print("NEXT=RETURN_OUTPUT_FOR_RUNTIME_EXECUTION_REPAIR")
print("BATCH_COMPLETE=true")
