"""Prepare one bounded review archive. Never run or modify source files."""
import csv
import hashlib
import io
import json
import os
import signal
import stat
import zipfile

BATCH = "IPHONE_R8_018_PREPARE_CAPEX_REVIEW_PACKET_888"
INDEX = "/root/FREYA_RAD_888/DIJAMANTI_POPIS.csv"
INDEX_SHA256 = "dd3521698da9b211812a040de638e2ba2db6a3cfa133417b73e219cdd7998a07"
INDEX_BYTES = 1400693
INDEX_ROWS = 3449
TARGET = "/root/ZA_PREGLED_CAPEX_I_KANON_888.zip"
# One-based DATA record numbers; the CSV header is not a record.
CSV_RECORDS = (4, 5, 6, 240, 241, 252, 253, 254, 256, 258, 259, 260,
               263, 264, 265, 266, 142, 155, 159, 164, 201, 205, 104,
               115, 120, 123, 124, 174, 175, 176, 177, 178, 179, 180,
               224, 225, 226, 231, 232, 233, 234, 108, 111, 112, 114,
               116, 121, 122)
SOURCE_ROOTS = (
    "/root/FREYA_SEGMENTS_014_d_20s9r2/PAYLOAD/DOCTRINE_PROJECT/",
    "/root/FREYA_RECOVERY_009_888_ugk9zsdm/RECOVERED/root/",
)
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024
MAX_PACKET = 10 * 1024 * 1024
MAX_SECONDS = 90
SCHEMA = ["vrsta", "ime", "bajtova", "kopija", "prljavstina",
          "u_ulazu", "najcistija_putanja"]


def emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def timeout(signum, frame):
    raise TimeoutError("TIME_LIMIT")


def parent_fd(path):
    """Open each directory component without following symbolic links."""
    if not path.startswith("/") or os.path.normpath(path) != path:
        raise ValueError("NON_CANONICAL_PATH")
    parts = path.split("/")[1:]
    if not parts or not parts[-1]:
        raise ValueError("EMPTY_FILE_NAME")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY |
                              os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd, parts[-1]
    except BaseException:
        os.close(fd)
        raise


def signature(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def read_regular(path, limit, exact_size=None):
    directory, name = parent_fd(path)
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        with os.fdopen(fd, "rb") as f:
            before = os.fstat(f.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("NOT_REGULAR_FILE")
            if before.st_size > limit:
                raise ValueError("FILE_BYTE_LIMIT")
            if exact_size is not None and before.st_size != exact_size:
                raise ValueError("SIZE_DIFFERS_FROM_REVIEWED_INDEX")
            data = f.read(limit + 1)
            after = os.fstat(f.fileno())
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if signature(before) != signature(after) or signature(after) != signature(current):
                raise ValueError("SOURCE_CHANGED_DURING_READ")
        if len(data) != before.st_size or len(data) > limit:
            raise ValueError("READ_SIZE_MISMATCH")
        return data
    finally:
        os.close(directory)


def put(z, name, data):
    # Fixed ZIP metadata permits exact, repeatable reuse. It is not an event date.
    item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    item.compress_type = zipfile.ZIP_STORED
    item.external_attr = 0o100600 << 16
    z.writestr(item, data)


def collect(rows):
    records, members, hashes = [], {}, {}
    used = 0
    for number in CSV_RECORDS:
        row = rows[number - 1]
        path = row["najcistija_putanja"]
        entry = dict(index_record=number, source_path=path,
                     indexed_name=row["ime"], indexed_bytes=row["bajtova"])
        try:
            if not path.startswith(SOURCE_ROOTS):
                raise ValueError("OUTSIDE_SELECTED_SOURCE_ROOTS")
            ext = os.path.splitext(path)[1].lower()
            if ext not in (".pdf", ".xlsx", ".docx", ".csv"):
                raise ValueError("SOURCE_TYPE_NOT_SELECTED")
            size = int(row["bajtova"])
            if size < 0 or size > MAX_FILE or used + size + 1 > MAX_TOTAL:
                raise ValueError("SOURCE_BYTE_BUDGET")
            # Count every attempted read against the budget, including failures.
            used += size + 1
            data = read_regular(path, size, size)
            sha = digest(data)
            if sha in hashes:
                name = hashes[sha]
                status = "IDENTICAL_BYTES_SHARED_MEMBER"
            else:
                name = "SOURCES/R%04d_%s%s" % (number, sha[:12], ext)
                hashes[sha] = name
                members[name] = data
                status = "COPIED_FOR_REVIEW"
            entry.update(status=status, bytes=len(data), sha256=sha,
                         archive_member=name, authority="NOT_ESTABLISHED")
        except (OSError, ValueError) as exc:
            if isinstance(exc, TimeoutError):
                raise
            entry.update(status="NOT_COPIED", reason=type(exc).__name__,
                         errno=getattr(exc, "errno", None), detail=str(exc)[:240])
        records.append(entry)
    return records, members, used


def packet_bytes(records, members):
    manifest = dict(batch=BATCH, role="REVIEW_COPY_NOT_CANON",
                    inventory_sha256=INDEX_SHA256,
                    selected_index_records=list(CSV_RECORDS),
                    source_contents_parsed=False, approval="NOT_ESTABLISHED",
                    originals_written=False, archive_timestamp_is_event_time=False,
                    records=records)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", allowZip64=False) as z:
        put(z, "MANIFEST.json", json.dumps(manifest, ensure_ascii=False,
                                         indent=2, sort_keys=True).encode("utf-8"))
        for name, data in members.items():
            put(z, name, data)
    data = out.getvalue()
    if len(data) > MAX_PACKET:
        raise ValueError("PACKET_BYTE_LIMIT")
    return data


def main():
    created = False
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(MAX_SECONDS)
    emit("HEADER", batch=BATCH, effect="CREATE_ONE_REVIEW_ZIP_IF_ABSENT",
         selected_paths=len(CSV_RECORDS), max_seconds=MAX_SECONDS,
         max_source_bytes=MAX_TOTAL, target=TARGET,
         source_writes=0, network_calls=0, project_execution=False)
    try:
        index = read_regular(INDEX, INDEX_BYTES, INDEX_BYTES)
        if digest(index) != INDEX_SHA256:
            raise ValueError("INVENTORY_SHA256_CHANGED")
        reader = csv.DictReader(io.StringIO(index.decode("utf-8-sig")))
        rows = list(reader)
        if reader.fieldnames != SCHEMA or len(rows) != INDEX_ROWS:
            raise ValueError("INVENTORY_SCHEMA_OR_COUNT")
        records, members, used = collect(rows)
        missing = [r for r in records if r["status"] == "NOT_COPIED"]
        for r in missing:
            emit("SOURCE_NOT_COPIED", **r)
        if not members:
            raise ValueError("NO_SOURCES_AVAILABLE")
        data = packet_bytes(records, members)
        directory, name = parent_fd(TARGET)
        try:
            try:
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600, dir_fd=directory)
            except FileExistsError:
                action = "REUSED_IDENTICAL_PACKET"
            else:
                created = True
                with os.fdopen(fd, "wb") as f:
                    if f.write(data) != len(data):
                        raise OSError("SHORT_WRITE")
                action = "CREATED_AND_READBACK_VERIFIED"
        finally:
            os.close(directory)
        saved = read_regular(TARGET, MAX_PACKET, len(data))
        if saved != data:
            raise ValueError("EXISTING_OR_WRITTEN_PACKET_DIFFERS")
        emit("FINAL", result="PASS_REVIEW_PACKET" if not missing else
             "PARTIAL_REVIEW_PACKET", action=action, path=TARGET,
             bytes=len(saved), sha256=digest(saved), selected_paths=len(records),
             copied_paths=len(records) - len(missing), unique_contents=len(members),
             identical_copies_grouped=len(records) - len(missing) - len(members),
             not_copied=len(missing), source_read_budget_used=used,
             created_files=int(created), existing_files_overwritten=0,
             source_writes=0, network_calls=0, project_starts=0,
             content_review="NOT_PERFORMED", canonical_activation=False,
             next="PRILOZI_ZIP_I_VRATI_CIJELI_IZLAZ")
        return 0
    except (OSError, ValueError, csv.Error, zipfile.BadZipFile) as exc:
        emit("FINAL", result="HOLD_PACKET_NOT_VERIFIED",
             reason=type(exc).__name__, detail=str(exc)[:240],
             target_created_this_run=created, automatically_removed=False,
             existing_files_overwritten=0, source_writes=0,
             next="VRATI_CIJELI_IZLAZ_NE_KORISTI_NEPROVJEREN_PAKET")
        return 2
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    raise SystemExit(main())
