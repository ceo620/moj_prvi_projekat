#!/usr/bin/env python3
import os,json,hashlib,zipfile,stat,platform,re
from pathlib import Path
P=888;NODE="FREYA_IPHONE_ISH_NODE_888";B="IPHONE_888_BATCH_07_PACKET_ACCEPTANCE_20260921";AUTH="DANIJELA_DJUROVIC_KESKIN"
PACKETS=[
Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_07dc7d558863/IPHONE_ZA_ASUS_888.zip"),
Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")]
EXPECTED={
str(PACKETS[0]):"09372246860fb8ad08a063b1ecba5d181dc80cbc656b501b4945ad16a6f8a59f",
str(PACKETS[1]):"78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"}
def out(**x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY",ASUS_SEND_AUTHORIZED="NO")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP");raise SystemExit(2)
out(event="IDENTITY",hostname=platform.node(),uid=os.getuid(),alpine=a.read_text().strip(),kernel=platform.release())
packet_hashes=[]
for q in PACKETS:
 if not q.is_file():
  out(event="PACKET",path=str(q),status="HOLD",reason="MISSING");continue
 digest=sha(q); packet_hashes.append(digest)
 st=q.stat(); exp=EXPECTED[str(q)]
 info={"event":"PACKET","path":str(q),"bytes":st.st_size,"sha256":digest,"expected_sha256":exp,"hash_match":digest==exp}
 try:
  with zipfile.ZipFile(q,"r") as z:
   names=z.namelist(); bad=z.testzip()
   unsafe=[n for n in names if n.startswith(("/", "\\")) or ".." in Path(n.replace("\\","/")).parts]
   members=[]
   for zi in z.infolist():
    members.append({"name":zi.filename,"bytes":zi.file_size,"compressed":zi.compress_size,"crc":f"{zi.CRC:08x}"})
   manifest_names=[n for n in names if any(k in n.upper() for k in ("MANIFEST","LINEAGE","RECEIPT"))]
   info.update(zip_open="PASS",crc_test="PASS" if bad is None else "FAIL",first_bad_member=bad,
               member_count=len(names),unsafe_paths=unsafe,manifest_lineage_receipt_members=manifest_names,members=members[:5000])
 except Exception as e:info.update(zip_open="FAIL",error=type(e).__name__+":"+str(e)[:300])
 out(**info)
out(event="PACKET_COMPARISON",packet_count=len(packet_hashes),distinct_sha256=len(set(packet_hashes)),
same_packet_bytes="NO" if len(set(packet_hashes))>1 else "YES",
NOTE="DISTINCT_HASHES_REQUIRE_SEPARATE_LINEAGE_REVIEW_NO_AUTOMATIC_CANONICAL_SELECTION")
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",ASUS_SEND_AUTHORIZED="NO",
STATUS="PACKET_ACCEPTANCE_READ_ONLY_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
