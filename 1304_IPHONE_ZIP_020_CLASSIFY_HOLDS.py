#!/usr/bin/env python3
import os
import io
import json
import stat
import time
import hashlib
import zipfile
import tempfile
from collections import Counter
from datetime import datetime, timezone

INPUT = "/root/ZA_CHAT_019_UPLOAD.zip"
INPUT_SHA = "64db0f7e1e6d795059206452f410019b56517a4cfe3fb1e31f94bfe1a262bcd5"
REPORT_SHA = "79fea166e9d60254d2ffeb99832635a5a7cb875c41fe5a8ba7aa59200e84b212"
RESULTS = "/root/FREYA_RAD_888/REZULTATI"
UPLOAD = "/root/ZA_CHAT_020_UPLOAD.zip"

TERMINFO_NAMES = {
    "sun", "dumb", "putty-256color", "st-256color", "screen", "xterm-256color",
    "vte-256color", "st-direct", "rxvt-256color", "vt100", "rxvt", "vt102",
    "putty", "gnome-256color", "xterm-xfree86", "gnome", "st-16color", "ansi",
    "vt220", "screen-256color", "terminology", "vte", "xterm", "konsole-linux",
    "kitty", "terminator", "tmux", "vt52", "konsole", "xterm-color",
    "alacritty", "konsole-256color"
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
            return data
        except FileNotFoundError as exc:
            last = exc
            if attempt < 4: time.sleep(0.25 * (attempt + 1))
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

def load_report():
    raw = read_stable(INPUT, 4 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA:
        raise RuntimeError("INPUT_ZIP_SHA256")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.infolist()) != 1:
            raise RuntimeError("INPUT_ZIP_STRUCTURE")
        report_raw = z.read(z.infolist()[0])
    if hashlib.sha256(report_raw).hexdigest() != REPORT_SHA:
        raise RuntimeError("INPUT_REPORT_SHA256")
    report = json.loads(report_raw)
    if report.get("batch") != "IPHONE_ZIP_019R3" or report.get("hold_records") != 77:
        raise RuntimeError("INPUT_REPORT_ROLE")
    return report

def sensitive_class(name):
    n = name.lower()
    if "_key" in n and "config" not in n:
        return "SECRET_PRIVATE_KEY_MATERIAL"
    if "history" in n:
        return "SENSITIVE_SHELL_HISTORY"
    if n in {"ssh_config.txt", "sshd_config.txt", "openssl.cnf.dist.txt", "screenrc.txt"}:
        return "SECURITY_CONFIGURATION_REFERENCE"
    if n == "services.txt":
        return "SYSTEM_SERVICE_CATALOG_REFERENCE"
    return "SENSITIVE_TEXT_MANUAL_HOLD"

def binary_class(name, data):
    stem = os.path.splitext(name)[0].lower()
    if stem in TERMINFO_NAMES or data[:2] in (b"\x1a\x01", b"\x1e\x02"):
        return "COMPILED_TERMINFO_REFERENCE"
    if "cpython" in stem or ".cpyth" in stem or "python" in stem:
        return "HISTORICAL_PYTHON_BYTECODE_REFERENCE"
    return "HISTORICAL_OPAQUE_BINARY_MANUAL_HOLD"

def main():
    if "ish" not in os.uname().release.lower() or os.geteuid() != 0:
        raise SystemExit("HOLD=Pogresno okruzenje")
    print("BATCH=IPHONE_ZIP_020; MODE=NON_EXECUTING_HOLD_CLASSIFICATION; DELETION=NOT_PERFORMED", flush=True)
    report = load_report(); rows = report["hold_items"]
    if len(rows) != 77 or len({x["sha256"] for x in rows}) != 77:
        raise SystemExit("HOLD=Hold zapis struktura")
    classes = Counter(); class_bytes = Counter(); output = []
    for number, row in enumerate(rows, 1):
        path = row["view_path"]; size = int(row["bytes"]); expected = row["sha256"]
        data = read_stable(path, size)
        if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit("HOLD=Objekat SHA256 ili velicina")
        name = os.path.basename(path)
        if row["disposition"] == "HOLD_SENSITIVE_PATTERN":
            classification = sensitive_class(name)
            handling = "PRESERVE_ISOLATED_NEVER_EXPOSE_VALUES"
        elif row["disposition"] == "HOLD_RUNTIME_OR_BINARY":
            classification = binary_class(name, data)
            handling = "PRESERVE_NON_EXECUTABLE_REFERENCE_ONLY"
        else:
            raise SystemExit("HOLD=Nepoznata dispozicija")
        classes[classification] += 1; class_bytes[classification] += size
        output.append({"sha256":expected,"bytes":size,"classification":classification,
                       "handling":handling,"view_path":path,"content_recorded":False,
                       "execution_performed":False})
        if number % 10 == 0: print("KLASIFIKOVANO=%d/77" % number, flush=True)
    result = {
        "batch":"IPHONE_ZIP_020", "created_utc":datetime.now(timezone.utc).isoformat(),
        "input_zip_sha256":INPUT_SHA, "input_report_sha256":REPORT_SHA,
        "objects_verified":77, "classification_counts":dict(sorted(classes.items())),
        "classification_bytes":dict(sorted(class_bytes.items())), "records":output,
        "content_values_recorded":False, "execution_performed":False,
        "network_used":False, "active_runtime_modified":False,
        "role_acceptance":"PRESERVATION_ROLES_ASSIGNED_WITH_MANUAL_HOLDS",
        "source_deletion":"NOT_PERFORMED", "retirement_authorized":False,
        "goal_status":"INCOMPLETE"
    }
    encoded = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    os.makedirs(RESULTS, mode=0o700, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="IPHONE_ZIP_020_CLASSIFICATION_", suffix=".json", dir=RESULTS)
    os.close(fd); atomic(path, encoded)
    report_sha = hashlib.sha256(encoded).hexdigest()
    if os.path.lexists(UPLOAD): raise SystemExit("HOLD=ZA_CHAT_020_UPLOAD.zip vec postoji")
    with zipfile.ZipFile(UPLOAD, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(os.path.basename(path), encoded)
    upload_raw = read_stable(UPLOAD, 4 * 1024 * 1024)
    print("CLASSIFICATION_COUNTS=" + json.dumps(dict(sorted(classes.items()))))
    print("OBJECTS_VERIFIED=77")
    print("SECRET_VALUES_RECORDED=NO")
    print("EXECUTION_PERFORMED=NO")
    print("REPORT=" + path)
    print("REPORT_SHA256=" + report_sha)
    print("UPLOAD_FILE=" + UPLOAD)
    print("UPLOAD_BYTES=" + str(len(upload_raw)))
    print("UPLOAD_SHA256=" + hashlib.sha256(upload_raw).hexdigest())
    print("DELETION=NOT_PERFORMED; RETIREMENT_AUTHORIZED=NO; GOAL_STATUS=INCOMPLETE")

if __name__ == "__main__":
    main()
