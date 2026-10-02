import hashlib,json,os,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
def e(k,v): print(f"{k}={v}",flush=True)
def hold(r): e("STATUS","HOLD");e("REASON",r);raise SystemExit(0)
e("PROTOCOL",888);e("BATCH","IPHONE_888_LOCAL_EVIDENCE_VALIDATION_10")
e("MODE","READ_ONLY_DETERMINISTIC_VALIDATION");e("HUMAN_GATE","ACTIVE");e("DEFAULT_MODE","DENY");e("FAIL_CLOSED","YES")
e("WRITES",0);e("NETWORK_ACTIONS",0);e("EXTERNAL_SEND","DENY")
p=Path("/root/mozak uzivo iphone/ZA_SLANJE/PAKET_cc5b080b7027_4c9fbcd725cb/IPHONE_ZA_ASUS_888.zip")
want="78afab0e896246906c9478fade3bff67185d45f37650c1139dbb751b8ad304fd"
if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=want:hold("PACKET_GATE")
with zipfile.ZipFile(p) as z:
 findings=[]
 for n in z.namelist():
  if n.endswith("/AI.json") or n.endswith("/AI_NALAZI.json"):
   o=json.loads(z.read(n).decode("utf-8","replace"))
   for f in o.get("findings",[]): findings.append((o.get("source_sha256"),f))
 sources={}
 for n in z.namelist():
  if n.startswith("IZVORI/") and not n.endswith("/"):
   sources[Path(n).stem]=(n,z.read(n))
 e("SOURCES",len(sources));e("FINDINGS",len(findings))
 # Evidence-only quote validation: exact quote token/value appears in raw OOXML/XML/text,
 # or quote is explicitly a formula and normalized formula appears.
 supported=partial=unresolved=0
 for i,(sh,f) in enumerate(findings,1):
  n,raw=sources[sh]
  quote=str(f.get("quote",""))
  ref=str(f.get("ref",""))
  ext=Path(n).suffix.lower()
  corpus=""
  if ext in (".xlsx",".docx"):
   try:
    with zipfile.ZipFile(__import__("io").BytesIO(raw)) as q:
     chunks=[]
     for m in q.namelist():
      if m.endswith(".xml"):
       try: chunks.append(q.read(m).decode("utf-8","replace"))
       except Exception: pass
     corpus="\n".join(chunks)
   except Exception: corpus=""
  else: corpus=raw.decode("utf-8","replace")
  # Build conservative tokens from quote; no semantic inference.
  tokens=[]
  for x in re.findall(r'(?<![A-Za-z0-9_])[-+]?\d+(?:[.,]\d+)?|[A-Za-zÀ-ž][A-Za-zÀ-ž0-9_./-]{3,}',quote):
   if len(x)>=4 or any(c.isdigit() for c in x): tokens.append(x)
  tokens=tokens[:20]
  hits=sum(1 for t in tokens if t in corpus or t.replace(",","") in corpus or t.replace(".","") in corpus)
  if tokens and hits==len(tokens): status="SOURCE_TEXT_SUPPORTED"; supported+=1
  elif tokens and hits>0: status="PARTIAL_SOURCE_SUPPORT"; partial+=1
  else: status="UNRESOLVED"; unresolved+=1
  e(f"FINDING_{i:02d}",f"{status}|SOURCE={sh[:12]}|REF={ref}|TOKENS={len(tokens)}|HITS={hits}")
 e("SOURCE_TEXT_SUPPORTED",supported);e("PARTIAL_SOURCE_SUPPORT",partial);e("UNRESOLVED",unresolved)
 e("IMPORTANT","SOURCE_TEXT_SUPPORT_DOES_NOT_PROVE_FINANCIAL_OR_SEMANTIC_TRUTH")
 e("FRESHNESS","NOT_ESTABLISHED_WITHOUT_AUTHORITATIVE_CURRENT_SOURCES")
 e("FINANCIAL_ACCURACY","NOT_AUTOMATICALLY_PROMOTED")
 e("ASUS_SEND_AUTHORIZED","NO")
e("STATUS","LOCAL_EVIDENCE_VALIDATION_COMPLETE");e("SOURCE_ORIGINALS_CHANGED","NO");e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
