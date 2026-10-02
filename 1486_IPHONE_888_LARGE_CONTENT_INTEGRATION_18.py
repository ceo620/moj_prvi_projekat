#!/usr/bin/env python3
import os,re,json,stat,hashlib,shutil
from pathlib import Path
from collections import defaultdict,Counter

R=Path("/root"); C=R/"FREYA_IPHONE_ISH_NODE_888"; LC=R/"FREYA_RAD_888/IPHONE_CANONICAL_888"
GM=R/"FREYA_GIANT_020_888/MEMBERS.jsonl"; DM=R/"FREYA_DEEP_016_888/RUN_1789208009922981000_cff2f695/MEMBERS.jsonl"
GO=R/"FREYA_GIANT_020_888/OBJECTS"; DO=R/"FREYA_DEEP_016_888/OBJECTS"; REC=R/"FREYA_RECOVERY_009_888_ugk9zsdm"
print("PROTOCOL=888\nNODE=FREYA_IPHONE_ISH_NODE_888\nBATCH=IPHONE_888_LARGE_CONTENT_INTEGRATION_18")
print("HUMAN_GATE=ACTIVE\nMODE=AUTHORIZED_LOCAL_MUTATION\nDELETE=NO\nRUNTIME_ACTIVATION=NO")
print("CANONICAL_ROOT="+str(C));print("="*72)
errors=[]; mutations=0
def sha(p):
 h=hashlib.sha256();n=0
 with p.open("rb",buffering=1048576) as f:
  while 1:
   b=f.read(1048576)
   if not b:break
   h.update(b);n+=len(b)
 return h.hexdigest(),n
def safe_name(x):
 x=re.sub(r'[\x00-\x1f/]+','_',x).strip()
 x=re.sub(r'\s+',' ',x)
 return x[:180] or "UNNAMED"
def atomic_copy(src,dst,h):
 global mutations
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  dh,_=sha(dst)
  if dh==h:return "ALREADY"
  raise RuntimeError("DESTINATION_CONFLICT "+str(dst))
 tmp=dst.with_name("."+dst.name+".tmp888")
 if tmp.exists():tmp.unlink()
 with src.open("rb") as a,tmp.open("xb") as b:
  while 1:
   q=a.read(1048576)
   if not q:break
   b.write(q)
 os.chmod(tmp,0o600)
 th,_=sha(tmp)
 if th!=h:
  tmp.unlink(missing_ok=True);raise RuntimeError("POSTCOPY_HASH_FAIL "+str(src))
 os.replace(tmp,dst);mutations+=1
 return "COPIED"

# Preflight: exact current canon
canon={};cb=0
for dp,dn,fn in os.walk(LC):
 for n in fn:
  p=Path(dp)/n
  try:
   if stat.S_ISREG(p.stat().st_mode):
    h,z=sha(p)
    if h in canon and canon[h]!=p: pass
    else: canon[h]=p
    cb+=z
  except Exception as e:errors.append(("CANON_READ",str(p),repr(e)))
if len(canon)!=444 or errors:
 print("RESULT=HOLD\nHOLD_REASON=CANON_PREFLIGHT actual=%d errors=%d"%(len(canon),len(errors)));raise SystemExit(2)

def member_set(mp,objdir):
 hs=set();meta={}
 with mp.open("r",encoding="utf-8") as f:
  for line in f:
   q=json.loads(line);h=str(q.get("sha256","")).lower();o=q.get("object")
   if re.fullmatch(r"[0-9a-f]{64}",h) and o:
    p=objdir/Path(o).name
    if p.is_file():hs.add(h);meta.setdefault(h,(p,q))
 return hs,meta
ga,gm=member_set(GM,GO);da,dm=member_set(DM,DO)
g=ga-set(canon);d=da-set(canon)

def hidden_component(p):
 try:rel=p.relative_to(R)
 except:return False
 return any(x.startswith(".") and x not in (".","..") for x in rel.parts)
def excluded(p):
 s=str(p).lower()
 return p.name in (".ash_history",".bash_history") or any(x in s for x in ("/.cache/","/.trash/","/.work/","/.batch_tmp/","/.magnus_sort_tmp_888/"))
hidden=set();hm={}
for dp,dn,fn in os.walk(REC,followlinks=False):
 for n in fn:
  p=Path(dp)/n
  try:
   if not hidden_component(p) or excluded(p):continue
   if not stat.S_ISREG(p.lstat().st_mode):continue
   h,z=sha(p)
   if h not in canon:hidden.add(h);hm.setdefault(h,(p,z))
  except Exception as e:errors.append(("HIDDEN_READ",str(p),repr(e)))
if errors:
 print("RESULT=HOLD\nHOLD_REASON=SOURCE_PREFLIGHT_READ_ERRORS "+str(len(errors)));raise SystemExit(2)

u=g|d|hidden
if len(u)!=556:
 print("RESULT=HOLD\nHOLD_REASON=UNION_DRIFT actual="+str(len(u)));raise SystemExit(2)
def pathof(h):
 if h in gm:return gm[h][0]
 if h in dm:return dm[h][0]
 if h in hm:return hm[h][0]
def origin(h):
 if h in gm:return str(gm[h][1].get("name",""))
 if h in dm:return str(dm[h][1].get("member",dm[h][1].get("archive","")))
 return str(hm[h][0]) if h in hm else ""
def classify(h):
 p=pathof(h);s=(str(p)+" "+origin(h)).lower();e=p.suffix.lower()
 if "__pycache__" in s or e==".pyc":return "COMPILED_DERIVATIVE"
 if any(x in s for x in ("canary","/tests/","test_","batches_active","result_receipt","compile_results","ast_results")):return "DEVELOPMENT_SUPERSEDED"
 if e in (".jpg",".jpeg",".png",".gif",".webp",".heic",".mov",".mp4",".m4v",".mp3",".wav",".m4a"):return "MEDIA"
 if any(x in s for x in ("financial","finance","capex","opex","ebitda","dscr","ars_","ars metal","investment","contract","market","project","governance","technical")):return "BUSINESS_VALUE"
 if any(x in s for x in ("knowledge","doctrine","doktrine","finansijski_kanoni","manual","architecture","procedure","policy")):return "KNOWLEDGE"
 if any(x in s for x in ("ssot","registry","register","manifest","ledger","index.tsv")):return "SSOT_REGISTRY"
 if any(x in s for x in ("evidence","audit","proof","seal","receipt")):return "EVIDENCE"
 if e in (".env",".ini",".cfg",".conf",".toml",".yaml",".yml"):return "CONFIG"
 if e in (".py",".sh"):return "SYSTEM_SOURCE"
 if any(x in s for x in ("archive","historical","legacy","backup")):return "HISTORICAL_REFERENCE"
 return "UNKNOWN_REVIEW"
allowed={"BUSINESS_VALUE","KNOWLEDGE","SSOT_REGISTRY","EVIDENCE","SYSTEM_SOURCE","CONFIG","HISTORICAL_REFERENCE","MEDIA"}
safe=[h for h in u if classify(h) in allowed]
if len(safe)!=451:
 print("RESULT=HOLD\nHOLD_REASON=CLASSIFICATION_DRIFT safe="+str(len(safe)));raise SystemExit(2)

print("PREFLIGHT_CANON_HASHES=444\nPREFLIGHT_TRUE_NEW_HASHES=556\nPREFLIGHT_SAFE_NEW_HASHES=451")
print("PHASE=SEED_CANONICAL_BASE")
base=C/"01_CANONICAL_BASE"
copied_base=already_base=0
for i,(h,src) in enumerate(sorted(canon.items()),1):
 rel=src.relative_to(LC)
 dst=base/rel
 try:
  r=atomic_copy(src,dst,h);copied_base+=r=="COPIED";already_base+=r=="ALREADY"
 except Exception as e:
  print("RESULT=HOLD\nHOLD_REASON="+repr(e));raise SystemExit(2)
 if i%100==0:print("PROGRESS_BASE=%d/444"%i)

destmap={"BUSINESS_VALUE":"02_BUSINESS_VALUE","KNOWLEDGE":"03_KNOWLEDGE","SSOT_REGISTRY":"04_SSOT_REGISTRY","EVIDENCE":"05_EVIDENCE","SYSTEM_SOURCE":"06_SYSTEM_SOURCE_HOLD","CONFIG":"07_CONFIG_HOLD","HISTORICAL_REFERENCE":"08_HISTORICAL_REFERENCE","MEDIA":"09_MEDIA"}
print("PHASE=INTEGRATE_SAFE_NEW")
copied_new=already_new=0; classcount=Counter()
for i,h in enumerate(sorted(safe),1):
 src=pathof(h);cl=classify(h);classcount[cl]+=1
 # Preserve useful origin basename where possible, hash prefix prevents collision.
 on=Path(origin(h)).name or src.name
 ext=src.suffix
 name=safe_name(Path(on).stem)
 dst=C/destmap[cl]/(name+"__"+h[:12]+ext)
 try:
  ah,az=sha(src)
  if ah!=h:raise RuntimeError("SOURCE_HASH_CHANGED "+str(src))
  r=atomic_copy(src,dst,h);copied_new+=r=="COPIED";already_new+=r=="ALREADY"
 except Exception as e:
  print("RESULT=HOLD\nHOLD_REASON="+repr(e));raise SystemExit(2)
 if i%50==0:print("PROGRESS_NEW=%d/451"%i)

print("PHASE=POST_MUTATION_VERIFY")
vh=set();vf=0;vb=0
for dp,dn,fn in os.walk(C):
 for n in fn:
  p=Path(dp)/n
  try:
   if stat.S_ISREG(p.stat().st_mode):
    h,z=sha(p);vh.add(h);vf+=1;vb+=z
  except Exception as e:errors.append(("POST_READ",str(p),repr(e)))
missing_base=set(canon)-vh;missing_new=set(safe)-vh
print("="*72)
print("BASE_COPIED="+str(copied_base));print("BASE_ALREADY_PRESENT="+str(already_base))
print("NEW_COPIED="+str(copied_new));print("NEW_ALREADY_PRESENT="+str(already_new))
print("CANONICAL_ROOT_FILES="+str(vf));print("CANONICAL_ROOT_UNIQUE_HASHES="+str(len(vh)));print("CANONICAL_ROOT_BYTES="+str(vb))
for k in sorted(classcount):print("INTEGRATED_"+k+"="+str(classcount[k]))
print("POST_MISSING_BASE_HASHES="+str(len(missing_base)))
print("POST_MISSING_SAFE_NEW_HASHES="+str(len(missing_new)))
print("POST_READ_ERRORS="+str(len(errors)))
print("UNIQUE_HASHES_AT_RISK="+str(len(missing_base)+len(missing_new)))
print("DELETE_OCCURRED=NO\nRUNTIME_ACTIVATION=NO")
if errors or missing_base or missing_new:
 print("RESULT=HOLD_POST_INTEGRATION_VERIFY")
else:
 print("RESULT=PASS_LARGE_CONTENT_INTEGRATION_18")
 print("NEXT=POST_INTEGRATION_HASH_VERIFICATION_AND_REMAINDER_19")
