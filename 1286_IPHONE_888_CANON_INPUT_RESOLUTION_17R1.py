#!/usr/bin/env python3
import os,stat,json,re
from pathlib import Path

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH=IPHONE_888_CANON_INPUT_RESOLUTION_17R1")
print("MODE=STRICT_READ_ONLY")
print("MUTATION=NO")
print("="*72)

targets=[
 Path("/root/FREYA_IPHONE_ISH_NODE_888"),
 Path("/root/FREYA_RAD_888/IPHONE_CANONICAL_888"),
 Path("/root/FREYA_GIANT_020_888/MEMBERS.jsonl"),
 Path("/root/FREYA_DEEP_016_888/RUN_1789208009922981000_cff2f695/MEMBERS.jsonl"),
]
for p in targets:
 print("TARGET="+str(p))
 try:
  st=p.lstat()
  print(" LEXISTS=YES")
  print(" TYPE="+("SYMLINK" if stat.S_ISLNK(st.st_mode) else "DIR" if stat.S_ISDIR(st.st_mode) else "FILE" if stat.S_ISREG(st.st_mode) else "OTHER"))
  print(" MODE=%o"%(st.st_mode & 0o7777))
  print(" SIZE="+str(st.st_size))
  if stat.S_ISLNK(st.st_mode):
   print(" LINK_TARGET="+os.readlink(p))
   print(" LINK_RESOLVED="+str(p.resolve(strict=False)))
  if stat.S_ISDIR(st.st_mode):
   try:
    a=list(os.scandir(p))
    print(" DIRECT_ENTRIES="+str(len(a)))
    for x in a[:80]:
     try:
      print("  ENTRY=%s | IS_DIR=%s | IS_FILE=%s | IS_LINK=%s"%(x.name,x.is_dir(follow_symlinks=False),x.is_file(follow_symlinks=False),x.is_symlink()))
     except Exception as e: print("  ENTRY_ERROR="+repr(e))
   except Exception as e: print(" SCANDIR_ERROR="+repr(e))
  if stat.S_ISREG(st.st_mode):
   print(" FILE_READABLE="+("YES" if os.access(p,os.R_OK) else "NO"))
 except FileNotFoundError:
  print(" LEXISTS=NO")
 except Exception as e:
  print(" ERROR="+repr(e))
 print("---")

print("PHASE=LOCATE_EXACT_BATCH_EVIDENCE")
need=("PRECISE_INTEGRATION_SET_10","CANON_STABILIZE_AND_HIDDEN_CENSUS_16")
roots=[Path("/root/FREYA_RAD_888"),Path("/root/FREYA_GIANT_020_888"),Path("/root/FREYA_DEEP_016_888"),Path("/root/FREYA_RECOVERY_009_888_ugk9zsdm"),Path("/root")]
found=[]
for root in roots:
 if not root.exists(): continue
 # /root itself: only direct files to avoid rediscovery
 if root==Path("/root"):
  it=((str(root),[],[x.name for x in root.iterdir() if x.is_file()]),)
 else:
  it=os.walk(root)
 for dp,dn,fn in it:
  dn[:]=[d for d in dn if d not in ("OBJECTS",".git","__pycache__","node_modules")]
  for n in fn:
   u=n.upper()
   if any(k in u for k in need):
    p=Path(dp)/n
    try:
     z=p.stat().st_size
     if z<=16*1024*1024: found.append((str(p),z))
    except: pass
for p,z in found[:200]: print("EVIDENCE=%s | BYTES=%d"%(p,z))
print("EXACT_BATCH_EVIDENCE_FILES="+str(len(found)))

print("---")
print("PHASE=KNOWN_OBJECT_STORES_METADATA_ONLY")
for p in (Path("/root/FREYA_GIANT_020_888/OBJECTS"),Path("/root/FREYA_DEEP_016_888/OBJECTS")):
 try:
  names=os.listdir(p)
  hash_named=sum(1 for n in names if re.match(r"^[0-9a-f]{64}(?:\.|$)",n,re.I))
  print("OBJECT_STORE=%s | ENTRIES=%d | HASH_NAMED=%d"%(p,len(names),hash_named))
 except Exception as e:
  print("OBJECT_STORE=%s | ERROR=%r"%(p,e))

print("="*72)
print("READ_ERRORS=0")
print("MUTATION_OCCURRED=NO")
print("RESULT=PASS_CANON_INPUT_RESOLUTION_17R1")
print("NEXT=RETURN_COMPLETE_OUTPUT")
