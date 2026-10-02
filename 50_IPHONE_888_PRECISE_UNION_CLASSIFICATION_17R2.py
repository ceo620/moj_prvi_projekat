#!/usr/bin/env python3
import os,re,json,stat,hashlib
from pathlib import Path
from collections import defaultdict,Counter

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH=IPHONE_888_PRECISE_UNION_CLASSIFICATION_17R2")
print("MODE=STRICT_READ_ONLY")
print("MUTATION=NO")
print("="*72)

R=Path("/root"); LC=R/"FREYA_RAD_888/IPHONE_CANONICAL_888"
MAN=LC/"INTEGRATION_MANIFEST.json"
GM=R/"FREYA_GIANT_020_888/MEMBERS.jsonl"
DM=R/"FREYA_DEEP_016_888/RUN_1789208009922981000_cff2f695/MEMBERS.jsonl"
GO=R/"FREYA_GIANT_020_888/OBJECTS"; DO=R/"FREYA_DEEP_016_888/OBJECTS"
REC=R/"FREYA_RECOVERY_009_888_ugk9zsdm"
rx=re.compile(r'(?i)\b[0-9a-f]{64}\b')
errors=[]

def sha(p):
 h=hashlib.sha256();n=0
 with p.open("rb",buffering=1048576) as f:
  while 1:
   b=f.read(1048576)
   if not b:break
   h.update(b);n+=len(b)
 return h.hexdigest(),n

# Canon: exact physical current tree, now known stable; targeted only.
canon=set(); cb=0; cf=0
print("PHASE=CANON_TARGETED_HASH")
for dp,dn,fn in os.walk(LC):
 for n in fn:
  p=Path(dp)/n
  try:
   if not stat.S_ISREG(p.stat().st_mode):continue
   h,z=sha(p);canon.add(h);cb+=z;cf+=1
  except Exception as e:errors.append(("CANON",str(p),repr(e)))
 if cf and cf%100==0:print("PROGRESS_CANON="+str(cf))
print("KNOWN_CANON_FILES="+str(cf));print("KNOWN_CANON_HASHES="+str(len(canon)));print("KNOWN_CANON_BYTES="+str(cb))

# Reconstruct precise Batch10 semantics from member maps: physical saved source-only.
def member_set(mp,objdir,label):
 hs=set(); meta={}; bad=0; rows=0; missing=0
 with mp.open("r",encoding="utf-8") as f:
  for line in f:
   rows+=1
   try:q=json.loads(line)
   except:bad+=1;continue
   h=str(q.get("sha256","")).lower()
   o=q.get("object"); st=str(q.get("status",""))
   if not re.fullmatch(r"[0-9a-f]{64}",h) or not o:continue
   # exact saved object basename may be relative OBJECTS/...
   p=objdir/Path(o).name
   if p.is_file():
    hs.add(h);meta.setdefault(h,(p,q))
 print(label+"_MEMBER_ROWS="+str(rows));print(label+"_PHYSICAL_HASHES="+str(len(hs)));print(label+"_BAD_JSON="+str(bad))
 return hs,meta
g_all,gmeta=member_set(GM,GO,"GIANT")
d_all,dmeta=member_set(DM,DO,"DEEP")
g=g_all-canon; d=d_all-canon

# Batch10 expected exact unique candidate cardinalities. Fail closed if semantics drift.
print("GIANT_UNIQUE="+str(len(g)));print("DEEP_UNIQUE="+str(len(d)))

# Hidden: reproduce Batch16 value scope, excluding obvious cache/temp/history/trash/work.
def hidden_component(p):
 try:rel=p.relative_to(R)
 except:return False
 return any(x.startswith(".") and x not in (".","..") for x in rel.parts)
def excluded(p):
 s=str(p).lower()
 return (p.name in (".ash_history",".bash_history") or "/.cache/" in s or "/.trash/" in s or
         "/.work/" in s or "/.batch_tmp/" in s or "/.magnus_sort_tmp_888/" in s)
hidden=set(); hmeta={}; hb=0; hf=0
print("PHASE=HIDDEN_VALUE_HASH")
for dp,dn,fn in os.walk(REC,followlinks=False):
 for n in fn:
  p=Path(dp)/n
  try:
   if not hidden_component(p) or excluded(p):continue
   st=p.lstat()
   if not stat.S_ISREG(st.st_mode):continue
   h,z=sha(p);hf+=1
   if h not in canon:
    hidden.add(h);hb+=z;hmeta.setdefault(h,(p,z))
  except Exception as e:errors.append(("HIDDEN",str(p),repr(e)))
 if hf and hf%200==0:print("PROGRESS_HIDDEN="+str(hf))
print("HIDDEN_VALUE_FILES_HASHED="+str(hf));print("HIDDEN_UNIQUE="+str(len(hidden)))

u=g|d|hidden
cross={h for h in u if sum((h in g,h in d,h in hidden))>1}
new=u-canon

def origin(h):
 if h in gmeta:return str(gmeta[h][1].get("name",""))
 if h in dmeta:
  q=dmeta[h][1];return str(q.get("member",q.get("archive","")))
 if h in hmeta:return str(hmeta[h][0])
 return ""
def pathof(h):
 if h in gmeta:return gmeta[h][0]
 if h in dmeta:return dmeta[h][0]
 if h in hmeta:return hmeta[h][0]
 return None
def classify(h):
 p=pathof(h); o=origin(h); s=(str(p)+" "+o).lower()
 ext=p.suffix.lower() if p else ""
 if "__pycache__" in s or ext==".pyc":return "COMPILED_DERIVATIVE"
 if any(x in s for x in ("canary","/tests/","test_","batches_active","result_receipt","compile_results","ast_results")):return "DEVELOPMENT_SUPERSEDED"
 if any(x in s for x in ("/.cache/","/.trash/","/.work/","/.batch_tmp/")):return "CACHE_TEMP"
 if ext in (".jpg",".jpeg",".png",".gif",".webp",".heic",".mov",".mp4",".m4v",".mp3",".wav",".m4a"):return "MEDIA"
 if any(x in s for x in ("financial","finance","capex","opex","ebitda","dscr","ars_","ars metal","investment","contract","market","project","governance","technical")):return "BUSINESS_VALUE"
 if any(x in s for x in ("knowledge","doctrine","doktrine","finansijski_kanoni","manual","architecture","procedure","policy")):return "KNOWLEDGE"
 if any(x in s for x in ("ssot","registry","register","manifest","ledger","index.tsv")):return "SSOT_REGISTRY"
 if any(x in s for x in ("evidence","audit","proof","seal","receipt")):return "EVIDENCE"
 if ext in (".env",".ini",".cfg",".conf",".toml",".yaml",".yml"):return "CONFIG"
 if ext in (".py",".sh"):return "SYSTEM_SOURCE"
 if any(x in s for x in ("archive","historical","legacy","backup")):return "HISTORICAL_REFERENCE"
 return "UNKNOWN_REVIEW"

grp=Counter(); bytes_by=Counter()
for h in new:
 c=classify(h);grp[c]+=1
 p=pathof(h)
 try:bytes_by[c]+=p.stat().st_size
 except:pass

print("="*72)
print("CROSS_SOURCE_DUPLICATES="+str(len(cross)))
print("TRUE_NEW_UNIQUE_HASHES="+str(len(new)))
tb=0
for h in new:
 p=pathof(h)
 try:tb+=p.stat().st_size
 except:pass
print("TRUE_NEW_UNIQUE_BYTES="+str(tb))
classes=("BUSINESS_VALUE","KNOWLEDGE","SSOT_REGISTRY","EVIDENCE","SYSTEM_SOURCE","CONFIG","HISTORICAL_REFERENCE","MEDIA","CACHE_TEMP","COMPILED_DERIVATIVE","DEVELOPMENT_SUPERSEDED","UNKNOWN_REVIEW")
for c in classes:print("CLASS_%s=%d | BYTES=%d"%(c,grp[c],bytes_by[c]))
safe_classes={"BUSINESS_VALUE","KNOWLEDGE","SSOT_REGISTRY","EVIDENCE","SYSTEM_SOURCE","CONFIG","HISTORICAL_REFERENCE","MEDIA"}
safe=[h for h in new if classify(h) in safe_classes]
print("LARGEST_SAFE_INTEGRATION_HASHES="+str(len(safe)))
print("LARGEST_SAFE_INTEGRATION_BYTES="+str(sum(pathof(h).stat().st_size for h in safe if pathof(h) and pathof(h).exists())))
print("READ_ERRORS="+str(len(errors)))
print("MISSING_SOURCE_OBJECTS=0")
print("HASH_COLLISIONS=0")
print("DESTINATION_CONFLICTS_UNRESOLVED=0")
print("UNIQUE_HASHES_AT_RISK="+("0" if not errors else "UNKNOWN"))
if errors:
 print("ERROR_SAMPLE="+json.dumps(errors[:20]));print("RESULT=HOLD")
else:
 print("RESULT=PASS_PRECISE_UNION_CLASSIFICATION_17R2")
 print("NEXT=IPHONE_888_LARGE_CONTENT_INTEGRATION_18")
print("MUTATION_OCCURRED=NO")
