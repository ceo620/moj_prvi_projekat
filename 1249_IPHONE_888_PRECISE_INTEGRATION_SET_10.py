#!/usr/bin/env python3
import json,re
from pathlib import Path

BATCH="IPHONE_888_PRECISE_INTEGRATION_SET_10"
R=Path("/root")
CAN=R/"FREYA_RAD_888/IPHONE_CANONICAL_888"
MAN=CAN/"INTEGRATION_MANIFEST.json"
SOURCES=[
 ("GIANT",R/"FREYA_GIANT_020_888",R/"FREYA_GIANT_020_888/MEMBERS.jsonl"),
 ("DEEP",R/"FREYA_DEEP_016_888",R/"FREYA_DEEP_016_888/RUN_1789208009922981000_cff2f695/MEMBERS.jsonl"),
]
HEX=re.compile(r'(?<![0-9a-fA-F])([0-9a-fA-F]{64})(?![0-9a-fA-F])')

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("MODE=STRICT_READ_ONLY")
print("MUTATION=NO")
print("="*72)

try:
    canon=set(x.lower() for x in HEX.findall(MAN.read_text("utf-8","ignore")))
except OSError as e:
    raise SystemExit("HOLD=CANON_MANIFEST_READ_"+type(e).__name__)

print("CANON_CONTENT_HASH_SET="+str(len(canon)))
all_candidates=[]
errors=0

for label,base,members in SOURCES:
    rows=0; covered=0; saved=0; candidate=0; missing_obj=0; bad=0
    cands=[]
    try:
        with members.open("r",encoding="utf-8",errors="strict") as f:
            for line in f:
                if not line.strip(): continue
                try: o=json.loads(line)
                except Exception:
                    bad+=1; continue
                if not isinstance(o,dict): continue
                rows+=1
                h=str(o.get("sha256","")).lower()
                obj=o.get("object")
                status=str(o.get("status",""))
                if h in canon:
                    covered+=1
                    continue
                if obj:
                    q=base/str(obj)
                    if q.is_file():
                        saved+=1; candidate+=1
                        rec=(label,h,str(q),int(o.get("bytes",q.stat().st_size)),status,
                             str(o.get("name",o.get("member",""))))
                        cands.append(rec); all_candidates.append(rec)
                    else:
                        missing_obj+=1
    except OSError:
        errors+=1
    # unique by content hash
    uniq={}
    for x in cands: uniq.setdefault(x[1],x)
    print("SOURCE="+label)
    print("MEMBER_ROWS="+str(rows))
    print("ALREADY_COVERED_BY_CANON="+str(covered))
    print("PHYSICAL_SAVED_SOURCE_ONLY_ROWS="+str(saved))
    print("UNIQUE_INTEGRATE_CANDIDATE_HASHES="+str(len(uniq)))
    print("MISSING_OBJECT_ROWS="+str(missing_obj))
    print("BAD_JSON_ROWS="+str(bad))
    for h,x in list(sorted(uniq.items()))[:80]:
        print(" CANDIDATE_SHA256="+h)
        print(" CANDIDATE_OBJECT="+x[2])
        print(" CANDIDATE_BYTES="+str(x[3]))
        print(" CANDIDATE_STATUS="+x[4])
        print(" CANDIDATE_ORIGIN="+x[5][:1200])
    print("---")

uniq_all={}
for x in all_candidates: uniq_all.setdefault(x[1],x)
print("="*72)
print("TOTAL_UNIQUE_INTEGRATE_CANDIDATES="+str(len(uniq_all)))
print("TOTAL_CANDIDATE_BYTES="+str(sum(x[3] for x in uniq_all.values())))
print("READ_ERRORS="+str(errors))
print("MUTATION_OCCURRED=NO")
print("DECISION="+("READY_FOR_HUMAN_GATE_INTEGRATION_DESIGN" if errors==0 else "HOLD_READ_ERROR"))
print("RESULT="+("PASS_PRECISE_INTEGRATION_SET" if errors==0 else "HOLD"))
print("NEXT=RETURN_COMPLETE_OUTPUT")
