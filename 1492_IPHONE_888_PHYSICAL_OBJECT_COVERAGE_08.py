#!/usr/bin/env python3
import os,re
from pathlib import Path

BATCH="IPHONE_888_PHYSICAL_OBJECT_COVERAGE_08"
ROOT=Path("/root")
CAN=ROOT/"FREYA_RAD_888/IPHONE_CANONICAL_888"
OBJDIRS=[
 ROOT/"FREYA_DEEP_016_888/OBJECTS",
 ROOT/"FREYA_GIANT_020_888/OBJECTS",
 ROOT/"FREYA_RECOVERY_009_888_ugk9zsdm/VERIFIED_PARTS",
]
HEX=re.compile(r'^([0-9a-fA-F]{64})(?:\.|$)')

def canon_manifest_hashes():
    p=CAN/"INTEGRATION_MANIFEST.json"
    import json
    hs=set()
    try:
        data=p.read_text("utf-8","ignore")
        hs.update(x.lower() for x in re.findall(r'(?<![0-9a-fA-F])([0-9a-fA-F]{64})(?![0-9a-fA-F])',data))
    except OSError: pass
    return hs

canon=canon_manifest_hashes()
print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("CONTENT_HASHING=NO")
print("MUTATION=NO")
print("CANON_MANIFEST_HASHES="+str(len(canon)))
print("="*72)

errors=0
for d in OBJDIRS:
    total=common=only=nonhash=0; bytes_total=bytes_only=0; samples=[]
    print("OBJECT_DIR="+str(d))
    print("EXISTS="+("YES" if d.is_dir() else "NO"))
    if d.is_dir():
        try:
            for e in os.scandir(d):
                try:
                    if not e.is_file(follow_symlinks=False): continue
                    st=e.stat(follow_symlinks=False); total+=1; bytes_total+=st.st_size
                    m=HEX.match(e.name)
                    if not m:
                        nonhash+=1; continue
                    h=m.group(1).lower()
                    if h in canon: common+=1
                    else:
                        only+=1; bytes_only+=st.st_size
                        if len(samples)<30: samples.append((e.name,st.st_size))
                except OSError: errors+=1
        except OSError: errors+=1
    print("FILES="+str(total))
    print("BYTES="+str(bytes_total))
    print("HASH_NAMED_COMMON_WITH_CANON="+str(common))
    print("HASH_NAMED_SOURCE_ONLY="+str(only))
    print("SOURCE_ONLY_BYTES="+str(bytes_only))
    print("NON_HASH_NAMED="+str(nonhash))
    for n,b in samples: print(" SOURCE_ONLY_FILE=%s | BYTES=%d"%(n,b))
    print("---")

print("READ_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("RESULT="+("PASS_PHYSICAL_OBJECT_COVERAGE" if errors==0 else "HOLD_OBJECT_READ_ERROR"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
