import os, pwd, hashlib, json, stat, re
from pathlib import Path
def e(k,v): print(f"{k}={v}",flush=True)
e("PROTOCOL",888); e("BATCH","IPHONE_888_VALUE_MAP_03"); e("MODE","READ_ONLY")
e("HUMAN_GATE","ACTIVE"); e("DEFAULT_MODE","DENY"); e("FAIL_CLOSED","YES")
e("WRITES",0); e("DELETIONS",0); e("OVERWRITES",0); e("NETWORK_ACTIONS",0)
if os.geteuid()!=0: e("STATUS","HOLD"); e("REASON","EXPECTED_ROOT"); raise SystemExit
roots=[Path("/root/IPHONE_888_LOKALNI_h2a8tu_8"),Path("/root/FREYA_SEGMENTS_014_d_20s9r2"),
       Path("/root/cmu"),Path("/root/Documents"),Path("/root")]
targets=[]
for r in roots:
    e("ROOT_"+re.sub(r'[^A-Z0-9]+','_',r.name.upper()),"PRESENT" if r.exists() else "NOT_FOUND")
# exact high-value files surfaced by batch 02 + nearby control/runtime candidates
exact=[
"/root/IPHONE_MOZAK_001_POKRENI_888.sh",
"/root/IPHONE_MOZAK_001_PRIPREMA_888.py",
"/root/IPHONE_MOZAK_004_KLJUC_ZA_ASUS_888.py",
"/root/IPHONE_ASUS_024_PRENOS_888.py",
"/root/IPHONE_ASUS_027_PRENOS_888.py",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/CODE/document_processor.py",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/CODE/financial_validator_v2_888.py",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/TESTS/TEST_RESULTS.json",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/TESTS/REGRESSION_RESULTS.json",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/REZULTAT.json",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/MODULE_LINEAGE.json",
"/root/IPHONE_FINAL_CLOSEOUT_20260921.env"]
for s in exact:
    p=Path(s)
    if p.is_file():
        b=p.read_bytes()
        e("FILE",s); e("SIZE",len(b)); e("SHA256",hashlib.sha256(b).hexdigest())
        e("MODE_OCT",oct(stat.S_IMODE(p.stat().st_mode)))
# bounded discovery of executable/control/db surfaces, no execution
patterns=("agent","runtime","worker","dispatcher","watchdog","queue","intake","policy",
          "recovery","knowledge","cmu","sqlite","asus","handoff","document","factory","seal","ssot")
hits=[]
for base in [Path("/root")]:
    for root,ds,fs in os.walk(base,topdown=True,followlinks=False):
        depth=len(Path(root).parts)-1
        if depth>7: ds[:]=[]; continue
        for n in fs:
            p=Path(root)/n; low=str(p).lower()
            if (n.endswith((".py",".sh",".db",".sqlite",".sqlite3",".json",".env")) and
                any(x in low for x in patterns)):
                try:
                    st=p.stat()
                    if stat.S_ISREG(st.st_mode):
                        hits.append((st.st_mtime,st.st_size,str(p)))
                except OSError: pass
hits.sort(reverse=True)
e("QUALIFIED_SURFACES",len(hits))
for i,(mt,sz,p) in enumerate(hits[:180],1):
    e(f"SURFACE_{i:03d}",f"{p}|SIZE={sz}|MTIME={int(mt)}")
# process snapshot via /proc only
procs=[]
proc=Path("/proc")
if proc.is_dir():
    for d in proc.iterdir():
        if d.name.isdigit():
            try:
                cmd=(d/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace").strip()
                if cmd and any(x in cmd.lower() for x in ("python","cron","freya","titan","iphone","agent","worker")):
                    procs.append((d.name,cmd[:500]))
            except OSError: pass
e("MATCHING_PROCESSES",len(procs))
for i,(pid,cmd) in enumerate(procs[:50],1): e(f"PROCESS_{i:02d}",f"PID={pid}|{cmd}")
e("STATUS","VALUE_MAP_COMPLETE"); e("SOURCE_ORIGINALS_CHANGED","NO")
e("PROJECT_CODE_EXECUTED","NO"); e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
