#!/usr/bin/env python3
"""Preserve the reviewed v4.5 source and the user's amount-specific approval.
No change to the financial source, generator, runtime permissions or documents.
"""
from pathlib import Path
import hashlib,json,zipfile,subprocess,os
R=Path('/root/FREYA_IPHONE_ISH_NODE_888')
Z=Path('/mnt/ios_pretraga/FREYA_HOME_888/FREYA_IPHONE_DODACI_015_20260912T092322Z_5f0b9741.zip')
H='ea9c69abccabbe86a81bdb1cc25c51c0712345f1043dda069bc66b26c6b34f47'
def need(c,m):
    if not c: raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def plain(p):
    need(not any(x.is_symlink() for x in (p,*p.parents)),'SYMLINK: '+str(p))
def preserve(p,b):
    plain(p)
    if p.exists():
        need(p.is_file() and p.read_bytes()==b,'EXISTING_CONTENT_DIFFERS: '+str(p))
        return 'ALREADY_VERIFIED'
    with p.open('xb') as f:
        f.write(b);f.flush();os.fsync(f.fileno())
    need(p.read_bytes()==b,'WRITE_VERIFY')
    return 'SAVED'
def main():
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=ISH_SSOT_ODOBRENJE_888',flush=True)
    need('ish' in os.uname().release.lower(),'WRONG_DEVICE')
    dest=R/'01_CANONICAL_BASE/KNOWLEDGE'
    plain(dest);need(dest.is_dir(),'CANONICAL_KNOWLEDGE_MISSING')
    plain(Z)
    with zipfile.ZipFile(Z) as z:
        a=[i for i in z.infolist() if i.filename.endswith('MASTER_ASSUMPTIONS_V45.json')]
        need(len(a)==1 and not a[0].is_dir() and a[0].file_size<10000,'MEMBER_CHECK')
        raw=z.read(a[0]);member=a[0].filename
    need(sha(raw)==H,'SOURCE_HASH_CHANGED')
    j=json.loads(raw)
    need(j['tpc_eur']==27796156 and j['direct_capex_eur']==24715200 and j['contingency_eur']==2471520 and j['other_project_costs_eur']==609436,'FINANCIAL_SOURCE_CHANGED')
    need(j['direct_capex_eur']+j['contingency_eur']+j['other_project_costs_eur']==j['tpc_eur'],'TOTAL_MISMATCH')
    source=dest/'TITAN1_MASTER_ASSUMPTIONS_V45.json'
    approval=dest/'TITAN1_V45_ODOBRENJE_20260927.json'
    record={'protocol':'888','human_gate':'ACTIVE','approval_authority':'Danijela Đurović Keskin',
        'approval_received_at':'2026-09-27T19:10:44+02:00','user_statement':'27.796.156 odobravam',
        'purpose':'New TITAN 1 memorandum','approved_field':'tpc_eur','approved_value':27796156,'currency':'EUR',
        'source_path':str(source),'source_sha256':H,'archive_path':str(Z),'archive_member':member,
        'scope':'Approval of total project cost for the new memorandum',
        'other_source_assumptions':'NOT_APPROVED_BY_THIS_RECEIPT',
        'idc_treatment':'UNRESOLVED_NOT_ADDED_TO_APPROVED_TOTAL',
        'document_signoff':'PENDING','external_send':'NOT_AUTHORIZED_BY_THIS_RECEIPT'}
    receipt=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
    # Check both destinations before writing either.
    for p,b in ((source,raw),(approval,receipt)):
        plain(p)
        if p.exists():need(p.is_file() and p.read_bytes()==b,'DESTINATION_CONFLICT: '+str(p))
    os.umask(0o077)
    print('SOURCE='+preserve(source,raw)+' | '+str(source))
    print('APPROVAL='+preserve(approval,receipt)+' | '+str(approval))
    print('APPROVED_TOTAL_PROJECT_COST_EUR=27796156\nSOURCE_HASH=PASS',flush=True)
    code='import docx; from docx import Document; print("DOCX_IMPORT=PASS"); print("DOCX_VERSION="+str(docx.__version__))'
    try:
        v=subprocess.run(['/usr/bin/python3','-I','-B','-c',code],capture_output=True,text=True,timeout=15)
        print(v.stdout.strip())
        if v.returncode:print('DOCX_IMPORT=HOLD\nDETAIL='+v.stderr[-2000:])
    except subprocess.TimeoutExpired:print('DOCX_IMPORT=HOLD_TIMEOUT')
    p=R/'05_SYSTEM_RUNTIME/generate_SIGNALNI_MEMORANDUM_TITAN1__97a18cecc6af.py'
    plain(p)
    print('GENERATOR_HASH='+('PASS' if sha(p.read_bytes())=='97a18cecc6af347637429d2765731ee758a2b0597568c702430ed27b504507ac' else 'HOLD'))
    print('RESULT=PASS_AMOUNT_APPROVAL_PRESERVED\nNEW_MEMORANDUM=NOT_YET_GENERATED\nBATCH_COMPLETE=YES')
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('RESULT=HOLD\nREASON='+str(e));raise SystemExit(2)
