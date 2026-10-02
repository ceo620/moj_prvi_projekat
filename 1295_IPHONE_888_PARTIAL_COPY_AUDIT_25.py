#!/usr/bin/env python3
"""Read-only audit of persisted batch 24 files and failed source record 32."""
import hashlib
import json
import os
import stat
import time
from pathlib import Path

C=Path('/root/FREYA_IPHONE_ISH_NODE_888')
D=C/'01_CANONICAL_BASE'
S=Path('/root/FREYA_RAD_888/IPHONE_CANONICAL_888')
OLD=Path('/root/FREYA_RAD_888/PRONADJENI_DIJELOVI_888/IPHONE_ZIP_018_INTEGRATED_VIEW')
M=D/'INTEGRATION_MANIFEST.json'
EXPECTED_M='c4fb6bf6a4505c8e3d66e0ec809a98757eca6e16d1392df28a70d0cca02a0d39'
EXPECTED_S='3ad916d76b599c1f00105ea67cee9c4f3c752c468f5eda4332a5901ec44d670a'
EXPECTED_P='1306821bae9a8cfd265bffcf5e98270b0c099bbe5384478d2efebad298536558'

def emit(k,v):
    print(k+'='+json.dumps(v,ensure_ascii=True),flush=True)

def sig(s):
    return dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)

def checked(p):
    for q in reversed(p.parents):
        if not stat.S_ISDIR(q.lstat().st_mode):
            raise ValueError('UNSAFE_PARENT '+str(q))
    s=p.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError('NOT_REGULAR '+str(p))
    return s

def small(p,expected):
    s=checked(p)
    if s.st_size>4000000:
        raise ValueError('MANIFEST_SIZE_LIMIT')
    with p.open('rb') as f:
        b=f.read(4000001)
    if hashlib.sha256(b).hexdigest()!=expected or sig(checked(p))!=sig(s):
        raise ValueError('EVIDENCE_CHANGED '+str(p))
    return b

def hash_file(p,expected,label,expected_size):
    before=checked(p)
    if before.st_size!=expected_size:
        raise ValueError('SIZE_MISMATCH '+str(p))
    emit('HASH_BEGIN',dict(label=label,path=str(p),bytes=before.st_size))
    h=hashlib.sha256(); total=0; last=time.monotonic()
    with p.open('rb') as f:
        opened=os.fstat(f.fileno())
        if sig(opened)!=sig(before):
            raise ValueError('OPEN_IDENTITY_CHANGED '+str(p))
        while True:
            b=f.read(1048576)
            if not b:
                break
            total+=len(b); h.update(b)
            if total>expected_size:
                raise ValueError('FILE_GREW '+str(p))
            if time.monotonic()-last>=5:
                emit('PROGRESS',dict(label=label,bytes=total,total=expected_size))
                last=time.monotonic()
        fd_after=os.fstat(f.fileno())
    try:
        path_after=sig(checked(p))
    except Exception as e:
        path_after={'error':str(e)}
    stable=sig(before)==sig(fd_after)==path_after
    match=h.hexdigest()==expected and total==expected_size
    emit('HASH_RESULT',dict(label=label,sha256=h.hexdigest(),expected_match=match,
                           metadata_stable=stable,bytes=total))
    if not stable or label!='PUBLISHED_COPY':
        emit('STAT_COMPARISON',dict(label=label,before=sig(before),fd_after=sig(fd_after),path_after=path_after))
    return match and stable

print('PROTOCOL=888\nBATCH=IPHONE_888_PARTIAL_COPY_AUDIT_25\nMODE=STRICT_READ_ONLY\nMUTATION=NO',flush=True)
try:
    small(C/'IPHONE_888_PERSISTENCE_PROBE_23.json',EXPECTED_P)
    original=json.loads(small(S/'INTEGRATION_MANIFEST.json',EXPECTED_S))
    document=json.loads(small(M,EXPECTED_M))
    rows=document['records']; original_rows=original['records']
    if len(rows)!=443 or len(original_rows)!=443:
        raise ValueError('RECORD_COUNT_CHANGED')
    emit('SAVED_CHECKPOINT',dict(batch=document.get('batch'),status=document.get('integration_status'),verified=document.get('verified_copy_count')))
    present=[]; absent=[]; plan=[]
    for i,(q,o) in enumerate(zip(rows,original_rows),1):
        rel=Path(o['view_path']).relative_to(OLD)
        if '..' in rel.parts or not rel.parts:
            raise ValueError('UNSAFE_RELATIVE_PATH')
        src=S/rel; dst=D/rel
        if q['source_path']!=str(src) or q['view_path']!=str(dst) or q['sha256']!=o['sha256'] or q['bytes']!=o['bytes']:
            raise ValueError('MAPPING_CHANGED_RECORD_'+str(i))
        plan.append((src,dst,o['sha256'],o['bytes']))
        try:
            checked(dst)
            present.append(i)
        except FileNotFoundError:
            absent.append(i)
    emit('PUBLISHED_RECORD_NUMBERS',present)
    emit('MISSING_DESTINATION_COUNT',len(absent))
    # Never broaden into a full base rehash or new copying pass.
    if any(i>31 for i in present):
        raise ValueError('UNEXPECTED_LATER_COPY; RETURN_METADATA_BEFORE_HASHING')
    if sum(plan[i-1][3] for i in present)>134217728:
        raise ValueError('PARTIAL_COPY_HASH_BUDGET_128_MIB')
    verified=0; problems=[]
    for i in present:
        src,dst,h,size=plan[i-1]
        if hash_file(dst,h,'PUBLISHED_COPY',size):
            verified+=1
        else:
            problems.append('PUBLISHED_RECORD_'+str(i))
    emit('PUBLISHED_CONTENT_VERIFIED',verified)
    src,dst,h,size=plan[31]
    if size!=94088778:
        raise ValueError('RECORD32_SIZE_UNEXPECTED')
    emit('RECORD32',dict(source=str(src),destination=str(dst),expected_sha256=h,bytes=size))
    if not hash_file(src,h,'SOURCE_RECORD32',size):
        problems.append('SOURCE_RECORD32')
    temp=dst.parent/('.batch24-'+h+'.tmp')
    try:
        ts=checked(temp)
        emit('TEMP_RECORD32',dict(path=str(temp),stat=sig(ts)))
        if ts.st_size==size:
            if not hash_file(temp,h,'TEMP_RECORD32',size):
                problems.append('TEMP_RECORD32')
        else:
            problems.append('TEMP_RECORD32_INCOMPLETE')
    except FileNotFoundError:
        emit('TEMP_RECORD32','ABSENT')
    small(C/'IPHONE_888_PERSISTENCE_PROBE_23.json',EXPECTED_P)
    small(M,EXPECTED_M)
    small(S/'INTEGRATION_MANIFEST.json',EXPECTED_S)
    emit('PROBLEMS',problems)
    emit('RESULT','HOLD_CONTENT_OR_METADATA_CHANGE' if problems else 'TARGETED_AUDIT_COMPLETE')
    print('MUTATION=NO\nCOPY_RESUME=NOT_EXECUTED\nNEXT=RETURN_COMPLETE_OUTPUT',flush=True)
except (Exception,KeyboardInterrupt) as e:
    emit('HOLD',repr(e))
    print('MUTATION=NO\nCOPY_RESUME=HOLD\nNEXT=RETURN_COMPLETE_OUTPUT',flush=True)
    raise SystemExit(2)
