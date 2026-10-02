import hashlib,os,re
from pathlib import Path
def e(k,v): print(f"{k}={v}",flush=True)
def hold(r): e("STATUS","HOLD");e("REASON",r);raise SystemExit(0)
e("PROTOCOL",888);e("BATCH","IPHONE_888_RUNTIME_TRIGGER_PREFLIGHT_14")
e("MODE","READ_ONLY_RUNTIME_TRIGGER_PREFLIGHT");e("HUMAN_GATE","ACTIVE");e("DEFAULT_MODE","DENY");e("FAIL_CLOSED","YES")
e("WRITES",0);e("NETWORK_ACTIONS",0);e("BACKGROUND_STARTS",0)
seal=Path("/root/IPHONE_LOCAL_PRODUCTION_SEAL_20260921.env")
want="f995fa40a34d5551f7df905c4bf857a986b56341a7408409bc6983454a3ea436"
if not seal.is_file() or hashlib.sha256(seal.read_bytes()).hexdigest()!=want:hold("FINAL_SEAL_GATE")
e("FINAL_SEAL_GATE","PASS")
# Discover existing schedulers/triggers only; do not create or start anything.
for p in (Path("/etc/crontabs/root"),Path("/var/spool/cron/crontabs/root")):
 if p.is_file():
  e("CRON_FILE",str(p))
  lines=[x for x in p.read_text(errors="replace").splitlines() if x.strip() and not x.lstrip().startswith("#")]
  e("CRON_ACTIVE_LINES",len(lines))
  for i,x in enumerate(lines,1):e(f"CRON_{i:02d}",x[:1000])
  break
else:e("CRON_FILE","NOT_FOUND");e("CRON_ACTIVE_LINES",0)
# Existing likely trigger scripts in /root only, excluding audit batches.
hits=[]
for p in Path("/root").iterdir():
 try:
  if p.is_file() and p.name not in {f"IPHONE_888_BATCH_{i:02d}_RUNTIME_TRIGGER_PREFLIGHT.py" for i in range(1,30)}:
   low=p.name.lower()
   if any(x in low for x in ("pokreni","start","runtime","watchdog","cron","daemon","worker","agent")) and p.suffix in (".py",".sh",".ash",""):
    hits.append(p)
 except OSError:pass
e("TRIGGER_CANDIDATES",len(hits))
for i,p in enumerate(sorted(hits,key=lambda x:x.name)[:120],1):
 b=p.read_bytes()
 e(f"TRIGGER_{i:03d}",f"{p}|SIZE={len(b)}|SHA256={hashlib.sha256(b).hexdigest()}")
# Check whether preparation launcher is suitable for repeated operation: it is create-only.
launcher=Path("/root/IPHONE_MOZAK_001_POKRENI_888.sh")
if launcher.is_file():
 e("KNOWN_LAUNCHER_SHA256",hashlib.sha256(launcher.read_bytes()).hexdigest())
 e("KNOWN_LAUNCHER","PRESENT")
else:e("KNOWN_LAUNCHER","MISSING")
# Current processes
matches=[]
proc=Path("/proc")
if proc.is_dir():
 for d in proc.iterdir():
  if d.name.isdigit():
   try:
    cmd=(d/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace").strip()
    if cmd and any(x in cmd.lower() for x in ("iphone_mozak","document_processor","financial_validator","watchdog","crond")):matches.append((d.name,cmd[:500]))
   except OSError:pass
e("CURRENT_MATCHING_PROCESSES",len(matches))
for pid,cmd in matches:e("PROCESS",f"PID={pid}|{cmd}")
e("STATUS","RUNTIME_TRIGGER_PREFLIGHT_COMPLETE")
e("RUNTIME_START_AUTHORIZED","NO")
e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
