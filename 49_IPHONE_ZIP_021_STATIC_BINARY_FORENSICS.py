#!/usr/bin/env python3
import os, io, json, stat, time, math, hashlib, zipfile, tempfile
from collections import Counter
from datetime import datetime, timezone

INPUT="/root/ZA_CHAT_020_UPLOAD.zip"
INPUT_SHA="ba7c05bab6ebabe39e52436c8728de8096ca20b2b3566526a6051af8409f813c"
REPORT_SHA="7b803d979ebdd04cb8651be87d2c1f562ad50d57cef1d3209ae9bb538bb65a94"
RESULTS="/root/FREYA_RAD_888/REZULTATI"
UPLOAD="/root/ZA_CHAT_021_UPLOAD.zip"

def ident(s): return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def read_stable(path,limit):
    last=None
    for attempt in range(5):
        try:
            if os.path.realpath(path)!=path or os.path.islink(path): raise RuntimeError("PATH_NOT_DIRECT")
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,"rb",buffering=0) as f:
                a=os.fstat(f.fileno())
                if not stat.S_ISREG(a.st_mode) or a.st_size>limit: raise RuntimeError("TYPE_OR_SIZE")
                b=f.read(limit+1); c=os.fstat(f.fileno())
            d=os.lstat(path)
            if len(b)>limit or ident(a)!=ident(c) or ident(c)!=ident(d): raise RuntimeError("FILE_CHANGED")
            return b
        except FileNotFoundError as exc:
            last=exc
            if attempt<4: time.sleep(0.25*(attempt+1))
    raise RuntimeError("ISH_PATH_UNAVAILABLE_AFTER_5_ATTEMPTS") from last

def atomic(path,data):
    fd,tmp=tempfile.mkstemp(prefix="pending_",dir=os.path.dirname(path))
    try:
        with os.fdopen(fd,"wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    except BaseException:
        if os.path.lexists(tmp): os.unlink(tmp)
        raise

def load():
    raw=read_stable(INPUT,4*1024*1024)
    if hashlib.sha256(raw).hexdigest()!=INPUT_SHA: raise RuntimeError("INPUT_ZIP_SHA256")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.infolist())!=1: raise RuntimeError("INPUT_ZIP_STRUCTURE")
        b=z.read(z.infolist()[0])
    if hashlib.sha256(b).hexdigest()!=REPORT_SHA: raise RuntimeError("INPUT_REPORT_SHA256")
    d=json.loads(b)
    if d.get("batch")!="IPHONE_ZIP_020" or d.get("objects_verified")!=77: raise RuntimeError("INPUT_ROLE")
    return [x for x in d["records"] if x["classification"]=="HISTORICAL_OPAQUE_BINARY_MANUAL_HOLD"]

def entropy(data):
    if not data: return 0.0
    c=Counter(data); n=len(data)
    return round(-sum((v/n)*math.log2(v/n) for v in c.values()),4)

def classify(data):
    if len(data)>=16 and data[2:4]==b"\r\n" and data[4:8] in (b"\x00\x00\x00\x00",b"\x01\x00\x00\x00",b"\x02\x00\x00\x00",b"\x03\x00\x00\x00"):
        return "PYTHON_BYTECODE_HEADER_CANDIDATE"
    if data.startswith(b"\x7fELF"): return "ELF_BINARY"
    if data.startswith(b"MZ"): return "PE_BINARY"
    if data.startswith(b"SQLite format 3\x00"): return "SQLITE_DATABASE"
    if data.startswith(b"\x1f\x8b"): return "GZIP_CONTAINER"
    if data.startswith((b"PK\x03\x04",b"PK\x05\x06",b"PK\x07\x08")): return "ZIP_CONTAINER"
    if data.startswith(b"{\"py/object\"") or data.startswith(b"{\n") or data.startswith(b"[\n"):
        return "TEXT_SERIALIZATION_CANDIDATE"
    return "OPAQUE_BINARY_PRESERVATION_ONLY"

def main():
    if "ish" not in os.uname().release.lower() or os.geteuid()!=0: raise SystemExit("HOLD=Pogresno okruzenje")
    print("BATCH=IPHONE_ZIP_021; MODE=STATIC_NON_EXECUTING_BINARY_FORENSICS; DELETION=NOT_PERFORMED",flush=True)
    rows=load()
    if len(rows)!=17 or len({x["sha256"] for x in rows})!=17: raise SystemExit("HOLD=Ocekivano 17 zapisa")
    kinds=Counter(); out=[]
    for n,row in enumerate(rows,1):
        data=read_stable(row["view_path"],int(row["bytes"]))
        if len(data)!=int(row["bytes"]) or hashlib.sha256(data).hexdigest()!=row["sha256"]: raise SystemExit("HOLD=Objekat SHA ili velicina")
        kind=classify(data); kinds[kind]+=1
        printable=sum(1 for x in data if x in (9,10,13) or 32<=x<=126)
        out.append({"sha256":row["sha256"],"bytes":len(data),"view_path":row["view_path"],
                    "static_type":kind,"entropy_bits_per_byte":entropy(data),
                    "zero_byte_count":data.count(0),"ascii_printable_ratio":round(printable/len(data),6) if data else 1.0,
                    "content_excerpt_recorded":False,"strings_recorded":False,"execution_performed":False,
                    "handling":"PRESERVE_NON_EXECUTABLE_REFERENCE_ONLY"})
        print("ANALIZIRANO=%d/17 TIP=%s"%(n,kind),flush=True)
    result={"batch":"IPHONE_ZIP_021","created_utc":datetime.now(timezone.utc).isoformat(),
            "input_zip_sha256":INPUT_SHA,"input_report_sha256":REPORT_SHA,"objects_verified":17,
            "static_type_counts":dict(sorted(kinds.items())),"records":out,
            "inspection_methods":["MAGIC_HEADER","BYTE_DISTRIBUTION","ENTROPY","ZERO_COUNT"],
            "forbidden_methods_confirmed":["NO_EXECUTION","NO_IMPORT","NO_MARSHAL","NO_DECOMPILATION","NO_STRINGS_OUTPUT"],
            "active_runtime_modified":False,"network_used":False,
            "role_acceptance":"STATIC_CLASSIFICATION_COMPLETE_PRESERVATION_ONLY",
            "source_deletion":"NOT_PERFORMED","retirement_authorized":False,"goal_status":"INCOMPLETE"}
    encoded=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
    os.makedirs(RESULTS,mode=0o700,exist_ok=True)
    fd,path=tempfile.mkstemp(prefix="IPHONE_ZIP_021_FORENSICS_",suffix=".json",dir=RESULTS); os.close(fd); atomic(path,encoded)
    report_sha=hashlib.sha256(encoded).hexdigest()
    if os.path.lexists(UPLOAD): raise SystemExit("HOLD=ZA_CHAT_021_UPLOAD.zip vec postoji")
    with zipfile.ZipFile(UPLOAD,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z: z.writestr(os.path.basename(path),encoded)
    u=read_stable(UPLOAD,4*1024*1024)
    print("STATIC_TYPE_COUNTS="+json.dumps(dict(sorted(kinds.items()))))
    print("OBJECTS_VERIFIED=17\nEXECUTION_PERFORMED=NO\nCONTENT_EXCERPTS_RECORDED=NO")
    print("REPORT="+path+"\nREPORT_SHA256="+report_sha)
    print("UPLOAD_FILE="+UPLOAD+"\nUPLOAD_BYTES="+str(len(u))+"\nUPLOAD_SHA256="+hashlib.sha256(u).hexdigest())
    print("DELETION=NOT_PERFORMED; RETIREMENT_AUTHORIZED=NO; GOAL_STATUS=INCOMPLETE")

if __name__=="__main__": main()
