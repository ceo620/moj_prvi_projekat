#!/usr/bin/env python3
"""Read existing integration records and immediate directories only. No mutations."""
import hashlib, json, os
from pathlib import Path

R=Path('/root/FREYA_IPHONE_ISH_NODE_888')
O=Path('/root/FREYA_RAD_888')
S=R/'05_SYSTEM_RUNTIME/STATE'
FILES=[
 R/'IPHONE_888_CANONICAL_STABILITY_REPAIR_07.json',
 R/'09_EVIDENCE/IPHONE_888_RUNTIME_CONTENT_RECOVERY_04.json',
 O/'PRONADJENI_DIJELOVI_888/MANIFEST.json',
 O/'INDEX.json',
 O/'NE_DIRATI.txt',
 O/'PRONADJENI_DIJELOVI_888/PROCITAJ_PRVO.txt',
]

def summary(v,depth=0):
    if isinstance(v,dict):
        if depth>=4:return {'keys':list(v),'count':len(v)}
        return {k:('[REDACTED]' if any(x in k.lower() for x in ('password','private_key','api_key','credential','secret')) else summary(x,depth+1)) for k,x in v.items()}
    if isinstance(v,list):
        return {'count':len(v),'sample':[summary(x,depth+1) for x in (v if len(v)<=4 else v[:3]+v[-1:])]}
    if isinstance(v,str) and len(v)>1400:return v[:1400]+' [TRUNCATED]'
    return v

def path_refs(v,out):
    if isinstance(v,str) and v.startswith(('/root/','/mnt/','/etc/')):out.add(v)
    elif isinstance(v,dict):
        for x in v.values():path_refs(x,out)
    elif isinstance(v,list):
        for x in v:path_refs(x,out)

print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nMODE=READ_EXISTING_EVIDENCE_ONLY',flush=True)
for p in FILES:
    print('\nFILE='+str(p),flush=True)
    try:
        raw=p.read_bytes()
        print('SHA256='+hashlib.sha256(raw).hexdigest())
        if p.suffix=='.json':
            data=json.loads(raw);print(json.dumps(summary(data),ensure_ascii=False,indent=2))
            refs=set();path_refs(data,refs)
            print('REFERENCED_PATH_COUNT='+str(len(refs)))
            for name in sorted(refs)[:60]:print('REFERENCE='+name)
        else:print(raw.decode(errors='replace')[:12000])
    except Exception as e:print('READ_ERROR='+str(e))

print('\nIMMEDIATE_DIRECTORY_STATE',flush=True)
for folder in (O,R,R/'01_CANONICAL_BASE',R/'15_RUNTIME',R/'PREGLED_I_POPRAVKA',O/'05_SISTEM'):
    print('DIRECTORY='+str(folder))
    try:
        for p in sorted(folder.iterdir()):
            if p.is_symlink():print('LINK | '+p.name+' | '+repr(os.readlink(p)))
            elif p.is_dir():print('DIR | '+p.name)
            else:print('FILE | '+p.name+' | '+str(p.stat().st_size))
    except Exception as e:print('READ_ERROR='+str(e))

print('\nCONSOLIDATION_JOURNAL_SUMMARY')
try:
    completed={};issues=[]
    for line in (S/'MAPPED_FILE_CONSOLIDATION.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row.get('event') in ('DONE','RECOVERED_LINK'):completed[row['source']]=row['destination']
        elif row.get('event')=='SKIPPED':issues.append(row)
    print('COMPLETED_SOURCE_PATHS='+str(len(completed)))
    print('DISTINCT_DESTINATIONS='+str(len(set(completed.values()))))
    print('RECORDED_ISSUES='+json.dumps([x for x in issues if x['source'] not in completed],ensure_ascii=False))
except Exception as e:print('READ_ERROR='+str(e))
print('FILES_CHANGED=0\nRECURSIVE_SCAN=NO\nBATCH_COMPLETE=YES')
