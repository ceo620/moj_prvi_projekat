import hashlib, json, os, stat, zipfile
from pathlib import Path

def e(k,v): print(f"{k}={v}",flush=True)
def hold(r): e("STATUS","HOLD"); e("REASON",r); raise SystemExit(0)

e("PROTOCOL",888); e("BATCH","IPHONE_888_PACKET_ACCEPTANCE_07")
e("MODE","READ_ONLY_POST_ACTIVATION_ACCEPTANCE"); e("HUMAN_GATE","ACTIVE")
e("DEFAULT_MODE","DENY"); e("FAIL_CLOSED","YES")
e("WRITES",0); e("DELETIONS",0); e("OVERWRITES",0); e("NETWORK_ACTIONS",0)
e("EXTERNAL_SEND","DENY")
if os.geteuid()!=0: hold("EXPECTED_ROOT")

packet=Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")
expected="78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"
if not packet.is_file(): hold("EXACT_PACKET_MISSING")
b=packet.read_bytes(); got=hashlib.sha256(b).hexdigest()
e("PACKET",packet); e("PACKET_BYTES",len(b)); e("PACKET_SHA256",got)
if got!=expected: hold("PACKET_SHA256_MISMATCH")
e("PACKET_HASH_GATE","PASS")

try:
 z=zipfile.ZipFile(packet,"r")
 bad=z.testzip()
 e("ZIP_CRC_GATE","PASS" if bad is None else "FAIL:"+str(bad))
 if bad is not None: hold("ZIP_CRC")
 infos=z.infolist()
 e("ZIP_MEMBERS",len(infos))
 total=sum(x.file_size for x in infos)
 e("ZIP_UNCOMPRESSED_BYTES",total)
 for i,x in enumerate(infos,1):
  name=x.filename
  if name.startswith("/") or ".." in Path(name).parts: hold("UNSAFE_MEMBER:"+name)
  e(f"MEMBER_{i:02d}",f"{name}|SIZE={x.file_size}|CRC={x.CRC:08x}")
 # Parse small governance/evidence JSON members without extraction.
 json_members=[x for x in infos if x.filename.lower().endswith(".json") and x.file_size<=2_000_000]
 for x in json_members:
  try:
   raw=z.read(x)
   obj=json.loads(raw.decode("utf-8","replace"))
   e("JSON_MEMBER",x.filename)
   e("JSON_SHA256",hashlib.sha256(raw).hexdigest())
   if isinstance(obj,dict):
    keys=sorted(obj.keys())
    e("JSON_KEYS",",".join(keys)[:2000])
    for k in ("protocol","batch","result","source_count","findings_count","network_calls",
              "source_writes","existing_files_overwritten","human_gate","next","snapshot_id"):
     if k in obj: e("JSON_FIELD_"+k.upper(),str(obj[k])[:1000])
  except Exception as ex:
   e("JSON_PARSE",x.filename+"|"+type(ex).__name__)
 z.close()
except zipfile.BadZipFile: hold("BAD_ZIP")

# Confirm source directory remains present; do not hash entire source again.
src=Path("/root/mozak uzivo iphone")
e("SOURCE_ROOT","PRESENT" if src.is_dir() else "MISSING")
# Confirm no background runtime matching project markers.
procs=[]
proc=Path("/proc")
if proc.is_dir():
 for d in proc.iterdir():
  if d.name.isdigit():
   try:
    cmd=(d/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace").strip()
    if cmd and any(x in cmd.lower() for x in ("iphone_mozak","document_processor","financial_validator","agent_contract")):
     procs.append((d.name,cmd[:500]))
   except OSError: pass
e("MATCHING_BACKGROUND_PROCESSES",len(procs))
for pid,cmd in procs: e("PROCESS",f"PID={pid}|{cmd}")

e("STATUS","PACKET_ACCEPTANCE_COMPLETE")
e("ASUS_SEND_AUTHORIZED","NO")
e("SOURCE_ORIGINALS_CHANGED_BY_THIS_BATCH","NO")
e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
