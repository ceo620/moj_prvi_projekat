#!/usr/bin/env python3
"""Repair the existing FREYA_RUN_V2 copy, classify the existing intake, verify receipts.
Reuses the exact previously approved/tested support script. No new agent or register.
The existing input directory and STATE remain at their current locations.
No network, source edits, archive extraction, background processes or financial approval.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shlex
import stat
import sys
import tempfile
import datetime

SUPPORT = Path('/root/ISH_DOZVOLA_I_TEST_888.py')
SUPPORT_SHA = '4e16bd08d450b3f9d308f078a084efd3a6487b553bccbf356e58b91c10f609b6'
OLD_LAUNCHER_SHA = 'ee7e37bd8707594f0eed9af1181c4454105a82b25c81f9aa5671724698a68f3f'
INPUT = Path('/root/FREYA_RAD_888/00_ULAZ')
STATE = Path('/root/FREYA_RAD_888/05_SISTEM/AGENT_FACTORY/STATE')
TYPES = {'.pdf': 'DOCUMENT', '.doc': 'DOCUMENT', '.docx': 'DOCUMENT',
         '.xls': 'FINANCIAL', '.xlsx': 'FINANCIAL', '.csv': 'FINANCIAL',
         '.txt': 'TEXT', '.md': 'TEXT', '.jpg': 'IMAGE', '.jpeg': 'IMAGE', '.png': 'IMAGE'}


def load_support():
    if SUPPORT.is_symlink() or any(p.is_symlink() for p in SUPPORT.parents):
        raise RuntimeError('SUPPORT_SYMLINK')
    raw = SUPPORT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SUPPORT_SHA:
        raise RuntimeError('SUPPORT_SCRIPT_CHANGED')
    # Reviewed code defines functions only when __name__ is not __main__.
    return runpy.run_path(str(SUPPORT), run_name='_reviewed_888_support')


def snapshot(read, need, no_links, digest):
    no_links(INPUT)
    need(INPUT.is_dir(), 'INPUT_DIRECTORY_MISSING')
    rows = {}
    total = 0
    def fail(error):
        raise error
    for base, dirs, files in os.walk(str(INPUT), followlinks=False, onerror=fail):
        for name in dirs + files:
            p = Path(base) / name
            need(not p.is_symlink(), 'INPUT_SYMLINK: ' + str(p))
        for name in files:
            p = Path(base) / name
            need(not any(c in str(p) for c in ('\n', '\r', '\t', '\\')), 'UNSUPPORTED_PATH: ' + str(p))
            need(p.suffix.lower() in TYPES, 'UNREVIEWED_INPUT_TYPE: ' + str(p))
            raw = read(p, 24 * 1024 * 1024)
            total += len(raw)
            need(total <= 96 * 1024 * 1024 and len(rows) < 200, 'INPUT_BATCH_LIMIT')
            rows[str(p)] = {'sha256': digest(raw), 'bytes': len(raw), 'classification': TYPES[p.suffix.lower()]}
    need(rows, 'INPUT_EMPTY')
    return dict(sorted(rows.items()))


def launcher_bytes(paths, allow, allow_sha):
    quote = shlex.quote
    lines = ['#!/bin/sh', 'set -eu', 'unset ENV BASH_ENV PYTHONPATH PYTHONHOME',
             'export PATH=/usr/bin:/bin', 'export PYTHONDONTWRITEBYTECODE=1', 'export PYTHONNOUSERSITE=1']
    for role, p in paths.items():
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append("printf '%s\\n' " + quote(sha + '  ' + str(p)) + ' | sha256sum -c - >/dev/null')
    lines.append("printf '%s\\n' " + quote(allow_sha + '  ' + str(allow)) + ' | sha256sum -c - >/dev/null')
    argv = ['/usr/bin/python3', '-I', '-S', '-B', str(paths['foreground']), '--cycle', str(INPUT),
            str(paths['integrated']), str(paths['processor']), str(paths['binder']), str(allow),
            'DOCUMENT_PROCESSOR', str(STATE)]
    lines.append('exec ' + ' '.join(quote(a) for a in argv))
    return ('\n'.join(lines) + '\n').encode()


def main():
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=ISH_STVARNI_TOK_888', flush=True)
    g = load_support()
    read, need, no_links, digest = [g[k] for k in ('read', 'need', 'no_links', 'digest')]
    new_file, run_logged = g['new_file'], g['run_logged']
    root, allow = g['ROOT'], g['ALLOW']
    need('ish' in os.uname().release.lower() and os.geteuid() == 0, 'WRONG_DEVICE_OR_USER')
    paths = g['verified_modules']()
    permissions = read(allow)
    need(g['contract_bytes'](permissions) == permissions, 'APPROVED_PROCESSOR_ROW_MISSING')
    launcher = root / '05_SYSTEM_RUNTIME/FREYA_RUN_V2__ee7e37bd8707.sh'
    old_launcher = read(launcher)
    need(digest(old_launcher) == OLD_LAUNCHER_SHA, 'LAUNCHER_CHANGED_OR_ALREADY_REPAIRED')
    for p in (STATE, root / '09_EVIDENCE'):
        no_links(p)
        need(p.is_dir(), 'DIRECTORY_MISSING: ' + str(p))
    need(not os.path.lexists(STATE / 'LOCK') and not os.path.lexists(STATE / 'STOP'), 'EXISTING_LOCK_OR_STOP')
    old_index = read(STATE / 'INDEX.json')
    need(json.loads(old_index) == {}, 'STATE_CHANGED_SINCE_REVIEW')
    old_checkpoint = read(STATE / 'CHECKPOINT.env')
    originals = snapshot(read, need, no_links, digest)
    os.umask(0o077)
    folder = Path(tempfile.mkdtemp(prefix='STVARNI_TOK_', dir=str(root / '09_EVIDENCE')))
    print('EVIDENCE=' + str(folder), flush=True)
    for name, raw in [('launcher_before.sh', old_launcher), ('index_before.json', old_index),
                      ('checkpoint_before.env', old_checkpoint)]:
        new_file(folder / name, raw)
    candidate = folder / 'reviewed_launcher_candidate.sh'
    replacement = launcher_bytes(paths, allow, digest(permissions))
    new_file(candidate, replacement)
    report = {'protocol': '888', 'result': 'HOLD', 'scope': 'Local classification and verified receipts',
              'input': str(INPUT), 'state': str(STATE), 'input_files': originals,
              'launcher': str(launcher), 'launcher_old_sha256': digest(old_launcher),
              'launcher_new_sha256': digest(replacement), 'launcher_installed': False,
              'network': 'NONE', 'financial_accuracy': 'NOT_ASSESSED',
              'document_generation': 'NOT_PERFORMED', 'canonical_consolidation': 'NOT_COMPLETED'}
    installed = False
    try:
        code, _ = run_logged(['/bin/sh', '-n', candidate], folder, 'syntax')
        need(code == 0, 'LAUNCHER_SYNTAX')
        need(read(STATE / 'INDEX.json') == old_index and read(STATE / 'CHECKPOINT.env') == old_checkpoint, 'STATE_CONCURRENT_CHANGE')
        print('STEP=REAL_CLASSIFICATION\nINPUT_FILES=' + str(len(originals)), flush=True)
        code, lines = run_logged(['/bin/sh', candidate], folder, 'real_cycle')
        need(code == 0 and {'RESULT=PASS', 'OBJECTS_PROCESSED=' + str(len(originals)),
                           'PROCESSED_INDEX_COUNT=' + str(len(originals))}.issubset(lines), 'REAL_CYCLE_FAILED')
        checkpoint = dict(line.split('=', 1) for line in read(STATE / 'CHECKPOINT.env').decode().splitlines() if '=' in line)
        work = Path(checkpoint['LAST_RUN_DIR'])
        no_links(work)
        need((STATE / 'RUNS').resolve() in work.resolve().parents, 'RUN_OUTSIDE_STATE')
        expected = {}
        for i, source_path in enumerate(sorted(Path(p) for p in originals), 1):
            source = str(source_path)
            info = originals[source]
            expected[str(work / 'INTAKE/STAGING' / ('%04d_%s' % (i, Path(source).name)))] = info
        receipts = sorted((work / 'OUTPUT/QUEUE/OBJECTS').glob('*/RECEIPT.json'))
        need(len(receipts) == len(originals), 'WRONG_RECEIPT_COUNT')
        verified = []
        seen = set()
        for receipt in receipts:
            raw = read(receipt)
            j = json.loads(raw)
            key = j['source']
            need(key in expected and key not in seen, 'RECEIPT_SOURCE_OR_DUPLICATE')
            info = expected[key]
            need(j['result'] == 'PASS' and j['classification'] == info['classification'], 'RECEIPT_CLASSIFICATION')
            need(j['sha256'] == info['sha256'] and j['bytes'] == info['bytes'], 'RECEIPT_HASH_OR_SIZE')
            need(j['risk'] == ['NONE'] and j['network_action'] == 'NONE' and j['original_modified'] == 'NO', 'RECEIPT_FLAGS')
            need(digest(read(Path(key), 24 * 1024 * 1024)) == info['sha256'], 'STAGED_COPY_CHANGED')
            seen.add(key)
            verified.append({'receipt': str(receipt), 'receipt_sha256': digest(raw), 'source_sha256': info['sha256']})
        need(seen == set(expected), 'MISSING_RECEIPT')
        need(snapshot(read, need, no_links, digest) == originals, 'INPUT_CHANGED')
        index = read(STATE / 'INDEX.json')
        need(json.loads(index) == {p: x['sha256'] for p, x in originals.items()}, 'INDEX_MISMATCH')
        print('STEP=SECOND_REAL_CYCLE_NO_DUPLICATES', flush=True)
        code, lines = run_logged(['/bin/sh', candidate], folder, 'second_cycle')
        need(code == 0 and {'RESULT=PASS', 'OBJECTS_PROCESSED=0', 'IDLE_CYCLES=1',
                           'PROCESSED_INDEX_COUNT=' + str(len(originals))}.issubset(lines), 'DUPLICATE_PREVENTION_FAILED')
        need(read(STATE / 'INDEX.json') == index, 'SECOND_INDEX_CHANGED')
        need(snapshot(read, need, no_links, digest) == originals, 'INPUT_CHANGED_AFTER_SECOND_CYCLE')
        for row in verified:
            need(digest(read(Path(row['receipt']))) == row['receipt_sha256'], 'RECEIPT_CHANGED')
        g['verified_modules']()
        need(read(allow) == permissions and read(launcher) == old_launcher, 'CONTRACT_OR_LAUNCHER_CHANGED')
        need(not os.path.lexists(STATE / 'LOCK'), 'LOCK_REMAINS')
        candidate.chmod(stat.S_IMODE(launcher.stat().st_mode))
        os.replace(str(candidate), str(launcher))
        installed = True
        need(read(launcher) == replacement, 'LAUNCHER_INSTALL_VERIFY')
        report.update(result='PASS_LOCAL_CLASSIFICATION_FLOW', launcher_installed=True,
                      verified_receipts=verified, first_cycle_processed=len(originals),
                      second_cycle_processed=0, input_hashes_unchanged=True,
                      production_output=str(work / 'OUTPUT'))
        print('LAUNCHER_REPAIRED=YES\nREAL_RECEIPTS_VERIFIED=' + str(len(verified)), flush=True)
        print('SOURCE_HASH_STABILITY=PASS\nSECOND_CYCLE=PASS_NO_DUPLICATES', flush=True)
        print('PRODUCTS=' + str(work / 'OUTPUT'), flush=True)
        print('RUN_COMMAND=sh ' + str(launcher), flush=True)
    except BaseException as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        if installed:
            try:
                if read(launcher) == replacement:
                    back = folder / 'launcher_restore.tmp'
                    new_file(back, old_launcher)
                    back.chmod(stat.S_IMODE(launcher.stat().st_mode))
                    os.replace(str(back), str(launcher))
                    report['launcher_rollback'] = 'RESTORED'
                else:
                    report['launcher_rollback'] = 'CONCURRENT_CHANGE_NOT_OVERWRITTEN'
            except BaseException as rollback_error:
                report['rollback_error'] = str(rollback_error)
        # Preserve processing receipts and live index for investigation/resumption.
        # Never erase or reset legitimate processing history after an error.
        raise
    finally:
        report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        new_file(folder / 'RESULT.json', (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
        print('REPORT=' + str(folder / 'RESULT.json'), flush=True)
    print('RESULT=PASS_LOCAL_CLASSIFICATION_FLOW\nFULL_SYSTEM_FINAL_SEAL=NOT_GRANTED\nBATCH_COMPLETE=YES', flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print('RESULT=HOLD\nREASON=' + type(error).__name__ + ': ' + str(error) + '\nBATCH_COMPLETE=NO', flush=True)
        sys.exit(2)
