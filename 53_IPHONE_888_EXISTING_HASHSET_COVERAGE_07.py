#!/usr/bin/env python3
import os,re,json
from pathlib import Path
BATCH="IPHONE_888_EXISTING_HASHSET_COVERAGE_07"
ROOT=Path("/root")
CAN=ROOT/"FREYA_RAD_888/IPHONE_CANONICAL_888"
SOURCES=[
 ROOT/"FREYA_COMPARE_014R1_d_20s9r2",
 ROOT/"FREYA_DEEP_016_888",
 ROOT/"FREYA_GIANT_020_888",
 ROOT/"FREYA_MAP_019_jyy5ir35",
 ROOT/"FREYA_RECOVERY_009_888_ugk9zsdm",
 ROOT/"FREYA_SEGMENTS_014_d_20s9r2",
]
HEX=re.compile(r'(?<![0-9a-fA-F])([0-9a-fA-F]{64})(?![0-9a-fA-F])')
MAX=8*1024*1024
NAMES=("manifest","sha256","hash","members","catalog","index","summary","comparison")
def harvest(base):
    hs=set(); files=[]; err=0
    if not base.exists(): return hs,files,1
    for dp,dns,fns in os.walk(base,followlinks=False):
        d=Path(dp)
        for n in fns:
            lo=n.lower()
            if not any(k in lo for k in NAMES): continue
            q=d/n
            try:
                st=q.stat()
                if st.st_size>MAX: continue
                b=q.read_bytes()
                if b"\0" in b[:4096]: continue
                t=b.decode("utf-8","ignore")
                got={m.lower() for m in HEX.findall(t)}
                if got:
                    hs.update(got); files.append((str(q),len(got),st.st_size))
            except OSError: err+=1
    return hs,files,err

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("CONTENT_HASHING=NO")
print("EXISTING_HASH_EVIDENCE_ONLY=YES")
print("MUTATION=NO")
print("="*72)

canon,cf,ce=harvest(CAN)
print("CANON_HASHES="+str(len(canon)))
print("CANON_EVIDENCE_FILES="+str(len(cf)))
for f,n,b in cf[:40]: print(" CANON_SOURCE=%s | HASHES=%d | BYTES=%d"%(f,n,b))
errors=ce
print("---")
for src in SOURCES:
    hs,fs,er=harvest(src); errors+=er
    common=hs & canon; only=hs-canon
    print("SOURCE="+str(src))
    print("EVIDENCE_HASHES="+str(len(hs)))
    print("COMMON_WITH_CANON="+str(len(common)))
    print("SOURCE_ONLY_HASHES="+str(len(only)))
    print("EVIDENCE_FILES="+str(len(fs)))
    for f,n,b in fs[:35]: print(" HASH_SOURCE=%s | HASHES=%d | BYTES=%d"%(f,n,b))
    for h in sorted(only)[:20]: print(" SOURCE_ONLY_SAMPLE="+h)
    print("---")
print("READ_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("RESULT="+("PASS_EXISTING_HASHSET_COVERAGE" if errors==0 else "HOLD_HASH_EVIDENCE_READ_ERROR"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
