#!/usr/bin/env python3
import os, sys, json, hashlib, stat, platform
from pathlib import Path
from collections import Counter

PROTOCOL=888
NODE="FREYA_IPHONE_ISH_NODE_888"
BATCH="IPHONE_888_BATCH_02_VALUE_MAP_20260921"
AUTH="DANIJELA_DJUROVIC_KESKIN"

def emit(**kw):
    print(json.dumps(kw, ensure_ascii=False, sort_keys=True), flush=True)

def sha256_file(p, limit=256*1024*1024):
    try:
        st=p.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
            return None
        h=hashlib.sha256()
        with p.open("rb") as f:
            for b in iter(lambda:f.read(1024*1024), b""):
                h.update(b)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None

emit(PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE="ACTIVE",
     HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
     MODE="READ_ONLY",NEW_AGENTS="DENY",NEW_ARCHITECTURE="DENY")

# Identity gate
try:
    uid=os.getuid(); user=os.environ.get("USER","")
    alpine=Path("/etc/alpine-release")
    alpine_v=alpine.read_text(errors="replace").strip() if alpine.exists() else ""
    emit(event="IDENTITY",hostname=platform.node(),user=user,uid=uid,
         alpine=alpine_v,kernel=platform.release(),home=os.environ.get("HOME",""))
    if uid != 0 or not alpine_v:
        emit(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP")
        raise SystemExit(2)
except Exception as e:
    emit(STATUS="HOLD",REASON="IPHONE_IDENTITY",detail=type(e).__name__,NEXT="STOP")
    raise SystemExit(2)

# Discovery roots: classify what exists; never mutate.
root=Path("/root")
candidate_roots=[]
try:
    for x in root.iterdir():
        n=x.name.upper()
        if x.is_dir() and ("FREYA" in n or "IPHONE" in n or "RECOVERY" in n):
            candidate_roots.append(x)
except OSError as e:
    emit(event="ROOT_SCAN_ERROR",error=type(e).__name__)

if not candidate_roots:
    emit(STATUS="HOLD",REASON="NO_FREYA_OR_IPHONE_ROOT_DISCOVERED",NEXT="STOP")
    raise SystemExit(3)

rules=[
("SSOT",("SSOT","SOVEREIGN","MASTER")),
("KNOWLEDGE",("KNOWLEDGE","KB","CORPUS")),
("DATABASE",(".DB",".SQLITE",".SQLITE3","DATABASE")),
("AGENT_CONTRACT",("AGENT_CONTRACT","CONTRACT")),
("AGENT",("AGENT",)),
("POLICY",("POLICY","DOCTRINE","HUMAN_GATE")),
("DOCUMENT_PROCESSING",("DOCUMENT","PROCESSOR","RENDER")),
("FINANCIAL_VALIDATION",("FINANC","VALIDATOR","CAPEX","BUDGET")),
("LOCAL_AI",("LOCAL_AI","QWEN","MODEL","LLM")),
("EVIDENCE",("EVIDENCE","RECEIPT","MANIFEST")),
("RUNTIME",("RUNTIME","LAUNCH","WORKER","WATCHDOG","CRON","SCHEDUL")),
("RECOVERY",("RECOVERY","RECOVERED")),
("ASUS_HANDOFF",("ASUS","HANDOFF","TRANSFER")),
("ARCHIVE",(".ZIP",".TAR",".TGZ",".GZ","ARCHIVE")),
("HOLD",("HOLD","COLLISION")),
("PRODUCTION_CANDIDATE",("PRODUCTION","CURRENT","FINAL","SEAL","CLOSEOUT")),
]
def classify(path):
    s=str(path).upper()
    out=[]
    for label,keys in rules:
        if any(k in s for k in keys): out.append(label)
    if not out: out=["LEGACY"]
    return out

counts=Counter(); important=[]
errors=0; files=0; dirs=0
MAX_ITEMS=250000
seen=0
for base in sorted(candidate_roots, key=lambda x:str(x)):
    for dp,dnames,fnames in os.walk(str(base), topdown=True, followlinks=False):
        dnames[:] = [d for d in dnames if d not in (".git","__pycache__")]
        dirs += 1
        for fn in fnames:
            seen += 1
            if seen > MAX_ITEMS:
                emit(STATUS="HOLD",REASON="SCAN_SAFETY_LIMIT",limit=MAX_ITEMS,NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
                raise SystemExit(4)
            q=Path(dp)/fn; files += 1
            labels=classify(q)
            for x in labels: counts[x]+=1
            # Hash only high-value, reasonably sized regular files.
            high=any(x in labels for x in ("SSOT","AGENT_CONTRACT","POLICY","DOCUMENT_PROCESSING",
                 "FINANCIAL_VALIDATION","EVIDENCE","RUNTIME","RECOVERY","ASUS_HANDOFF","PRODUCTION_CANDIDATE"))
            if high:
                try:
                    st=q.stat()
                    if stat.S_ISREG(st.st_mode) and st.st_size <= 32*1024*1024:
                        digest=sha256_file(q,32*1024*1024)
                        important.append((str(q),st.st_size,labels,digest))
                except (OSError,PermissionError):
                    errors+=1

emit(event="ROOTS",roots=[str(x) for x in candidate_roots])
emit(event="VALUE_MAP_COUNTS",files=files,directories=dirs,classification=dict(sorted(counts.items())),
     read_errors=errors)
for path,size,labels,digest in sorted(important)[:4000]:
    emit(event="VALUE_ITEM",path=path,bytes=size,classification=labels,sha256=digest)

emit(PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE="ACTIVE",
     HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
     WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,
     SOURCE_ORIGINALS_CHANGED="NO",STATUS="VALUE_MAP_COMPLETE",
     NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
