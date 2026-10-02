import hashlib,json,os,zipfile
from pathlib import Path
def e(k,v): print(f"{k}={v}",flush=True)
def hold(r): e("STATUS","HOLD");e("REASON",r);raise SystemExit(0)
e("PROTOCOL",888);e("BATCH","IPHONE_888_REVIEW_SCOPE_09");e("MODE","READ_ONLY_REVIEW_SCOPE")
e("HUMAN_GATE","ACTIVE");e("DEFAULT_MODE","DENY");e("FAIL_CLOSED","YES");e("WRITES",0);e("NETWORK_ACTIONS",0)
p=Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")
want="78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"
if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=want: hold("PACKET_GATE")
with zipfile.ZipFile(p) as z:
 pred=json.loads(z.read("PREDAJA.json").decode("utf-8","replace"))
 rep=json.loads(z.read("POSTOJECI_IZVJESTAJ.json").decode("utf-8","replace"))
 e("PRED_BINDINGS_TYPE",type(pred.get("bindings")).__name__)
 e("REPORT_ROWS_TYPE",type(rep.get("rows")).__name__)
 rows=rep.get("rows") if isinstance(rep.get("rows"),list) else []
 e("REPORT_ROWS",len(rows))
 for i,row in enumerate(rows,1):
  if not isinstance(row,dict): continue
  e(f"ROW_{i:02d}_KEYS",",".join(sorted(row.keys())))
  for k in ("source_sha256","name","filename","path","status","financial_accuracy_verified",
            "semantic_accuracy","information_freshness","findings","result","source"):
   if k in row:
    v=row[k]
    if isinstance(v,(dict,list)): v=json.dumps(v,ensure_ascii=False,separators=(",",":"))
    e(f"ROW_{i:02d}_{k.upper()}",str(v)[:2500])
 # Summarize each findings file including finding objects, but bounded.
 fns=[n for n in z.namelist() if n.endswith("/AI.json") or n.endswith("/AI_NALAZI.json")]
 e("FINDING_FILES",len(fns))
 total=0
 for i,n in enumerate(fns,1):
  o=json.loads(z.read(n).decode("utf-8","replace"))
  fs=o.get("findings",[])
  e(f"FIND_{i:02d}_SOURCE",str(o.get("source_sha256")))
  e(f"FIND_{i:02d}_FINANCIAL_VERIFIED",str(o.get("financial_accuracy_verified")))
  e(f"FIND_{i:02d}_COUNT",len(fs) if isinstance(fs,list) else -1)
  if isinstance(fs,list):
   total+=len(fs)
   for j,x in enumerate(fs,1):
    v=json.dumps(x,ensure_ascii=False,separators=(",",":")) if isinstance(x,(dict,list)) else str(x)
    e(f"FIND_{i:02d}_{j:02d}",v[:1800])
 e("TOTAL_FINDINGS_ENUMERATED",total)
 # Correctly classify uncovered value (can be int or list).
 u=pred.get("source_hashes_without_report_rows")
 if isinstance(u,int): uc=u
 elif isinstance(u,list): uc=len(u)
 elif u in (None,"",False): uc=0
 else: uc=-1
 e("UNCOVERED_SOURCE_COUNT",uc)
 e("UNMAPPED_SOURCE_GATE","PASS" if uc==0 else "HOLD")
 e("REVIEW_REQUIREMENT","HUMAN_OR_AUTHORITATIVE_DOMAIN_VALIDATION_REQUIRED")
 e("AUTOMATIC_TRUTH_PROMOTION","DENY")
 e("ASUS_SEND_AUTHORIZED","NO")
e("STATUS","REVIEW_SCOPE_COMPLETE");e("SOURCE_ORIGINALS_CHANGED","NO");e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
