#!/usr/bin/env python3
import json,re
from pathlib import Path

BATCH="IPHONE_888_OBJECT_MEMBER_MAPPING_09"
ROOT=Path("/root")
FILES=[
 ROOT/"FREYA_GIANT_020_888/MEMBERS.jsonl",
 ROOT/"FREYA_DEEP_016_888/RUN_1789208009922981000_cff2f695/MEMBERS.jsonl",
 ROOT/"FREYA_COMPARE_014R1_d_20s9r2/RUN_1789173782048236000_dcbf9ae9/CONTENT_COMPARISON.jsonl",
]
HEX=re.compile(r'^[0-9a-fA-F]{64}$')

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("MUTATION=NO")
print("="*72)

errors=0
for f in FILES:
    print("FILE="+str(f))
    print("EXISTS="+("YES" if f.is_file() else "NO"))
    if not f.is_file():
        print("---"); continue
    keys=set(); rows=0; shown=0
    try:
        with f.open("r",encoding="utf-8",errors="ignore") as h:
            for line in h:
                line=line.strip()
                if not line: continue
                try: obj=json.loads(line)
                except Exception: continue
                if not isinstance(obj,dict): continue
                rows+=1; keys.update(obj.keys())
                if shown<12:
                    print(" ROW="+json.dumps(obj,ensure_ascii=True,separators=(",",":"))[:3500])
                    shown+=1
    except OSError:
        errors+=1
    print("ROWS="+str(rows))
    print("KEYS="+",".join(sorted(str(k) for k in keys)))
    print("---")

print("READ_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("RESULT="+("PASS_OBJECT_MEMBER_MAPPING" if errors==0 else "HOLD_READ_ERROR"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
