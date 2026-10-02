#!/usr/bin/env python3
import os, stat, hashlib, json, pathlib, collections

CANON="/root/FREYA_IPHONE_ISH_NODE_888"
ROOTS=["/root","/home","/tmp","/var","/etc","/opt","/usr/local"]
PRUNE={"/proc","/sys","/dev","/run","/var/run","/var/lock","/var/cache","/var/tmp","/usr/lib","/usr/share","/usr/bin","/usr/sbin","/bin","/sbin","/lib"}
TEXT={".txt",".md",".json",".jsonl",".csv",".yaml",".yml",".ini",".cfg",".conf",".env",".sh",".py",".log",".xml",".toml",".service",".timer"}
SIG=("freya","protocol","888","ssot","evidence","registry","report","recover","preserv","backup","archive","manifest","seal","canonical","iphone","ish","audit","receipt","governance","config","dispatcher","agent","integrat")

def inside(p):
    try: return os.path.commonpath([os.path.realpath(p),os.path.realpath(CANON)])==os.path.realpath(CANON)
    except: return False

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def signals(p,n):
    hits=set(s for s in SIG if s in p.lower())
    ext=pathlib.Path(p).suffix.lower()
    if ext in TEXT or n<=262144:
        try:
            with open(p,"rb") as f: t=f.read(min(n,2097152)).decode("utf-8","ignore").lower()
            hits.update(s for s in SIG if s in t)
        except: pass
    return sorted(hits)

print(json.dumps({"event":"BEGIN","PROTOCOL":888,"BATCH":"IPHONE_888_CENSUS_01","MODE":"READ_ONLY","CANON":CANON,"ZIP":0,"DELETE":"NO","NETWORK":"NO"}))
if not os.path.isdir(CANON):
    print(json.dumps({"event":"FAIL_CLOSED","reason":"CANONICAL_ROOT_MISSING"})); raise SystemExit(88)

objs=[]; errs=[]; seen=set()
for sr in ROOTS:
    if not os.path.exists(sr): continue
    for base,dirs,files in os.walk(sr,topdown=True,followlinks=False):
        rb=os.path.realpath(base)
        if rb in seen: dirs[:]=[]; continue
        seen.add(rb)
        dirs[:]=[d for d in dirs if os.path.realpath(os.path.join(base,d)) not in PRUNE]
        for name in files:
            p=os.path.join(base,name)
            try:
                st=os.lstat(p)
                if not stat.S_ISREG(st.st_mode): continue
                h=sha(p); sig=signals(p,st.st_size)
                objs.append({"path":p,"size":st.st_size,"mtime":int(st.st_mtime),"sha256":h,"canonical":inside(p),"signals":sig})
            except Exception as e:
                errs.append({"path":p,"error":type(e).__name__+":"+str(e)[:120]})

groups=collections.defaultdict(list)
for o in objs: groups[o["sha256"]].append(o)
canonhash={h for h,g in groups.items() if any(x["canonical"] for x in g)}

review=[]; dup=[]
for o in objs:
    if o["canonical"]: continue
    if o["sha256"] in canonhash: dup.append(o)
    elif o["signals"]: review.append(o)

print(json.dumps({"event":"SUMMARY","files":len(objs),"canonical":sum(x["canonical"] for x in objs),"outside_review":len(review),"outside_duplicate":len(dup),"errors":len(errs)}))
print("=== REVIEW ===")
for o in sorted(review,key=lambda x:(-len(x["signals"]),-x["size"],x["path"])): print(json.dumps(o,sort_keys=True))
print("=== DUPLICATE_WITH_CANONICAL ===")
for o in sorted(dup,key=lambda x:x["path"]): print(json.dumps(o,sort_keys=True))
print("=== ERRORS ===")
for e in errs: print(json.dumps(e,sort_keys=True))
print(json.dumps({"event":"GATE","result":"PASS" if not errs else "HOLD_READ_ERRORS","mutation":"NO","delete":"NO","next":"RETURN_FULL_OUTPUT"}))
