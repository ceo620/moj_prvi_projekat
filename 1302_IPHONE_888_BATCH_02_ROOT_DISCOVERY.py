import os, pwd, json
from pathlib import Path

def e(k,v): print(f"{k}={v}", flush=True)

e("PROTOCOL",888)
e("BATCH","IPHONE_888_ROOT_DISCOVERY_02")
e("MODE","READ_ONLY")
e("HUMAN_GATE","ACTIVE")
e("DEFAULT_MODE","DENY")
e("FAIL_CLOSED","YES")
e("WRITES",0); e("DELETIONS",0); e("OVERWRITES",0); e("NETWORK_ACTIONS",0)
e("HOST",os.uname().nodename)
e("USER",pwd.getpwuid(os.geteuid()).pw_name)
e("UID",os.geteuid())

if os.geteuid()!=0:
    e("STATUS","HOLD"); e("REASON","EXPECTED_ROOT_USER"); raise SystemExit

names=("freya","titan","iphone","ish","ssot","sovereign","cmu","knowledge",
       "agent","factory","document","evidence","seal","current","master",
       "runtime","automation","asus","handoff")
hits=[]
for base in (Path("/root"), Path("/mnt")):
    if not base.exists(): continue
    try:
        for root, dirs, files in os.walk(base, topdown=True, followlinks=False):
            depth=len(Path(root).parts)-len(base.parts)
            if depth>5:
                dirs[:]=[]
                continue
            low=root.lower()
            if any(x in low for x in names):
                hits.append(root)
            for n in files:
                p=str(Path(root)/n)
                if any(x in p.lower() for x in names):
                    hits.append(p)
            if len(hits)>=500:
                dirs[:]=[]
                break
    except OSError:
        pass
    if len(hits)>=500: break

uniq=[]
seen=set()
for x in hits:
    if x not in seen:
        seen.add(x); uniq.append(x)

e("CANDIDATES",len(uniq))
for i,x in enumerate(uniq[:500],1):
    e(f"CANDIDATE_{i:03d}",x)

e("STATUS","DISCOVERY_COMPLETE" if uniq else "HOLD")
e("REASON","CANONICAL_ROOT_NOT_ASSUMED_DISCOVERY_ONLY" if uniq else "NO_CANDIDATE_SURFACE_FOUND")
e("SOURCE_ORIGINALS_CHANGED","NO")
e("PROJECT_CODE_EXECUTED","NO")
e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
