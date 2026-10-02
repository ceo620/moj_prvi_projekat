import ast, hashlib, json, os, re
from pathlib import Path
def e(k,v): print(f"{k}={v}",flush=True)
def hold(r): e("STATUS","HOLD"); e("REASON",r); raise SystemExit(0)
e("PROTOCOL",888); e("BATCH","IPHONE_888_ACTIVATION_GATE_05")
e("MODE","READ_ONLY_ACTIVATION_GATE"); e("HUMAN_GATE","ACTIVE"); e("DEFAULT_MODE","DENY"); e("FAIL_CLOSED","YES")
e("WRITES",0); e("DELETIONS",0); e("OVERWRITES",0); e("NETWORK_ACTIONS",0); e("PROJECT_CODE_EXECUTED",0)
if os.geteuid()!=0: hold("EXPECTED_ROOT")
expected={
"/root/IPHONE_MOZAK_001_POKRENI_888.sh":"924b61e76263e30ba011154008cc0f43bb8051dcf009bae51a117c187a892459",
"/root/IPHONE_MOZAK_001_PRIPREMA_888.py":"d2c40751268303ce032e1aadea6d58ba80e57c50a23cbdca0e5d736dd1faf41d",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/CODE/document_processor.py":"8236c31e63747752248df5c70c13e7d3786dd53336387bb115a63fef5cc8f64d",
"/root/IPHONE_888_LOKALNI_h2a8tu_8/CODE/financial_validator_v2_888.py":"97a77c63383646e81e56e2b5712714778dee6e4e9235b0d71e92cd1431a67db1"}
for p,h in expected.items():
 q=Path(p)
 if not q.is_file(): hold("MISSING:"+p)
 got=hashlib.sha256(q.read_bytes()).hexdigest(); e("HASH",p+"|"+got)
 if got!=h: hold("HASH_MISMATCH:"+p)
e("PINNED_HASH_GATE","PASS")
launcher=Path("/root/IPHONE_MOZAK_001_POKRENI_888.sh").read_text(errors="replace")
cmds=[x.strip() for x in launcher.splitlines() if x.strip() and not x.lstrip().startswith("#")]
e("LAUNCHER_COMMAND_COUNT",len(cmds))
for i,x in enumerate(cmds,1): e(f"LAUNCHER_{i:02d}",x[:1000])
prep=Path("/root/IPHONE_MOZAK_001_PRIPREMA_888.py").read_text(errors="replace")
tree=ast.parse(prep)
e("PREP_FUNCTIONS",",".join(n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))))
for n in tree.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  name=n.targets[0].id
  if name.upper()==name:
   try: e("PREP_CONST_"+name,str(ast.literal_eval(n.value))[:1000])
   except Exception: pass
base=Path("/root/FREYA_SEGMENTS_014_d_20s9r2/PAYLOAD/AGENT_CONTRACTS/PAYLOAD/AGENT_CONTRACTS")
for i in range(1,19):
 d=base/f"{i:02d}"; docs=[]
 for n in ("DOCTRINE.env","INPUT_CONTRACT.env","OUTPUT_CONTRACT.env"):
  p=d/n
  if not p.is_file(): hold(f"AGENT_{i:02d}_{n}_MISSING")
  docs.append(p.read_text(errors="replace"))
 joined="\n".join(docs)
 if "PROTOCOL=888" not in joined or "HUMAN_GATE" not in joined: hold(f"AGENT_{i:02d}_POLICY_INCOMPLETE")
 if "EXTERNAL_SEND=DENY" not in docs[0] or "AUTO_SEND=DENY" not in docs[2]: hold(f"AGENT_{i:02d}_SEND_POLICY_FAIL")
e("AGENT_POLICY_GATE","PASS_18_OF_18")
for fn in ("TEST_RESULTS.json","REGRESSION_RESULTS.json"):
 p=Path("/root/IPHONE_888_LOKALNI_h2a8tu_8/TESTS")/fn
 try: obj=json.loads(p.read_text())
 except Exception: hold("BAD_TEST_EVIDENCE:"+str(p))
 if not obj or not all(v is True for v in obj.values()): hold("TEST_EVIDENCE_NOT_ALL_TRUE:"+fn)
 e(fn.replace(".json","")+"_GATE","PASS")
paths=set(re.findall(r'["\\\'](/root/[^"\\\']+)["\\\']',launcher+"\n"+prep))
for p in sorted(paths): e("DECLARED_PATH",p+"|"+("PRESENT" if Path(p).exists() else "NOT_FOUND"))
missing=[p for p in sorted(paths) if not Path(p).exists()]
e("DECLARED_ABSOLUTE_PATHS",len(paths)); e("DECLARED_PATHS_MISSING",len(missing))
for p in missing: e("MISSING_PATH",p)
e("STATUS","ACTIVATION_GATE_COMPLETE"); e("ACTIVATION_AUTHORIZED","NO")
e("REASON","HUMAN_GATE_REVIEW_REQUIRED_BEFORE_FIRST_WRITE_OR_RUNTIME_START")
e("SOURCE_ORIGINALS_CHANGED","NO"); e("NEXT","RETURN_COMPLETE_OUTPUT_TO_MAGNUS")
