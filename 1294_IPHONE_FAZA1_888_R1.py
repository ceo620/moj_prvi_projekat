#!/usr/bin/env python3
"""FREYA 888: bounded-memory archive verification, no project-code execution.

Run in iSH with Python 3.9+: python3 -u -I -S -B IPHONE_FAZA1_888_R1.py
Only this verifier's checkpoint and receipts are written, inside the existing
excluded scanner directory. Originals, scanner and database are not modified.
An interrupted source-stream pass must replay its prefix: hashlib state cannot
be portably serialized. Completed local-part hashes are reused only with the
same input fingerprints. Metadata continuity is not a substitute for a new hash.
"""
import ast
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import stat
import sys
import time
import uuid

ROOT = Path('/root/FREYA_IPHONE_ISH_NODE_888')
D = ROOT / '15_RUNTIME/SIGNAL_HARVESTER_V1'
SOURCE = Path('/mnt/ios_pretraga/FREYA_HOME_888/IPHONE_BACKUPS_888/'
              'IPHONE_CRITICAL_RECOVERY_BACKUP_005_888_20260909T124605Z_PID1020')
RESTORE = ROOT / 'PREGLED_I_POPRAVKA/Oporavak_009'
GROUPS = [('SOURCE', SOURCE / 'PAYLOAD'), ('LOCAL', RESTORE / 'VERIFIED_PARTS')]
NAMES = ['PART_a' + c for c in 'abcdefghijklmno']
MANIFEST_SHA = '81262d3d3bcc7b0d0065200e12fc96ea19ebdc1b77758c5c6dd5019809cc9366'
STREAM_SHA = '7a630df2b2fd95e21cb43a6c096b1c30c1066b2983ac71feb89a6bd23b9d0f91'
TOTAL = 3846471680
PART_SIZE = 268435456
LAST_PART_SIZE = 88375296
CHUNK = 1024 * 1024
SMALL_LIMIT = 8 * 1024 * 1024
OWNER = 'FREYA_ARCHIVE_VERIFY_888_V1'
STATE_PATH = D / 'ARCHIVE_VERIFY_888_STATE.json'
CURRENT = None
STATE = None
LOCK = None
RUN_ID = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]


class Hold(Exception):
    pass


def require(ok, message):
    if not ok:
        raise Hold(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def say(key, value):
    print(key + '=' + (value if isinstance(value, str) else json.dumps(value, ensure_ascii=True)), flush=True)


def fingerprint(p):
    s = os.lstat(str(p))
    require(stat.S_ISREG(s.st_mode), 'NOT_REGULAR_OR_SYMLINK:' + str(p))
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def fd_fingerprint(fd):
    s = os.fstat(fd)
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def open_checked(p, expected):
    fd = os.open(str(p), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        require(fd_fingerprint(fd) == expected, 'SOURCE_CHANGED_AT_OPEN:' + str(p))
        return os.fdopen(fd, 'rb')
    except BaseException:
        os.close(fd)
        raise


def small(p):
    before = fingerprint(p)
    require(before[2] <= SMALL_LIMIT, 'CONTROL_FILE_TOO_LARGE:' + str(p))
    with open_checked(p, before) as f:
        data = f.read(SMALL_LIMIT + 1)
        require(fd_fingerprint(f.fileno()) == before, 'CONTROL_CHANGED:' + str(p))
    require(len(data) == before[2] and fingerprint(p) == before, 'CONTROL_CHANGED:' + str(p))
    return data, before


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_json(p, value, previous_bytes=None):
    # Replace only a checkpoint that this run has read and validated.
    if p.exists() or p.is_symlink():
        require(previous_bytes is not None, 'OUTPUT_EXISTS:' + str(p))
        old, _ = small(p)
        require(old == previous_bytes, 'CHECKPOINT_CHANGED_EXTERNALLY')
    else:
        require(previous_bytes is None, 'CHECKPOINT_DISAPPEARED')
    data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode()
    tmp = p.with_name(p.name + '.tmp_' + uuid.uuid4().hex)
    with tmp.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    # R1: verify the destination again immediately before commit, then make
    # the directory entry durable and read it back. A successful rename alone
    # does not establish that a usable checkpoint was persisted.
    if previous_bytes is not None:
        check, _ = small(p)
        require(check == previous_bytes, 'CHECKPOINT_CHANGED_BEFORE_RENAME')
    else:
        require(not os.path.lexists(str(p)), 'OUTPUT_APPEARED_BEFORE_RENAME')
    directory_fd = os.open(str(p.parent), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        ds = os.fstat(directory_fd)
        os.replace(str(tmp), str(p))
        os.fsync(directory_fd)
        now = os.stat(str(p.parent))
        require((now.st_dev, now.st_ino) == (ds.st_dev, ds.st_ino), 'OUTPUT_DIRECTORY_REPLACED')
        readback, _ = small(p)
        require(readback == data, 'OUTPUT_READBACK_MISMATCH:' + str(p))
    finally:
        os.close(directory_fd)
    return data


def save_state():
    global CURRENT
    STATE['updated_utc'] = utc()
    try:
        CURRENT = atomic_json(STATE_PATH, STATE, CURRENT)
    except Exception:
        # Preserve any confirmed hashes without repairing or bypassing a
        # missing/conflicting checkpoint. This is evidence for explicit recovery.
        rescue = D / ('ARCHIVE_VERIFY_888_RECOVERY_' + RUN_ID + '_' + uuid.uuid4().hex[:8] + '.json')
        try:
            data = (json.dumps(STATE, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode()
            with rescue.open('xb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            directory_fd = os.open(str(D), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            readback, _ = small(rescue)
            require(readback == data, 'RECOVERY_RECEIPT_READBACK_MISMATCH')
            say('RECOVERY_RECEIPT', str(rescue))
            say('RECOVERY_RECEIPT_SHA256', digest(readback))
            say('RECOVERY_VERIFIED_PARTS', len(STATE.get('parts', {})))
        except Exception as rescue_error:
            say('RECOVERY_RECEIPT_ERROR', type(rescue_error).__name__ + ':' + str(rescue_error))
        raise


def discover_controls():
    wanted = {'PARTS.sha256', 'TAR_STREAM.sha256', 'FINAL_SEAL.env'}
    found = {name: [] for name in wanted}
    seen = set()
    directory_count = 0
    for base in (SOURCE, RESTORE):
        require(base.is_dir(), 'MISSING_DIRECTORY:' + str(base))
        pending = [(base, 0)]
        while pending:
            directory, depth = pending.pop()
            require(not directory.is_symlink(), 'CONTROL_DIRECTORY_SYMLINK:' + str(directory))
            if str(directory) in seen:
                continue
            seen.add(str(directory))
            directory_count += 1
            require(directory_count <= 96, 'CONTROL_DISCOVERY_DIRECTORY_LIMIT')
            with os.scandir(str(directory)) as entries:
                for i, entry in enumerate(entries):
                    require(i < 512, 'CONTROL_DISCOVERY_ENTRY_LIMIT:' + str(directory))
                    if entry.name in wanted:
                        require(entry.is_file(follow_symlinks=False), 'CONTROL_NOT_REGULAR:' + entry.path)
                        found[entry.name].append(Path(entry.path))
                    elif (depth < 2 and entry.name not in {'RECOVERED', 'VERIFIED_PARTS', 'PAYLOAD'}
                          and entry.is_dir(follow_symlinks=False)):
                        pending.append((Path(entry.path), depth + 1))
        # PAYLOAD is a known flat segment directory; inspect control names only.
        for leaf in ('PAYLOAD', 'VERIFIED_PARTS'):
            for name in wanted:
                p = base / leaf / name
                if p.exists() and p not in found[name]:
                    found[name].append(p)
    return found


def parse_manifest(data):
    result = {}
    for line in data.decode('utf-8-sig').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.fullmatch(r'([0-9a-fA-F]{64})[ \t]+\*?(.+)', line)
        require(m is not None, 'MANIFEST_LINE_FORMAT_UNRECOGNIZED')
        name = m.group(2).replace('\\', '/').rsplit('/', 1)[-1]
        require(name in NAMES and name not in result, 'MANIFEST_MEMBER_SET_OR_DUPLICATE')
        result[name] = m.group(1).lower()
    require(set(result) == set(NAMES), 'MANIFEST_NOT_EXACTLY_15_PARTS')
    return result


def scanner_preflight(data, expected):
    text = data.decode('utf-8')
    tree = ast.parse(text, filename=str(D / 'harvest.py'))
    definitions = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ARCHIVE_PARTS' for t in node.targets):
            definitions.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == 'ARCHIVE_PARTS':
            definitions.append(node.value)
    require(len(definitions) == 1, 'ARCHIVE_PARTS_MUST_HAVE_ONE_LITERAL_DEFINITION')
    routes = ast.literal_eval(definitions[0])
    require(isinstance(routes, dict) and routes == expected, 'SCANNER_MAP_DIFFERS_FROM_VERIFIED_MANIFEST')
    fragments = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test_names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
        body = ast.Module(body=node.body, type_ignores=[])
        literals = {n.value for n in ast.walk(body) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        if 'ARCHIVE_PARTS' in test_names and 'HOLD:ARCHIVE_PART_REQUIRES_VERIFICATION' in literals:
            fragment = '\n'.join(text.splitlines()[node.lineno - 1:min(node.body[-1].end_lineno, node.lineno + 24)])
            fragments.append(fragment)
    require(bool(fragments), 'ARCHIVE_ROUTING_BRANCH_NOT_FOUND')
    lock_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == 'flock']
    require(bool(lock_calls), 'SCANNER_FLOCK_PROTOCOL_NOT_CONFIRMED')
    return {'syntax': 'PASS_AST_PARSE', 'map': 'PASS_30_EXACT_PATHS_AND_HASHES',
            'routing': 'BRANCH_PRESENT_STATIC_ONLY', 'runtime_test': 'NOT_EXECUTED',
            'branch_fragments': fragments, 'scanner_sha256': digest(data)}


def database_snapshot(expected):
    dbpath = D / 'STATE.db'
    fingerprint(dbpath)
    db = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True, timeout=5)
    deadline = time.monotonic() + 60
    db.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        schemas = {}
        totals = {}
        rows = {}
        for table in ('queue', 'files', 'findings'):
            schemas[table] = [list(r) for r in db.execute('PRAGMA table_info(' + table + ')')]
            columns = {r[1] for r in schemas[table]}
            require({'path', 'status'}.issubset(columns) if table != 'findings' else {'path', 'sha', 'report'}.issubset(columns),
                    'DATABASE_SCHEMA_UNEXPECTED:' + table)
            if table in ('queue', 'files'):
                totals[table] = [list(r) for r in db.execute('SELECT status,COUNT(*) FROM ' + table + ' GROUP BY status')]
                selected = []
                for path in sorted(expected):
                    cols = 'path,status,sha' if table == 'files' else 'path,status'
                    selected.extend([list(r) for r in db.execute('SELECT ' + cols + ' FROM ' + table + ' WHERE path=?', (path,))])
                rows[table] = selected
            else:
                totals[table] = db.execute('SELECT COUNT(*) FROM findings').fetchone()[0]
        return {'schemas': schemas, 'status_counts': totals, 'archive_rows': rows,
                'writes': 'NONE', 'snapshot_utc': utc()}
    finally:
        db.close()


def recovery_references(obj, path='$', depth=0):
    require(depth <= 32, 'RESTORE_REPORT_NESTING_LIMIT')
    hits = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            hits.extend(recovery_references(value, path + '.' + str(key), depth + 1))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            hits.extend(recovery_references(value, path + '[' + str(i) + ']', depth + 1))
    elif isinstance(obj, str):
        for label, token in (('STREAM_SHA', STREAM_SHA), ('PARTS_MANIFEST_SHA', MANIFEST_SHA),
                             ('BACKUP_SOURCE_PATH', str(SOURCE)), ('RECOVERED_PATH', str(RESTORE / 'RECOVERED'))):
            if token in obj:
                hits.append({'json_field': path, 'reference': label})
    elif obj == 54453:
        hits.append({'json_field': path, 'reference': 'REPORTED_RECOVERED_COUNT_54453'})
    return hits


def stream_part(p, fp, expected_sha, combined=None, group=''):
    require(fingerprint(p) == fp, 'SOURCE_CHANGED_BEFORE_HASH:' + str(p))
    h = hashlib.sha256()
    done = 0
    last = time.monotonic()
    with open_checked(p, fp) as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            done += len(block)
            require(done <= fp[2], 'SOURCE_GREW:' + str(p))
            h.update(block)
            if combined is not None:
                combined.update(block)
            if time.monotonic() - last >= 10:
                say('PROGRESS', {'set': group, 'part': p.name, 'bytes': done, 'of': fp[2]})
                last = time.monotonic()
        require(fd_fingerprint(f.fileno()) == fp, 'SOURCE_CHANGED_DURING_HASH:' + str(p))
    require(done == fp[2] and fingerprint(p) == fp, 'SOURCE_CHANGED_AFTER_HASH:' + str(p))
    observed = h.hexdigest()
    require(observed == expected_sha, 'PART_HASH_MISMATCH:' + str(p) + ':observed=' + observed)
    return {'sha256': observed, 'bytes': done, 'fingerprint': fp, 'verified_utc': utc(),
            'method': 'FULL_STREAM_SHA256'}


def verify_group(group, directory, expected, fingerprints, source=False):
    combined = hashlib.sha256() if source else None
    if source and STATE.get('source_stream', {}).get('sha256') == STREAM_SHA:
        require(all(STATE['parts'].get(str(directory / n), {}).get('sha256') == expected[str(directory / n)] for n in NAMES),
                'CHECKPOINT_STREAM_WITHOUT_ALL_PART_RECORDS')
        say('SOURCE_STREAM', 'REUSED_COMPLETED_EVIDENCE_WITH_UNCHANGED_FINGERPRINTS')
        return
    if source and any(str(directory / n) in STATE['parts'] for n in NAMES):
        say('RESUME', 'SOURCE_STREAM_REPLAY_REQUIRED_FOR_CORRECT_JOINED_SHA256')
    for i, name in enumerate(NAMES, 1):
        p = directory / name
        key = str(p)
        prior = STATE['parts'].get(key)
        if not source and prior:
            require(prior.get('sha256') == expected[key] and prior.get('fingerprint') == fingerprints[key],
                    'CHECKPOINT_PART_RECORD_MISMATCH:' + key)
            require(fingerprint(p) == fingerprints[key], 'CACHED_PART_CHANGED:' + key)
            say('PART_REUSED', group + ':' + name)
            continue
        say('HASHING', group + ':' + name + ':' + str(i) + '/15')
        STATE['parts'][key] = stream_part(p, fingerprints[key], expected[key], combined, group)
        STATE['last_completed'] = key
        save_state()
        say('PART_PASS', group + ':' + name + ':' + str(i) + '/15')
    if source:
        observed = combined.hexdigest()
        require(observed == STREAM_SHA, 'TAR_STREAM_HASH_MISMATCH:observed=' + observed)
        STATE['source_stream'] = {'sha256': observed, 'bytes': TOTAL, 'order': NAMES,
                                  'verified_utc': utc(), 'method': 'DIRECT_CONCATENATED_SOURCE_STREAM'}
        save_state()
        say('SOURCE_TAR_STREAM_SHA256', observed)


def interrupted(signum, frame):
    raise KeyboardInterrupt('signal=' + str(signum))


def main():
    global LOCK, STATE, CURRENT
    say('PROTOCOL', '888; HUMAN_GATE=ACTIVE; FAZA=1')
    say('MODE', 'VERIFY_30_PARTS_AND_JOINED_TAR_WITH_CHECKPOINT')
    say('NETWORK_EXTERNAL_SEND_INSTALL_PROJECT_EXECUTION', 'NONE')
    say('WRITES', 'OWN_CHECKPOINT_AND_RECEIPTS_ONLY')
    require(ROOT.is_dir() and D.is_dir() and not D.is_symlink(), 'IPHONE_SCANNER_DIRECTORY_MISSING_OR_LINKED')
    lockpath = D / 'LOCK'
    lockfp = fingerprint(lockpath)
    fd = os.open(str(lockpath), os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0))
    LOCK = os.fdopen(fd, 'r+b')
    require(fd_fingerprint(fd) == lockfp, 'LOCK_FILE_CHANGED')
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise Hold('SCANNER_OR_VERIFIER_BUSY')
    controls = {}
    expected = {}
    discovered = discover_controls()
    manifests = []
    stream_controls = []
    for name, paths in discovered.items():
        for p in sorted(paths):
            data, fp = small(p)
            sha = digest(data)
            controls[str(p)] = {'sha256': sha, 'fingerprint': fp}
            if name == 'PARTS.sha256':
                require(sha == MANIFEST_SHA, 'CONTROL_MANIFEST_HASH_MISMATCH:' + str(p))
                manifests.append(parse_manifest(data))
            elif name == 'TAR_STREAM.sha256':
                hashes = re.findall(r'(?i)(?<![a-f0-9])[a-f0-9]{64}(?![a-f0-9])', data.decode('utf-8-sig'))
                require(len(hashes) == 1 and hashes[0].lower() == STREAM_SHA, 'TAR_STREAM_CONTROL_MISMATCH:' + str(p))
                stream_controls.append(str(p))
    require(manifests and stream_controls, 'MISSING_PARTS_OR_STREAM_CONTROL_WITHIN_BOUNDED_LOCATIONS')
    require(all(m == manifests[0] for m in manifests), 'MANIFEST_COPIES_DISAGREE')
    fingerprints = {}
    for group, directory in GROUPS:
        require(directory.is_dir() and not directory.is_symlink(), 'PART_DIRECTORY_MISSING_OR_LINKED:' + str(directory))
        for name in NAMES:
            p = directory / name
            fp = fingerprint(p)
            size = LAST_PART_SIZE if name == 'PART_ao' else PART_SIZE
            require(fp[2] == size, 'PART_SIZE_MISMATCH:' + str(p))
            fingerprints[str(p)] = fp
            expected[str(p)] = manifests[0][name]
    scanner, scannerfp = small(D / 'harvest.py')
    controls[str(D / 'harvest.py')] = {'sha256': digest(scanner), 'fingerprint': scannerfp}
    routing = scanner_preflight(scanner, expected)
    say('SCANNER', {k: v for k, v in routing.items() if k != 'branch_fragments'})
    say('SCANNER_BRANCH_STATIC', routing['branch_fragments'])
    reportpath = RESTORE / 'RESTORE_REPORT.json'
    restorebytes, restorefp = small(reportpath)
    restoreobj = json.loads(restorebytes)
    controls[str(reportpath)] = {'sha256': digest(restorebytes), 'fingerprint': restorefp}
    recovery = {'report_path': str(reportpath), 'report_sha256': digest(restorebytes),
                'references': recovery_references(restoreobj),
                'current_recovered_content_validation': 'NOT_PERFORMED',
                'reuse_authorized_by_this_verifier': False}
    labels = {r['reference'] for r in recovery['references']}
    recovery['link'] = ('REPORT_REFERENCES_EXPECTED_ARCHIVE_HASH' if 'STREAM_SHA' in labels
                        else 'INCOMPLETE_REPORT_ARCHIVE_LINK')
    before = database_snapshot(expected)
    say('DATABASE_BEFORE', before['status_counts'])
    scriptbytes, _ = small(Path(__file__).absolute())
    binding = {'script_sha256': digest(scriptbytes), 'controls': controls,
               'part_fingerprints': fingerprints, 'expected_hashes': expected,
               'total_per_set': TOTAL, 'stream_sha256': STREAM_SHA}
    if STATE_PATH.exists() or STATE_PATH.is_symlink():
        CURRENT, _ = small(STATE_PATH)
        STATE = json.loads(CURRENT)
        require(STATE.get('owner') == OWNER and STATE.get('binding') == binding, 'CHECKPOINT_INPUT_BINDING_CHANGED')
        require(isinstance(STATE.get('parts'), dict) and set(STATE['parts']).issubset(expected), 'CHECKPOINT_PART_SET_INVALID')
        for path, entry in STATE['parts'].items():
            require(entry.get('sha256') == expected[path] and entry.get('fingerprint') == fingerprints[path]
                    and entry.get('bytes') == fingerprints[path][2], 'CHECKPOINT_RECORD_INVALID:' + path)
    else:
        STATE = {'owner': OWNER, 'created_utc': utc(), 'binding': binding, 'parts': {}}
        save_state()
    say('CHECKPOINT', str(STATE_PATH))
    say('CHECKPOINT_DURABILITY', 'DIRECTORY_FSYNC_AND_EXACT_READBACK_R1')
    say('PARTS_PREVIOUSLY_VERIFIED', len(STATE['parts']))
    verify_group('SOURCE', GROUPS[0][1], expected, fingerprints, source=True)
    verify_group('LOCAL', GROUPS[1][1], expected, fingerprints)
    require(len(STATE['parts']) == 30, 'INCOMPLETE_PART_HASH_SET')
    for path, fp in fingerprints.items():
        require(fingerprint(Path(path)) == fp, 'SOURCE_CHANGED_BEFORE_FINAL_RECEIPT:' + path)
        require(STATE['parts'][path]['sha256'] == expected[path], 'FINAL_PART_EVIDENCE_MISMATCH:' + path)
    for path, entry in controls.items():
        data, fp = small(Path(path))
        require(fp == entry['fingerprint'] and digest(data) == entry['sha256'], 'CONTROL_CHANGED_BEFORE_FINAL_RECEIPT:' + path)
    require(fd_fingerprint(LOCK.fileno())[:2] == fingerprint(lockpath)[:2], 'LOCK_REPLACED')
    after = database_snapshot(expected)
    require(after['status_counts'] == before['status_counts'] and after['archive_rows'] == before['archive_rows'],
            'DATABASE_STATUS_CHANGED_DURING_VERIFICATION')
    STATE['integrity_result'] = 'PASS_ARCHIVE_INTEGRITY_ONLY'
    STATE['local_stream'] = {'sha256': STREAM_SHA, 'bytes': TOTAL,
                             'method': 'DERIVED_FROM_15_ORDERED_PART_HASH_MATCHES_TO_DIRECTLY_VERIFIED_SOURCE'}
    save_state()
    receipt = {'owner': OWNER, 'run_id': RUN_ID, 'utc': utc(), 'phase': 1,
               'archive_integrity': 'PASS', 'verified_parts': 30,
               'source_stream': STATE['source_stream'], 'local_stream': STATE['local_stream'],
               'parts': STATE['parts'], 'controls': controls, 'scanner': routing,
               'recovery': recovery, 'database_before': before, 'database_after': after,
               'checkpoint': str(STATE_PATH), 'checkpoint_sha256': digest(CURRENT),
               'source_content_scanned': False, 'full_coverage': False,
               'changes': 'NEW_VERIFICATION_EVIDENCE_ONLY', 'database_changed': False,
               'backup': 'NOT_NEEDED_ORIGINALS_UNCHANGED',
               'remaining': ['Routing confirmed statically; scanner branch not executed.',
                             'Existing recovered members need content/provenance verification before reuse.',
                             'Existing database HOLD statuses retained pending supported routing reconciliation.',
                             'Document, nested archive, media and finding-context work remains.']}
    output = D / ('ARCHIVE_VERIFY_888_REPORT_' + RUN_ID + '.json')
    written = atomic_json(output, receipt)
    say('FAZA', '1:ARCHIVE_INTEGRITY_COMPLETE; CONTENT_AND_ROUTING_RECONCILIATION_PENDING')
    say('OBRADJENO', '30/30_SEGMENTS; SOURCE_JOINED_TAR_DIRECT_HASH; LOCAL_JOINED_TAR_DERIVED_IDENTITY')
    say('PREOSTALO', receipt['remaining'])
    say('HOLD_OVI', after['status_counts'])
    say('NALAZI', 'INTEGRITY_EVIDENCE_ONLY; NO_BUSINESS_FINDINGS_INFERRED')
    say('IZMJENE', 'CHECKPOINT_AND_RECEIPT; DB_AND_SCANNER_UNCHANGED')
    say('BACKUP', receipt['backup'])
    say('TEST', '30_PART_HASHES_PASS; SOURCE_STREAM_HASH_PASS; INPUT_CONTINUITY_PASS')
    say('DOKAZ', str(output))
    say('REPORT_SHA256', digest(written))
    say('RECOVERY_LINK', recovery)
    say('SLJEDECI_KORAK', 'RETURN_FULL_OUTPUT_FOR_ROUTING_RECONCILIATION_AND_PHASE_2')
    say('FULL_COVERAGE', False)
    say('BATCH_COMPLETE', True)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        main()
    except KeyboardInterrupt:
        say('RESULT', 'PAUSED_OR_INTERRUPTED')
        say('CHECKPOINT', str(STATE_PATH))
        say('NEXT', 'RUN_SAME_COMMAND; COMPLETED_LOCAL_PARTS_REUSED; INCOMPLETE_SOURCE_STREAM_REPLAYED')
        say('BATCH_COMPLETE', False)
        sys.exit(130)
    except Exception as exc:
        say('RESULT', 'HOLD')
        say('BLOCKER', type(exc).__name__ + ':' + str(exc))
        say('VERIFIED_CHECKPOINT_PARTS', len(STATE.get('parts', {})) if isinstance(STATE, dict) else 0)
        say('DB_CHANGED', False)
        say('NEXT', 'RETURN_FULL_OUTPUT; DO_NOT_DELETE_OR_EDIT_CHECKPOINT_TO_BYPASS_HOLD')
        say('BATCH_COMPLETE', False)
        sys.exit(2)
    finally:
        if LOCK is not None:
            LOCK.close()
