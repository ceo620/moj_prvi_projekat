#!/usr/bin/env python3
"""Reuse recorded executable candidates and compare only direct canonical runtime files."""
import hashlib, importlib.util, json, os, sys, time
from pathlib import Path
import fcntl

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def main():
    need(sys.argv[1:] == ['--povezi-888'], 'Use --povezi-888')
    helper = Path('/root/IPHONE_UJEDINI_MAPIRANE_NASTAVAK_888.py')
    need(not helper.is_symlink(), 'HELPER_SYMLINK')
    need(hashlib.sha256(helper.read_bytes()).hexdigest() == 'a0ba4e6c0a9d9613308d34984b811c318a9648e6d691ece610a0949737df0b59', 'HELPER_HASH_CHANGED')
    spec = importlib.util.spec_from_file_location('verified_merge_888', helper)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.budget()
    need(os.geteuid() == 0, 'ROOT_REQUIRED')
    need(m.plain_parents(m.STATE) and not m.STATE.is_symlink(), 'STATE_SYMLINK')
    lock_path = m.STATE / 'autopilot_schedule.lock'
    need(not lock_path.is_symlink() and not m.JOURNAL.is_symlink(), 'CONTROL_SYMLINK')
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        evidence = m.ROOT / 'IPHONE_888_EXECUTABLE_RECOVERY_08R1.json'
        evidence_raw = evidence.read_bytes()
        data = json.loads(evidence_raw)
        need(data.get('batch') == 'IPHONE_888_EXECUTABLE_RECOVERY_08R1', 'EVIDENCE_ID')
        candidates = data.get('candidates')
        need(isinstance(candidates, list), 'CANDIDATE_SCHEMA')
        runtime = m.ROOT / '05_SYSTEM_RUNTIME'
        targets = {}
        # One known directory only, no recursive inventory and no old-root walk.
        for p in sorted(runtime.iterdir()):
            m.budget()
            if p.is_symlink() or not p.is_file() or p.stat().st_size > 5242880:
                continue
            targets.setdefault(m.digest(p), []).append(p)
        outcomes = []
        with m.JOURNAL.open('a') as journal:
            for i, item in enumerate(candidates, 10001):
                if time.time() >= m.DEADLINE:
                    outcomes.append({'status':'TIME_WINDOW_ENDED'}); break
                src = Path(item['source']); expected = item['sha256']
                need(m.inside(src, m.OLD), 'SOURCE_SCOPE')
                matches = targets.get(expected, [])
                row = {'source':str(src), 'sha256':expected}
                if len(matches) != 1:
                    row['status'] = 'PRESERVED_NO_UNIQUE_CURRENT_RUNTIME_MATCH'
                    row['matches'] = len(matches)
                else:
                    dst = matches[0]
                    row['destination'] = str(dst)
                    try:
                        row['status'], row['duplicate_bytes_removed'] = m.apply_pair(src,dst,expected,journal,i)
                    except Exception as e:
                        row['status']='PRESERVED_FOR_REVIEW'; row['reason']=str(e)
                outcomes.append(row)
                print(row['status'] + ' | ' + src.name, flush=True)
            # Retry exactly the one recorded media exception; no rehash of 422 completed files.
            manifest = json.loads(m.MAP.read_bytes())
            suffix = '/IPHONE_CANONICAL_888/MEDIA/00-59-20_1.MP4'
            media = [r for r in manifest['integrated'] if r[0] == str(m.OLD)+suffix]
            need(len(media) == 1, 'MEDIA_MAP_NOT_UNIQUE')
            src, dst, expected = media[0]
            media_row = {'source':src, 'destination':dst}
            for attempt in range(3):
                if time.time() >= m.DEADLINE:
                    media_row['status']='TIME_WINDOW_ENDED'; break
                try:
                    media_row['status'], media_row['duplicate_bytes_removed'] = m.apply_pair(Path(src),Path(dst),expected,journal,20001)
                    break
                except Exception as e:
                    media_row['status']='PRESERVED_FOR_REVIEW'; media_row['reason']=str(e)
                    if 'embedded null byte' not in str(e) and not isinstance(e,OSError):
                        break
                    time.sleep(0.3)
            outcomes.append(media_row)
        summaries = []
        for root in (m.OLD,m.ROOT):
            p = root / 'IPHONE_CANONICAL_888/INTEGRATION_MANIFEST.json'
            row = {'path':str(p)}
            try:
                raw=p.read_bytes(); obj=json.loads(raw)
                row['sha256']=hashlib.sha256(raw).hexdigest()
                if isinstance(obj,dict):
                    row['fields']={k:({'type':type(v).__name__,'count':len(v),'sample':v[:2] if isinstance(v,list) else dict(list(v.items())[:2])} if isinstance(v,(dict,list)) else v) for k,v in obj.items()}
                else:
                    row['type']=type(obj).__name__;row['sample']=obj[:2]
            except Exception as e:
                row['error']=str(e)
            summaries.append(row)
        report={'protocol':'888','human_gate':'ACTIVE','runtime_evidence_sha256':hashlib.sha256(evidence_raw).hexdigest(),
                'outcomes':outcomes,'manifest_comparison':summaries,'old_code_executed':False,
                'external_send':'NONE','parallel_system_closure':'NOT_CLAIMED'}
        dest=m.STATE/('EXECUTABLE_CONSOLIDATION_'+str(time.time_ns())+'.json')
        with dest.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
        print('SUMMARY_BEGIN')
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print('REPORT='+str(dest))
        print('BATCH_COMPLETE=YES')

if __name__=='__main__':
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=IPHONE_POVEZI_IZVRSNE_KOMPONENTE_888',flush=True)
    try:main()
    except Exception as e:
        print('RESULT=HOLD\nREASON='+str(e)+'\nBATCH_COMPLETE=NO',flush=True)
        sys.exit(1)
