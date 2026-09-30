'''apport package hook for ubuntu-release-upgrader

(c) 2011-2022 Canonical Ltd.
Author: Brian Murray <brian@ubuntu.com>
'''

import os
import re
from glob import glob

from apport.hookutils import (
    attach_gsettings_package,
    attach_file_if_exists,
    attach_root_command_outputs,
    command_output,
    root_command_output)


def add_info(report, ui):
    try:
        attach_gsettings_package(report, 'ubuntu-release-upgrader')
    except:
        pass
    report['CrashDB'] = 'ubuntu'
    report.setdefault('Tags', 'dist-upgrade')
    report['Tags'] += ' dist-upgrade'
    clone_file = '/var/log/dist-upgrade/apt-clone_system_state.tar.gz'
    if os.path.exists(clone_file):
        report['VarLogDistupgradeAptclonesystemstate.tar.gz'] =  \
            root_command_output(["cat", clone_file], decode_utf8=False)
    attach_file_if_exists(report, '/var/log/dist-upgrade/apt.log',
        'VarLogDistupgradeAptlog')
    attach_file_if_exists(report, '/var/log/dist-upgrade/apt-term.log',
        'VarLogDistupgradeApttermlog')
    attach_file_if_exists(report, '/var/log/dist-upgrade/history.log',
        'VarLogDistupgradeAptHistorylog')
    attach_file_if_exists(report, '/var/log/dist-upgrade/lspci.txt',
        'VarLogDistupgradeLspcitxt')
    attach_file_if_exists(report, '/var/log/dist-upgrade/main.log',
        'VarLogDistupgradeMainlog')
    attach_file_if_exists(report, '/var/log/dist-upgrade/term.log',
        'VarLogDistupgradeTermlog')
    attach_file_if_exists(report, '/var/log/dist-upgrade/xorg_fixup.log',
        'VarLogDistupgradeXorgFixuplog')
    attach_file_if_exists(report, '/var/log/dist-upgrade/screenlog.0',
        'VarLogDistupgradeScreenlog')
    attach_root_command_outputs(
        report,
        {'CurrentDmesg.txt':
            'dmesg | comm -13 --nocheck-order /var/log/dmesg -'})
    if os.path.exists('/run/systemd/system'):
        report['JournalErrors'] = command_output(
            ['journalctl', '-b', '--priority=warning', '--lines=1000'])
    # the release upgrade may have crashed due to something else crashing
    reports = glob('/var/crash/*')
    if reports:
        report['CrashReports'] = command_output(
            ['stat', '-c', '%a:%u:%g:%s:%y:%x:%n'] + reports)
    problem_type = report.get("ProblemType", None)
    if problem_type == 'Crash':
        tmpdir = re.compile(r'ubuntu-release-upgrader-\w+')
        tb = report.get("Traceback", None)
        if tb:
            dupe_sig = ''
            for line in tb.splitlines():
                scrub_line = tmpdir.sub('ubuntu-release-upgrader-tmpdir', line)
                dupe_sig += scrub_line + '\n'
            report["DuplicateSignature"] = dupe_sig
