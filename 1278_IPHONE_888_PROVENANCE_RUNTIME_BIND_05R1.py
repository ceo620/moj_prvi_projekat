#!/usr/bin/env python3
import os, sys, json, hashlib, re, time
from pathlib import Path

BATCH="IPHONE_888_PROVENANCE_RUNTIME_BIND_05R1"
ROOT=Path("/root/FREYA_IPHONE_ISH_NODE_888")
EVID=ROOT/"09_EVIDENCE"
OUT=EVID/(BATCH+".json")

print("PROTOCOL=888")
print("BATCH="+BATCH)
print("HUMAN_GATE=ACTIVE")
print("FAIL_CLOSED=YES")

def hold(x):
    print("HOLD="+x); raise SystemExit(2)

u=os.uname()
if os.geteuid()!=0 or u.sysname!="Linux" or u.machine!="i686" or "ish" not in u.release.lower():
    hold("IPHONE_IDENTITY_NOT_PROVEN")
if not ROOT.is_dir(): hold("CANONICAL_ROOT_NOT_PROVEN")

# Diagnose evidence path before any repair.
state={
 "exists":EVID.exists(),
 "is_dir":EVID.is_dir(),
 "is_symlink":EVID.is_symlink(),
}
try:
    state["resolved"]=str(EVID.resolve(strict=False))
except Exception as e:
    state["resolve_error"]=repr(e)
print("PROGRESS="+json.dumps({"evidence_path_state":state},separators=(",",":")))

# This is an approved canonical evidence directory, not a new root/system.
# Re-create only this missing canonical directory if absent.
if EVID.exists() and not EVID.is_dir():
    hold("EVIDENCE_PATH_COLLISION")
if not EVID.exists():
    EVID.mkdir(parents=True,exist_ok=True)
    print("PROGRESS="+json.dumps({"canonical_evidence_directory_repaired":True},separators=(",",":")))

# Targeted content classification only inside the already-integrated canonical root.
# No old-root scan and no execution.
code_ext={".py",".sh",".bash",".ash",".js",".ts",".rb",".pl",".lua"}
runtime_content=re.compile(rb'(subprocess|Popen|os\.system|socket|serve_forever|sys\.argv|__main__|workflow|pipeline|factory|runtime|worker|router|daemon|service)',re.I)
structure=re.compile(rb'(^|\n)\s*(def |class |import |from )',re.M)
candidates=[]
checked=0
errors=[]

for base, dirs, names in os.walk(ROOT):
    # Skip evidence itself to avoid classifying audit scripts/reports as runtime.
    dirs[:] = sorted(d for d in dirs if Path(base,d) != EVID)
    for n in sorted(names):
        p=Path(base)/n
        if p.suffix.lower() not in code_ext:
            continue
        checked+=1
        try:
            b=p.read_bytes()
            score=8
            reasons=["CODE_EXTENSION"]
            if b.startswith(b"#!"):
                score+=4; reasons.append("SHEBANG")
            if structure.search(b):
                score+=5; reasons.append("CODE_STRUCTURE")
            if runtime_content.search(b):
                score+=4; reasons.append("RUNTIME_CONTENT")
            if str(ROOT).encode() in b:
                score+=2; reasons.append("CANONICAL_REFERENCE")
            candidates.append({
                "path":str(p),"sha256":hashlib.sha256(b).hexdigest(),
                "size":len(b),"score":score,"reasons":reasons
            })
        except Exception as e:
            errors.append({"path":str(p),"error":repr(e)})

candidates.sort(key=lambda x:(-x["score"],x["path"]))
print("PROGRESS="+json.dumps({"canonical_code_files_checked":checked,"runtime_candidates":len(candidates),"errors":len(errors)},separators=(",",":")))

# Strong enough for later controlled execution only when code structure + runtime semantics exist.
strong=[c for c in candidates if "CODE_STRUCTURE" in c["reasons"] and "RUNTIME_CONTENT" in c["reasons"]]
status="RUNTIME_CANDIDATE_UNIQUE" if len(strong)==1 else ("RUNTIME_CANDIDATES_MULTIPLE" if len(strong)>1 else "RUNTIME_CANDIDATE_NOT_PROVEN")

report={
 "protocol":"888","batch":BATCH,"root":str(ROOT),
 "prior_batch_observation":{"referenced_canonical_paths":2504,"code_runtime_candidates":2,"strong_candidates":0},
 "evidence_path_initial_state":state,
 "canonical_code_files_checked":checked,
 "candidates":candidates[:50],"strong_candidates":strong[:25],
 "errors":errors[:100],"status":status
}
tmp=OUT.with_suffix(".json.tmp")
tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
os.replace(tmp,OUT)
rh=hashlib.sha256(OUT.read_bytes()).hexdigest()

print("COMPLETED_CHANGES="+("2" if not state["exists"] else "1"))
print("CANONICAL_ROOT="+str(ROOT))
print("INTEGRATED_UNIQUE=0")
print("DUPLICATES_CONFIRMED=0")
print("ARCHIVE_REFERENCE=0")
print("DELETE_CANDIDATES=0")
print("HUMAN_GATE_REVIEW="+str(max(0,len(strong)-1)))
print("ACTIVE_FLOW_RESULT="+status)
print("PRODUCT | FILE/PATH | SHA256 | OPENED/VALIDATED | READY/BLOCKED")
print("EVIDENCE | %s | %s | JSON_VALIDATED | READY"%(OUT,rh))
for c in candidates[:20]:
    print("RUNTIME_CANDIDATE | %s | %s | SCORE_%d_%s | %s"%(
        c["path"],c["sha256"],c["score"],"+".join(c["reasons"]),
        "READY_FOR_CONTROLLED_TEST" if len(strong)==1 and c["path"]==strong[0]["path"] else "REVIEW"))
print("CONFIRMED_BLOCKERS="+("FUNCTIONAL_RUNTIME_PRODUCT_TEST_REQUIRED" if len(strong)==1 else "ACTIVE_RUNTIME_SELECTION_NOT_YET_PROVEN"))
print("NEXT="+("CONTROLLED_RUNTIME_PRODUCT_TEST" if len(strong)==1 else "RETURN_EXACT_CANDIDATES_FOR_DECISION_REPAIR"))
print("BATCH_COMPLETE=true")
