import hashlib, json, os, signal, stat

SOURCE = (
    "/root/FREYA_SEGMENTS_014_d_20s9r2/PAYLOAD/DOCTRINE_PROJECT/DOCX/"
    "01649__5_default.tar.gz__storage__emulated__0__"
    "Titan_Full_Harvest_10_Godina__CMU__Doctrine__Diamond_Harvest__"
    "HELL_12_KERNEL_JEZGRA__002.__INVESTICIONI__PLAN__IRF__-ACTIVE__DATA.docx"
)
TARGET = "/root/ZA_PREGLED_IRF_ACTIVE_DATA_888.docx"
EXPECTED = "e28fc44013f1a834a4802447b3ff6cf3475c5040268bbf2fb2f890fa0227481b"
SIZE = 235166

def emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)

def timeout(signum, frame):
    raise TimeoutError("TIME_LIMIT")

def verified_read(path):
    if os.path.realpath(path) != path:
        raise ValueError("LINK_PATH")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size != SIZE:
            raise ValueError("TYPE_OR_SIZE")
        data = stream.read(SIZE + 1)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ):
        raise ValueError("FILE_CHANGED_DURING_READ")
    if len(data) != SIZE or hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError("CONTENT_SHA256")
    return data

def main():
    created = False
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(30)
    emit("HEADER", batch="IPHONE_R8_017_PREPARE_IRF_REVIEW_COPY_888",
         effect="CREATE_ONE_EXACT_REVIEW_COPY_IF_ABSENT", target=TARGET,
         max_seconds=30, source_writes=0, network_calls=0,
         project_execution=False)
    try:
        data = verified_read(SOURCE)
        if os.path.realpath(os.path.dirname(TARGET)) != os.path.dirname(TARGET):
            raise ValueError("TARGET_PARENT_LINK")
        try:
            fd = os.open(TARGET, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            verified_read(TARGET)
            action = "REUSED_IDENTICAL_COPY"
        else:
            created = True
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
            verified_read(TARGET)
            action = "CREATED_AND_READBACK_VERIFIED"
        emit("FINAL", result="PASS_REVIEW_COPY", action=action,
             path=TARGET, bytes=SIZE, sha256=EXPECTED,
             created_files=int(created), existing_files_overwritten=0,
             source_writes=0, content_review="NOT_PERFORMED",
             next="PRILOZI_OVAJ_DOCX_U_RAZGOVOR")
        return 0
    except (OSError, ValueError) as exc:
        emit("FINAL", result="HOLD_REVIEW_COPY_NOT_VERIFIED",
             reason=type(exc).__name__, detail=str(exc)[:240],
             target_created_this_run=created,
             automatically_removed=False, automatically_overwritten=False,
             next="VRATI_CIJELI_IZLAZ")
        return 2
    finally:
        signal.alarm(0)

if __name__ == "__main__":
    raise SystemExit(main())
