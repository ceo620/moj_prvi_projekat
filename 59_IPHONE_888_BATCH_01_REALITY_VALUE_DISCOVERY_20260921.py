#!/usr/bin/env python3
import os, sys, stat, hashlib, json, platform, subprocess, shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

PROTOCOL=888
NODE='FREYA_IPHONE_ISH_NODE_888'
BATCH='IPHONE_888_BATCH_01_REALITY_VALUE_DISCOVERY_20260921'
AUTH='DANIJELA_DJUROVIC_KESKIN'
MAX_FILES=120000
MAX_HASH_BYTES=32*1024*1024
HASH_BUDGET=384*1024*1024
HASH_EXT={'.py','.sh','.env','.json','.jsonl','.yaml','.yml','.toml','.ini','.cfg','.conf','.policy','.contract','.manifest','.receipt','.seal','.sql','.db','.sqlite','.sqlite3','.csv','.md','.txt'}
KEYWORDS={
 'SSOT':['ssot','single_source'], 'KNOWLEDGE':['knowledge','znanje','mozak'], 'DATABASE':['sqlite','.db','database'],
 'AGENT':['agent'], 'CONTRACT':['contract','ugovor'], 'POLICY':['policy','human_gate','protocol'],
 'DOCUMENT_PROCESSING':['document','docx','xlsx','pdf','processor','renderer'], 'FINANCIAL_VALIDATION':['financial','finance','validator','budget','capex'],
 'EVIDENCE':['evidence','dokaz','receipt','manifest'], 'TESTS':['test','regression'], 'RECOVERY':['recovery','recover'],
 'ASUS_HANDOFF':['asus','handoff','transport','ssh'], 'SEALS':['seal','closeout','final'], 'RUNTIME':['runtime','launcher','worker','watchdog','cron','scheduler','startup'],
 'ARCHIVE':['.zip','.tar','.tgz','.gz','.7z','archive'], 'HOLD':['hold','collision']
}

def emit(**kw): print(json.dumps(kw, ensure_ascii=False, sort_keys=True), flush=True)
def hold(reason):
    emit(PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE='ACTIVE',HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE='DENY',FAIL_CLOSED='YES',STATUS='HOLD',REASON=reason,WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED='NO',NEXT='STOP')
    raise SystemExit(2)
def read_small(p, limit=65536):
    try:
        with open(p,'rb') as f: return f.read(limit)
    except Exception: return b''
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        while True:
            b=f.read(1024*1024)
            if not b: break
            h.update(b)
    return h.hexdigest()
def cmd(args, timeout=4):
    try:
        r=subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
        return r.stdout.strip()[:12000]
    except Exception as e: return 'UNAVAILABLE:'+type(e).__name__

def classify(path):
    s=str(path).lower(); out=[]
    for k,vals in KEYWORDS.items():
        if any(v in s for v in vals): out.append(k)
    return out

# Identity gate
try:
    uid=os.geteuid(); user=cmd(['id','-un']); host=platform.node(); home=os.environ.get('HOME','')
    alpine=''
    if Path('/etc/alpine-release').is_file(): alpine=Path('/etc/alpine-release').read_text(errors='replace').strip()
    kernel=platform.release(); system=platform.system()
    root_ok=Path('/root').is_dir()
    if uid != 0 or user != 'root' or not alpine or not root_ok:
        hold('IPHONE_IDENTITY')
except Exception:
    hold('IPHONE_IDENTITY')

st=os.statvfs('/')
emit(event='BEGIN',PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE='ACTIVE',HUMAN_GATE_AUTHORITY=AUTH,OPERATOR=AUTH,DEFAULT_MODE='DENY',FAIL_CLOSED='YES',SSOT='SOVEREIGN',READ_ONLY_FIRST='YES',EVIDENCE_FIRST='YES',SCOPE_BOUND='YES',MODE='READ_ONLY',UTC=datetime.now(timezone.utc).isoformat())
emit(event='IDENTITY',hostname=host,user=user,uid=uid,system=system,alpine=alpine,kernel=kernel,HOME=home,root_exists=root_ok,filesystem_root_device=os.stat('/').st_dev,free_bytes=st.f_bavail*st.f_frsize,total_bytes=st.f_blocks*st.f_frsize)

# Discover plausible roots without assuming one canonical root.
root=Path('/root')
roots=[]
try:
    for p in root.iterdir():
        try:
            if p.is_dir() and any(x in p.name.lower() for x in ('freya','iphone','titan','ars','888')): roots.append(p)
        except OSError: pass
except OSError as e: hold('ROOT_ENUMERATION_FAILED:'+type(e).__name__)
roots=sorted(set(roots), key=lambda p:str(p))
emit(event='DISCOVERED_ROOTS',count=len(roots),paths=[str(x) for x in roots[:250]],truncated=len(roots)>250)

scan_roots=roots if roots else [root]
counts=Counter(); category_counts=Counter(); examples={k:[] for k in KEYWORDS}; db=[]; scripts=[]; archives=[]; candidates=[]; errors=[]
files_seen=0; hash_used=0
skip_prefixes=('/proc/','/sys/','/dev/','/run/')
for base in scan_roots:
    for dirpath, dirnames, filenames in os.walk(base, topdown=True, followlinks=False):
        dirnames[:] = [d for d in dirnames if not os.path.join(dirpath,d).startswith(skip_prefixes)]
        counts['directories'] += 1
        for name in filenames:
            files_seen += 1
            if files_seen > MAX_FILES: counts['scan_truncated']=1; break
            p=Path(dirpath)/name
            try:
                s=p.lstat()
                if stat.S_ISLNK(s.st_mode): counts['symlinks']+=1; continue
                if not stat.S_ISREG(s.st_mode): counts['nonregular']+=1; continue
                counts['files']+=1; counts['bytes']+=s.st_size
                cats=classify(p)
                for c in cats:
                    category_counts[c]+=1
                    if len(examples[c])<30: examples[c].append(str(p))
                ext=p.suffix.lower()
                if ext in ('.db','.sqlite','.sqlite3'): db.append((str(p),s.st_size))
                if ext in ('.py','.sh'): scripts.append((str(p),s.st_size))
                if ext in ('.zip','.tar','.tgz','.gz','.7z'): archives.append((str(p),s.st_size))
                # Hash only high-value/small metadata/code candidates, bounded by a total read budget.
                high = bool(cats) or ext in HASH_EXT
                if high and s.st_size <= MAX_HASH_BYTES and hash_used+s.st_size <= HASH_BUDGET:
                    try:
                        digest=sha256_file(p); hash_used += s.st_size
                        if len(candidates)<1500:
                            candidates.append({'path':str(p),'bytes':s.st_size,'sha256':digest,'categories':cats,'mode':oct(stat.S_IMODE(s.st_mode))})
                    except Exception as e:
                        if len(errors)<100: errors.append({'path':str(p),'error':type(e).__name__})
            except Exception as e:
                counts['stat_errors']+=1
                if len(errors)<100: errors.append({'path':str(p),'error':type(e).__name__})
        if files_seen > MAX_FILES: break
    if files_seen > MAX_FILES: break

emit(event='SCAN_SUMMARY',**dict(counts),hash_bytes_read=hash_used,hash_budget_bytes=HASH_BUDGET,scan_roots=[str(x) for x in scan_roots])
emit(event='VALUE_CATEGORY_COUNTS',counts=dict(category_counts))
for k in KEYWORDS: emit(event='CATEGORY_EXAMPLES',category=k,paths=examples[k])
emit(event='DATABASE_CANDIDATES',count=len(db),items=[{'path':p,'bytes':b} for p,b in db[:120]],truncated=len(db)>120)
emit(event='SCRIPT_CANDIDATES',count=len(scripts),items=[{'path':p,'bytes':b} for p,b in scripts[:200]],truncated=len(scripts)>200)
emit(event='ARCHIVE_STATE',count=len(archives),items=[{'path':p,'bytes':b} for p,b in archives[:160]],truncated=len(archives)>160)
emit(event='HASHED_HIGH_VALUE_CANDIDATES',count=len(candidates),items=candidates,truncated=(len(candidates)>=1500))

# Runtime/config discovery remains read-only.
emit(event='PROCESS_SNAPSHOT',ps=cmd(['ps','-ef'],6))
cron_paths=[]
for cp in ('/etc/crontabs','/etc/periodic','/var/spool/cron','/root/.ssh','/root/.profile','/root/.ashrc'):
    p=Path(cp)
    if p.exists(): cron_paths.append({'path':cp,'type':'dir' if p.is_dir() else 'file'})
emit(event='RUNTIME_CONFIG_LOCATIONS',items=cron_paths)
# SSH config metadata only; do not expose private key contents.
ssh=[]
sp=Path('/root/.ssh')
if sp.is_dir():
    try:
        for p in sp.iterdir():
            try:
                s=p.lstat(); ssh.append({'path':str(p),'bytes':s.st_size,'mode':oct(stat.S_IMODE(s.st_mode)),'type':'symlink' if stat.S_ISLNK(s.st_mode) else 'file' if stat.S_ISREG(s.st_mode) else 'other'})
            except OSError: pass
    except OSError: pass
emit(event='SSH_TRANSPORT_METADATA',items=ssh,CONTENT_READ='NO_PRIVATE_KEY_CONTENT')
if errors: emit(event='READ_ERRORS',count=len(errors),items=errors)

emit(PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE='ACTIVE',HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE='DENY',FAIL_CLOSED='YES',WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED='NO',STATUS='DISCOVERY_COMPLETE',NEXT='RETURN_COMPLETE_OUTPUT_TO_MAGNUS')
