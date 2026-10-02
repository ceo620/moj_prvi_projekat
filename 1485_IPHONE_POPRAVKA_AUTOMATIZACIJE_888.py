#!/usr/bin/env python3
"""Repair only the observed iSH cron binding; never approve or send documents."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

R = Path('/root/FREYA_IPHONE_ISH_NODE_888')
RT = R / '05_SYSTEM_RUNTIME'
STATE = RT / 'STATE'
RUNNER = RT / 'FREYA_RUN_V2__ee7e37bd8707.sh'
RUNNER_HASH = 'ed9745973bba49d90cd188b10f9b090609eb865e3a4d790e297eb482864cdf66'
OLD = '/root/FREYA_RAD_888/05_SISTEM/AGENT_FACTORY/AUTOPILOT/IPHONE_888_AUTOPILOT.sh'
TAG = '# PROTOCOL888_IPHONE_AUTOPILOT'
CRON = Path('/etc/crontabs/root')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': '/root', 'SHELL': '/bin/sh', 'LANG': 'C'}

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def checked_path(p):
    need(not any(q.is_symlink() for q in (p, *p.parents)), 'SYMLINK: ' + str(p))

def read(p):
    checked_path(p)
    need(p.is_file(), 'MISSING: ' + str(p))
    return p.read_bytes()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def run(args, **kwargs):
    return subprocess.run(args, env=ENV, check=True, **kwargs)

def processes():
    return subprocess.check_output(['ps'], env=ENV, universal_newlines=True)

def cron_pids():
    result = []
    for line in processes().splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) == 4 and re.match(r'(?:\S*/)?crond(?:\s|$)', parts[3]):
            result.append(int(parts[0]))
    return result

def build_command(flock, trigger):
    log = STATE / ('AUTOPILOT_CRON_LAST.log' if trigger == 'CRON' else 'AUTOPILOT_MANUAL_TEST.log')
    checked_path(log)
    q = shlex.quote
    # No '%' in the crontab command: BusyBox cron treats it specially.
    body = (
        "{ echo PROTOCOL=888; echo HUMAN_GATE=ACTIVE; echo TRIGGER=" + trigger +
        "; date -u; echo '" + RUNNER_HASH + '  ' + str(RUNNER) +
        "' | sha256sum -c - && /bin/sh " + q(str(RUNNER)) +
        '; rc=$?; echo AUTOPILOT_EXIT=$rc; date -u; exit "$rc"; } >' + q(str(log)) + ' 2>&1'
    )
    lock = STATE / 'autopilot_schedule.lock'
    checked_path(lock)
    return q(flock) + ' -n ' + q(str(lock)) + ' /bin/sh -c ' + q(body)

def main():
    need(sys.argv[1:] == ['--primijeni-888'], 'Use --primijeni-888')
    need(os.geteuid() == 0, 'ROOT_REQUIRED')
    need(STATE.is_dir(), 'CANONICAL_STATE_MISSING')
    checked_path(STATE)
    raw = read(RUNNER)
    need(sha(raw) == RUNNER_HASH, 'RUNNER_HASH_CHANGED')
    checks = re.findall(r"'([0-9a-f]{64})  (/[^']+)'", raw.decode())
    need(len(checks) == 6, 'EXPECTED_SIX_COMPONENTS')
    for expected, name in checks:
        need(sha(read(Path(name))) == expected, 'COMPONENT_HASH: ' + name)
    print('COMPONENT_HASHES=6/6_PASS', flush=True)
    need(sha(read(Path(OLD))) == 'd3d409532b346c81e54727a1df2f0631eb90d551287c132757cacb76d64c8935', 'LEGACY_AUTOPILOT_CHANGED')
    flock = shutil.which('flock', path=ENV['PATH'])
    crontab = shutil.which('crontab', path=ENV['PATH'])
    crond = shutil.which('crond', path=ENV['PATH'])
    need(flock and crontab and crond, 'REQUIRED_EXISTING_COMMAND_MISSING')
    need(len(cron_pids()) <= 1, 'MULTIPLE_CROND_PROCESSES')
    ps = processes()
    for token in ('foreground_business__', 'integrated_runtime_', 'document_processor', 'IPHONE_888_AUTOPILOT.sh', 'FREYA_RUN_V2__'):
        need(token not in ps, 'ACTIVE_RUNTIME: ' + token)

    scheduled = build_command(flock, 'CRON')
    manual = build_command(flock, 'MANUAL_VERIFY')
    need('%' not in scheduled, 'UNESCAPED_CRON_PERCENT')
    run(['/bin/sh', '-n'], input=scheduled.encode())
    new_line = '*/15 * * * * ' + scheduled + ' ' + TAG
    before = read(CRON)
    lines = before.decode().splitlines()
    matches = [i for i, line in enumerate(lines) if line.strip() and not line.lstrip().startswith('#') and TAG in line]
    need(len(matches) == 1, 'EXPECTED_ONE_AUTOPILOT_CRON_ENTRY')
    idx = matches[0]
    old_parts = lines[idx].split()
    need(lines[idx] == new_line or old_parts == ['*/15','*','*','*','*',OLD,'#','PROTOCOL888_IPHONE_AUTOPILOT'], 'UNEXPECTED_AUTOPILOT_CRON_ENTRY')
    permitted = {
        '*/15 * * * * run-parts /etc/periodic/15min',
        '0 * * * * run-parts /etc/periodic/hourly',
        '0 2 * * * run-parts /etc/periodic/daily',
        '0 3 * * 6 run-parts /etc/periodic/weekly',
        '0 5 1 * * run-parts /etc/periodic/monthly',
    }
    for i, line in enumerate(lines):
        if i != idx and line.strip() and not line.lstrip().startswith('#'):
            need(' '.join(line.split()) in permitted, 'UNREVIEWED_CRON_ENTRY')
    lines[idx] = new_line
    after = ('\n'.join(lines) + '\n').encode()
    # Verify the existing runner before enabling its scheduled replacement.
    print('STEP=CANONICAL_MANUAL_TEST', flush=True)
    test = subprocess.run(['/bin/sh', '-c', manual], env=ENV)
    log = read(STATE / 'AUTOPILOT_MANUAL_TEST.log').decode(errors='replace')
    print(log, flush=True)
    need(test.returncode == 0 and 'AUTOPILOT_EXIT=0' in log and 'RESULT=PASS_CLASSIFICATION_AND_MEMORANDUM' in log, 'MANUAL_TEST_FAILED')
    need(read(CRON) == before, 'CRONTAB_CHANGED_DURING_TEST')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + str(os.getpid())
    backup = STATE / ('CRONTAB_BEFORE_REPAIR_' + stamp + '.txt')
    with backup.open('xb') as f:
        f.write(before)
    os.chmod(backup, 0o600)
    changed = before != after
    try:
        if changed:
            run([crontab, '-'], input=after)
        need(read(CRON) == after, 'CRONTAB_WRITE_VERIFICATION_FAILED')
        if not cron_pids():
            run([crond, '-b'])
        pids = cron_pids()
        need(len(pids) == 1, 'CROND_NOT_CONFIRMED_SINGLE')
    except Exception:
        # Fail closed: never re-enable the broken legacy job with a live daemon.
        safe_lines = before.decode().splitlines()
        safe_lines[idx] = '# HOLD_AUTOMATION_REPAIR ' + safe_lines[idx]
        safe = ('\n'.join(safe_lines) + '\n').encode()
        run([crontab, '-'], input=safe)
        need(read(CRON) == safe, 'CRON_FAIL_CLOSED_WRITE_FAILED')
        print('CRON_FAILURE_SAFE=AUTOPILOT_DISABLED; ORIGINAL_CRONTAB_IN_BACKUP', flush=True)
        raise
    report = {
        'protocol': '888', 'human_gate': 'ACTIVE',
        'result': 'PASS_CRON_REBOUND_AND_DAEMON_RUNNING',
        'cron_changed': changed, 'crond_pids': pids,
        'cron_sha256_before': sha(before), 'cron_sha256_after': sha(after),
        'previous_crontab': str(backup), 'canonical_runner': str(RUNNER),
        'manual_test': 'PASS', 'scheduled_execution': 'PENDING_REAL_CRON_LOG',
        'new_input_processing': 'NOT_TESTED', 'restart_persistence': 'NOT_VERIFIED',
        'ios_background_continuity': 'NOT_VERIFIED',
        'document_signoff': 'PENDING', 'external_send': 'NONE',
        'cron_log': str(STATE / 'AUTOPILOT_CRON_LAST.log'),
    }
    report_path = STATE / ('AUTOMATION_REPAIR_' + stamp + '.json')
    with report_path.open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    print('REPORT=' + str(report_path))
    print('REPORT_SHA256=' + sha(read(report_path)))
    print('SCHEDULE=EVERY_15_MINUTES_WHILE_CRON_CAN_RUN')
    print('CRON_LOG=' + str(STATE / 'AUTOPILOT_CRON_LAST.log'))
    print('BATCH_COMPLETE=YES')

if __name__ == '__main__':
    print('PROTOCOL=888\nHUMAN_GATE=ACTIVE\nBATCH=IPHONE_POPRAVKA_AUTOMATIZACIJE_888', flush=True)
    try:
        main()
    except Exception as exc:
        print('RESULT=HOLD\nREASON=' + str(exc) + '\nEXTERNAL_SEND=NONE\nBATCH_COMPLETE=NO', flush=True)
        sys.exit(1)
