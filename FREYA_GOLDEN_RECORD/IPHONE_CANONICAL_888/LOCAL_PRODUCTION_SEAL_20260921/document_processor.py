import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path

src=Path(sys.argv[1])
out=Path(sys.argv[2])
if not src.is_file():
    raise SystemExit(2)

h=hashlib.sha256()
with src.open("rb") as f:
    for b in iter(lambda:f.read(1048576),b""):
        h.update(b)

ext=src.suffix.lower()
types={
 ".pdf":"DOCUMENT",".doc":"DOCUMENT",".docx":"DOCUMENT",
 ".xls":"FINANCIAL",".xlsx":"FINANCIAL",".csv":"FINANCIAL",
 ".txt":"TEXT",".md":"TEXT",".jpg":"IMAGE",".jpeg":"IMAGE",
 ".png":"IMAGE"
}
risk=[]
if ext in {".sh",".py",".exe",".apk"}: risk.append("EXECUTABLE_TYPE")
if src.stat().st_size>52428800: risk.append("LARGE_FILE")
if ext not in types: risk.append("UNKNOWN_TYPE")

out.mkdir(parents=True,exist_ok=True)
receipt={
 "result":"PASS","source":str(src),"sha256":h.hexdigest(),
 "bytes":src.stat().st_size,"extension":ext,
 "classification":types.get(ext,"UNKNOWN"),
 "risk":risk or ["NONE"],
 "mtime_utc":datetime.fromtimestamp(
   src.stat().st_mtime,timezone.utc).isoformat(),
 "network_action":"NONE","original_modified":"NO"
}
(out/"RECEIPT.json").write_text(
 json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print("RESULT=PASS")
print("RECEIPT="+str(out/"RECEIPT.json"))
