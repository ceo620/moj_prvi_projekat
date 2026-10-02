#!/usr/bin/env python3
# PROTOCOL 888 — iPhone/iSH
# Batch 16: fast canonical stabilization + hidden-value candidate census
# HUMAN_GATE authorization supplied in chat. Local mutation only.
# No network, no execution of discovered files, no delete/move/rename of originals.

import os, stat, hashlib
from pathlib import Path
from collections import Counter

BATCH="IPHONE_888_CANON_STABILIZE_AND_HIDDEN_CENSUS_16"
OLD=Path("/root/FREYA_RAD_888/IPHONE_CANONICAL_888")
NEW=Path("/root/FREYA_IPHONE_ISH_NODE_888")
REC=Path("/root/FREYA_RECOVERY_009_888_ugk9zsdm")
EXCLUDE_TOP={OLD, NEW}
CHUNK=1024*1024

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb", buffering=0) as f:
        while True:
            b=f.read(CHUNK)
            if not b: break
            h.update(b)
    return h.hexdigest()

def safe_regular(p):
    try:
        s=p.lstat()
        return stat.S_ISREG(s.st_mode)
    except OSError:
        return False

print("PROTOCOL=888")
print("NODE=FREYA_IPHONE_ISH_NODE_888")
print("BATCH="+BATCH)
print("HUMAN_GATE=ACTIVE")
print("LOCAL_MUTATION_AUTHORIZED=YES")
print("DELETE=NO")
print("MOVE_ORIGINALS=NO")
print("RENAME_ORIGINALS=NO")
print("OVERWRITE=NO")
print("NETWORK=NO")
print("="*72)

# Canonical root: create only if absent. Do not create parallel content tree.
created=0
if not NEW.exists():
    NEW.mkdir(mode=0o700)
    created=1
elif not NEW.is_dir():
    raise SystemExit("HOLD=CANONICAL_ROOT_NOT_DIRECTORY")

# Hash current readable legacy canonical content. FileNotFound races are skipped,
# but every other read error fails closed.
canon={}
canon_errors=[]
canon_bytes=0
if OLD.is_dir():
    for base, dirs, files in os.walk(str(OLD), followlinks=False):
        dirs[:] = [d for d in dirs if not Path(base,d).is_symlink()]
        for n in files:
            p=Path(base,n)
            if p.is_symlink(): continue
            try:
                if not safe_regular(p): continue
                h=sha256(p)
                canon.setdefault(h,p)
                canon_bytes += p.stat().st_size
            except FileNotFoundError:
                continue
            except Exception as e:
                canon_errors.append((str(p),type(e).__name__,str(e)))
                if len(canon_errors)>=20: break
        if canon_errors: break

print("CANONICAL_ROOT="+str(NEW))
print("CANONICAL_ROOT_CREATED="+str(created))
print("LEGACY_CANONICAL="+str(OLD))
print("CANON_HASH_OK="+str(len(canon)))
print("CANON_HASH_BYTES="+str(canon_bytes))
print("CANON_FATAL_READ_ERRORS="+str(len(canon_errors)))
if canon_errors:
    for x in canon_errors: print(" ERROR=%s | %s | %s"%x)
    print("RESULT=HOLD_CANON_FATAL_READ_ERRORS")
    raise SystemExit(2)

# Fast hidden-value census only inside already-proven recovery source.
# Ignore caches/temp/history/config/runtime metadata and zero-byte files.
skip_parts={
    ".cache",".config",".obsidian",".WORK",".batch_tmp","__pycache__",
    ".Trash"
}
skip_names={".ash_history",".bashrc",".ashrc",".profile",".sha256"}
ext_count=Counter()
unique={}
covered=0
errors=0
scanned=0

if REC.is_dir():
    for base, dirs, files in os.walk(str(REC), followlinks=False):
        dirs[:] = [d for d in dirs if d not in skip_parts and not Path(base,d).is_symlink()]
        bparts=set(Path(base).parts)
        if bparts & skip_parts:
            dirs[:] = []
            continue
        for n in files:
            if not n.startswith(".") and ".titan_backup" not in Path(base).parts:
                continue
            p=Path(base,n)
            if n in skip_names or p.is_symlink(): continue
            try:
                s=p.stat()
                if not stat.S_ISREG(s.st_mode) or s.st_size==0: continue
                scanned+=1
                h=sha256(p)
                if h in canon:
                    covered+=1
                    continue
                unique.setdefault(h,(s.st_size,str(p)))
                ext_count[p.suffix.lower() or "<none>"]+=1
            except FileNotFoundError:
                continue
            except Exception:
                errors+=1

print("---")
print("HIDDEN_VALUE_FILES_HASHED="+str(scanned))
print("ALREADY_CANON_COVERED="+str(covered))
print("SOURCE_ONLY_UNIQUE_HASHES="+str(len(unique)))
print("SOURCE_ONLY_BYTES="+str(sum(v[0] for v in unique.values())))
print("HIDDEN_SCAN_ERRORS="+str(errors))
print("TOP_EXTENSIONS="+",".join("%s:%d"%x for x in ext_count.most_common(15)))
print("---")
print("LARGEST_SOURCE_ONLY_SAMPLE")
for h,(size,p) in sorted(unique.items(), key=lambda kv: kv[1][0], reverse=True)[:60]:
    print(" SHA256=%s | BYTES=%d | FILE=%s"%(h,size,p))

print("="*72)
print("MUTATION_OCCURRED="+("CANONICAL_ROOT_CREATE_ONLY" if created else "NO_CONTENT_MUTATION"))
if errors:
    print("RESULT=HOLD_HIDDEN_SCAN_ERRORS")
else:
    print("RESULT=PASS_CANON_STABILIZE_HIDDEN_CENSUS")
print("NEXT=RETURN_COMPLETE_OUTPUT_FOR_LARGEST_SAFE_INTEGRATION_BATCH")
