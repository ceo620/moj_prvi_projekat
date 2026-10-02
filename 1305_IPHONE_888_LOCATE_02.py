#!/usr/bin/env python3
import os,json,stat,hashlib,collections,pathlib
EXPECTED="/root/FREYA_IPHONE_ISH_NODE_888"
ROOT="/root"
SIG=("freya","iphone","ish","888","ssot","protocol","evidence","registry","manifest","seal","audit","report","recover","preserv","backup","archive","canonical")
SKIP=("/proc/","/sys/","/dev/","/run/")
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
print(json.dumps({"event":"BEGIN","batch":"IPHONE_888_LOCATE_02","mode":"READ_ONLY","expected":EXPECTED}))
roots=[]; files=[]; errs=[]
for base,ds,fs in os.walk(ROOT,topdown=True,followlinks=False):
 if any(base.startswith(x) for x in SKIP): ds[:]=[]; continue
 low=base.lower()
 if any(s in low for s in SIG): roots.append(base)
 for n in fs:
  p=os.path.join(base,n)
  try:
   st=os.lstat(p)
   if not stat.S_ISREG(st.st_mode): continue
   pl=p.lower()
   if any(s in pl for s in SIG):
    files.append({"path":p,"size":st.st_size,"mtime":int(st.st_mtime),"sha256":sha(p)})
  except Exception as e: errs.append({"path":p,"error":type(e).__name__})
print("=== CANDIDATE_DIRECTORIES ===")
for p in sorted(set(roots)): print(p)
print("=== SIGNAL_FILES ===")
for x in sorted(files,key=lambda z:z["path"]): print(json.dumps(x,sort_keys=True))
print("=== ROOT_TOP_LEVEL ===")
try:
 for n in sorted(os.listdir(ROOT)):
  p=os.path.join(ROOT,n)
  try:
   s=os.lstat(p)
   print(json.dumps({"path":p,"type":"DIR" if stat.S_ISDIR(s.st_mode) else "FILE","size":s.st_size,"mtime":int(s.st_mtime)}))
  except Exception as e: print(json.dumps({"path":p,"error":type(e).__name__}))
except Exception as e: errs.append({"path":ROOT,"error":type(e).__name__})
print(json.dumps({"event":"GATE","expected_exists":os.path.isdir(EXPECTED),"candidate_dirs":len(set(roots)),"signal_files":len(files),"errors":len(errs),"mutation":"NO","delete":"NO","next":"RETURN_FULL_OUTPUT"}))
