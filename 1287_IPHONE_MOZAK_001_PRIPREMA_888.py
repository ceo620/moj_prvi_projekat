#!/usr/bin/env python3
"""Prepare one local review packet from the existing iSH signal workflow.
Only new folders/files are written. No network, source execution or scheduling.
Delivery and the meaning of '24 signale' remain unresolved.
"""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import signal
import stat
import zipfile

ROOT = Path('/root/FREYA_RAD_888')
DEST = Path('/root/mozak uzivo iphone')
REPORT_REL = 'AI_SVAKODNEVNI_888/SESIJE/RAD__867esa3/REZULTAT.json'
ASUS = r'C:\Users\ceo\OneDrive\Desktop\mozak uzivo iphone'
MAX_READ = 64 * 1024 * 1024
MAX_PACKET = 32 * 1024 * 1024
USED = 0
CREATED = []
PACKET = None
IDENTITY = {
    'protocol': '888', 'version': 1,
    'engine_sha256': '01cd6ee9c07d76f2b974b655791c4bcb8426e128bdb29ca221cfcce502064525',
    'document_sha256': '8236c31e63747752248df5c70c13e7d3786dd53336387bb115a63fef5cc8f64d',
    'validator_sha256': '97a77c63383646e81e56e2b5712714778dee6e4e9235b0d71e92cd1431a67db1'
}

def emit(event, **data):
    print(json.dumps(dict(event=event, **data), ensure_ascii=True), flush=True)

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')

def open_dir(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'DIRECTORY_PATH')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for name in path.parts[1:]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise

def read(path, cap=1024 * 1024):
    global USED
    path = Path(path)
    fd = open_dir(path.parent)
    try:
        child = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    finally:
        os.close(fd)
    with os.fdopen(child, 'rb') as f:
        a = os.fstat(f.fileno())
        need(stat.S_ISREG(a.st_mode) and a.st_size <= cap, 'FILE_TYPE_OR_SIZE')
        need(USED + a.st_size + 1 <= MAX_READ, 'READ_BUDGET')
        data = f.read(a.st_size + 1)
        USED += len(data)
        b = os.fstat(f.fileno())
    need(len(data) == a.st_size and
         (a.st_size, a.st_mtime_ns, a.st_ctime_ns) ==
         (b.st_size, b.st_mtime_ns, b.st_ctime_ns), 'FILE_CHANGED_DURING_READ')
    return data

def entries(path, cap):
    fd = open_dir(path)
    os.close(fd)
    with os.scandir(path) as scan:
        items = []
        for item in scan:
            need(len(items) < cap, 'DIRECTORY_LIMIT')
            items.append(item)
    return sorted(items, key=lambda item: item.name)

def prepare_snapshot(root):
    files = {}
    report_bytes = read(root / REPORT_REL)
    report = json.loads(report_bytes)
    need(isinstance(report, dict), 'REPORT_OBJECT')
    rows = report.get('rows')
    need(isinstance(rows, list) and 0 < len(rows) <= 50, 'REPORT_ROWS')
    wanted = set()
    for row in rows:
        need(isinstance(row, dict), 'ROW_OBJECT')
        h = row.get('source_sha256')
        need(isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h), 'SOURCE_HASH')
        need(isinstance(row.get('findings'), list) and 0 < len(row['findings']) <= 20,
             'FINDINGS_SCHEMA')
        wanted.add(h)
    need(len(wanted) == len(rows), 'DUPLICATE_SOURCE_IN_REPORT')
    sources = {}
    current_hashes = set()
    for item in entries(root / 'ULAZ', 50):
        if not item.is_file(follow_symlinks=False):
            continue
        ext = Path(item.name).suffix.lower()
        if ext not in ('.csv', '.xlsx', '.docx'):
            continue
        data = read(item.path, 8 * 1024 * 1024)
        h = digest(data)
        current_hashes.add(h)
        if h in wanted:
            key = 'IZVORI/' + h + ext
            files[key] = data
            sources.setdefault(h, []).append({'path': item.path, 'member': key})
    need(wanted <= set(sources), 'SAVED_REPORT_SOURCE_MISSING_OR_CHANGED')
    evidence = {}
    for rel in ('AI_SADRZAJ_01', 'AI_SADRZAJ_01R1', 'AI_SVAKODNEVNI_888/JOBS'):
        for item in entries(root / rel, 64):
            if not item.is_dir(follow_symlinks=False):
                continue
            folder = Path(item.path)
            for name in ('AI_NALAZI.json', 'AI.json'):
                path = folder / name
                if not os.path.lexists(path):
                    continue
                answer_bytes = read(path)
                answer = json.loads(answer_bytes)
                need(isinstance(answer, dict), 'ANSWER_OBJECT')
                h = answer.get('source_sha256')
                if h not in wanted:
                    continue
                row = next(r for r in rows if r['source_sha256'] == h)
                if answer.get('findings') != row['findings']:
                    continue
                excerpt_bytes = read(folder / 'EXCERPT.json')
                excerpt = json.loads(excerpt_bytes)
                need(isinstance(excerpt, dict), 'EXCERPT_OBJECT')
                records = excerpt.get('records')
                need(isinstance(records, list) and len(records) <= 2000, 'EXCERPT_SCHEMA')
                refs = {}
                for rec in records:
                    need(isinstance(rec, dict) and isinstance(rec.get('ref'), str)
                         and isinstance(rec.get('text'), str), 'EXCERPT_RECORD')
                    need(rec['ref'] not in refs, 'DUPLICATE_EXCERPT_REF')
                    refs[rec['ref']] = rec['text']
                for finding in row['findings']:
                    need(isinstance(finding, dict), 'FINDING_OBJECT')
                    ref, quote = finding.get('ref'), finding.get('quote')
                    need(isinstance(ref, str) and isinstance(quote, str)
                         and quote and ref in refs and quote in refs[ref], 'QUOTE_MISMATCH')
                key = 'DOKAZI/' + h + '/' + digest(answer_bytes)[:16] + '/'
                files[key + name] = answer_bytes
                files[key + 'EXCERPT.json'] = excerpt_bytes
                evidence.setdefault(h, []).append({
                    'path': str(folder), 'member_prefix': key,
                    'partial': excerpt.get('partial'),
                    'quotes_match_saved_excerpt': True})
    need(wanted <= set(evidence), 'SAVED_EVIDENCE_NOT_BOUND_TO_REPORT')
    files['POSTOJECI_IZVJESTAJ.json'] = report_bytes
    binding = [{
        'source_sha256': row['source_sha256'],
        'sources': sources[row['source_sha256']],
        'evidence': evidence[row['source_sha256']],
        'findings_count': len(row['findings'])
    } for row in rows]
    return files, binding, len(current_hashes - wanted)

def transport_observation():
    result = {'tools': {n: shutil.which(n) for n in ('ssh', 'scp', 'sftp', 'rsync')},
              'ssh_config': '/root/.ssh/config', 'asus_host_blocks': [],
              'scope': 'STATIC_DECLARATIONS_ONLY_NOT_EFFECTIVE_SSH_CONFIG',
              'connection_tested': False}
    path = Path(result['ssh_config'])
    if not os.path.lexists(path):
        result['config_status'] = 'MISSING'
        return result
    try:
        content = read(path, 32768).decode('utf-8-sig')
        block = None
        directives = set()
        for line in content.splitlines():
            words = shlex.split(line, comments=True)
            if not words:
                continue
            key = words[0].lower()
            if key in ('include', 'match'):
                directives.add(key)
                block = None
            if key == 'host':
                aliases = [v for v in words[1:] if re.fullmatch('[a-zA-Z0-9_.-]{1,100}', v)
                           and 'asus' in v.lower()]
                block = {'aliases': aliases} if aliases else None
                if block is not None:
                    need(len(result['asus_host_blocks']) < 16, 'SSH_BLOCK_LIMIT')
                    result['asus_host_blocks'].append(block)
            elif block is not None and key in ('hostname', 'user', 'port') and len(words) == 2:
                if re.fullmatch('[a-zA-Z0-9_.:@%\\-]{1,200}', words[1]):
                    block[key] = words[1]
        result['config_status'] = 'READ_WITHOUT_EXECUTION'
        result['include_or_match_present'] = sorted(directives)
    except (OSError, ValueError) as exc:
        result['config_status'] = type(exc).__name__
    return result

def mkdir_child(parent_fd, name, path):
    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        CREATED.append(str(path))
    except FileExistsError:
        pass
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)

def write_new(parent_fd, name, data):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=parent_fd)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def timeout(*args):
    raise TimeoutError('TIME_LIMIT')

def main():
    global PACKET
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(60)
    emit('HEADER', batch='IPHONE_MOZAK_001_PRIPREMA_888',
         effect='CREATE_LOCAL_FOLDERS_AND_ONE_REVIEW_PACKET', max_seconds=60,
         source_writes=0, network_calls=0, project_execution=False)
    need(os.geteuid() == 0 and 'ish' in os.uname().release.lower(), 'WRONG_ISH_CONTEXT')
    need(read('/etc/alpine-release', 128).strip().startswith(b'3.'), 'ALPINE_CONTEXT')
    need(json.loads(read(ROOT / 'IDENTITY.json', 4096)) == IDENTITY, 'WORKSPACE_IDENTITY')
    files, binding, uncovered = prepare_snapshot(ROOT)
    transport = transport_observation()
    emit('TRANSPORT_OBSERVATION', **transport)
    inventory = [{'member': key, 'bytes': len(data), 'sha256': digest(data)}
                 for key, data in sorted(files.items())]
    snapshot_id = digest(encoded(inventory))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    findings_count = sum(b['findings_count'] for b in binding)
    manifest = {
        'protocol': 888, 'source_device': 'IPHONE_ISH', 'workspace': str(ROOT),
        'observed_utc': now, 'snapshot_id': snapshot_id,
        'report_path': str(ROOT / REPORT_REL), 'report_is_saved_history': True,
        'source_count': len(binding), 'findings_count': findings_count,
        'source_hashes_without_report_rows': uncovered,
        'selection': 'ALL_ROWS_OF_ONE_KNOWN_SAVED_REPORT_NOT_ALL_FACTORIES',
        'content_status': 'EXISTING_FINDINGS_FOR_REVIEW',
        'source_hash_check': 'MATCHED_BYTES_READ_THIS_RUN',
        'quotes_check': 'MATCH_SAVED_EXCERPTS_ONLY',
        'semantic_accuracy': 'NOT_ASSESSED', 'information_freshness': 'NOT_ESTABLISHED',
        'source_excerpt_reproduction': 'NOT_TESTED', 'formulas_recalculated': False,
        'signature_release': 'NOT_ASSESSED', 'canonical_activation': False,
        'requested_24_meaning': 'UNRESOLVED_COUNT_OR_CONTINUOUS_OPERATION',
        'asus_target': ASUS, 'network_delivery': 'NOT_PERFORMED',
        'transport_configured': False, 'background_service_started': False,
        'members': inventory, 'bindings': binding}
    files['PREDAJA.json'] = encoded(manifest)
    need(sum(map(len, files.values())) < MAX_PACKET - 131072, 'PACKET_SIZE_LIMIT')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as z:
        for key, data in sorted(files.items()):
            z.writestr(key, data)
    payload = buffer.getvalue()
    need(len(payload) <= MAX_PACKET, 'PACKET_SIZE_LIMIT')
    space = os.statvfs('/root')
    need(space.f_bavail * space.f_frsize >= len(payload) + 16 * 1024 * 1024, 'SPACE_LIMIT')
    fds = []
    try:
        parent = open_dir('/root'); fds.append(parent)
        dest_fd = mkdir_child(parent, DEST.name, DEST); fds.append(dest_fd)
        queue_fd = mkdir_child(dest_fd, 'ZA_SLANJE', DEST / 'ZA_SLANJE'); fds.append(queue_fd)
        receipt_fd = mkdir_child(dest_fd, 'POTVRDE_PRIJEMA', DEST / 'POTVRDE_PRIJEMA')
        fds.append(receipt_fd)
        name = 'PAKET_' + snapshot_id[:12] + '_' + secrets.token_hex(6)
        packet_dir = DEST / 'ZA_SLANJE' / name
        os.mkdir(name, 0o700, dir_fd=queue_fd)
        CREATED.append(str(packet_dir))
        run_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=queue_fd)
        fds.append(run_fd)
        PACKET = packet_dir / 'IPHONE_ZA_ASUS_888.zip'
        write_new(run_fd, PACKET.name, payload)
        check = read(PACKET, MAX_PACKET)
        need(digest(check) == digest(payload), 'PACKET_READBACK')
        with zipfile.ZipFile(io.BytesIO(check), 'r') as z:
            need(set(z.namelist()) == set(files), 'MEMBER_SET')
            for key, data in files.items():
                need(digest(z.read(key)) == digest(data), 'MEMBER_READBACK')
        receipt = {
            'batch': 'IPHONE_MOZAK_001_PRIPREMA_888',
            'result': 'LOCAL_REVIEW_PACKET_READY_NOT_SENT',
            'packet': str(PACKET), 'packet_bytes': len(payload), 'packet_sha256': digest(payload),
            'snapshot_id': snapshot_id, 'saved_findings': findings_count,
            'source_count': len(binding), 'readback': 'PASS',
            'network_calls': 0, 'asus_receipt': None, 'background_service_started': False,
            'observed_utc': now}
        write_new(run_fd, 'SPREMNO_ZA_PREGLED.json', encoded(receipt))
        emit('FINAL', **receipt, created_directories=CREATED, source_writes=0,
             existing_files_overwritten=0, semantic_accuracy='NOT_ASSESSED',
             information_freshness='NOT_ESTABLISHED',
             next='VRATI_CIJELI_IZLAZ_I_POJASNI_24')
    finally:
        for fd in reversed(fds):
            os.close(fd)

if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        emit('FINAL', batch='IPHONE_MOZAK_001_PRIPREMA_888', result='HOLD',
             reason=type(exc).__name__, detail=str(exc)[:180],
             created_directories=CREATED, possible_partial_packet=str(PACKET) if PACKET else None,
             automatically_removed=False, source_writes=0, network_calls=0,
             next='VRATI_CIJELI_IZLAZ')
        raise SystemExit(2)
    finally:
        signal.alarm(0)
