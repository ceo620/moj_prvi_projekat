# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

# Copyright (C) 2018 Canonical Ltd.
#
# Functions useful for the final install.py script and for ubiquity
# plugins to use
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import json
import logging
import os
import platform
import pwd
import shutil
import stat
import subprocess


def get():
    """Return a singleton _Telemetry instance."""
    if _Telemetry._telemetry is None:
        _Telemetry._telemetry = _Telemetry()
    return _Telemetry._telemetry


class _Telemetry():

    _telemetry = None

    def __init__(self):
        self._metrics = {}
        self._stages_hist = {}
        self._start_time = self._get_current_uptime()
        self._metrics["From"] = platform.freedesktop_os_release().get(
            'VERSION_ID'
        )
        self.add_stage('start')
        self._dest_path = '/var/log/upgrade/telemetry'
        self._source = 'ubuntu_release_upgrader'
        try:
            with open('/var/log/installer/media-info') as f:
                self._metrics['InstallMedia'] = f.readline()
        except FileNotFoundError:
            pass

    def _get_current_uptime(self):
        """Get current uptime info. None if we couldn't fetch it."""
        uptime = None
        try:
            with open('/proc/uptime') as f:
                uptime = float(f.read().split()[0])
        except (FileNotFoundError, OSError, ValueError) as e:
            logging.warning("Exception while fetching current uptime: " +
                            str(e))
        return uptime

    def add_stage(self, stage_name):
        """Record installer stage with current time"""
        now = self._get_current_uptime()
        if self._start_time is None or now is None:
            return
        self._stages_hist[int(now - self._start_time)] = stage_name

    def set_updater_type(self, updater_type):
        """Record updater type"""
        self._metrics['Type'] = updater_type

    def set_using_third_party_sources(self, using):
        """Record if the user had third party sources"""
        self._metrics['ThirdPartySources'] = using

    def done(self):
        """Close telemetry collection

        Save to destination file"""

        self._metrics['Stages'] = self._stages_hist

        target_dir = os.path.dirname(self._dest_path)
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            with open(self._dest_path, 'w') as f:
                json.dump(self._metrics, f)
            os.chmod(self._dest_path,
                     stat.S_IRUSR | stat.S_IWUSR |
                     stat.S_IRGRP | stat.S_IROTH)
        except OSError as e:
            logging.warning("Exception while storing telemetry data: " +
                            str(e))
            return

        if not shutil.which('ubuntu-insights'):
            logging.info("ubuntu-insights not available, skipping collection")
            return

        try:
            users = [
                u.pw_name
                for u in pwd.getpwall()
                if u.pw_uid >= 1000
                and os.path.isdir(u.pw_dir + '/.config/ubuntu-insights')
            ]
        except Exception as e:
            logging.warning("Exception while retrieving users: " + str(e))
            return

        if not users:
            logging.warning("No regular users with home directories found")
            return

        for user in users:
            env = os.environ.copy()
            env['HOME'] = pwd.getpwnam(user).pw_dir
            env['XDG_RUNTIME_DIR'] = f'/run/user/{pwd.getpwnam(user).pw_uid}'
            # Check if source-specific consent already exists
            try:
                result = subprocess.run(
                    ['ubuntu-insights', 'consent', self._source],
                    user=user,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, 
                    # Error expected in case of null consent.
                )
            except Exception as e:
                logging.warning(
                    f"Exception while checking {self._source} consent "
                    f"with ubuntu-insights for user {user}: {e}"
                )
                continue

            # If no source-specific consent, check default consent
            # (platform) and migrate.
            if result.returncode != 0:
                try:
                    result = subprocess.run(
                        ['ubuntu-insights', 'consent'],
                        capture_output=True,
                        user=user,
                        env=env,
                    )
                except Exception as e:
                    logging.warning(
                        f"Exception while checking default consent "
                        f"with ubuntu-insights for user {user}: {e}"
                    )
                    continue

                if result.returncode != 0:
                    # Unable to determine consent, skip this user
                    continue

                # Parse and migrate global consent to source-specific
                consent_str = result.stdout.decode('utf-8').strip().lower()
                consent = consent_str.endswith('true')
                try:
                    subprocess.run(
                        [
                            'ubuntu-insights',
                            'consent',
                            self._source,
                            '-s',
                            str(consent).lower(),
                        ],
                        user=user,
                        env=env,
                        stdout=subprocess.DEVNULL,
                    )
                except Exception as e:
                    logging.warning(
                        f"Exception while setting {self._source} consent "
                        f"with ubuntu-insights for user {user}: {e}"
                    )

            # Collect telemetry
            try:
                subprocess.run(
                    [
                        'ubuntu-insights',
                        'collect',
                        self._source,
                        self._dest_path,
                    ],
                    user=user,
                    env=env,
                    stdout=subprocess.DEVNULL,
                )
            except Exception as e:
                logging.warning(
                    f"Exception while collecting with ubuntu-insights "
                    f"for user {user}: {e}"
                )


# vim:ai:et:sts=4:tw=80:sw=4:
