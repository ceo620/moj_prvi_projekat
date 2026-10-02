#!/usr/bin/env python3
import os,json,hashlib,zipfile,platform
from pathlib import Path
P=888;NODE="FREYA_IPHONE_ISH_NODE_888";B="IPHONE_888_BATCH_09_REVIEW_SCOPE_20260921";AUTH="DANIJELA_DJUROVIC_KESKIN"
Z=Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")
ZH="78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"
def out(**x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP");raise SystemExit(2)
if not Z.is_file() or sha(Z)!=ZH:out(STATUS="HOLD",REASON="PACKET_PIN_MISMATCH",NEXT="STOP");raise SystemExit(3)
with zipfile.ZipFile(Z) as z:
 pred=json.loads(z.read("PREDAJA.json").decode("utf-8"))
 total=0; exact_source=0; partial_bindings=0; missing_members=0
 for i,b in enumerate(pred.get("bindings",[]),1):
  source_sha=b.get("source_sha256"); findings=b.get("findings_count",0); total+=findings
  sources=b.get("sources",[]); evidence=b.get("evidence",[])
  src_results=[]
  for s in sources:
   m=s.get("member"); present=m in z.namelist()
   actual=hashlib.sha256(z.read(m)).hexdigest() if present else None
   match=(actual==source_sha) if present else False
   if match:exact_source+=1
   if not present:missing_members+=1
   src_results.append({"member":m,"present":present,"actual_sha256":actual,"source_sha256_match":match,"original_path":s.get("path")})
  ev_results=[]
  for e in evidence:
   prefix=e.get("member_prefix",""); members=sorted(n for n in z.namelist() if n.startswith(prefix))
   partial=bool(e.get("partial")); partial_bindings+=int(partial)
   ev_results.append({"member_prefix":prefix,"members":members,"partial":partial,
      "quotes_match_saved_excerpt":e.get("quotes_match_saved_excerpt"),"evidence_path":e.get("path")})
  out(event="FINDING_SOURCE_SCOPE",binding=i,findings_count=findings,source_sha256=source_sha,sources=src_results,evidence=ev_results)
 out(event="REVIEW_SCOPE_SUMMARY",bindings=len(pred.get("bindings",[])),findings_count_declared=pred.get("findings_count"),
     findings_count_summed=total,source_count_declared=pred.get("source_count"),source_bindings_hash_matched=exact_source,
     partial_evidence_bindings=partial_bindings,missing_source_members=missing_members,
     EXACT_REFERENCE_STATUS="NOT_YET_VALIDATED",SEMANTIC_TRUTH="NOT_ASSESSED")
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",ASUS_SEND_AUTHORIZED="NO",
STATUS="REVIEW_SCOPE_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
