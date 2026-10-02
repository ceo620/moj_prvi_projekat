#!/usr/bin/env python3
"""Resume after app termination. Preserve manifest; defer suspect MP4; journal metadata steps."""
import fcntl, hashlib, json, os, stat, sys, time
from pathlib import Path
R=Path('/root/FREYA_IPHONE_ISH_NODE_888')
O=Path('/root/FREYA_RAD_888')
S=R/'05_SYSTEM_RUNTIME/STATE'
OLD=O/'IPHONE_CANONICAL_888'
NEW=R/'IPHONE_CANONICAL_888'
OLD_HASH='3ad916d76b599c1f00105ea67cee9c4f3c752c468f5eda4332a5901ec44d670a'
NEW_HASH='1656959fc6a1e02df417aa904aa92bfda8d9dcd3f2583e967f721c2058c388be'

def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def safe(p):need(not any(q.is_symlink() for q in (p,*p.parents)),'CONTROL_SYMLINK: '+str(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def event(f,kind,**kw):
    f.write(json.dumps(dict(event=kind,**kw),ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
def replace_link(src,target):
    tmp=src.with_name('.freya-alias-repair-'+str(os.getpid()))
    need(not os.path.lexists(tmp),'TEMP_LINK_EXISTS')
    os.symlink(str(target),tmp)
    try:os.replace(tmp,src)
    finally:
        if os.path.lexists(tmp):os.unlink(tmp)
    need(os.readlink(src)==str(target),'LINK_WRITE_FAILED')

def main():
    need(sys.argv[1:]==['--popravi-888'],'Use --popravi-888')
    need(os.geteuid()==0,'ROOT_REQUIRED')
    journal=S/'RESIDUAL_CANON_REPAIR.jsonl'
    for p in (R,O,S,OLD,NEW,R/'03_ARHIVA',journal,S/'autopilot_schedule.lock'):safe(p)
    need(OLD.is_dir() and NEW.is_dir(),'CANON_DIRECTORY_MISSING')
    with (S/'autopilot_schedule.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        outcomes=[]
        print('STEP=VERIFY_SAVED_MANIFEST',flush=True)
        with journal.open('a') as jf:
            old_m=OLD/'INTEGRATION_MANIFEST.json'
            new_m=NEW/'INTEGRATION_MANIFEST.json'
            archive=R/'03_ARHIVA/Manifest_integracije_prije_prevezivanja_2026-09-19.json'
            event(jf,'MANIFEST_VERIFY_BEGIN')
            safe(archive);safe(new_m)
            need(sha(new_m)==NEW_HASH,'CANONICAL_MANIFEST_CHANGED')
            if old_m.is_symlink():
                need(os.readlink(old_m)==str(archive) and sha(archive)==OLD_HASH,'OTHER_MANIFEST_ALIAS')
                outcomes.append('HISTORICAL_MANIFEST_ALREADY_PRESERVED')
            else:
                need(sha(old_m)==OLD_HASH,'HISTORICAL_MANIFEST_CHANGED')
                need(not os.path.lexists(archive),'ARCHIVE_NAME_CONFLICT')
                inode=old_m.stat().st_ino
                event(jf,'MANIFEST_INTENT',source=str(old_m),destination=str(archive),sha256=OLD_HASH,inode=inode)
                os.rename(old_m,archive)
                try:os.symlink(str(archive),old_m)
                except Exception:
                    if not os.path.lexists(old_m):os.rename(archive,old_m)
                    raise
                need(archive.stat().st_ino==inode and sha(archive)==OLD_HASH,'ARCHIVED_MANIFEST_VERIFICATION')
                event(jf,'MANIFEST_DONE',source=str(old_m),destination=str(archive),sha256=OLD_HASH)
                outcomes.append('HISTORICAL_MANIFEST_MOVED_AND_OLD_REFERENCE_PRESERVED')
            media={'source':str(OLD/'MEDIA/00-59-20_1.MP4'),
                   'destination':str(NEW/'MEDIA/00-59-20_1.MP4'),
                   'status':'DEFERRED_AFTER_APP_TERMINATION',
                   'accessed':False,'changed':False}
            event(jf,'MEDIA_DEFERRED',**media)
            print('MEDIA=DEFERRED_NO_ACCESS',flush=True)
        # Metadata-only enumeration of the single remaining branch. No link following.
        physical=[];broken=[];aliases=0;directories=0;stack=[OLD]
        deferred=[];alias_targets_unverified=0
        with journal.open('a') as jf:
            while stack:
                folder=stack.pop();directories+=1
                event(jf,'DIRECTORY_BEGIN',path=str(folder))
                for p in folder.iterdir():
                    # Do not stat, readlink, resolve, open or hash the suspect entry.
                    if p == OLD/'MEDIA/00-59-20_1.MP4':
                        deferred.append(str(p));continue
                    event(jf,'ENTRY_BEGIN',path=str(p))
                    st=p.lstat()
                    if stat.S_ISLNK(st.st_mode):
                        aliases+=1;alias_targets_unverified+=1
                    elif stat.S_ISDIR(st.st_mode):stack.append(p)
                    else:physical.append({'path':str(p),'size':st.st_size,'mode':oct(st.st_mode)})
                    event(jf,'ENTRY_DONE',path=str(p))
                event(jf,'DIRECTORY_DONE',path=str(folder))
                print('DIRECTORIES_READ='+str(directories),flush=True)
        report={'protocol':'888','human_gate':'ACTIVE','outcomes':outcomes,'media':media,
                'scope_enumerated':str(OLD),'directories':directories,'aliases':aliases,
                'remaining_physical_files':physical,'deferred_paths':deferred,
                'alias_targets_not_followed':alias_targets_unverified,
                'broken_alias_validation':'NOT_PERFORMED',
                'canonical_manifest_reference_repair':'PENDING',
                'result':'PARTIAL_RESIDUAL_REPAIR_MEDIA_DEFERRED',
                'full_system_closure':'NOT_CLAIMED','external_send':'NONE'}
        report_path=S/('RESIDUAL_CANON_R2_RESULT_'+str(time.time_ns())+'.json')
        with report_path.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
        print('SUMMARY_BEGIN');print(json.dumps(report,ensure_ascii=False,indent=2))
        print('REPORT='+str(report_path));print('BATCH_COMPLETE=YES')

if __name__=='__main__':
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=IPHONE_PREOSTALI_KANON_NASTAVAK_R2_888',flush=True)
    try:main()
    except Exception as e:
        print('RESULT=HOLD\nREASON='+str(e)+'\nBATCH_COMPLETE=NO',flush=True);sys.exit(1)
