#!/usr/bin/env python3
import os,json,hashlib,stat
R="/root"
EXCLUDE=("FREYA_SEGMENTS_014_d_20s9r2","FREYA_COMPARE_014R1_d_20s9r2")
KEY=("FINAL","SEAL","SSOT","CANON","STATUS","MANIFEST","REGISTRY","FREYA_RAD_888")
def H(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
print(json.dumps({"event":"BEGIN","batch":"IPHONE_888_CANON_DECISION_03","mode":"READ_ONLY","root":R}))
print("=== TOP_LEVEL_DIR_SUMMARY ===")
for n in sorted(os.listdir(R)):
 p=os.path.join(R,n)
 try:
  st=os.lstat(p)
  if not stat.S_ISDIR(st.st_mode): continue
  fc=dc=sz=0
  for b,ds,fs in os.walk(p,followlinks=False):
   dc+=len(ds); fc+=len(fs)
   for f in fs:
    try: sz+=os.lstat(os.path.join(b,f)).st_size
    except: pass
  print(json.dumps({"dir":p,"files":fc,"dirs":dc,"bytes":sz}))
 except Exception as e: print(json.dumps({"dir":p,"error":type(e).__name__}))
print("=== CANONICAL_CONTROL_SIGNALS ===")
hits=[]
for b,ds,fs in os.walk(R,topdown=True,followlinks=False):
 if b==R:
  ds[:]=[d for d in ds if d not in EXCLUDE]
 rel=b[len(R)+1:]
 if rel.count(os.sep)>5: ds[:]=[]; continue
 for f in fs:
  u=(b+"/"+f).upper()
  if any(k in u for k in KEY):
   p=os.path.join(b,f)
   try:
    st=os.lstat(p)
    if stat.S_ISREG(st.st_mode) and st.st_size<=5_000_000:
     hits.append((int(st.st_mtime),p,st.st_size,H(p)))
   except: pass
for m,p,z,h in sorted(hits,reverse=True)[:250]:
 print(json.dumps({"mtime":m,"path":p,"size":z,"sha256":h}))
print(json.dumps({"event":"GATE","signals":len(hits),"mutation":"NO","delete":"NO","zip_create":"NO","decision":"NO_NEW_CANON_YET","next":"RETURN_FULL_OUTPUT"}))
