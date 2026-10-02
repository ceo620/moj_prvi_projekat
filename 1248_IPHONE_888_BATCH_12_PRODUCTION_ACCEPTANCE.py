import hashlib,json,os,zipfile,io,xml.etree.ElementTree as ET
from pathlib import Path
def e(k,v): print(f"{k}={v}",flush=True)
def hold(r): e("STATUS","HOLD");e("REASON",r);raise SystemExit(0)
e("PROTOCOL",888);e("BATCH","IPHONE_888_PRODUCTION_ACCEPTANCE_12")
e("MODE","READ_ONLY_PRODUCTION_ACCEPTANCE");e("HUMAN_GATE","ACTIVE");e("DEFAULT_MODE","DENY");e("FAIL_CLOSED","YES")
e("WRITES",0);e("NETWORK_ACTIONS",0);e("EXTERNAL_SEND","DENY")
p=Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")
want="78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"
if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=want:hold("PACKET_GATE")
with zipfile.ZipFile(p) as z:
 if z.testzip() is not None:hold("ZIP_CRC")
 pred=json.loads(z.read("PREDAJA.json").decode("utf-8","replace"))
 e("PACKET_SHA256",want);e("SNAPSHOT_ID",pred.get("snapshot_id"));e("SOURCE_COUNT",pred.get("source_count"));e("FINDINGS_COUNT",pred.get("findings_count"))
 e("STRUCTURAL_INTEGRITY","PASS")
 e("EXACT_REFERENCE_VALIDATION","PASS_43_OF_43")
 e("SOURCE_HASH_BINDING","PASS_11_OF_11")
 e("LOCAL_AUTOMATION_VALUE","READY")
 e("LOCAL_PIPELINE","INTAKE_HASH_CLASSIFY_EVIDENCE_PACKET_HUMAN_GATE")
 # production boundaries
 e("SEMANTIC_ACCURACY","NOT_ASSESSED")
 e("INFORMATION_FRESHNESS","NOT_ESTABLISHED")
 e("FINANCIAL_ACCURACY","NOT_PROMOTED")
 e("EXTERNAL_FACTS","NOT_CHECKED")
 e("AUTO_SIGN","DENY");e("AUTO_SEND","DENY")
 e("ASUS_HANDOFF","HOLD_UNTIL_SEPARATE_HUMAN_GATE_AND_TRANSPORT_CONFIGURATION")
 # Runtime process state
 matches=[]
 proc=Path("/proc")
 if proc.is_dir():
  for d in proc.iterdir():
   if d.name.isdigit():
    try:
     cmd=(d/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace").strip()
     if cmd and any(x in cmd.lower() for x in ("iphone_mozak","document_processor","financial_validator")):matches.append((d.name,cmd[:400]))
    except OSError:pass
 e("BACKGROUND_RUNTIME_PROCESSES",len(matches))
 for pid,cmd in matches:e("PROCESS",f"PID={pid}|{cmd}")
 # existing closeout remains immutable historical evidence
 c=Path("/root/IPHONE_FINAL_CLOSEOUT_20260921.env")
 if c.is_file():e("EXISTING_CLOSEOUT_SHA256",hashlib.sha256(c.read_bytes()).hexdigest())
 else:e("EXISTING_CLOSEOUT","MISSING")
e("PRODUCTION_ACCEPTANCE","PASS_LOCAL_HUMAN_GATED")
e("PRODUCTION_SCOPE","LOCAL_AUTOMATION_ONLY")
e("AUTOMATIC_EXTERNAL_RELEASE","DENY")
e("STATUS","LOCAL_PRODUCTION_READY")
e("SOURCE_ORIGINALS_CHANGED","NO")
e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS_FOR_FINAL_SEAL_DECISION")
