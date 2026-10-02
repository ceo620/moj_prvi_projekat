#!/usr/bin/env python3
import os, json
from pathlib import Path

BATCH="IPHONE_888_CORE_AUTHORITY_TRIAGE_04"
RAD=Path("/root/FREYA_RAD_888")
CAN=RAD/"IPHONE_CANONICAL_888"
SYS=RAD/"05_SISTEM"
REC=Path("/root/FREYA_RECOVERY_009_888_ugk9zsdm/RECOVERED/root/FREYA_IPHONE_ISH_NODE_888")
MAX=1024*1024
KEYWORDS=("registry","runtime","binding","current","ssot","authority","identity","control",
          "human_gate","human-gate","dispatcher","launcher","orchestrator","seal","manifest")

def shallow(base, depth=2):
    out=[]; err=0
    if not base.is_dir(): return out,1
    bd=len(base.parts)
    for dp,dns,fns in os.walk(base,followlinks=False):
        d=Path(dp); dep=len(d.parts)-bd
        if dep>=depth: dns[:]=[]
        for n in sorted(fns):
            q=d/n
            try:
                st=q.stat()
                low=str(q.relative_to(base)).lower()
                if any(k in low for k in KEYWORDS):
                    out.append((str(q.relative_to(base)),st.st_size))
            except OSError: err+=1
    return out,err

def control_text(base, depth=2):
    rows=[]; err=0
    if not base.is_dir(): return rows,1
    bd=len(base.parts)
    for dp,dns,fns in os.walk(base,followlinks=False):
        d=Path(dp); dep=len(d.parts)-bd
        if dep>=depth: dns[:]=[]
        for n in sorted(fns):
            q=d/n; low=n.lower()
            if not any(k in low for k in KEYWORDS): continue
            try:
                st=q.stat()
                if st.st_size>MAX or q.suffix.lower() not in {".txt",".env",".json",".jsonl",".csv",".md",".sh",".py"}:
                    continue
                data=q.read_bytes()
                if b"\0" in data[:4096]: continue
                txt=data.decode("utf-8","ignore")
                rows.append((str(q.relative_to(base)),st.st_size,
                    "/root/FREYA_IPHONE_ISH_NODE_888" in txt,
                    "/root/FREYA_RAD_888" in txt,
                    "/root/FREYA_RAD_888/IPHONE_CANONICAL_888" in txt))
            except OSError: err+=1
    return rows,err

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("MUTATION=NO")
print("FULL_HASH=NO")
print("="*72)

errors=0
for label,base,depth in [("RECOVERED_CORE",REC,2),("CURRENT_05_SISTEM",SYS,3),("CANONICAL",CAN,2)]:
    print("SECTION="+label)
    print("PATH="+str(base))
    print("EXISTS="+("YES" if base.is_dir() else "NO"))
    rows,er=shallow(base,depth); errors+=er
    print("CONTROL_CANDIDATES="+str(len(rows)))
    for rel,size in rows[:180]:
        print(" ITEM=%s | BYTES=%d"%(rel,size))
    text,er=control_text(base,depth); errors+=er
    print("CONTROL_TEXT_READ="+str(len(text)))
    for rel,size,old,rad,can in text[:180]:
        print(" REF=%s | BYTES=%d | OLD_ROOT=%s | RAD_ROOT=%s | CANON_ROOT=%s"%
              (rel,size,"YES" if old else "NO","YES" if rad else "NO","YES" if can else "NO"))
    print("---")

print("="*72)
print("RECOVERY_CORE_TOPLEVEL")
if REC.is_dir():
    try:
        for e in sorted(os.scandir(REC),key=lambda x:x.name.lower()):
            if e.is_dir(follow_symlinks=False):
                try:
                    fc=sum(1 for x in os.scandir(e.path) if x.is_file(follow_symlinks=False))
                    dc=sum(1 for x in os.scandir(e.path) if x.is_dir(follow_symlinks=False))
                    print(" DIR=%s | DIRECT_DIRS=%d | DIRECT_FILES=%d"%(e.name,dc,fc))
                except OSError:
                    errors+=1; print(" DIR=%s | READ=ERROR"%e.name)
    except OSError: errors+=1

print("="*72)
print("SCAN_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("RESULT="+("PASS_CORE_AUTHORITY_TRIAGE" if errors==0 else "HOLD_CORE_READ_ERROR"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
