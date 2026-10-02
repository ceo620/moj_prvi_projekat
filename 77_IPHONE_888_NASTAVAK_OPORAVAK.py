#!/usr/bin/env python3
"""PROTOKOL 888, initial read batch 1; Python standard library, iSH only.

Continues batch 1 after SQLite disk I/O failure, preserving its original DB.
SQLite is used only in RAM after checkpoint import; optional rollback recovery
uses a separate audit copy. Source files are never changed. The only writes are exclusive audit/checkpoint
files below the sole authorised root. No source code is executed, archives are
not extracted, no packages/network/full-content hashing are used. Samples are
discovery hints only. This report cannot certify integration or functionality.
Rerunning resumes this batch, never starts a second batch or repeats batch 18.
"""
import os
import sys
import re
import stat
import json
import time
import sqlite3
import fcntl
import hashlib
import tempfile
from pathlib import Path
from collections import Counter

R = Path('/root')
C = R / 'FREYA_IPHONE_ISH_NODE_888'
OLD = R / 'FREYA_RAD_888/IPHONE_CANONICAL_888'
WORK = C / 'PREGLED_I_POPRAVKA' / 'STANJE_IZVORA'
VERSION = '20260927.1'
HEAD = 2048
START = time.monotonic()
LAST_PROGRESS = 0.0
SYSTEM = re.compile(r'freya|titan|human[_ -]?gate|protocol.{0,8}888|protokol.{0,8}888', re.I)
PATHS = re.compile(r'''(?<![\w:])/(?:root|home|mnt|media|etc|opt|srv|var|usr/local)(?:/[^\s\x00"'<>;,\)\]\}]+)+''')
STATUS = re.compile(r'(?m)^(RESULT|BATCH_COMPLETE|FINAL_STATUS|NEXT|PHASE|HOLD_REASON)\s*[=:]\s*([A-Z][A-Z0-9_./:-]{1,150})\s*$')
TOKENS = {
    'system_identity': r'freya|titan',
    'human_gate_rules': r'human[_ -]?gate|fail[_ -]?closed|default[_ -]?deny',
    'ssot_or_registry': r'\bssot\b|sha256|source_hash|registry|manifest',
    'business_or_models': r'capex|opex|ebitda|dscr|cash.?flow|investment|ars.metal|formula',
    'products_or_templates': r'template|render|reportlab|docx|openpyxl|document|proizvod',
    'execution_or_config': r'def |import |subprocess|exec |cron|sqlite|config|#!/',
}
TOKEN_RX = {k: re.compile(v, re.I) for k, v in TOKENS.items()}


def say(k, v):
    print(k + '=' + (json.dumps(v, ensure_ascii=True) if isinstance(v, (dict, list)) else str(v)), flush=True)


def hold(reason):
    say('RESULT', 'HOLD')
    say('HOLD_REASON', reason)
    say('SOURCE_MUTATION', 'NO')
    raise SystemExit(2)


def sig(s):
    return [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def small_read(p, n):
    """Do not follow symlinks or block on a FIFO after a concurrent replacement."""
    fd = os.open(str(p), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode):
            raise ValueError('NOT_REGULAR_FILE')
        data = os.read(fd, n)
        if sig(s) != sig(os.fstat(fd)):
            raise ValueError('CHANGED_DURING_SAMPLE')
        return data, s
    finally:
        os.close(fd)


def file_hint(b):
    if b.startswith((b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')): return 'ZIP_CONTAINER'
    if b.startswith(b'\x1f\x8b'): return 'GZIP_CONTAINER'
    if b.startswith(b'BZh'): return 'BZIP2_CONTAINER'
    if b.startswith(b'\xfd7zXZ\x00'): return 'XZ_CONTAINER'
    if b.startswith(b'7z\xbc\xaf\x27\x1c'): return 'SEVENZIP_CONTAINER'
    if b.startswith(b'Rar!'): return 'RAR_CONTAINER'
    if b[257:262] == b'ustar': return 'TAR_CONTAINER'
    if b.startswith(b'%PDF-'): return 'PDF'
    if b.startswith(b'SQLite format 3\x00'): return 'SQLITE_DATABASE'
    if b.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'): return 'OLE_DOCUMENT'
    if b.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a')): return 'IMAGE'
    if b.startswith(b'\x7fELF'): return 'ELF_EXECUTABLE'
    if len(b) > 12 and b[4:8] == b'ftyp': return 'MEDIA_CONTAINER'
    if not b: return 'EMPTY'
    if b.startswith((b'\xff\xfe', b'\xfe\xff')): return 'UTF16_TEXT'
    if b'\x00' in b: return 'BINARY_UNRESOLVED'
    try:
        t = b.decode('utf-8-sig')
    except UnicodeDecodeError:
        t = b.decode('utf-8-sig', 'replace')
        if t.count('\ufffd') > max(3, len(t) // 50): return 'BINARY_OR_ENCODING_UNRESOLVED'
    if t.startswith('#!'): return 'SCRIPT_TEXT'
    if re.search(r'(?m)^(?:from \w.* import |import \w|def \w|class \w)', t): return 'PYTHON_LIKE_TEXT'
    if t.lstrip().startswith(('{', '[')): return 'JSON_LIKE_TEXT'
    return 'TEXT'


def identity():
    u = os.uname()
    out = dict(sysname=u.sysname, host=u.nodename, release=u.release,
               machine=u.machine, euid=os.geteuid(), python=sys.version.split()[0])
    say('IDENTITY', out)
    if os.geteuid() != 0 or u.sysname != 'Linux' or 'ish' not in (u.release + ' ' + u.version).lower():
        hold('ISH_IDENTITY_NOT_CONFIRMED_NO_FILES_CHANGED')
    return out


def process_snapshot():
    result = {'processes': [], 'errors': [], 'possible_writers': [], 'fd_visibility': 0}
    ancestors = {os.getpid()}
    p = os.getppid()
    while p > 0 and p not in ancestors:
        ancestors.add(p)
        try:
            m = re.search(r'^PPid:\s*(\d+)', Path('/proc/%d/status' % p).read_text(), re.M)
            p = int(m.group(1)) if m else 0
        except OSError:
            break
    try:
        entries = list(Path('/proc').iterdir())
    except OSError as e:
        result['errors'].append(type(e).__name__)
        return result
    for entry in entries:
        if not entry.name.isdigit(): continue
        pid = int(entry.name)
        try:
            raw = (entry / 'cmdline').read_bytes()[:8192]
            args = [x.decode('utf-8', 'replace') for x in raw.split(b'\0') if x]
            program = Path(args[0]).name if args else (entry / 'comm').read_text().strip()
            try: cwd = os.readlink(str(entry / 'cwd'))
            except OSError: cwd = None
            related = bool(SYSTEM.search(' '.join(args))) or bool(cwd and str(cwd).startswith(str(C)))
            writes = []
            try:
                for fd in (entry / 'fd').iterdir():
                    try:
                        dest = os.readlink(str(fd))
                        info = (entry / 'fdinfo' / fd.name).read_text()
                        m = re.search(r'^flags:\s*([0-7]+)', info, re.M)
                        if m and (int(m.group(1), 8) & 3) in (1, 2) and dest.startswith(str(R) + '/'):
                            writes.append(dest)
                        result['fd_visibility'] += 1
                    except OSError:
                        pass
            except OSError:
                pass
            interpreter = bool(re.match(r'^(python|pypy|perl|ruby|node|php)', program))
            shell_job = program in ('sh', 'ash', 'bash') and len(args) > 1
            mover = program in ('mv', 'cp', 'rsync', 'tar', 'unzip', 'dd', 'rm')
            reasons = []
            if pid not in ancestors:
                if writes: reasons.append('OPEN_WRITE_FD_IN_ROOT')
                if related and (interpreter or shell_job or mover): reasons.append('SYSTEM_JOB_RUNNING')
                elif interpreter or mover or shell_job: reasons.append('POSSIBLE_JOB_REVIEW')
            row = dict(pid=pid, program=program, related=related, ancestor=pid in ancestors,
                       write_paths=writes[:12], reasons=reasons)
            result['processes'].append(row)
            if reasons: result['possible_writers'].append(row)
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as e:
            result['errors'].append({'pid': pid, 'error': type(e).__name__})
    return result


def real_dir(p):
    """Create only audit directories; reject any existing symlink component."""
    chain = []
    q = p
    while q != R:
        chain.append(q)
        if q == q.parent: raise ValueError('AUDIT_PATH_OUTSIDE_ROOT')
        q = q.parent
    if not stat.S_ISDIR(R.lstat().st_mode): raise ValueError('ROOT_NOT_REAL_DIRECTORY')
    for q in reversed(chain):
        try: s = q.lstat()
        except FileNotFoundError:
            q.mkdir(mode=0o700)
            s = q.lstat()
        if not stat.S_ISDIR(s.st_mode): raise ValueError('AUDIT_DIRECTORY_COLLISION:' + str(q))


SCHEMA = '''
create table meta(key text primary key, value text);
create table dirs(path text primary key, done integer default 0, signature text);
create table files(path text primary key, signature text, kind text, flags text,
 refs text, status text, sample_bytes integer, observed text, error text);
create table links(path text primary key, target text);
create table errors(path text, phase text, error text);
create table members(manifest text, hash text, object_path text, object_present integer,
 object_bytes integer, primary key(manifest,hash,object_path));
create table manifests(path text primary key, signature text, offset integer default 0,
 lines integer default 0, matched integer default 0, done integer default 0);
create index member_hash_lookup on members(hash);
'''
TABLES = ('meta', 'dirs', 'files', 'links', 'errors', 'members', 'manifests')
FLAT_NAME = 'nastavak_oporavljen.jsonl'
MAX_FRAME = 8 * 1024 * 1024


def frame(seq, operations):
    body = json.dumps({'sequence': seq, 'operations': operations},
                      ensure_ascii=True, separators=(',', ':')).encode('ascii')
    if len(body) > MAX_FRAME - 100:
        raise ValueError('CHECKPOINT_TRANSACTION_TOO_LARGE')
    return hashlib.sha256(body).hexdigest().encode('ascii') + b' ' + body + b'\n'


def memory_db():
    db = sqlite3.connect(':memory:')
    db.execute('pragma page_size=4096')
    db.execute('pragma max_page_count=12288')  # 48 MiB ceiling for the metadata database.
    db.execute('pragma temp_store=MEMORY')
    db.executescript(SCHEMA)
    return db


def regular_fd(p, flags):
    fd = os.open(str(p), flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError('CHECKPOINT_NOT_REGULAR:' + str(p))
    return fd


def space_probe():
    v = os.statvfs(str(WORK))
    free = v.f_bavail * v.f_frsize
    say('AUDIT_STORAGE', {'free_bytes': free, 'free_inodes_reported': v.f_favail})
    if free < 8 * 1024 * 1024:
        raise OSError('INSUFFICIENT_FREE_SPACE_FOR_CHECKPOINT_MINIMUM_8_MIB')
    fd, name = tempfile.mkstemp(prefix='.provjera_upisa_', dir=str(WORK))
    token = os.urandom(128)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(token); f.flush(); os.fsync(f.fileno())
        if small_read(Path(name), 129)[0] != token:
            raise OSError('PLAIN_FILE_WRITE_READ_MISMATCH')
        say('PLAIN_FILE_WRITE_FSYNC_READ', 'PASS')
    finally:
        # Only this invocation's disposable write-test file is removed.
        os.unlink(name)


def copy_tables(source, target):
    tag = source.execute("select value from meta where key='version'").fetchone()
    if not tag or tag[0] != VERSION:
        raise ValueError('OLD_CHECKPOINT_VERSION_MISMATCH')
    for table in TABLES:
        cursor = source.execute('select * from ' + table + ' order by rowid')
        while True:
            rows = cursor.fetchmany(128)
            if not rows: break
            sql = 'insert into ' + table + ' values (' + ','.join('?' for _ in rows[0]) + ')'
            target.executemany(sql, rows)
    target.commit()


def import_old_checkpoint():
    """Original DB/journal are never opened for writing or repaired in place."""
    old = WORK / 'nastavak.sqlite3'
    if not old.exists() or not stat.S_ISREG(old.lstat().st_mode):
        raise ValueError('PREVIOUS_CHECKPOINT_MISSING_OR_NOT_REGULAR_NO_NEW_SCAN')
    target = memory_db()
    source = None
    try:
        source = sqlite3.connect('file:' + str(old) + '?mode=ro', uri=True, timeout=1)
        source.execute('pragma query_only=ON')
        copy_tables(source, target)
        say('PREVIOUS_CHECKPOINT_READ', 'READ_ONLY_PASS')
        return target
    except (sqlite3.Error, OSError) as e:
        target.close()
        say('READ_ONLY_CHECKPOINT_ERROR', type(e).__name__ + ':' + str(e))
    finally:
        if source is not None: source.close()
    # A hot rollback journal may require recovery. Preserve the original and
    # ask SQLite to recover a byte-for-byte audit copy, using Unix dotfile locks.
    sources = []
    for suffix in ('', '-journal', '-wal', '-shm'):
        p = Path(str(old) + suffix)
        if os.path.lexists(str(p)):
            s = p.lstat()
            if not stat.S_ISREG(s.st_mode): raise ValueError('SQLITE_SIDECAR_NOT_REGULAR')
            sources.append((p, sig(s)))
    required = sum(s[3] for _, s in sources) * 2 + 8 * 1024 * 1024
    v = os.statvfs(str(WORK))
    if required > v.f_bavail * v.f_frsize:
        raise OSError('INSUFFICIENT_SPACE_FOR_PRESERVED_CHECKPOINT_RECOVERY_COPY')
    recovery = Path(tempfile.mkdtemp(prefix='oporavak_baze_', dir=str(WORK)))
    for p, expected in sources:
        fd = regular_fd(p, os.O_RDONLY)
        with os.fdopen(fd, 'rb') as src, (recovery / p.name).open('xb') as dst:
            while True:
                b = src.read(65536)
                if not b: break
                dst.write(b)
            dst.flush(); os.fsync(dst.fileno())
            if sig(os.fstat(src.fileno())) != expected:
                raise ValueError('CHECKPOINT_CHANGED_DURING_COPY_NO_SCAN')
    for p, expected in sources:
        if sig(p.lstat()) != expected: raise ValueError('CHECKPOINT_CHANGED_NO_SCAN')
    say('SQLITE_RECOVERY_COPY', str(recovery))
    copy = recovery / old.name
    repaired = None
    target = memory_db()
    try:
        repaired = sqlite3.connect('file:' + str(copy) + '?mode=rw&vfs=unix-dotfile', uri=True, timeout=1)
        repaired.execute('pragma synchronous=OFF')
        check = repaired.execute('pragma quick_check').fetchone()
        if check != ('ok',): raise ValueError('RECOVERY_COPY_INTEGRITY:' + str(check))
        copy_tables(repaired, target)
        say('SQLITE_RECOVERY_COPY_RESULT', 'READABLE_ORIGINAL_PRESERVED')
        return target
    except Exception:
        target.close()
        raise
    finally:
        if repaired is not None: repaired.close()


def load_flat(path):
    db = memory_db()
    sequence, last_good, tail = 0, 0, None
    fd = regular_fd(path, os.O_RDONLY)
    try:
        with os.fdopen(fd, 'rb') as f:
            while True:
                line = f.readline(MAX_FRAME + 1)
                if not line: break
                if len(line) > MAX_FRAME: raise ValueError('CHECKPOINT_FRAME_LIMIT')
                if not line.endswith(b'\n'):
                    tail = line
                    if f.read(1): raise ValueError('CHECKPOINT_INVALID_INTERIOR_FRAME')
                    break
                checksum, body = line[:-1].split(b' ', 1)
                if hashlib.sha256(body).hexdigest().encode('ascii') != checksum:
                    raise ValueError('CHECKPOINT_CHECKSUM_MISMATCH_NO_TRUNCATION')
                record = json.loads(body)
                if record['sequence'] != sequence + 1:
                    raise ValueError('CHECKPOINT_SEQUENCE_MISMATCH')
                for sql, params in record['operations']:
                    if sql.strip().split()[0].lower() not in ('insert', 'update', 'create'):
                        raise ValueError('UNEXPECTED_CHECKPOINT_STATEMENT')
                    db.execute(sql, params)
                db.commit()
                sequence += 1
                last_good = f.tell()
        if tail is not None:
            # Save the incomplete audit tail before removing only its partial bytes.
            backup_fd, backup_name = tempfile.mkstemp(prefix='prekinuti_zapis_', suffix='.bin', dir=str(WORK))
            with os.fdopen(backup_fd, 'wb') as saved:
                saved.write(tail); saved.flush(); os.fsync(saved.fileno())
            fd = regular_fd(path, os.O_WRONLY)
            try:
                os.ftruncate(fd, last_good); os.fsync(fd)
            finally: os.close(fd)
            say('PARTIAL_AUDIT_TAIL_PRESERVED', {'bytes': len(tail), 'path': backup_name})
        tag = db.execute("select value from meta where key='version'").fetchone()
        if not tag or tag[0] != VERSION: raise ValueError('FLAT_CHECKPOINT_VERSION_MISMATCH')
        return db, sequence
    except Exception:
        db.close()
        raise


def publish_seed(db, path):
    fd, name = tempfile.mkstemp(prefix='.prenos_nastavka_', dir=str(WORK))
    sequence = 0
    try:
        with os.fdopen(fd, 'wb') as f:
            for table in TABLES:
                cursor = db.execute('select * from ' + table + ' order by rowid')
                while True:
                    rows = cursor.fetchmany(128)
                    if not rows: break
                    sql = 'insert into ' + table + ' values (' + ','.join('?' for _ in rows[0]) + ')'
                    sequence += 1
                    f.write(frame(sequence, [[sql, list(row)] for row in rows]))
            f.flush(); os.fsync(f.fileno())
        os.link(name, str(path))
    finally:
        os.unlink(name)
    return sequence


class DurableMemoryDB:
    """SQLite queries run in RAM; persistence uses ordinary append/fsync only."""
    def __init__(self, db, path, sequence):
        self.db, self.path, self.sequence = db, path, sequence
        self.pending = []
        self.poisoned = False

    def execute(self, sql, params=()):
        cursor = self.db.execute(sql, params)
        if sql.strip().split()[0].lower() in ('insert', 'update', 'create'):
            self.pending.append([sql, list(params)])
        return cursor

    def commit(self):
        if self.poisoned: raise OSError('CHECKPOINT_APPEND_FAILED_DO_NOT_APPEND_AGAIN')
        if self.pending:
            try:
                packet = frame(self.sequence + 1, self.pending)
                fd = regular_fd(self.path, os.O_WRONLY | os.O_APPEND)
                with os.fdopen(fd, 'ab') as f:
                    f.write(packet); f.flush(); os.fsync(f.fileno())
                self.db.commit()
                self.sequence += 1
                self.pending.clear()
            except BaseException:
                self.poisoned = True
                raise
        else: self.db.commit()

    def close(self):
        self.db.close()


def connect():
    space_probe()
    path = WORK / FLAT_NAME
    if os.path.lexists(str(path)):
        db, sequence = load_flat(path)
        say('CHECKPOINT_BACKEND', 'RESUMED_FLAT_FILE_SQLITE_QUERIES_IN_RAM')
    else:
        db = import_old_checkpoint()
        files = db.execute('select count(*) from files').fetchone()[0]
        if files == 0:
            db.close()
            raise ValueError('NO_SAVED_FILE_OBSERVATIONS_RECOVERED_NO_FULL_RESCAN')
        sequence = publish_seed(db, path)
        say('CHECKPOINT_BACKEND', 'RECOVERED_TO_FLAT_FILE_SQLITE_QUERIES_IN_RAM')
    say('RECOVERED_CHECKPOINT', {
        'files': db.execute('select count(*) from files').fetchone()[0],
        'directories_done': db.execute('select count(*) from dirs where done=1').fetchone()[0],
        'directories_pending': db.execute('select count(*) from dirs where done=0').fetchone()[0],
        'source_rescan_from_beginning': False,
        'original_sqlite_checkpoint_preserved': True,
        'metadata_database_memory_limit_bytes': 48 * 1024 * 1024})
    return DurableMemoryDB(db, path, sequence)



def progress(db, phase, force=False):
    global LAST_PROGRESS
    now = time.monotonic()
    if force or now - LAST_PROGRESS >= 5:
        db.commit()
        say('PROGRESS', {'phase': phase,
            'files': db.execute('select count(*) from files').fetchone()[0],
            'directories_done': db.execute('select count(*) from dirs where done=1').fetchone()[0],
            'directories_pending': db.execute('select count(*) from dirs where done=0').fetchone()[0],
            'seconds_this_run': round(now - START, 1)})
        LAST_PROGRESS = now


def error(db, p, phase, e):
    db.execute('insert into errors values (?,?,?)', (str(p), phase, type(e).__name__ + ':' + str(e)[:240]))


def sample(db, p, before):
    signature = json.dumps(sig(before))
    row = db.execute('select signature from files where path=?', (str(p),)).fetchone()
    if row and row[0] == signature: return
    hint, flags, refs, statuses, amount, err = 'UNREAD', [], [], [], 0, None
    try:
        b, actual = small_read(p, HEAD)
        if sig(actual) != sig(before): raise ValueError('FILE_CHANGED_BEFORE_SAMPLE')
        hint = file_hint(b)
        amount = len(b)
        if 'TEXT' in hint:
            t = b.decode('utf-16' if hint == 'UTF16_TEXT' else 'utf-8-sig', 'replace')
            flags = [k for k, rx in TOKEN_RX.items() if rx.search(t)]
            refs = sorted(set(PATHS.findall(t)))[:48]
            # Never interpret status words embedded in executable source as receipts.
            if hint not in ('SCRIPT_TEXT', 'PYTHON_LIKE_TEXT'):
                statuses = [list(x) for x in STATUS.findall(t)][:20]
        if sig(p.lstat()) != sig(actual): raise ValueError('PATH_CHANGED_DURING_SAMPLE')
    except (OSError, ValueError) as e:
        err = type(e).__name__ + ':' + str(e)[:160]
        error(db, p, 'SAMPLE', e)
    db.execute('insert or replace into files values (?,?,?,?,?,?,?,?,?)',
        (str(p), signature, hint, json.dumps(flags), json.dumps(refs), json.dumps(statuses),
         amount, str(time.time()), err))


def inventory(db):
    if db.execute("select value from meta where key='inventory_complete'").fetchone():
        say('INVENTORY', 'REUSING_COMPLETED_CHECKPOINT_NOT_A_NEW_SCAN')
        return
    # Only an interrupted directory is re-enumerated; unchanged samples are reused.
    # Completed directories stay at their recorded observation time. Batch 2/3 must
    # re-stat each selected input before a decision or write.
    while True:
        row = db.execute('select path from dirs where done=0 order by rowid limit 1').fetchone()
        if not row: break
        dp = Path(row[0])
        try:
            s = dp.lstat()
            if not stat.S_ISDIR(s.st_mode): raise ValueError('DIRECTORY_CHANGED_OR_SYMLINK')
            with os.scandir(str(dp)) as entries:
                for entry in entries:
                    p = dp / entry.name
                    if p == WORK: continue
                    try:
                        st = entry.stat(follow_symlinks=False)
                        if stat.S_ISDIR(st.st_mode):
                            db.execute('insert or ignore into dirs(path) values (?)', (str(p),))
                        elif stat.S_ISREG(st.st_mode): sample(db, p, st)
                        elif stat.S_ISLNK(st.st_mode):
                            db.execute('insert or replace into links values (?,?)', (str(p), os.readlink(str(p))))
                        else:
                            db.execute('insert or replace into files values (?,?,?,?,?,?,?,?,?)',
                              (str(p), json.dumps(sig(st)), 'SPECIAL_NOT_OPENED', '[]', '[]', '[]', 0, str(time.time()), None))
                    except OSError as e: error(db, p, 'ENTRY', e)
                    progress(db, 'ALL_DEPTH_METADATA_AND_SMALL_SAMPLES')
            end = dp.lstat()
            if (s.st_mtime_ns, s.st_ctime_ns) != (end.st_mtime_ns, end.st_ctime_ns):
                error(db, dp, 'DIRECTORY_DRIFT', ValueError('CHANGED_WHILE_ENUMERATING'))
            db.execute('update dirs set done=1,signature=? where path=?', (json.dumps(sig(end)), str(dp)))
        except OSError as e:
            error(db, dp, 'DIRECTORY', e)
            db.execute('update dirs set done=2 where path=?', (str(dp),))
        except ValueError as e:
            error(db, dp, 'DIRECTORY', e)
            db.execute('update dirs set done=2 where path=?', (str(dp),))
        db.commit()
    db.execute('insert or replace into meta values (?,?)', ('inventory_complete', str(time.time())))
    db.commit()


def reference_manifest(db, p, objectdir):
    """Stream the two known batch-18 manifests. Hashes remain UNVERIFIED claims."""
    if not p.exists(): return
    try:
        s = p.lstat()
        if not stat.S_ISREG(s.st_mode): raise ValueError('MANIFEST_NOT_REGULAR')
        signature = json.dumps(sig(s))
        old = db.execute('select signature,offset,lines,matched,done from manifests where path=?', (str(p),)).fetchone()
        if old and old[0] != signature:
            error(db, p, 'MANIFEST', ValueError('CHANGED_SINCE_CHECKPOINT_TARGETED_REVIEW_REQUIRED'))
            return
        if old and old[4]: return
        offset, lines, matched = old[1:4] if old else (0, 0, 0)
        fd = os.open(str(p), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as f:
            if sig(os.fstat(f.fileno())) != sig(s): raise ValueError('MANIFEST_CHANGED_BEFORE_OPEN')
            f.seek(offset)
            while True:
                raw = f.readline(262145)
                if not raw: break
                if len(raw) > 262144:
                    raise ValueError('OVERSIZED_RECORD_AT_BYTE_%d' % offset)
                lines += 1
                try:
                    q = json.loads(raw)
                    h, obj = str(q.get('sha256', '')).lower(), q.get('object')
                    if re.fullmatch('[0-9a-f]{64}', h) and isinstance(obj, str) and obj:
                        op = objectdir / Path(obj).name
                        try:
                            st = op.lstat()
                            present = int(stat.S_ISREG(st.st_mode))
                            size = st.st_size if present else None
                        except FileNotFoundError: present, size = 0, None
                        db.execute('insert or replace into members values (?,?,?,?,?)', (str(p), h, str(op), present, size))
                        matched += 1
                except (ValueError, TypeError, AttributeError) as e: error(db, p, 'MANIFEST_RECORD', e)
                offset = f.tell()
                db.execute('insert or replace into manifests values (?,?,?,?,?,?)',
                           (str(p), signature, offset, lines, matched, 0))
                progress(db, 'LINKING_EXISTING_MANIFEST_CLAIMS')
                if lines % 250 == 0: db.commit()
            if sig(os.fstat(f.fileno())) != sig(s): raise ValueError('MANIFEST_CHANGED_DURING_READ')
        db.execute('insert or replace into manifests values (?,?,?,?,?,?)',
                   (str(p), signature, offset, lines, matched, 1))
        db.commit()
    except (OSError, ValueError) as e:
        error(db, p, 'MANIFEST', e)
        db.commit()


def paths_state():
    paths = [C, R / 'FREYA_RAD_888', OLD, R / 'FREYA_GIANT_020_888',
             R / 'FREYA_DEEP_016_888', R / 'FREYA_RECOVERY_009_888_ugk9zsdm']
    out = []
    for p in paths:
        try:
            st = p.lstat()
            kind = 'directory' if stat.S_ISDIR(st.st_mode) else 'symlink' if stat.S_ISLNK(st.st_mode) else 'other'
            out.append({'path': str(p), 'exists': True, 'kind': kind})
        except FileNotFoundError: out.append({'path': str(p), 'exists': False})
    return out


def build_summary(db, ident, proc_start, proc_end, roots_before):
    branches = {}
    archive_examples, important, receipts, external = [], [], [], {}
    types, flags = Counter(), Counter()
    files = nbytes = sampled = partials = 0
    base_presence = Counter()
    for path, signature, kind, fl, refs, status_values, nb, observed, err in db.execute('select * from files order by path'):
        p, s = Path(path), json.loads(signature)
        files += 1
        if files % 200 == 0: progress(db, 'BUILDING_CURRENT_SOURCE_MAP')
        nbytes += s[3]
        sampled += nb
        types[kind] += 1
        f = json.loads(fl)
        flags.update(f)
        rel = p.relative_to(R)
        branch = '/'.join(rel.parts[:2]) if len(rel.parts) > 1 else '(files directly in /root)'
        b = branches.setdefault(branch, {'files': 0, 'bytes': 0, 'sample_hints': 0, 'containers': 0})
        b['files'] += 1; b['bytes'] += s[3]; b['sample_hints'] += int(bool(f))
        if kind.endswith('_CONTAINER') and kind != 'MEDIA_CONTAINER':
            b['containers'] += 1
            if len(archive_examples) < 16: archive_examples.append({'path': path, 'kind': kind, 'bytes': s[3]})
        if 'human_gate_rules' in f or 'ssot_or_registry' in f or 'business_or_models' in f:
            if len(important) < 16: important.append({'path': path, 'hints': f, 'kind': kind})
        if json.loads(status_values) and len(receipts) < 12:
            receipts.append({'path': path, 'status_words_only_not_proof': json.loads(status_values)})
        for ref in json.loads(refs):
            if not ref.startswith('/root/') and ref != '/root':
                key = (ref, path)
                if len(external) < 500: external[key] = {'path': ref, 'source': path, 'system_hint': bool(f), 'exists': os.path.lexists(ref)}
        if p.name.endswith('.tmp888'): partials += 1
        try: old_rel = p.relative_to(OLD)
        except ValueError: old_rel = None
        if old_rel is not None and stat.S_ISREG(s[2]):
            target = C / '01_CANONICAL_BASE' / old_rel
            try:
                t = target.lstat()
                status_name = 'same_size_unverified' if stat.S_ISREG(t.st_mode) and t.st_size == s[3] else 'different_or_not_regular'
            except FileNotFoundError: status_name = 'missing'
            base_presence[status_name] += 1
    linked = db.execute('select count(*),coalesce(sum(object_present),0) from members').fetchone()
    # No matching based on names/size is accepted as a hash or integration proof.
    new_presence = Counter()
    for path, in db.execute('select path from files where path like ?', (str(C) + '/%',)):
        m = re.search(r'__([0-9a-f]{12})(?:\.[^/]*)?$', Path(path).name)
        if m:
            prefix = m.group(1)
            matches = db.execute('select count(distinct hash) from members where hash>=? and hash<?', (prefix, prefix + 'g')).fetchone()[0]
            new_presence['single_prefix_claim_unverified' if matches == 1 else 'ambiguous_or_unmatched_name'] += 1
    vfs = os.statvfs(str(C))
    errors = db.execute('select count(*) from errors').fetchone()[0]
    incomplete = db.execute('select count(*) from dirs where done<>1').fetchone()[0]
    return {
        'protocol': 888, 'batch': 'IPHONE_888_STANJE_I_IZVORI', 'initial_read_batch': 1,
        'identity': ident, 'target': str(C), 'roots_before_audit': roots_before,
        'source_mutation': False, 'writes_only': str(WORK), 'network_used': False,
        'full_file_hashes_computed': 0, 'files_observed': files, 'file_bytes_observed': nbytes,
        'sample_bytes_read': sampled, 'file_types_from_samples': dict(types),
        'content_hints_not_final_classification': dict(flags), 'branches': branches,
        'archive_examples': archive_examples, 'priority_examples': important,
        'receipt_candidates_not_verified_completion': receipts,
        'batch18_completion': 'NOT_ESTABLISHED_FROM_AVAILABLE_EVIDENCE',
        'batch18_base_destination_presence_only': dict(base_presence),
        'batch18_new_destination_name_hints_only': dict(new_presence),
        'batch18_temporary_files_found': partials,
        'manifest_records_linked': linked[0], 'manifest_objects_present': linked[1],
        'manifest_hash_claims_verified': False,
        'symlinks_recorded_not_followed': db.execute('select count(*) from links').fetchone()[0],
        'external_reference_examples_for_targeted_review': list(external.values())[:20],
        'external_references_in_sample': len(external), 'free_bytes': vfs.f_bavail * vfs.f_frsize,
        'errors': errors, 'incomplete_directories': incomplete,
        'error_examples': list(db.execute('select path,phase,error from errors limit 12')),
        'process_start': proc_start, 'process_end': proc_end,
        'process_visibility_note': 'Snapshot only; fdinfo may be incomplete on iSH; no claim that all writers are excluded.',
        'coverage_note': 'All depths under /root, hidden entries included; symlink targets and archive members not traversed. 2048-byte samples do not prove absence of value. Observations retain their timestamps across resume; selected inputs require fresh stat before repair.',
        'systems_functionally_verified': 0, 'final_acceptance': 'NOT_EVALUATED',
        'next': 'BATCH_2_TARGETED_CONTENT_DEPENDENCIES_AND_CONCRETE_REPAIR_MAP_THEN_BATCH_3_REPAIR',
    }


def emit_summary(report):
    say('SUMMARY_BEGIN', 'IPHONE_888_STANJE_I_IZVORI')
    for key in ('initial_read_batch', 'target', 'roots_before_audit', 'files_observed', 'file_bytes_observed',
                'sample_bytes_read', 'full_file_hashes_computed', 'free_bytes', 'file_types_from_samples',
                'batch18_completion', 'batch18_base_destination_presence_only',
                'batch18_new_destination_name_hints_only', 'batch18_temporary_files_found',
                'manifest_records_linked', 'manifest_objects_present', 'errors', 'incomplete_directories'):
        say(key.upper(), report[key])
    branches = report['branches']
    # Small console output; the complete branch inventory stays in the report.
    selected = sorted(branches, key=lambda k: (-branches[k]['sample_hints'], -branches[k]['files'], k))[:24]
    for k in selected: say('BRANCH', dict(path='/root/' + k, **branches[k]))
    for key in ('archive_examples', 'priority_examples', 'receipt_candidates_not_verified_completion',
                'external_reference_examples_for_targeted_review', 'error_examples'):
        say(key.upper(), report[key])
    say('ACTIVE_PROCESS_REVIEW', report['process_end'])
    say('INTEGRATION_COMPLETE', 'NOT_ESTABLISHED')
    say('SOURCE_MUTATION', 'NO')
    say('REPORT', str(WORK / 'izvjestaj.json'))
    say('CHECKPOINT', str(WORK / FLAT_NAME))
    say('RESULT', 'READ_BATCH_1_COMPLETE_WITH_ITEMS_FOR_TARGETED_REVIEW')
    say('NEXT', report['next'])
    say('BATCH_COMPLETE', 'YES')
    say('SUMMARY_END', 'RETURN_SUMMARY_BEGIN_THROUGH_SUMMARY_END')


def publish_report(report):
    """Publish only complete JSON; a crash leaves at most an audit temporary file."""
    destination = WORK / 'izvjestaj.json'
    if destination.exists() or destination.is_symlink():
        current = json.loads(small_read(destination, 16 * 1024 * 1024)[0])
        if current.get('batch') != report['batch']: hold('REPORT_COLLISION')
        return
    fd, name = tempfile.mkstemp(prefix='.izvjestaj_', suffix='.tmp', dir=str(WORK))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=True, indent=2)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.link(name, str(destination))
    finally:
        os.unlink(name)


def main():
    os.umask(0o077)
    say('PROTOCOL', 888)
    say('BATCH', 'IPHONE_888_STANJE_I_IZVORI_CONTINUATION_REPAIR')
    say('INITIAL_READ_BATCH', '1_CONTINUED_NOT_A_NEW_READ_BATCH')
    say('HUMAN_GATE', 'ACTIVE')
    say('MODE', 'READ_SOURCES_WRITE_AUDIT_CHECKPOINT_ONLY')
    ident = identity()
    proc_start = process_snapshot()
    say('PROCESSES_BEFORE', proc_start)
    if not proc_start['processes']: hold('PROCESS_VISIBILITY_UNAVAILABLE_NO_FILES_CHANGED')
    blocking = [p for p in proc_start['possible_writers']
                if 'SYSTEM_JOB_RUNNING' in p['reasons'] or
                any(x.startswith(str(C) + '/') for x in p['write_paths'])]
    if blocking:
        hold('EXISTING_SYSTEM_JOB_OR_TARGET_WRITER_REVIEW_PIDS_ABOVE_NO_FILES_CHANGED')
    roots_before = paths_state()
    say('ROOTS_BEFORE', roots_before)
    try:
        real_dir(WORK)
        lockpath = WORK / 'zakljucavanje'
        if lockpath.exists() and not stat.S_ISREG(lockpath.lstat().st_mode): hold('LOCK_PATH_COLLISION')
        fd = os.open(str(lockpath), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except (OSError, ValueError) as e:
        hold('AUDIT_PATH:' + type(e).__name__ + ':' + str(e))
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: hold('THIS_BATCH_ALREADY_RUNNING')
    db = None
    try:
        db = connect()
        cached = db.execute("select value from meta where key='summary'").fetchone()
        if cached:
            report = json.loads(cached[0])
            publish_report(report)
            say('REUSED_COMPLETED_BATCH', 'YES_INVENTORY_IS_THE_SAVED_OBSERVATION')
            report['process_end'] = process_snapshot()
            emit_summary(report)
            return
        progress(db, 'START_OR_RESUME', True)
        inventory(db)
        reference_manifest(db, R / 'FREYA_GIANT_020_888/MEMBERS.jsonl', R / 'FREYA_GIANT_020_888/OBJECTS')
        reference_manifest(db, R / 'FREYA_DEEP_016_888/RUN_1789208009922981000_cff2f695/MEMBERS.jsonl', R / 'FREYA_DEEP_016_888/OBJECTS')
        progress(db, 'SUMMARISING', True)
        report = build_summary(db, ident, proc_start, process_snapshot(), roots_before)
        db.execute('insert or replace into meta values (?,?)', ('summary', json.dumps(report, ensure_ascii=True)))
        db.commit()
        publish_report(report)
        emit_summary(report)
    except KeyboardInterrupt:
        try:
            if db is not None: db.commit()
            say('RESULT', 'PAUSED_CHECKPOINT_SAVED')
        except (OSError, sqlite3.Error, ValueError) as e:
            say('RESULT', 'PAUSED_LAST_DURABLE_CHECKPOINT_RETAINED')
            say('CHECKPOINT_NOTE', str(e))
        say('NEXT', 'RUN_THE_SAME_COMMAND_TO_RESUME_THIS_BATCH')
    except (OSError, ValueError, sqlite3.Error) as e:
        if db is not None:
            try: db.commit()
            except sqlite3.Error: pass
        say('RESULT', 'HOLD_CHECKPOINT_RETAINED')
        say('HOLD_REASON', type(e).__name__ + ':' + str(e)[:300])
        raise SystemExit(2)
    finally:
        if db is not None: db.close()
        os.close(fd)


if __name__ == '__main__':
    main()
