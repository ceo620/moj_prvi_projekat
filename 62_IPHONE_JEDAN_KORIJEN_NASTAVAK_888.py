#!/usr/bin/env python3
"""Move reviewed non-conflicting legacy top-level objects into the canonical root.
No recursive scan, no overwrite, no source execution, no document signoff.
Authorization: renewed integration approval 2026-09-28, Human Gate active.
"""
import fcntl, hashlib, json, os, stat, subprocess, sys, time
from pathlib import Path

R=Path('/root/FREYA_IPHONE_ISH_NODE_888')
O=Path('/root/FREYA_RAD_888')
S=R/'05_SYSTEM_RUNTIME/STATE'
RUNNER=R/'05_SYSTEM_RUNTIME/FREYA_RUN_V2__ee7e37bd8707.sh'
PIN='ed9745973bba49d90cd188b10f9b090609eb865e3a4d790e297eb482864cdf66'
ENV={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','SHELL':'/bin/sh','LANG':'C'}
NAMES=('01_PROIZVODI','02_REZULTATI_TEHNICKI','03_ARHIVA','04_HUMAN_GATE','05_SISTEM',
 'AI_PILOT_1USD_01','AI_SADRZAJ_01','AI_SADRZAJ_01R1','AI_SVAKODNEVNI_888','CODE',
 'DAN1.env','DIJAMANTI','DIJAMANTI_POPIS.csv','FREYA_888_IPHONE_FACTORY_TEST_INPUT.xlsx',
 'FREYA_888_PRVI_PROIZVOD.xlsx','FREYA_888_PRVI_PROIZVOD_RECEIPT.env',
 'FREYA_888_PRVI_PROIZVOD_REZULTAT.txt','IDENTITY.json','INDEX.json',
 'IZLAZ_REAL_TEST_20260921T230415Z_8','NE_DIRATI.txt','POSLJEDNJI_REZULTAT.txt',
 'PREGLED.html','PRONADJENI_DIJELOVI_888','REZULTATI','REZULTATI_V2','RUN.lock',
 'SESIJE','ULAZ','UNI_MAK_CFO_REVIEW.txt')

def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def no_links(p):need(not any(q.is_symlink() for q in (p,*p.parents)),'CONTROL_SYMLINK: '+str(p))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def meta(p):
    s=p.lstat()
    return {'dev':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'size':s.st_size,'mtime_ns':s.st_mtime_ns,
            'link':os.readlink(p) if stat.S_ISLNK(s.st_mode) else None}
def snapshot(p):
    result={'self':meta(p),'children':{}}
    if p.is_dir() and not p.is_symlink():
        result['children']={q.name:meta(q) for q in p.iterdir()}
    else:result['sha256']=sha(p)
    return result
def log(f,event,**data):
    f.write(json.dumps(dict(event=event,**data),ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())

def move_one(src,dst,journal,number):
    before=snapshot(src)
    need(before['self']['dev']==R.stat().st_dev,'CROSS_DEVICE')
    temp=O/('.freya-root-link-'+str(os.getpid())+'-'+str(number))
    need(not os.path.lexists(temp),'TEMP_LINK_EXISTS')
    need(not os.path.lexists(dst),'DESTINATION_CONFLICT')
    log(journal,'INTENT',source=str(src),destination=str(dst),before=before)
    os.symlink(str(dst),temp)
    moved=False
    try:
        need(snapshot(src)==before and not os.path.lexists(dst),'SOURCE_CHANGED_OR_TARGET_APPEARED')
        os.rename(src,dst);moved=True
        os.replace(temp,src)
        need(src.is_symlink() and src.resolve()==dst.resolve(),'SOURCE_ALIAS_FAILED')
        need(snapshot(dst)==before,'POST_MOVE_METADATA_OR_HASH_CHANGED')
        log(journal,'DONE',source=str(src),destination=str(dst),before=before)
    except Exception:
        if moved and not os.path.lexists(src):os.symlink(str(dst),src)
        raise
    finally:
        if os.path.lexists(temp):os.unlink(temp)
    return before

def main():
    need(sys.argv[1:]==['--integrisi-888'],'Use --integrisi-888')
    need(os.geteuid()==0,'ROOT_REQUIRED')
    journal_path=S/'ROOT_INTEGRATION_RENEWED_888.jsonl'
    for p in (R,O,S,journal_path,S/'autopilot_schedule.lock',RUNNER):no_links(p)
    need(sha(RUNNER)==PIN,'CANONICAL_RUNNER_CHANGED')
    ps=subprocess.check_output(['ps'],env=ENV,universal_newlines=True)
    for name in ('foreground_business__','integrated_runtime_all_files','document_processor__'):
        need(name not in ps,'RUNTIME_BUSY: '+name)
    outcomes=[]
    with (S/'autopilot_schedule.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Complete only an interrupted rename explicitly recorded by this batch.
        intents={}
        if journal_path.exists():
            for line in journal_path.read_text().splitlines():
                row=json.loads(line)
                if row['event']=='INTENT':intents[row['source']]=row
                elif row['event'] in ('DONE','RECOVERED'):intents.pop(row['source'],None)
        with journal_path.open('a') as journal:
            os.chmod(journal_path,0o600)
            for name,row in intents.items():
                src=Path(name);dst=Path(row['destination'])
                need(src.parent==O and src.name in NAMES and dst==R/src.name,'JOURNAL_SCOPE')
                if not os.path.lexists(src):
                    need(not dst.is_symlink() and snapshot(dst)==row['before'],'RECOVERY_TARGET_MISMATCH')
                    os.symlink(str(dst),src)
                    log(journal,'RECOVERED',source=str(src),destination=str(dst))
            for i,name in enumerate(NAMES):
                src=O/name;dst=R/name
                if src.is_symlink():
                    status='ALREADY_CANONICAL_ALIAS' if src.resolve()==dst.resolve() and dst.exists() else 'PRESERVED_OTHER_LINK'
                elif not os.path.lexists(src):status='PRESERVED_SOURCE_MISSING'
                elif os.path.lexists(dst):status='PRESERVED_DESTINATION_CONFLICT'
                else:
                    move_one(src,dst,journal,i);status='MOVED_AND_REFERENCES_PRESERVED'
                outcomes.append({'name':name,'status':status,'destination':str(dst)})
                print(status+' | '+name,flush=True)
        # Test the already approved canonical flow, never any relocated legacy code.
        need(sha(RUNNER)==PIN,'RUNNER_CHANGED_AFTER_MOVE')
        print('STEP=POST_INTEGRATION_CANONICAL_FLOW',flush=True)
        check_log=S/'ROOT_INTEGRATION_RUNTIME_TEST.log';no_links(check_log)
        with check_log.open('w') as output:
            test=subprocess.run(['/bin/sh',str(RUNNER)],env=ENV,stdout=output,stderr=subprocess.STDOUT)
        print(check_log.read_text(errors='replace'),flush=True)
        remaining=[p.name for p in O.iterdir() if not p.is_symlink()]
        report={'protocol':'888','human_gate':'ACTIVE','authorization':'RENEWED_2026-09-28',
                'outcomes':outcomes,'moved_top_level_objects':sum(x['status']=='MOVED_AND_REFERENCES_PRESERVED' for x in outcomes),
                'remaining_physical_objects_in_old_root':sorted(remaining),'runtime_exit':test.returncode,
                'result':'PASS_NONCONFLICTING_ROOT_INTEGRATION' if test.returncode==0 else 'HOLD_POST_MOVE_RUNTIME',
                'nested_duplicate_resolution':'NOT_COMPLETED','full_parallel_system_integration':'NOT_CLAIMED',
                'data_deleted':False,'old_code_executed':False,'external_send':'NONE'}
        report_path=S/('ROOT_INTEGRATION_RESULT_'+str(time.time_ns())+'.json')
        with report_path.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
        print('SUMMARY_BEGIN');print(json.dumps(report,ensure_ascii=False,indent=2))
        print('REPORT='+str(report_path));print('BATCH_COMPLETE=YES' if test.returncode==0 else 'BATCH_COMPLETE=NO')

if __name__=='__main__':
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=IPHONE_JEDAN_KORIJEN_NASTAVAK_888',flush=True)
    try:main()
    except Exception as e:
        print('RESULT=HOLD\nREASON='+str(e)+'\nBATCH_COMPLETE=NO',flush=True);sys.exit(1)
