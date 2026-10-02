#!/usr/bin/env python3
import hashlib, json, os, stat, subprocess, tempfile
from pathlib import Path
R=Path('/root/FREYA_IPHONE_ISH_NODE_888')
L=Path('/usr/local/bin/freya')
T=R/'05_SYSTEM_RUNTIME/FREYA_RUN_V2__ee7e37bd8707.sh'
C=R/'15_RUNTIME/HUMAN_GATE_CONSOLE_V1/freya_gate.py'
E=R/'09_EVIDENCE/STVARNI_TOK_jq6nmicx/RESULT.json'
def need(ok, reason):
    if not ok: raise RuntimeError(reason)
def read(p):
    need(not any(q.is_symlink() for q in (p,*p.parents)), 'SYMLINK: '+str(p))
    need(p.is_file() and p.stat().st_size<1048576,'INVALID_FILE: '+str(p))
    return p.read_bytes()
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE',flush=True)
    need('ish' in os.uname().release.lower(),'WRONG_DEVICE')
    old=read(L)
    expected=('#!/bin/sh\nunset ENV BASH_ENV PYTHONPATH PYTHONHOME\nexec /usr/bin/python3 -I -S -B '+str(C)+' "$@"\n').encode()
    need(old==expected,'LAUNCHER_CHANGED')
    report=json.loads(read(E))
    runtime=read(T)
    need(report['result']=='PASS_LOCAL_CLASSIFICATION_FLOW' and report['launcher_installed'],'FLOW_NOT_VERIFIED')
    need(sha(runtime)==report['launcher_new_sha256'],'RUNTIME_CHANGED')
    console=read(C)
    new=('#!/bin/sh\nunset ENV BASH_ENV PYTHONPATH PYTHONHOME\ncase "${1-}" in\n'
         '  obradi)\n    [ "$#" -eq 1 ] || exit 2\n'
         '    exec /bin/sh '+str(T)+'\n    ;;\n'
         '  "") exec /usr/bin/python3 -I -S -B '+str(C)+' ;;\n'
         '  *) printf "%s\\n" "Upotreba: freya | freya obradi"; exit 2 ;;\nesac\n').encode()
    os.umask(0o077)
    d=Path(tempfile.mkdtemp(prefix='FREYA_POVEZIVANJE_',dir=R/'09_EVIDENCE'))
    (d/'launcher_before.sh').write_bytes(old)
    candidate=d/'candidate.sh'
    candidate.write_bytes(new)
    v=subprocess.run(['/bin/sh','-n',str(candidate)],capture_output=True,timeout=10)
    need(v.returncode==0,'SYNTAX')
    v=subprocess.run(['/bin/sh',str(candidate)],input='0\n',text=True,capture_output=True,timeout=15)
    need(v.returncode==0 and 'HUMAN_GATE_CONSOLE=CLOSED' in v.stdout,'CONSOLE_TEST')
    # Test explicit dispatch without executing another production cycle.
    probe=d/'dispatch_test.sh'
    probe.write_bytes(new.replace(('exec /bin/sh '+str(T)).encode(),b'printf "DISPATCH_OK\\n"'))
    v=subprocess.run(['/bin/sh',str(probe),'obradi'],capture_output=True,text=True,timeout=10)
    need(v.returncode==0 and v.stdout=='DISPATCH_OK\n','DISPATCH_TEST')
    need(read(L)==old and read(T)==runtime and read(C)==console,'CONCURRENT_CHANGE')
    candidate.chmod(stat.S_IMODE(L.stat().st_mode))
    os.replace(candidate,L)
    need(read(L)==new,'INSTALL_CHECK')
    result={'result':'PASS_COMMAND_BINDING','launcher_sha256':sha(new),'runtime_sha256':sha(runtime),'backup':str(d/'launcher_before.sh'),'production_cycle_executed':False}
    (d/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CONSOLE_TEST=PASS\nDISPATCH_TEST=PASS\nFREYA_OBRADI=CONNECTED\nPRODUCTION_CYCLE_EXECUTED=NO\nREPORT='+str(d/'RESULT.json')+'\nBATCH_COMPLETE=YES')
if __name__=='__main__':
    try: main()
    except Exception as e:
        print('RESULT=HOLD\nREASON='+str(e))
        raise SystemExit(2)
