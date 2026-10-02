#!/usr/bin/env python3
import os,json,hashlib,re,stat
from pathlib import Path

PROTOCOL=888
NODE="FREYA_IPHONE_ISH_NODE_888"
BATCH="IPHONE_888_BATCH_15_WRITES_AUDIT_20260921"
AUTH="DANIJELA_DJUROVIC_KESKIN"
SEAL=Path("/root/IPHONE_888_FINAL_LOCAL_PRODUCTION_SEAL_20260921.env")
SEAL_HASH="13ee3ff93a6a9a23d178b8164a868609e06f613acccf6072c80095b9d31bd775"

def emit(**x):
    print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

emit(PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE="ACTIVE",
     HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
     READ_ONLY="YES",MODE="READ_ONLY_WRITES_AUDIT")

alpine=Path("/etc/alpine-release")
if os.getuid()!=0 or not alpine.is_file():
    emit(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP")
    raise SystemExit(2)

if not SEAL.is_file():
    emit(STATUS="HOLD",REASON="FINAL_SEAL_GATE",detail="SEAL_MISSING",NEXT="STOP")
    raise SystemExit(3)
actual=sha256(SEAL)
emit(event="FINAL_SEAL_VERIFY",path=str(SEAL),expected_sha256=SEAL_HASH,
     actual_sha256=actual,match=(actual==SEAL_HASH))
if actual!=SEAL_HASH:
    emit(STATUS="HOLD",REASON="FINAL_SEAL_GATE",detail="SEAL_HASH_CHANGED",NEXT="STOP")
    raise SystemExit(4)

# Static discovery only: identify existing code/config containing write-capable primitives.
# Presence is NOT evidence that a write occurred.
patterns={
    "PYTHON_WRITE":[r"\.write_text\s*\(",r"\.write_bytes\s*\(",r"\bopen\s*\([^)\n]*['\"](?:w|a|x|w\+|a\+|x\+)"],
    "OS_WRITE":[r"\bos\.write\s*\(",r"\bos\.open\s*\("],
    "SHELL_REDIRECT":[r"(^|[;&| ])(?:echo|printf|cat)\b[^\n]*(?:>>|>)"],
    "COPY_CREATE":[r"\b(?:cp|install|touch|mkdir)\b"],
}
compiled={k:[re.compile(x,re.I|re.M) for x in v] for k,v in patterns.items()}
hits=[]
files_scanned=0
roots=[]
for q in Path("/root").iterdir():
    try:
        if q.is_dir() and any(k in q.name.upper() for k in ("FREYA","IPHONE","MOZAK")):
            roots.append(q)
    except OSError:
        pass

for base in roots:
    for dp,dn,fn in os.walk(str(base),topdown=True,followlinks=False):
        dn[:]=[d for d in dn if d not in (".git","__pycache__")]
        for name in fn:
            q=Path(dp)/name
            try:
                st=q.stat()
                if not stat.S_ISREG(st.st_mode) or st.st_size>2*1024*1024:
                    continue
                files_scanned+=1
                if q.suffix.lower() not in (".py",".sh",".env",".txt",".md",".json",".jsonl",""):
                    continue
                text=q.read_text(errors="replace")
                found=[]
                for kind,rxs in compiled.items():
                    if any(rx.search(text) for rx in rxs):
                        found.append(kind)
                if found:
                    hits.append({"path":str(q),"bytes":st.st_size,"sha256":sha256(q),"write_capability_markers":found})
            except OSError:
                pass

# Read current mounts to report writable filesystem surfaces without changing them.
mounts=[]
try:
    for line in Path("/proc/mounts").read_text(errors="replace").splitlines():
        parts=line.split()
        if len(parts)>=4:
            mounts.append({"device":parts[0],"mountpoint":parts[1],"fstype":parts[2],
                           "options":parts[3],"writable":"rw" in parts[3].split(",")})
except OSError:
    pass

emit(event="WRITES_STATIC_AUDIT",files_scanned=files_scanned,
     write_capability_candidate_count=len(hits),candidates=hits[:3000],
     note="CAPABILITY_MARKER_PRESENCE_IS_NOT_EXECUTION_EVIDENCE")
emit(event="FILESYSTEM_WRITE_SURFACES",mounts=mounts,
     note="RW_MOUNT_IS_CAPABILITY_NOT_PROOF_OF_WRITE")

emit(PROTOCOL=PROTOCOL,NODE=NODE,BATCH=BATCH,HUMAN_GATE="ACTIVE",
     HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
     READ_ONLY="YES",WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,
     SOURCE_ORIGINALS_CHANGED="NO",FINAL_SEAL_SHA256=actual,
     WRITE_ACTIONS_PERFORMED_BY_THIS_BATCH=0,
     STATUS="WRITES_AUDIT_COMPLETE",
     NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
