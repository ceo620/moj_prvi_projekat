#!/usr/bin/env python3
"""Consolidate only hash-identical mapped files; preserve legacy paths as links."""
import datetime, fcntl, hashlib, json, os, stat, sys, time
from pathlib import Path

ROOT = Path('/root/FREYA_IPHONE_ISH_NODE_888')
OLD = Path('/root/FREYA_RAD_888')
MAP = ROOT / '09_EVIDENCE/IPHONE_888_UNION_INTEGRATE_REPAIR_02.json'
STATE = ROOT / '05_SYSTEM_RUNTIME/STATE'
JOURNAL = STATE / 'MAPPED_FILE_CONSOLIDATION.jsonl'
DEADLINE = datetime.datetime(2026, 9, 27, 22, 2, tzinfo=datetime.timezone.utc).timestamp()

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def budget():
    need(time.time() < DEADLINE, 'MUTATION_WINDOW_ENDED')

def inside(p, root):
    return str(p).startswith(str(root) + '/') and '..' not in p.parts

def plain_parents(p):
    return not any(q.is_symlink() for q in p.parents)

def fingerprint(p):
    s = p.stat()
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        while True:
            budget()
            b = f.read(1048576)
            if not b:
                return h.hexdigest()
            h.update(b)

def append(f, record):
    f.write(json.dumps(record, ensure_ascii=False) + '\n')
    f.flush()
    os.fsync(f.fileno())

def apply_pair(src, dst, expected, journal, sequence):
    budget()
    need(plain_parents(src) and plain_parents(dst), 'SYMLINK_PARENT')
    need(not dst.is_symlink() and dst.is_file(), 'DESTINATION_NOT_REGULAR')
    if src.is_symlink():
        need(src.resolve() == dst.resolve(), 'OTHER_SOURCE_LINK')
        need(digest(dst) == expected, 'LINK_TARGET_HASH_CHANGED')
        return 'ALREADY_LINKED', 0
    need(src.is_file(), 'SOURCE_MISSING_OR_NOT_REGULAR')
    a, b = fingerprint(src), fingerprint(dst)
    need(a[0] == b[0], 'CROSS_DEVICE')
    need(stat.S_ISREG(src.stat().st_mode) and stat.S_ISREG(dst.stat().st_mode), 'NONREGULAR')
    need(digest(src) == expected and digest(dst) == expected, 'HASH_CHANGED')
    need(fingerprint(src) == a and fingerprint(dst) == b, 'FILE_CHANGED_DURING_CHECK')
    tmp = src.with_name('.freya-link-' + str(os.getpid()) + '-' + str(sequence))
    need(not os.path.lexists(tmp), 'TEMP_LINK_EXISTS')
    budget()
    # A prepared link is recorded before moving the original over its verified copy.
    record = {'source': str(src), 'destination': str(dst), 'sha256': expected,
              'temporary_link': str(tmp), 'source_fingerprint': a,
              'destination_fingerprint': b, 'size': a[2]}
    append(journal, dict(record, event='INTENT'))
    os.symlink(str(dst), str(tmp))
    moved = False
    try:
        need(fingerprint(src) == a and fingerprint(dst) == b, 'FILE_CHANGED_BEFORE_MOVE')
        os.replace(src, dst)
        moved = True
        os.replace(tmp, src)
        need(src.is_symlink() and src.resolve() == dst.resolve(), 'LINK_VERIFY_FAILED')
        need(dst.stat().st_ino == a[1] and dst.stat().st_size == a[2], 'MOVED_INODE_VERIFY_FAILED')
        append(journal, dict(record, event='DONE'))
    except Exception:
        # Restore the legacy pathname even if link installation was interrupted.
        if moved and not os.path.lexists(src) and dst.is_file():
            os.symlink(str(dst), str(src))
        raise
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)
    return 'CONSOLIDATED', a[2] if a[1] != b[1] else 0

def main():
    need(sys.argv[1:] == ['--ujedini-888'], 'Use --ujedini-888')
    need(os.geteuid() == 0, 'ROOT_REQUIRED')
    budget()
    need(ROOT.is_dir() and OLD.is_dir() and STATE.is_dir(), 'KNOWN_ROOT_MISSING')
    for p in (ROOT, OLD, STATE, MAP, JOURNAL, STATE / 'autopilot_schedule.lock'):
        need(not p.is_symlink() and plain_parents(p), 'SYMLINK_CONTROL_PATH: ' + str(p))
    lock = (STATE / 'autopilot_schedule.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    raw = MAP.read_bytes()
    data = json.loads(raw)
    need(data.get('source_root') == str(OLD) and data.get('canonical_root') == str(ROOT), 'MAP_SCOPE_MISMATCH')
    need(data.get('batch') == 'IPHONE_888_UNION_INTEGRATE_REPAIR_02', 'MAP_ID_MISMATCH')
    rows = data.get('integrated')
    need(isinstance(rows, list) and rows, 'MAP_ROWS_MISSING')
    prepared, seen_src, seen_dst = [], set(), {}
    for row in rows:
        need(isinstance(row, list) and len(row) == 3, 'MAP_SCHEMA_MISMATCH')
        s, d, h = row
        need(isinstance(s, str) and isinstance(d, str) and isinstance(h, str), 'MAP_VALUE_TYPE')
        src, dst = Path(s), Path(d)
        need(inside(src, OLD) and inside(dst, ROOT), 'OUT_OF_SCOPE_MAPPING')
        need(len(h) == 64 and all(c in '0123456789abcdef' for c in h), 'INVALID_HASH')
        need(s not in seen_src, 'NON_UNIQUE_SOURCE_MAPPING')
        need(d not in seen_dst or seen_dst[d] == h, 'CONFLICTING_DESTINATION_HASH')
        seen_src.add(s); seen_dst[d] = h
        prepared.append((src, dst, h))
    # Recover only a move explicitly recorded by this script, with the original inode.
    pending = {}
    if JOURNAL.exists():
        for line in JOURNAL.read_text().splitlines():
            item = json.loads(line)
            if item.get('event') == 'INTENT':
                pending[item['source']] = item
            elif item.get('event') in ('DONE', 'RECOVERED_LINK'):
                pending.pop(item['source'], None)
    counts = {'CONSOLIDATED': 0, 'ALREADY_LINKED': 0, 'SKIPPED': 0}
    saved = 0
    skipped = []
    with JOURNAL.open('a') as jf:
        os.chmod(JOURNAL, 0o600)
        for s, item in pending.items():
            src, dst = Path(s), Path(item['destination'])
            need(inside(src, OLD) and inside(dst, ROOT), 'JOURNAL_SCOPE')
            need(plain_parents(src) and plain_parents(dst) and not dst.is_symlink(), 'JOURNAL_LINK_CONFLICT')
            if not os.path.lexists(src):
                budget()
                need(dst.is_file() and dst.stat().st_ino == item['source_fingerprint'][1], 'RECOVERY_INODE_MISMATCH')
                need(digest(dst) == item['sha256'], 'RECOVERY_HASH_MISMATCH')
                os.symlink(str(dst), str(src))
                append(jf, dict(item, event='RECOVERED_LINK'))
        for i, (src, dst, expected) in enumerate(prepared, 1):
            if time.time() >= DEADLINE:
                print('STOP=TIME_WINDOW_ENDED', flush=True)
                break
            try:
                status, reclaimed = apply_pair(src, dst, expected, jf, i)
                counts[status] += 1
                saved += reclaimed
            except Exception as e:
                counts['SKIPPED'] += 1
                item = {'source': str(src), 'destination': str(dst), 'reason': str(e)}
                skipped.append(item)
                append(jf, dict(item, event='SKIPPED'))
                if str(e) == 'MUTATION_WINDOW_ENDED':
                    break
                # Stop if an operation began but could not finish safely.
                if not os.path.lexists(src):
                    raise
            if i % 20 == 0:
                print('PROGRESS=%d/%d | CONSOLIDATED=%d | SKIPPED=%d' % (i, len(prepared), counts['CONSOLIDATED'], counts['SKIPPED']), flush=True)
    report = {'protocol': '888', 'human_gate': 'ACTIVE',
              'result': 'MAPPED_FILE_CONSOLIDATION_FINISHED',
              'map_sha256': hashlib.sha256(raw).hexdigest(),
              'mapped_files': len(prepared), 'counts': counts,
              'duplicate_logical_bytes_removed': saved,
              'remaining_unattempted': len(prepared) - sum(counts.values()),
              'skipped': skipped, 'journal': str(JOURNAL),
              'unique_unmapped_files': 'NOT_SCANNED_OR_CHANGED',
              'parallel_system_closure': 'NOT_CLAIMED',
              'external_send': 'NONE'}
    report_path = STATE / ('MAPPED_CONSOLIDATION_' + str(os.getpid()) + '_' + str(time.time_ns()) + '.json')
    with report_path.open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    compact = dict(report)
    compact['skipped'] = skipped[:12]
    print(json.dumps(compact, ensure_ascii=False, indent=2), flush=True)
    print('REPORT=' + str(report_path))
    print('BATCH_COMPLETE=YES')
    lock.close()

if __name__ == '__main__':
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=IPHONE_UJEDINI_MAPIRANE_FAJLOVE_888', flush=True)
    try:
        main()
    except Exception as e:
        print('RESULT=HOLD\nREASON=' + str(e) + '\nBATCH_COMPLETE=NO', flush=True)
        sys.exit(1)
