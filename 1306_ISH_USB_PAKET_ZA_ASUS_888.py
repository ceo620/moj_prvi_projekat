#!/usr/bin/env python3
"""Explicit export of the canonical iSH root and launcher; no execution/import.
USB content-addressed chunks preserve arbitrary Linux names via a JSON manifest.
Re-run --spakuj-888 to reuse verified chunks after interruption. No ZIP created.
--provjeri PACKAGE verifies an exported snapshot without modifying it.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

ROOT = Path('/root/FREYA_IPHONE_ISH_NODE_888')
LAUNCHER = Path('/usr/local/bin/freya')
USB = Path('/mnt/freya_usb_888')
PACKAGE_NAME = 'IPHONE_ZA_ASUS_888'
FORMAT = 'FREYA_USB_CHUNKS_V1'
CHUNK = 16 * 1024 * 1024

def say(s):
    print(s, flush=True)

def require(ok, why):
    if not ok:
        raise RuntimeError(why)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def encoded(j):
    return (json.dumps(j, ensure_ascii=True, sort_keys=True, indent=2)+'\n').encode()

def no_links(p):
    for q in (p,) + tuple(p.parents):
        require(not q.is_symlink(), 'SYMLINK_PATH: '+str(q))

def signature(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def exclusive(p, data):
    no_links(p)
    with p.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def read_regular(p, limit=None):
    no_links(p)
    require(stat.S_ISREG(p.lstat().st_mode), 'NOT_REGULAR: '+str(p))
    with p.open('rb') as f:
        b=f.read() if limit is None else f.read(limit+1)
    require(limit is None or len(b)<=limit, 'SIZE_LIMIT: '+str(p))
    return b

def inventory(root, launcher):
    no_links(root)
    no_links(launcher)
    require(root.is_dir() and launcher.is_file(), 'SOURCE_MISSING')
    items={}
    def visit(p):
        s=p.lstat()
        row={'source':str(p), 'mode':stat.S_IMODE(s.st_mode),
             'mtime_ns':s.st_mtime_ns, 'signature':list(signature(s))}
        if stat.S_ISLNK(s.st_mode):
            row.update(kind='symlink', target=os.readlink(str(p)))
        elif stat.S_ISDIR(s.st_mode):
            row['kind']='directory'
        elif stat.S_ISREG(s.st_mode):
            row.update(kind='file', bytes=s.st_size)
        else:
            raise RuntimeError('SPECIAL_OBJECT_NOT_PACKAGED: '+str(p))
        items[str(p)]=row
        if row['kind']=='directory':
            for name in sorted(os.listdir(str(p))):
                visit(p/name)
    visit(root)
    visit(launcher)
    return items

def chunk_path(package, digest):
    require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest), 'BAD_CHUNK_HASH')
    return package/'SADRZAJ'/digest[:2]/(digest+'.bin')

def verify(package, manifest, progress=True):
    require(manifest.get('format')==FORMAT, 'BAD_FORMAT')
    count=0
    total=0
    for row in manifest['entries']:
        if row['kind']!='file':
            continue
        h=hashlib.sha256()
        size=0
        for digest in row['chunks']:
            b=read_regular(chunk_path(package,digest),CHUNK)
            require(sha(b)==digest, 'USB_CHUNK_HASH_MISMATCH: '+digest)
            h.update(b)
            size+=len(b)
        require(size==row['bytes'] and h.hexdigest()==row['sha256'],
                'USB_FILE_HASH_MISMATCH: '+row['source'])
        count+=1
        total+=size
        if progress and count%25==0:
            say('PROVJERENO_FAJLOVA='+str(count))
    require(count==manifest['file_count'] and total==manifest['total_bytes'], 'COUNT_MISMATCH')
    return count

def latest(package):
    pointer=json.loads(read_regular(package/'POSLJEDNJI_PAKET.json',10000))
    name=pointer['snapshot']
    require(re.fullmatch('[0-9TZ_]+[0-9a-f]{8}', name) is not None, 'BAD_SNAPSHOT_NAME')
    raw=read_regular(package/'POTVRDE'/name/'MANIFEST.json')
    require(sha(raw)==pointer['manifest_sha256'], 'MANIFEST_HASH_MISMATCH')
    return json.loads(raw)

def export(root=ROOT, launcher=LAUNCHER, usb=USB):
    no_links(usb)
    require(usb.is_dir(), 'USB_MISSING')
    say('KORAK=POPIS_KANONSKOG_KORIJENA')
    before=inventory(root,launcher)
    rows=list(before.values())
    files=[r for r in rows if r['kind']=='file']
    total=sum(r['bytes'] for r in files)
    say('FAJLOVI='+str(len(files)))
    say('IZVORNI_BAJTOVI='+str(total))
    package=usb/PACKAGE_NAME
    info={'format':FORMAT,'source_root':str(root),'launcher':str(launcher)}
    no_links(package)
    if package.exists():
        require(json.loads(read_regular(package/'PAKET_INFO.json',10000))==info,
                'DESTINATION_NOT_OUR_PACKAGE')
    else:
        package.mkdir()
        exclusive(package/'PAKET_INFO.json',encoded(info))
    for name in ('SADRZAJ','POTVRDE'):
        q=package/name
        no_links(q)
        q.mkdir(exist_ok=True)
    # Only verified chunk files in this package are reusable. Other USB data is untouched.
    copied=0
    reused=0
    done=0
    for number,row in enumerate(files,1):
        p=Path(row['source'])
        no_links(p)
        require(list(signature(p.lstat()))==row['signature'], 'SOURCE_CHANGED: '+str(p))
        h=hashlib.sha256()
        chunks=[]
        size=0
        with p.open('rb') as f:
            require(list(signature(os.fstat(f.fileno())))==row['signature'], 'SOURCE_OPEN_CHANGED')
            while True:
                b=f.read(CHUNK)
                if not b:
                    break
                h.update(b)
                size+=len(b)
                digest=sha(b)
                target=chunk_path(package,digest)
                no_links(target)
                if target.exists():
                    require(sha(read_regular(target,CHUNK))==digest, 'EXISTING_CHUNK_CORRUPT: '+digest)
                    reused+=1
                else:
                    v=os.statvfs(str(usb))
                    require(v.f_bavail*v.f_frsize >= len(b)+32*1024*1024, 'USB_SPACE_LOW')
                    target.parent.mkdir(exist_ok=True)
                    temporary=target.with_name(digest+'.partial_'+uuid.uuid4().hex)
                    exclusive(temporary,b)
                    os.rename(str(temporary),str(target))
                    copied+=1
                chunks.append(digest)
                done+=len(b)
                if len(chunks)%4==0:
                    say('NAPREDAK_BAJTOVI=%d/%d'%(done,total))
            require(list(signature(os.fstat(f.fileno())))==row['signature'], 'SOURCE_READ_CHANGED')
        require(list(signature(p.lstat()))==row['signature'] and size==row['bytes'], 'SOURCE_CHANGED: '+str(p))
        row.update(sha256=h.hexdigest(),chunks=chunks)
        if number%25==0 or number==len(files):
            say('KOPIRANO_FAJLOVA=%d/%d'%(number,len(files)))
    # Compare metadata and membership again, ignoring fields added by the exporter.
    after=inventory(root,launcher)
    baseline={k:{f:v for f,v in r.items() if f not in ('sha256','chunks')} for k,r in before.items()}
    require(after==baseline, 'SOURCE_TREE_CHANGED_DURING_EXPORT; RERUN_SAME_COMMAND')
    external=[]
    for r in rows:
        if r['kind']=='symlink':
            p=Path(r['source'])
            target=os.path.normpath(os.path.join(str(p.parent),r['target']))
            if target not in before:
                external.append({'source':str(p),'target':r['target'], 'status':'TARGET_NOT_PACKAGED'})
    manifest={'format':FORMAT, 'protocol':'888','human_gate':'ACTIVE',
              'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_root':str(root),'file_count':len(files),'total_bytes':total,
              'entries':rows,'external_or_unresolved_links':external,
              'scope':'Canonical iPhone root and /usr/local/bin/freya only; no external roots or OS packages',
              'runtime_portability':'NOT_TESTED_ON_ASUS','human_signoff':'PENDING'}
    say('KORAK=CITANJE_USB_KOPIJE_I_SHA256_PROVJERA')
    verify(package,manifest)
    require(inventory(root,launcher)==baseline,'SOURCE_CHANGED_DURING_USB_VERIFICATION')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
    snapshot=package/'POTVRDE'/stamp
    snapshot.mkdir()
    raw=encoded(manifest)
    exclusive(snapshot/'MANIFEST.json',raw)
    receipt={'result':'PASS_CANONICAL_COPY_VERIFIED','manifest_sha256':sha(raw),
             'files_verified':len(files),'source_bytes':total,'new_chunks':copied,
             'reused_chunks':reused,'external_links':external,
             'originals_modified':False,'network':'NONE','asus_import':'NOT_PERFORMED',
             'full_system_final_seal':'NOT_GRANTED'}
    exclusive(snapshot/'REZULTAT.json',encoded(receipt))
    # Keep a self-contained verifier with every snapshot; it never executes copied scripts.
    exclusive(snapshot/'PROVJERI_PAKET_888.py',Path(__file__).read_bytes())
    instructions=('IPHONE PREDAJA ASUS-U / PROTOKOL 888\n\n'
      'Ovo je kopija cijelog navedenog kanonskog korijena i pokretaca freya.\n'
      'SADRZAJ cuva bajtove u segmentima; MANIFEST.json cuva originalne putanje,\n'
      'SHA-256, redosljed segmenata, direktorijume i simbolicke veze.\n'
      'Segmenti nijesu zasebni dokumenti. Ne preimenovati ih. Nema ZIP arhive.\n'
      'Na ASUS prenijeti cijeli folder IPHONE_ZA_ASUS_888.\n'
      'Provjera na ASUS Debian: python3 -I -S -B PROVJERI_PAKET_888.py --provjeri PUTANJA_PAKETA\n'
      'Koristiti provjeravac iz ove POTVRDE podmape i punu putanju paketa.\n'
      'Oporavak u originalne nazive i uvoz u C:\\FREYA_PLATFORM_2_0 su naredni korak.\n'
      'Ne pokretati iPhone skripte na ASUS-u automatski.\n'
      'Veze van obuhvata su popisane, njihove mete nijesu kopirane.\n'
      'Sadrzaj starih Lenovo/MSI paketa na USB-u nije mijenjan niti provjeravan.\n'
      'Human Gate ACTIVE; nacrti i finansijske pretpostavke zadrzavaju svoj status.\n')
    exclusive(snapshot/'PROCITAJ_PRVO.txt',instructions.encode('utf-8'))
    pointer={'snapshot':stamp,'manifest_sha256':sha(raw)}
    temporary=package/('POKAZIVAC_'+uuid.uuid4().hex+'.tmp')
    exclusive(temporary,encoded(pointer))
    current=package/'POSLJEDNJI_PAKET.json'
    no_links(current)
    os.replace(str(temporary),str(current))
    if hasattr(os,'sync'):
        os.sync()
    say('RESULT=PASS_CANONICAL_COPY_VERIFIED')
    say('USB_FILES_VERIFIED='+str(len(files)))
    say('EXTERNAL_OR_UNRESOLVED_LINKS='+str(len(external)))
    say('PACKAGE='+str(package))
    say('MANIFEST_SHA256='+sha(raw))
    say('REPORT='+str(snapshot/'REZULTAT.json'))
    say('ORIGINALS_MODIFIED=NO\nASUS_IMPORT=NOT_PERFORMED\nHUMAN_GATE=ACTIVE\nBATCH_COMPLETE=YES')
    return package,manifest

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--provjeri':
        package=Path(sys.argv[2]).absolute()
        manifest=latest(package)
        count=verify(package,manifest)
        say('RESULT=PASS_USB_PACKAGE_HASHES\nFILES_VERIFIED='+str(count)+'\nMUTATION=NO')
        return
    require(sys.argv[1:]==['--spakuj-888'],'USAGE: --spakuj-888 OR --provjeri PACKAGE')
    import fcntl
    no_links(USB)
    require(any(len(x.split())>=3 and x.split()[1]==str(USB) and x.split()[2]=='ios'
                for x in Path('/proc/mounts').read_text().splitlines()),'USB_NOT_IOS_MOUNT')
    require((USB/'LENOVO_ASUS_P01_888_6796693f.zip').is_file() and
            (USB/'MSI_TO_ASUS_3CORE_888').is_dir(),'SELECTED_USB_DOES_NOT_MATCH_OBSERVED_CONTENT')
    with open('/tmp/ISH_USB_PAKET_ZA_ASUS_888.lock','a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        say('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nNETWORK=NONE')
        export()

if __name__=='__main__':
    try:
        main()
    except (Exception,KeyboardInterrupt) as e:
        say('RESULT=HOLD\nREASON='+type(e).__name__+': '+str(e))
        say('BATCH_COMPLETE=NO\nNEXT=KEEP_USB_CONNECTED_AND_RETURN_OUTPUT')
        sys.exit(2)
