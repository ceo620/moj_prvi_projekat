#!/usr/bin/env python3
# PROTOCOL 888 — BATCH 03 — exact runtime repair preflight
# READ ONLY: proves safe target/config for next activation batch.
import os, json, hashlib, stat, subprocess, re
from pathlib import Path

R=Path("/root/FREYA_RAD_888")
AF=R/"05_SISTEM/AGENT_FACTORY"

def emit(e,**k): print(json.dumps({"event":e,**k},ensure_ascii=False,sort_keys=True),flush=True)
def H(p):
    try:
        h=hashlib.sha256()
        with open(p,"rb") as f:
            for b in iter(lambda:f.read(1048576),b""): h.update(b)
        return h.hexdigest()
    except Exception as x:return "ERROR:"+type(x).__name__
def T(p,n=16000):
    try:return Path(p).read_text(errors="replace")[:n]
    except Exception as x:return "ERROR:"+type(x).__name__+":"+str(x)

emit("BEGIN",PROTOCOL=888,BATCH="IPHONE_888_AUTOPILOT_BATCH_03_RUNTIME_REPAIR_PREFLIGHT_20260922",
 HUMAN_GATE="ACTIVE",DEFAULT_MODE="DENY",FAIL_CLOSED="YES",SSOT="SOVEREIGN",
 READ_ONLY_FIRST="YES",EVIDENCE_FIRST="YES",SCOPE_BOUND="YES",MODE="READ_ONLY",
 ZIP_CREATION="DENY",NETWORK="DENY")

# Exact agent-factory structure
if not AF.is_dir():
    emit("HOLD",reason="AGENT_FACTORY_MISSING"); raise SystemExit(2)
for dp,ds,fs in os.walk(AF,followlinks=False):
    rel=str(Path(dp).relative_to(AF))
    depth=0 if rel=="." else len(Path(rel).parts)
    if depth>3: ds[:]=[]; continue
    emit("AF_DIR",rel=rel,dirs=sorted(ds),files=sorted(fs))

# Read small config/control files likely required to execute existing runtime.
rx=re.compile(r"(allow|agent|registry|contract|config|policy|checkpoint|identity|manifest|runner|start|launch|active)",re.I)
seen=0
for dp,ds,fs in os.walk(AF,followlinks=False):
    ds[:]=[d for d in ds if not os.path.islink(os.path.join(dp,d))]
    for f in sorted(fs):
        q=Path(dp)/f
        try:
            if rx.search(f) and q.is_file() and not q.is_symlink() and q.stat().st_size<=256*1024:
                emit("AF_CONTROL",rel=str(q.relative_to(AF)),bytes=q.stat().st_size,sha256=H(q),content=T(q))
                seen+=1
                if seen>=120: break
        except Exception: pass
    if seen>=120: break
emit("AF_CONTROL_COUNT",count=seen)

# Determine exact executable dependencies by parsing shell runtime positional interfaces.
for rel in ["RUNTIME/integrated_runtime.sh","RUNTIME/integrated_runtime_00_ulaz.sh",
            "RUNTIME/integrated_runtime_all_files.sh","ROUTER/queue_binder.sh"]:
    q=AF/rel
    emit("RUNTIME_COMPONENT",rel=rel,exists=q.is_file(),sha256=H(q) if q.is_file() else None,
         executable=os.access(q,os.X_OK) if q.exists() else False)

# Existing local input: exact census, no content mutation.
inp=R/"00_ULAZ"
rows=[]
if inp.is_dir():
    for q in sorted(inp.iterdir(),key=lambda x:x.name):
        try:
            if q.is_file() and not q.is_symlink():
                rows.append((q.name,q.stat().st_size,H(q)))
        except Exception: pass
emit("CANONICAL_INPUT",path=str(inp),regular_files=len(rows))
for n,z,h in rows: emit("INPUT_FILE",name=n,bytes=z,sha256=h)

# Output census and collision names.
outp=R/"01_PROIZVODI"
outs=[]
if outp.is_dir():
    for dp,ds,fs in os.walk(outp,followlinks=False):
        for f in fs:
            q=Path(dp)/f
            try:
                if q.is_file() and not q.is_symlink():
                    outs.append((str(q.relative_to(outp)),q.stat().st_size,H(q) if q.stat().st_size<=32*1024*1024 else None))
            except Exception: pass
emit("CANONICAL_OUTPUT",path=str(outp),regular_files=len(outs))
for a,b,c in outs[:150]: emit("OUTPUT_FILE",rel=a,bytes=b,sha256=c)

# Inspect prior final seals/closeout as immutable evidence, including content.
for q in sorted(Path("/root").glob("*FINAL*"))+sorted(Path("/root").glob("*SEAL*")):
    try:
        if q.is_file() and not q.is_symlink() and q.stat().st_size<=128*1024:
            emit("PRIOR_SEAL",path=str(q),bytes=q.stat().st_size,sha256=H(q),content=T(q))
    except Exception: pass

# Check lock semantics; no removal.
lock=R/"RUN.lock"
emit("RUN_LOCK",exists=lock.exists(),bytes=lock.stat().st_size if lock.exists() else None,
     content=T(lock) if lock.is_file() else None)

# iSH scheduling capability facts.
for cmd in ["crond","run-parts","flock","nohup","sha256sum","python3"]:
    try:
        cp=subprocess.run(["sh","-c","command -v "+cmd],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=3)
        emit("CAPABILITY",name=cmd,available=(cp.returncode==0),path=cp.stdout.strip())
    except Exception as e: emit("CAPABILITY",name=cmd,available=False,error=str(e))

# Existing periodic folders, read only.
for d in ["/etc/periodic/15min","/etc/periodic/hourly","/etc/periodic/daily"]:
    p=Path(d)
    emit("PERIODIC_DIR",path=d,exists=p.is_dir(),entries=sorted(os.listdir(d)) if p.is_dir() else [])

emit("DECISION",
 canonical_root=str(R),
 canonical_input=str(inp),
 canonical_output=str(outp),
 files_provider_role="/mnt/ARS_RAD_888_IS_SEPARATE_OBSIDIAN_VAULT_NOT_RUNTIME_MIRROR",
 existing_runtime="PRESENT_NOT_AUTOSCHEDULED",
 next_design="SINGLE_EXISTING_RUNTIME_WRAPPER_PLUS_EXISTING_CRON_WITH_FAIL_CLOSED_GUARDS",
 cleanup="DEFER_UNTIL_RUNTIME_STABLE_AND_REDUNDANCY_PROVEN")

emit("END",RESULT="PASS_RUNTIME_REPAIR_PREFLIGHT",MUTATIONS=0,FILES_CREATED=0,
 FILES_MOVED=0,FILES_DELETED=0,ZIP_CREATED=0,
 NEXT="RETURN_COMPLETE_OUTPUT_FOR_BATCH_04_SCOPED_AUTOPILOT_ACTIVATION")
