#!/usr/bin/env python3
import os
import json
import stat
import hashlib
import tempfile
import zipfile
import time
from collections import Counter
from datetime import datetime, timezone

ROOT = "/root/FREYA_RAD_888"
VIEW = ROOT + "/PRONADJENI_DIJELOVI_888/IPHONE_ZIP_018_INTEGRATED_VIEW"
MANIFEST = VIEW + "/INTEGRATION_MANIFEST.json"
MANIFEST_SHA = "3ad916d76b599c1f00105ea67cee9c4f3c752c468f5eda4332a5901ec44d670a"
RESULTS = ROOT + "/REZULTATI"
UPLOAD = "/root/ZA_CHAT_019_UPLOAD.zip"
ALLOWED = {
    "INTEGRATED_VIEW": ("MEDIA", "DOCUMENTS", "KNOWLEDGE", "TEXT_REVIEW"),
    "HOLD_SENSITIVE_PATTERN": ("SENSITIVE_TEXT_HOLD",),
    "HOLD_RUNTIME_OR_BINARY": ("RUNTIME_HOLD",),
}

def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def read_stable(path, limit):
    last = None
    for attempt in range(5):
        try:
            if os.path.realpath(path) != path or os.path.islink(path):
                raise RuntimeError("PATH_NOT_DIRECT")
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb", buffering=0) as f:
                before = os.fstat(f.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                    raise RuntimeError("TYPE_OR_SIZE")
                data = f.read(limit + 1)
                after = os.fstat(f.fileno())
            current = os.lstat(path)
            if len(data) > limit or identity(before) != identity(after) or identity(after) != identity(current):
                raise RuntimeError("FILE_CHANGED")
            return data, after
        except FileNotFoundError as exc:
            last = exc
            if attempt < 4:
                time.sleep(0.25 * (attempt + 1))
    raise RuntimeError("ISH_PATH_UNAVAILABLE_AFTER_5_ATTEMPTS") from last

def atomic(path, data):
    fd, tmp = tempfile.mkstemp(prefix="pending_", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.lexists(tmp): os.unlink(tmp)
        raise

def main():
    if "ish" not in os.uname().release.lower() or os.geteuid() != 0:
        raise SystemExit("HOLD=Pogresno okruzenje")
    print("BATCH=IPHONE_ZIP_019R3; MODE=ISH_RETRY_SAFE_INTEGRATION_ACCEPTANCE; DELETION=NOT_PERFORMED", flush=True)
    raw, _ = read_stable(MANIFEST, 4 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise SystemExit("HOLD=Manifest SHA256")
    manifest = json.loads(raw)
    rows = manifest.get("records")
    if manifest.get("batch") != "IPHONE_ZIP_018R1" or not isinstance(rows, list) or len(rows) != 443:
        raise SystemExit("HOLD=Manifest struktura")

    dispositions = Counter(); folders = Counter(); bytes_by_role = Counter()
    seen_sha = set(); seen_view = set(); holds = []
    for number, row in enumerate(rows, 1):
        sha = row.get("sha256", ""); size = int(row.get("bytes", -1))
        vault = row.get("vault_path", ""); view = row.get("view_path", "")
        disp = row.get("disposition", "")
        if len(sha) != 64 or sha in seen_sha or view in seen_view:
            raise SystemExit("HOLD=Duplikat ili SHA zapis")
        seen_sha.add(sha); seen_view.add(view)
        if disp not in ALLOWED:
            raise SystemExit("HOLD=Nepoznata dispozicija")
        if not vault.startswith(ROOT + "/PRONADJENI_DIJELOVI_888/IPHONE_ZIP_016_PRESERVATION/OBJECTS/"):
            raise SystemExit("HOLD=Vault putanja")
        if not view.startswith(VIEW + "/"):
            raise SystemExit("HOLD=View putanja")
        rel = os.path.relpath(view, VIEW)
        top = rel.split(os.sep, 1)[0]
        if top not in ALLOWED[disp]:
            raise SystemExit("HOLD=Ruta ne odgovara dispoziciji")
        vb, vs = read_stable(vault, size)
        wb, ws = read_stable(view, size)
        if len(vb) != size or len(wb) != size or vb != wb or hashlib.sha256(vb).hexdigest() != sha:
            raise SystemExit("HOLD=Sadrzaj ili SHA se ne podudara")
        # iSH fake filesystem exposes the same device+inode for linked paths,
        # but may report st_nlink=1. Do not apply a native-Linux link-count gate.
        if (vs.st_dev, vs.st_ino) != (ws.st_dev, ws.st_ino):
            raise SystemExit("HOLD=iSH alias identity nije potvrdjen")
        dispositions[disp] += 1; folders[top] += 1; bytes_by_role[disp] += size
        if disp != "INTEGRATED_VIEW":
            holds.append({"sha256": sha, "bytes": size, "disposition": disp,
                          "detected_format": row.get("detected_format"), "view_path": view,
                          "review_status": "HUMAN_REVIEW_REQUIRED"})
        if number % 50 == 0:
            print("PROVJERENO=%d/443" % number, flush=True)

    expected = {"INTEGRATED_VIEW":366, "HOLD_SENSITIVE_PATTERN":11, "HOLD_RUNTIME_OR_BINARY":66}
    if dict(dispositions) != expected or len(holds) != 77:
        raise SystemExit("HOLD=Brojevi dispozicija")
    report = {
        "batch":"IPHONE_ZIP_019R3", "created_utc":datetime.now(timezone.utc).isoformat(),
        "input_manifest":MANIFEST, "input_manifest_sha256":MANIFEST_SHA,
        "records_verified":443, "unique_objects_verified":443,
        "byte_equal_pairs_verified":443, "ish_same_device_inode_pairs_verified":443,
        "native_link_count_gate":"NOT_APPLICABLE_ON_ISH_FAKE_FILESYSTEM",
        "transient_path_retry_policy":"5_ATTEMPTS_BOUNDED_FAIL_CLOSED",
        "disposition_counts":dict(sorted(dispositions.items())),
        "view_folder_counts":dict(sorted(folders.items())),
        "disposition_bytes":dict(sorted(bytes_by_role.items())),
        "integrated_records_accepted":366, "hold_records":77, "hold_items":holds,
        "active_runtime_modified":False, "source_archives_modified":False,
        "source_deletion":"NOT_PERFORMED", "retirement_authorized":False,
        "role_acceptance":"PASS_PARTIAL_WITH_77_HOLDS", "goal_status":"INCOMPLETE"
    }
    encoded = (json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    os.makedirs(RESULTS, mode=0o700, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="IPHONE_ZIP_019_ACCEPTANCE_", suffix=".json", dir=RESULTS)
    os.close(fd); atomic(path, encoded)
    report_sha = hashlib.sha256(encoded).hexdigest()
    if os.path.lexists(UPLOAD):
        raise SystemExit("HOLD=ZA_CHAT_019_UPLOAD.zip vec postoji")
    with zipfile.ZipFile(UPLOAD, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(os.path.basename(path), encoded)
    upload_raw, _ = read_stable(UPLOAD, 4 * 1024 * 1024)
    print("INTEGRATED_ACCEPTED=366")
    print("HOLD_FOR_HUMAN_REVIEW=77")
    print("ISH_SAME_DEVICE_INODE_PAIRS_VERIFIED=443")
    print("NATIVE_LINK_COUNT_GATE=NOT_APPLICABLE_ON_ISH_FAKE_FILESYSTEM")
    print("TRANSIENT_PATH_RETRY_POLICY=5_ATTEMPTS_BOUNDED_FAIL_CLOSED")
    print("REPORT=" + path)
    print("REPORT_SHA256=" + report_sha)
    print("UPLOAD_FILE=" + UPLOAD)
    print("UPLOAD_BYTES=" + str(len(upload_raw)))
    print("UPLOAD_SHA256=" + hashlib.sha256(upload_raw).hexdigest())
    print("DELETION=NOT_PERFORMED; RETIREMENT_AUTHORIZED=NO; GOAL_STATUS=INCOMPLETE")

if __name__ == "__main__":
    main()
