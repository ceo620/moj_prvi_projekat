#!/usr/bin/env python3
"""Bounded, read-only investigation of disappearing batch-20 output.
No process signals, no execution of discovered scripts, no file writes.
"""
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import time
from pathlib import Path

R = Path('/root')
PATHS = [R, R/'FREYA_RAD_888', R/'FREYA_RAD_888/IPHONE_CANONICAL_888',
         R/'FREYA_IPHONE_ISH_NODE_888', R/'FREYA_IPHONE_ISH_NODE_888/01_CANONICAL_BASE']
ERRORS = []
SNAPS = []

def emit(k, v):
    print(k+'='+json.dumps(v, ensure_ascii=True), flush=True)

def error(scope, e):
    ERRORS.append([scope, str(e)])
    emit('READ_ERROR', [scope, str(e)])

def metadata(p):
    try:
        s = p.lstat()
        return {'dev':s.st_dev,'inode':s.st_ino,'mode':oct(s.st_mode),
                'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
    except OSError as e:
        return {'errno':e.errno,'error':str(e)}

def small_read(p, limit):
    for ancestor in reversed(p.parents):
        if not stat.S_ISDIR(ancestor.lstat().st_mode):
            raise ValueError('NON_DIRECTORY_PARENT '+str(ancestor))
    s = p.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_size > limit:
        raise ValueError('NON_REGULAR_OR_SIZE_LIMIT')
    with p.open('rb') as f:
        data = f.read(limit+1)
    if len(data) > limit:
        raise ValueError('READ_LIMIT')
    return data

def snapshot(label):
    result = {str(p):metadata(p) for p in PATHS}
    for p in PATHS[1:]:
        try:
            if stat.S_ISDIR(p.lstat().st_mode):
                names = sorted(x.name for x in p.iterdir())
                result[str(p)]['child_count'] = len(names)
                if p == PATHS[-2]:
                    result[str(p)]['children'] = names[:30]
        except OSError as e:
            result[str(p)]['listing_error'] = str(e)
    SNAPS.append(result)
    emit('PATH_SNAPSHOT_'+label, result)

print('PROTOCOL=888\nBATCH=IPHONE_888_PATH_STABILITY_22\nMODE=STRICT_READ_ONLY\nMUTATION=NO', flush=True)
emit('IDENTITY', {'uid':os.getuid(),'pid':os.getpid(),'uname':list(os.uname())})
snapshot('START')

# Compare absolute lookups with lookups anchored to the current /root inode.
try:
    fd = os.open(str(R), os.O_RDONLY | getattr(os,'O_DIRECTORY',0))
    try:
        s = os.fstat(fd)
        emit('ROOT_FD', {'dev':s.st_dev,'inode':s.st_ino})
        for name in ('FREYA_RAD_888','FREYA_IPHONE_ISH_NODE_888'):
            try:
                s = os.stat(name, dir_fd=fd, follow_symlinks=False)
                emit('ANCHORED_PATH', {'name':name,'dev':s.st_dev,'inode':s.st_ino})
            except Exception as e:
                error('ANCHORED '+name,e)
    finally:
        os.close(fd)
except Exception as e:
    error('ROOT_FD',e)

for rel, expected in (
    ('IPHONE_888_VERIFIED_BASE_COPY_20.py','dc03f2acc6f158cd5d3d6fecb34b2fa18953d88377b7837531a4e44ab5508771'),
    ('IPHONE_888_PATH_HOLD_DIAG_21.py','dffbf59c6248367c1148f1c86648cd572668d4602bd8d332e3583be2ce2ece38'),
    ('FREYA_RAD_888/IPHONE_CANONICAL_888/INTEGRATION_MANIFEST.json','3ad916d76b599c1f00105ea67cee9c4f3c752c468f5eda4332a5901ec44d670a')):
    try:
        actual = hashlib.sha256(small_read(R/rel, 1000000)).hexdigest()
        emit('KNOWN_FILE', {'path':str(R/rel),'sha256':actual,'expected_match':actual==expected})
    except Exception as e:
        error(rel,e)

scripts = set()
try:
    r = subprocess.run(['ps','-o','pid,ppid,stat,args'], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=10, check=False)
    emit('PS_EXIT',r.returncode)
    if r.returncode:
        emit('PS_ERROR',r.stderr.decode(errors='replace')[:1000])
    for line in r.stdout.decode(errors='replace').splitlines()[1:101]:
        parts = line.split(None,3)
        if len(parts)!=4:
            continue
        try:
            args = shlex.split(parts[3])
        except ValueError:
            args = parts[3].split()
        if not args:
            continue
        # Do not disclose arbitrary command arguments or inline shell payloads.
        named = [a for a in args[1:] if re.fullmatch(r'[A-Za-z0-9_./-]+\.(?:py|sh)',a)]
        emit('PROCESS',{'pid':parts[0],'ppid':parts[1],'state':parts[2],
                        'executable':args[0],'scripts':named})
        if parts[0] != str(os.getpid()):
            for name in named:
                if name.startswith('/root/') and '..' not in Path(name).parts:
                    scripts.add(Path(name))
                elif '/' not in name:
                    # A candidate only; its process working directory is unverified.
                    scripts.add(R/name)
except Exception as e:
    error('PROCESS_LIST',e)

# Read only conventional scheduling files and scripts named by running processes.
scheduled = [Path('/etc/crontabs/root'),Path('/var/spool/cron/crontabs/root'),Path('/etc/inittab')]
pattern = re.compile(r'FREYA_RAD_888|FREYA_IPHONE_ISH_NODE_888|IPHONE_CANONICAL_888|01_CANONICAL_BASE|rmtree|os\.(?:rename|replace|unlink)|shutil\.(?:move|rmtree)|\b(?:rm|mv|rsync|crond|crontab)\b')
for p in scheduled+sorted(scripts)[:8]:
    try:
        data = small_read(p,262144)
        emit('STATIC_FILE',{'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        count = 0
        for number,line in enumerate(data.decode(errors='replace').splitlines(),1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if p in scheduled or pattern.search(line):
                count += 1
                # Only indicators and referenced script paths; never credential values.
                emit('STATIC_INDICATOR',{'path':str(p),'line':number,
                     'indicators':pattern.findall(line),
                     'script_paths':re.findall(r'/[A-Za-z0-9_./-]+\.(?:py|sh)\b',line)})
                if count >= 35:
                    emit('STATIC_OUTPUT_LIMIT',str(p))
                    break
    except FileNotFoundError:
        emit('STATIC_ABSENT',str(p))
    except Exception as e:
        error(str(p),e)

for p in (Path('/proc/mounts'),Path('/etc/mtab')):
    try:
        data = small_read(p,65536)
        rows=[]
        for line in data.decode(errors='replace').splitlines():
            cols=line.split()
            if len(cols)>=3 and cols[1] in ('/','/root','/proc'):
                rows.append({'mountpoint':cols[1],'filesystem':cols[2]})
        emit('MOUNT_TYPES',{'path':str(p),'entries':rows})
    except Exception as e:
        error(str(p),e)

time.sleep(1)
snapshot('END')
emit('PATH_SNAPSHOTS_EQUAL',SNAPS[0]==SNAPS[-1])
emit('READ_ERROR_COUNT',len(ERRORS))
print('RESULT=DIAGNOSTIC_ONLY\nCAUSE=NOT_AUTOMATICALLY_DETERMINED\nCOPY_RESUME=HOLD\nMUTATION=NO\nNEXT=RETURN_COMPLETE_OUTPUT',flush=True)
