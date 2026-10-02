#!/usr/bin/env python3
import os,json,hashlib,platform
from pathlib import Path
P=888;NODE="FREYA_IPHONE_ISH_NODE_888";B="IPHONE_888_BATCH_05R1_TEST_EVIDENCE_SEMANTIC_BINDING_20260921";AUTH="DANIJELA_DJUROVIC_KESKIN"
BASE=Path("/root/IPHONE_888_LOKALNI_h2a8tu_8"); T=BASE/"TESTS"
FILES=["TEST_RESULTS.json","REGRESSION_RESULTS.json","CORRUPT_XLSX.log","MISSING_INPUT.log","default.log","malformed.log","prefixed.log","strict.log","zero.log"]
CODE={"DOCUMENT_PROCESSOR":(BASE/"CODE/document_processor.py","8236c31e63747752248df5c70c13e7d3786dd53336387bb115a63fef5cc8f64d"),
"FINANCIAL_VALIDATOR":(BASE/"CODE/financial_validator_v2_888.py","97a77c63383646e81e56e2b5712714778dee6e4e9235b0d71e92cd1431a67db1")}
def out(**x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(q):
 h=hashlib.sha256()
 with q.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",MODE="READ_ONLY")
a=Path("/etc/alpine-release")
if os.getuid()!=0 or not a.exists():out(STATUS="HOLD",REASON="IPHONE_IDENTITY",NEXT="STOP");raise SystemExit(2)
out(event="IDENTITY",hostname=platform.node(),uid=os.getuid(),alpine=a.read_text().strip(),kernel=platform.release())
for role,(q,exp) in CODE.items():
 act=sha(q) if q.is_file() else None
 out(event="CODE_BINDING",role=role,path=str(q),sha256=act,expected_sha256=exp,hash_match=(act==exp))
for name in FILES:
 q=T/name
 if not q.is_file():
  out(event="EVIDENCE_DETAIL",path=str(q),status="MISSING");continue
 raw=q.read_bytes(); text=raw.decode("utf-8","replace")
 parsed=None
 if q.suffix.lower()==".json":
  try:parsed=json.loads(text)
  except Exception as e:parsed={"PARSE_ERROR":type(e).__name__}
 out(event="EVIDENCE_DETAIL",path=str(q),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
     content=text[:12000] if parsed is None else None,json=parsed)
# Verify receipt source bindings deterministically.
for q in sorted(T.glob("*/PROCESSOR/RECEIPT.json")):
 try:
  r=json.loads(q.read_text()); src=Path(r.get("source","")); claimed=r.get("sha256")
  actual=sha(src) if src.is_file() else None
  out(event="RECEIPT_SOURCE_BINDING",receipt=str(q),receipt_sha256=sha(q),source=str(src),
      claimed_source_sha256=claimed,actual_source_sha256=actual,hash_match=(claimed==actual),
      result=r.get("result"),network_action=r.get("network_action"),original_modified=r.get("original_modified"))
 except Exception as e:out(event="RECEIPT_SOURCE_BINDING",receipt=str(q),status="HOLD",reason=type(e).__name__)
out(event="AGENT_PRODUCTION_GATE",status="HOLD",reason="18_CONTRACT_SETS_MISSING_EXPLICIT_AUTHORIZED_FUNCTION_AND_DOCTRINE")
out(PROTOCOL=P,NODE=NODE,BATCH=B,HUMAN_GATE="ACTIVE",HUMAN_GATE_AUTHORITY=AUTH,DEFAULT_MODE="DENY",FAIL_CLOSED="YES",
WRITES=0,DELETIONS=0,OVERWRITES=0,NETWORK_ACTIONS=0,SOURCE_ORIGINALS_CHANGED="NO",TESTS_EXECUTED=0,
STATUS="TEST_EVIDENCE_SEMANTIC_BINDING_COMPLETE",NEXT="RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
