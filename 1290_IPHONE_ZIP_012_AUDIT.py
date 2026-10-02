#!/usr/bin/env python3
"""Protocol 888: bounded source-read-only ZIP audit; creates one new JSON report.
No extraction, deletion, imports of discovered code, network or package changes.
Run on iSH with python3 -I -S -B. Incomplete reads remain explicitly unresolved.
"""
import os, stat, json, hashlib, zipfile, struct, signal, time, tempfile
from datetime import datetime, timezone
from collections import Counter

ROOT = '/root/FREYA_RAD_888'
INVENTORY = ROOT + '/REZULTATI/IPHONE_ZIP_011_INVENTAR.json'
PIN = '8d773619b1dd20b9336f1f59108e4f55d5fcbdfe3ae4b58ba048de33a0edfba3'
MIB = 1024 * 1024

class Hold(Exception):
    pass

def utc():
    return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def safe_open(path):
    if not os.path.isabs(path) or os.path.normpath(path) != path:
        raise Hold('PATH_INVALID')
    current = '/'
    for part in path.strip('/').split('/'):
        current = os.path.join(current, part)
        s = os.lstat(current)
        if stat.S_ISLNK(s.st_mode) or os.path.ismount(current):
            raise Hold('SYMLINK_OR_MOUNT')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    f = os.fdopen(fd, 'rb')
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        f.close()
        raise Hold('NOT_REGULAR')
    return f

def timeout(signum, frame):
    raise Hold('ARCHIVE_TIME_LIMIT')

def central_guard(f, size):
    # Bound ZipFile's initial allocation before it parses the central directory.
    f.seek(max(0, size - 65557))
    tail = f.read(65557)
    pos = tail.rfind(b'PK\x05\x06')
    if pos < 0 or pos + 22 > len(tail):
        raise Hold('EOCD_NOT_FOUND_OR_UNSUPPORTED_LAYOUT')
    _, disk, cd_disk, on_disk, total, cd_size, offset, comment = struct.unpack(
        '<4s4H2IH', tail[pos:pos + 22])
    if pos + 22 + comment != len(tail):
        raise Hold('TRAILING_DATA_OR_AMBIGUOUS_EOCD')
    if disk or cd_disk or on_disk != total:
        raise Hold('MULTIVOLUME_UNSUPPORTED')
    if total == 65535 or cd_size == 0xffffffff or offset == 0xffffffff:
        raise Hold('ZIP64_REQUIRES_SEPARATE_AUDIT')
    if total > 50000 or cd_size > 16 * MIB:
        raise Hold('CENTRAL_DIRECTORY_LIMIT')
    f.seek(0)

def audit(candidate, budget, deadline):
    path = candidate['path']
    row = {'path': path, 'inventory_identity': candidate, 'members': [],
           'content_integration': 'NOT_VERIFIED', 'deletion': 'NOT_PERFORMED'}
    try:
        signal.alarm(45)
        with safe_open(path) as f:
            before = os.fstat(f.fileno())
            expected = (candidate['device'], candidate['inode'], candidate['bytes'],
                        candidate['mtime_ns'])
            if identity(before)[:4] != expected or before.st_nlink != candidate['hardlinks']:
                raise Hold('CHANGED_SINCE_INVENTORY')
            row['stat'] = {'mode': before.st_mode, 'uid': before.st_uid,
                'gid': before.st_gid, 'atime_ns': before.st_atime_ns,
                'ctime_ns': before.st_ctime_ns, 'hardlinks': before.st_nlink}
            central_guard(f, before.st_size)
            with zipfile.ZipFile(f) as z:
                infos = z.infolist()
                names = Counter(i.filename for i in infos)
                row.update(format='ZIP_CENTRAL_DIRECTORY_PARSED',
                    member_count=len(infos), declared_bytes=sum(i.file_size for i in infos),
                    duplicate_names=[n for n, count in names.items() if count > 1],
                    archive_comment_hex=z.comment.hex())
                archive_budget = 256 * MIB
                for number, i in enumerate(infos):
                    name = i.filename
                    mode = i.external_attr >> 16
                    item = {'id': number, 'name': name, 'bytes': i.file_size,
                        'compressed_bytes': i.compress_size, 'crc32': i.CRC,
                        'compression': i.compress_type, 'flags': i.flag_bits,
                        'date_time': list(i.date_time), 'external_attr': i.external_attr,
                        'internal_attr': i.internal_attr, 'create_system': i.create_system,
                        'extra_hex': i.extra.hex(), 'comment_hex': i.comment.hex(),
                        'unsafe_path': name.startswith('/') or '..' in name.split('/')
                            or '\\' in name or ':' in name or '\x00' in name,
                        'special_type': stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR),
                        'nested_zip_name': name.lower().endswith('.zip')}
                    row['members'].append(item)
                    if i.is_dir():
                        item['read_status'] = 'DIRECTORY_METADATA_ONLY'
                        continue
                    allowance = min(32 * MIB, archive_budget, budget[0])
                    if i.flag_bits & 1:
                        item['read_status'] = 'HOLD_ENCRYPTED'
                    elif i.file_size > allowance or time.monotonic() >= deadline:
                        item['read_status'] = 'HOLD_RESOURCE_LIMIT'
                    else:
                        h = hashlib.sha256()
                        read_bytes = 0
                        prefix = b''
                        try:
                            with z.open(i) as source:
                                while True:
                                    chunk = source.read(min(65536, allowance - read_bytes + 1))
                                    if not chunk:
                                        break
                                    budget[0] -= len(chunk)
                                    archive_budget -= len(chunk)
                                    read_bytes += len(chunk)
                                    if len(prefix) < 4:
                                        prefix = (prefix + chunk)[:4]
                                    if read_bytes > allowance:
                                        raise Hold('ACTUAL_OUTPUT_LIMIT')
                                    if time.monotonic() >= deadline:
                                        raise Hold('RUN_TIME_LIMIT')
                                    h.update(chunk)
                            if read_bytes != i.file_size:
                                raise Hold('MEMBER_SIZE_MISMATCH')
                            item.update(read_status='READ_CRC_VERIFIED', sha256=h.hexdigest(),
                                nested_zip_signature=prefix in (b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'))
                        except Exception as exc:
                            item['read_status'] = 'HOLD_' + (str(exc) if isinstance(exc, Hold) else type(exc).__name__)
                        item['bytes_read'] = read_bytes
                row['member_enumeration'] = 'COMPLETE'
            if before.st_size <= min(64 * MIB, budget[0]) and time.monotonic() < deadline:
                f.seek(0)
                h = hashlib.sha256()
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    budget[0] -= len(chunk)
                    h.update(chunk)
                    if time.monotonic() >= deadline:
                        raise Hold('RUN_TIME_LIMIT')
                row['archive_sha256'] = h.hexdigest()
            else:
                row['archive_hash_status'] = 'HOLD_RESOURCE_LIMIT'
            if identity(before) != identity(os.fstat(f.fileno())) or identity(before) != identity(os.lstat(path)):
                raise Hold('SOURCE_CHANGED_DURING_AUDIT')
            row['source_stability'] = 'PASS'
    except Exception as exc:
        row['hold'] = str(exc) if isinstance(exc, Hold) else type(exc).__name__
    finally:
        signal.alarm(0)
    return row

def main():
    if 'ish' not in os.uname().release.lower():
        raise SystemExit('HOLD=Pogresno okruzenje')
    signal.signal(signal.SIGALRM, timeout)
    with safe_open(INVENTORY) as f:
        data = f.read(2 * MIB + 1)
    if digest(data) != PIN:
        raise SystemExit('HOLD=Inventar SHA256')
    inventory = json.loads(data)
    candidates = inventory['candidates']
    if len(candidates) != 46 or len({c['path'] for c in candidates}) != 46:
        raise SystemExit('HOLD=Inventar struktura')
    print('BATCH=IPHONE_ZIP_012; SOURCE_MODE=READ_ONLY', flush=True)
    report = {'batch': 'IPHONE_ZIP_012', 'started_utc': utc(), 'inventory_sha256': PIN,
        'scope': inventory['scope'], 'excluded_subtrees': inventory['excluded_subtrees'],
        'limits': {'member_bytes': 32*MIB, 'archive_content_bytes': 256*MIB,
            'run_read_bytes': 512*MIB, 'content_seconds': 300, 'archive_seconds': 45},
        'archives': [], 'nested_archive_recursion': 'NOT_PERFORMED',
        'role_and_backup_acceptance': 'NOT_VERIFIED', 'deletion': 'NOT_PERFORMED',
        'zip_count': 'UNKNOWN', 'goal_status': 'INCOMPLETE'}
    budget = [512 * MIB]
    deadline = time.monotonic() + 300
    for n, candidate in enumerate(sorted(candidates, key=lambda c: c['bytes']), 1):
        row = audit(candidate, budget, deadline)
        report['archives'].append(row)
        done = sum(m.get('read_status') == 'READ_CRC_VERIFIED' for m in row['members'])
        print('NAPREDAK=%d/46 PROCITANO=%d STATUS=%s' %
              (n, done, row.get('hold', row.get('member_enumeration', 'PARTIAL'))), flush=True)
    report['finished_utc'] = utc()
    report['central_directories_parsed'] = sum(r.get('format') == 'ZIP_CENTRAL_DIRECTORY_PARSED' for r in report['archives'])
    report['fully_read_stable_archives'] = sum(r.get('source_stability') == 'PASS' and
        r.get('member_enumeration') == 'COMPLETE' and all(m.get('read_status') in
        ('READ_CRC_VERIFIED', 'DIRECTORY_METADATA_ONLY') for m in r['members']) for r in report['archives'])
    target = ROOT + '/REZULTATI'
    if os.path.realpath(target) != target or not os.path.isdir(target) or os.path.ismount(target):
        raise SystemExit('HOLD=Report direktorijum')
    raw = (json.dumps(report, ensure_ascii=True, indent=2) + '\n').encode()
    fd, path = tempfile.mkstemp(prefix='IPHONE_ZIP_012_AUDIT_', suffix='.json', dir=target)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    print('CENTRAL_DIRECTORIES_PARSED=' + str(report['central_directories_parsed']))
    print('FULLY_READ_STABLE_ARCHIVES=' + str(report['fully_read_stable_archives']))
    print('REPORT=' + path)
    print('REPORT_SHA256=' + digest(raw))
    print('INTEGRATION=NOT_VERIFIED; DELETION=NOT_PERFORMED; GOAL_STATUS=INCOMPLETE')

if __name__ == '__main__':
    main()
