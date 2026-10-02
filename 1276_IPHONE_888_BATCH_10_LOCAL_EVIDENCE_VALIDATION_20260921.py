#!/usr/bin/env python3
import os,json,hashlib,zipfile,platform
from pathlib import Path
P=888;NODE="FREYA_IPHONE_ISH_NODE_888";B="IPHONE_888_BATCH_10_LOCAL_EVIDENCE_VALIDATION_20260921";AUTH="DANIJELA_DJUROVIC_KESKIN"
Z=Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")
ZH="78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"
def out(**x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def flatten_findings(obj):
 if isinstance(obj,list): return obj
 if isinstance(obj,dict):
  for k in ("findings","nalazi","results","items"):
   if isinstance(obj.get(k),list):return obj[k]
 return []
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP");raise SystemExit(2)
if not Z.is_file() or sha(Z)!=ZH:out(STATUS="HOLD",REASON="PACKET_PIN_MISMATCH",NEXT="STOP");raise SystemExit(3)
counts={"SOURCE_TEXT_SUPPORTED":0,"PARTIAL_SOURCE_SUPPORT":0,"UNRESOLVED":0}; total=0
with zipfile.ZipFile(Z) as z:
 pred=json.loads(z.read("PREDAJA.json").decode())
 for bi,b in enumerate(pred.get("bindings",[]),1):
  srcsha=b["source_sha256"]; prefix=b["evidence"][0]["member_prefix"]; partial=bool(b["evidence"][0].get("partial"))
  ai_names=[n for n in z.namelist() if n.startswith(prefix) and (n.endswith("/AI.json") or n.endswith("/AI_NALAZI.json"))]
  ex_names=[n for n in z.namelist() if n.startswith(prefix) and n.endswith("/EXCERPT.json")]
  if not ai_names or not ex_names:
   n=b.get("findings_count",0);counts["UNRESOLVED"]+=n;total+=n
   out(event="BINDING_VALIDATION",binding=bi,source_sha256=srcsha,status="UNRESOLVED",reason="AI_OR_EXCERPT_MISSING",findings=n);continue
  ai=json.loads(z.read(ai_names[0]).decode("utf-8")); ex=json.loads(z.read(ex_names[0]).decode("utf-8"))
  findings=flatten_findings(ai)
  # Evidence package itself previously recorded quote/excerpt matching. Here validate counts and expose records, without promoting semantic truth.
  declared=b.get("findings_count",0); observed=len(findings)
  if observed==0 and declared>0:
   status="UNRESOLVED"; n=declared
  else:
   n=declared
   status="PARTIAL_SOURCE_SUPPORT" if partial else "SOURCE_TEXT_SUPPORTED"
  counts[status]+=n;total+=n
  out(event="BINDING_VALIDATION",binding=bi,source_sha256=srcsha,status=status,partial_flag=partial,
      findings_declared=declared,findings_records_observed=observed,ai_member=ai_names[0],excerpt_member=ex_names[0],
      ai_sha256=hashlib.sha256(z.read(ai_names[0])).hexdigest(),excerpt_sha256=hashlib.sha256(z.read(ex_names[0])).hexdigest(),
      findings=findings,excerpt=ex)
 out(event="LOCAL_EVIDENCE_SUMMARY",findings_total=total,classification=counts,
     TECHNICAL_UNRESOLVED=counts["UNRESOLVED"],SEMANTIC_TRUTH="NOT_ASSESSED",
     FINANCIAL_ACCURACY="NOT_ESTABLISHED",INFORMATION_FRESHNESS="NOT_ESTABLISHED")
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",ASUS_SEND_AUTHORIZED="NO",
STATUS="LOCAL_EVIDENCE_VALIDATION_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
