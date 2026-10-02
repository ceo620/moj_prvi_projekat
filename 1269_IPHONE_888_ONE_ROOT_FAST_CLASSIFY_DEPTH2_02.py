#!/usr/bin/env python3
import os
from pathlib import Path

ROOT=Path("/root")
BATCH="IPHONE_888_ONE_ROOT_FAST_CLASSIFY_DEPTH2_02"

def info(path):
    files=dirs=others=errors=0
    total=0
    try:
        with os.scandir(path) as it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False): dirs+=1
                    elif e.is_file(follow_symlinks=False):
                        files+=1
                        try: total+=e.stat(follow_symlinks=False).st_size
                        except OSError: errors+=1
                    else: others+=1
                except OSError: errors+=1
    except OSError: errors+=1
    return dirs,files,others,total,errors

def sig(name):
    x=name.lower()
    rules=[
      ("CANONICAL","canonical"),("SSOT","ssot"),("REGISTRY","registr"),
      ("RUNTIME","runtime"),("EVIDENCE","evidence"),("AUDIT","audit"),
      ("RESULTS","result"),("RESULTS","rezultat"),("REPORT","report"),
      ("OUTPUT","output"),("RECOVERY","recover"),("BACKUP","backup"),
      ("ARCHIVE","archiv"),("LEGACY","legacy"),("STAGING","stag"),
      ("SYSTEM","sistem"),("SYSTEM","system"),("ZIP","zip")]
    a=[]
    for label,key in rules:
        if key in x and label not in a: a.append(label)
    return ",".join(a) if a else "UNKNOWN"

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("DEPTH=2")
print("CONTENT_READ=NO")
print("FULL_HASH=NO")
print("MUTATION=NO")
print("="*72)

if os.geteuid()!=0: raise SystemExit("HOLD=NOT_ROOT")
errors=0
roots=[]
for e in sorted(os.scandir(ROOT),key=lambda z:z.name.lower()):
    try:
        if e.is_dir(follow_symlinks=False): roots.append(Path(e.path))
    except OSError: errors+=1

for r in roots:
    d,f,o,b,er=info(r); errors+=er
    print("ROOT="+str(r))
    print("ROOT_DIRECT_DIRS=%d ROOT_DIRECT_FILES=%d ROOT_DIRECT_FILE_BYTES=%d SIGNAL=%s"%(d,f,b,sig(r.name)))
    try:
        children=sorted(os.scandir(r),key=lambda z:z.name.lower())
    except OSError:
        errors+=1; print("CHILD_SCAN=ERROR"); print("---"); continue
    for e in children:
        try:
            if e.is_dir(follow_symlinks=False):
                q=Path(e.path); d2,f2,o2,b2,er2=info(q); errors+=er2
                print(" CHILD=%s | DIRS=%d | FILES=%d | FILE_BYTES=%d | SIGNAL=%s"%(e.name,d2,f2,b2,sig(e.name)))
            elif e.is_file(follow_symlinks=False):
                try: z=e.stat(follow_symlinks=False).st_size
                except OSError: z=-1; errors+=1
                print(" FILE=%s | BYTES=%d | SIGNAL=%s"%(e.name,z,sig(e.name)))
        except OSError: errors+=1
    print("---")

canon=Path("/root/FREYA_RAD_888/IPHONE_CANONICAL_888")
print("="*72)
print("CANONICAL_CANDIDATE="+str(canon))
print("CANONICAL_EXISTS="+("YES" if canon.is_dir() else "NO"))
if canon.is_dir():
    d,f,o,b,er=info(canon); errors+=er
    print("CANON_DIRECT_DIRS=%d"%d)
    print("CANON_DIRECT_FILES=%d"%f)
    print("CANON_DIRECT_FILE_BYTES=%d"%b)
    try:
        for e in sorted(os.scandir(canon),key=lambda z:z.name.lower()):
            if e.is_dir(follow_symlinks=False):
                q=Path(e.path); d2,f2,o2,b2,er2=info(q); errors+=er2
                print(" CANON_CHILD=%s | DIRS=%d | FILES=%d | FILE_BYTES=%d | SIGNAL=%s"%(e.name,d2,f2,b2,sig(e.name)))
            elif e.is_file(follow_symlinks=False):
                print(" CANON_FILE=%s | BYTES=%d | SIGNAL=%s"%(e.name,e.stat(follow_symlinks=False).st_size,sig(e.name)))
    except OSError: errors+=1

print("="*72)
print("SCAN_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("RESULT="+("PASS_FAST_CLASSIFY_DEPTH2" if errors==0 else "HOLD_READ_ERRORS"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
