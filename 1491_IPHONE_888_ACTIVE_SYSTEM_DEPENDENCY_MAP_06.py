#!/usr/bin/env python3
import os,re
from pathlib import Path

BATCH="IPHONE_888_ACTIVE_SYSTEM_DEPENDENCY_MAP_06"
BASE=Path("/root/FREYA_RAD_888/05_SISTEM")
AUTO=BASE/"AGENT_FACTORY/AUTOPILOT/IPHONE_888_AUTOPILOT.sh"
MAX=1024*1024
EXT={".sh",".py",".env",".json",".jsonl",".csv",".txt",".md"}

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("SCOPE="+str(BASE))
print("MUTATION=NO")
print("="*72)

if not BASE.is_dir(): raise SystemExit("HOLD=05_SISTEM_MISSING")
print("AUTOPILOT="+str(AUTO))
print("AUTOPILOT_EXISTS="+("YES" if AUTO.is_file() else "NO"))

refs=set(); errors=0; scanned=0
for dp,dns,fns in os.walk(BASE,followlinks=False):
    d=Path(dp)
    for n in fns:
        q=d/n
        try:
            st=q.stat()
            if st.st_size>MAX or q.suffix.lower() not in EXT: continue
            data=q.read_bytes()
            if b"\0" in data[:4096]: continue
            txt=data.decode("utf-8","ignore"); scanned+=1
            found=sorted(set(re.findall(r'/root/[A-Za-z0-9_./ \-]+',txt)))
            if found or any(k in n.lower() for k in ("registry","current","pointer","binding","runtime","autopilot","manifest")):
                print("FILE="+str(q.relative_to(BASE))+" BYTES="+str(st.st_size))
                for x in found[:30]:
                    x=x.rstrip(" '\"\t\r\n);,")
                    refs.add(x)
                    print(" ABS_REF="+x[:1200])
                for i,line in enumerate(txt.splitlines(),1):
                    lo=line.lower()
                    if any(k in lo for k in ("registry","current","pointer","binding","runtime","autopilot")):
                        print(" SIGNAL_LINE_%d=%s"%(i,line[:1200]))
        except OSError:
            errors+=1

print("="*72)
print("ABSOLUTE_REFERENCE_EXISTENCE")
for x in sorted(refs):
    try:
        q=Path(x)
        print("REF=%s | EXISTS=%s"%(x,"YES" if q.exists() else "NO"))
    except Exception:
        print("REF=%s | EXISTS=UNPARSEABLE"%x)

print("="*72)
print("TEXT_FILES_SCANNED="+str(scanned))
print("READ_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("RESULT="+("PASS_ACTIVE_DEPENDENCY_MAP" if errors==0 else "HOLD_READ_ERRORS"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
