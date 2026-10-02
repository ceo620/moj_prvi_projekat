#!/usr/bin/env python3
"""Re-read all regular members after ctime change; compare all prior available hashes.
Does not extract, delete, execute archive contents or claim semantic integration.
"""
import os, json, hashlib, sqlite3, time, zipfile, signal, tempfile
from datetime import datetime, timezone
ROOT='/root/FREYA_RAD_888/REZULTATI'
REPORT=ROOT+'/IPHONE_ZIP_012_AUDIT_cb8vq9dk.json'
PIN='fb274afb8c933d262b145691fb163d48554ef296fd6e973778ada966b2ef02b5'
HELPER='/root/IPHONE_ZIP_012_AUDIT.py'
HPIN='da8847442d719d4ed2b323fcc82d92b88eebfd88658e2ad7d44f6be00e6a228a'
DB=ROOT+'/IPHONE_ZIP_013R1_PROGRESS.sqlite3'

def sha(b): return hashlib.sha256(b).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()

def main():
    if 'ish' not in os.uname().release.lower():
        raise SystemExit('HOLD=Pogresno okruzenje')
    with open(HELPER,'rb') as f: raw=f.read(100000)
    if sha(raw)!=HPIN: raise SystemExit('HOLD=Helper SHA256')
    h={'__name__':'verified_audit_helper','__file__':HELPER}
    exec(compile(raw,HELPER,'exec'),h)
    safe=h['safe_open']; ident=h['identity']; Hold=h['Hold']
    signal.signal(signal.SIGALRM,h['timeout'])
    with safe(REPORT) as f: raw=f.read(64*1024*1024+1)
    if sha(raw)!=PIN: raise SystemExit('HOLD=Report SHA256')
    report=json.loads(raw)
    targets=[a for a in report['archives'] if any(m.get('read_status') not in
        ('READ_CRC_VERIFIED','DIRECTORY_METADATA_ONLY') for m in a['members'])]
    if len(targets)!=1: raise SystemExit('HOLD=Target count')
    a=targets[0]; c=a['inventory_identity']
    if os.path.realpath(ROOT)!=ROOT: raise SystemExit('HOLD=Report directory')
    # Retain the old checkpoint; revalidate its bytes against the source.
    oldpath=ROOT+'/IPHONE_ZIP_013_PROGRESS.sqlite3'
    with safe(oldpath): pass
    olddb=sqlite3.connect('file:'+oldpath+'?mode=ro',uri=True)
    if olddb.execute('PRAGMA quick_check').fetchone()[0]!='ok':
        raise SystemExit('HOLD=Old checkpoint integrity')
    oldmeta=dict(olddb.execute('SELECT key,value FROM meta'))
    if oldmeta.get('report_sha256')!=PIN or oldmeta.get('path')!=a['path']:
        raise SystemExit('HOLD=Old checkpoint identity')
    oldrows=list(olddb.execute('SELECT id,bytes,sha256 FROM members'))
    olddb.close()
    if len(oldrows)!=1350:
        raise SystemExit('HOLD=Old checkpoint count changed')
    expected_hashes={m['id']:m['sha256'] for m in a['members']
                     if m.get('read_status')=='READ_CRC_VERIFIED'}
    for i,size,digest in oldrows:
        if i<0 or i>=len(a['members']) or size!=a['members'][i]['bytes']:
            raise SystemExit('HOLD=Old checkpoint member')
        if i in expected_hashes and expected_hashes[i]!=digest:
            raise SystemExit('HOLD=Conflicting prior hashes')
        expected_hashes[i]=digest
    existed=os.path.lexists(DB)
    if existed:
        with safe(DB): pass
    else:
        fd=os.open(DB,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd)
    for suffix in ('-journal','-wal','-shm'):
        if os.path.lexists(DB+suffix):
            with safe(DB+suffix): pass
    db=sqlite3.connect(DB,timeout=2)
    db.execute('PRAGMA trusted_schema=OFF')
    db.execute('PRAGMA synchronous=FULL')
    if not existed:
        db.execute('CREATE TABLE meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        db.execute('CREATE TABLE members (id INTEGER PRIMARY KEY,bytes INTEGER NOT NULL,sha256 TEXT NOT NULL)')
        db.executemany('INSERT INTO meta VALUES (?,?)',[('report_sha256',PIN),('path',a['path'])])
        db.commit()
    if dict(db.execute('SELECT key,value FROM meta')).get('report_sha256')!=PIN:
        raise SystemExit('HOLD=Checkpoint identity')
    print('BATCH=IPHONE_ZIP_013R1; SOURCE_MODE=READ_ONLY; DELETION=NOT_PERFORMED',flush=True)
    started=utc(); deadline=time.monotonic()+480; new=0; holds=[]
    pending={m['id']:m for m in a['members'] if m.get('read_status') != 'DIRECTORY_METADATA_ONLY'}
    with safe(a['path']) as f:
        before=os.fstat(f.fileno())
        if ident(before)[:4]!=(c['device'],c['inode'],c['bytes'],c['mtime_ns']) or before.st_ctime_ns!=1789820603796082023:
            raise SystemExit('HOLD=Source changed since audit')
        snapshot=json.dumps(ident(before))
        meta=dict(db.execute('SELECT key,value FROM meta'))
        if 'source_identity' in meta and meta['source_identity']!=snapshot:
            raise SystemExit('HOLD=Checkpoint source changed')
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',('source_identity',snapshot));db.commit()
        done={i:(size,digest) for i,size,digest in db.execute('SELECT id,bytes,sha256 FROM members')}
        if any(i not in pending or size!=pending[i]['bytes'] or len(digest)!=64
               for i,(size,digest) in done.items()):
            raise SystemExit('HOLD=Checkpoint member mismatch')
        with zipfile.ZipFile(f) as z:
            infos=z.infolist()
            if len(infos)!=a['member_count']: raise SystemExit('HOLD=Member count')
            for i,m in pending.items():
                if i in done: continue
                if time.monotonic()>=deadline: break
                info=infos[i]
                if (info.filename,info.file_size,info.CRC)!=(m['name'],m['bytes'],m['crc32']):
                    raise SystemExit('HOLD=Member identity')
                if info.flag_bits&1 or info.file_size>512*1024*1024:
                    holds.append({'id':i,'reason':'ENCRYPTED_OR_SIZE_LIMIT'});continue
                try:
                    signal.alarm(120)
                    digest=hashlib.sha256();size=0
                    with z.open(info) as source:
                        while True:
                            chunk=source.read(262144)
                            if not chunk: break
                            size+=len(chunk)
                            if size>info.file_size: raise Hold('SIZE_MISMATCH')
                            if time.monotonic()>=deadline: raise Hold('RUN_TIME_LIMIT')
                            digest.update(chunk)
                    if size!=info.file_size: raise Hold('SIZE_MISMATCH')
                    if ident(before)!=ident(os.fstat(f.fileno())) or ident(before)!=ident(os.lstat(a['path'])):
                        raise SystemExit('HOLD=Source changed during read')
                    if i in expected_hashes and digest.hexdigest()!=expected_hashes[i]:
                        db.rollback()
                        raise SystemExit('HOLD=PRIOR_CONTENT_HASH_MISMATCH member='+str(i))
                    db.execute('INSERT INTO members VALUES (?,?,?)',(i,size,digest.hexdigest()))
                    new+=1
                    if new%50==0:
                        db.commit()
                        print('NOVIH=%d PREOSTALO=%d'%(new,len(pending)-len(done)-new),flush=True)
                except Exception as exc:
                    holds.append({'id':i,'reason':str(exc) if isinstance(exc,Hold) else type(exc).__name__})
                finally: signal.alarm(0)
        if ident(before)!=ident(os.fstat(f.fileno())) or ident(before)!=ident(os.lstat(a['path'])):
            db.rollback();raise SystemExit('HOLD=Source changed; checkpoint unusable')
    db.commit()
    rows=[{'id':i,'bytes':size,'sha256':digest,'read_status':'READ_CRC_VERIFIED'}
          for i,size,digest in db.execute('SELECT id,bytes,sha256 FROM members ORDER BY id')]
    db.close()
    remaining=len(pending)-len(rows)
    result={'batch':'IPHONE_ZIP_013R1','started_utc':started,'finished_utc':utc(),
        'parent_report_sha256':PIN,'path':a['path'],'source_identity':json.loads(snapshot),
        'completed_members':rows,'prior_hashes_to_revalidate':len(expected_hashes),
        'prior_hashes_revalidated':sum(r['id'] in expected_hashes for r in rows),'remaining_members':remaining,'holds_this_run':holds,
        'archive_sha256':'NOT_YET_COMPUTED','semantic_integration':'NOT_VERIFIED',
        'nested_archive_recursion':'NOT_PERFORMED','deletion':'NOT_PERFORMED',
        'goal_status':'INCOMPLETE','checkpoint':DB}
    raw=(json.dumps(result,ensure_ascii=True,indent=2)+'\n').encode()
    fd,out=tempfile.mkstemp(prefix='IPHONE_ZIP_013R1_RESULT_',suffix='.json',dir=ROOT)
    with os.fdopen(fd,'wb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
    print('NOVIH_PROVJERENIH='+str(new))
    print('PREOSTALO_CLANOVA='+str(remaining))
    print('REPORT='+out)
    print('REPORT_SHA256='+sha(raw))
    print('DELETION=NOT_PERFORMED; GOAL_STATUS=INCOMPLETE')

if __name__=='__main__': main()
