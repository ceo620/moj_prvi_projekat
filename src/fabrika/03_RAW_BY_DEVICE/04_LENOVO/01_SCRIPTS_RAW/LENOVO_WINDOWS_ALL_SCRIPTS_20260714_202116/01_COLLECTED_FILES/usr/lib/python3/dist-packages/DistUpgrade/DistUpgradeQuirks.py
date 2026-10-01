# DistUpgradeQuirks.py
#
#  Copyright (c) 2004-2010 Canonical
#
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import apt
import atexit
import distro_info
import glob
import logging
import os
import re
import subprocess
import pathlib
from subprocess import PIPE, Popen
from datetime import datetime, timezone

from .DistUpgradeGettext import gettext as _
from .RiscvProfile import (RiscvProfile, RiscvProfileException)
from .S390xGeneration import (S390xGeneration, get_system_s390x_generation)


class DistUpgradeQuirks(object):
    """
    This class collects the various quirks handlers that can
    be hooked into to fix/work around issues that the individual
    releases have.

    The following handlers are supported:
    - PreCacheOpen: run *before* the apt cache is opened the first time
                    to set options that affect the cache
    - PostInitialUpdate: run *before* the sources.list is rewritten but
                         after an initial apt-get update
    - PreDistUpgradeCache: run *right before* the dist-upgrade is
                           calculated in the cache
    - PostDistUpgradeCache: run *after* the dist-upgrade was calculated
                            in the cache
    - StartUpgrade: before the first package gets installed (but the
                    download is finished)
    - PostUpgrade: run *after* the upgrade is finished successfully and
                   packages got installed
    - PostCleanup: run *after* the cleanup (orphaned etc) is finished
    """

    def __init__(self, controller, config):
        self.controller = controller
        self._view = controller._view
        self.config = config
        self.uname = Popen(["uname", "-r"], stdout=PIPE,
                           universal_newlines=True).communicate()[0].strip()
        self.extra_snap_space = 0
        self._poke = None
        self._snapstore_reachable = False
        self._snap_list = None
        self._did_change_font = False

    # individual quirks handler that run *before* the cache is opened
    def PreCacheOpen(self):
        """ run before the apt cache is opened the first time """
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        logging.debug("running Quirks.PreCacheOpen")
        self._add_apport_ignore_list()

    # individual quirks handler that run *after* the cache is opened
    def PostInitialUpdate(self):
        # PreCacheOpen would be better but controller.abort fails terribly
        """ run after the apt cache is opened the first time """
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        logging.debug("running Quirks.PostInitialUpdate")
        self._test_and_fail_on_rva23()
        self._test_and_fail_without_cgroupv2()
        self._test_and_fail_on_z13()
        self._test_and_fail_on_pi_old_eeprom()
        self._test_and_fail_rabbitmq_server_installed_and_not_upgradable()

        self._test_and_fail_on_tpm_fde()

        cache = self.controller.cache
        self._test_and_warn_if_ros_installed(cache)

        self._maybe_prevent_flatpak_auto_removal()

        if 'snapd' not in cache:
            logging.debug("package required for Quirk not in cache")
            return
        if cache['snapd'].is_installed and \
                (os.path.exists('/run/snapd.socket') or
                 os.path.exists('/run/snapd-snap.socket')):
            self._checkStoreConnectivity()
        # If the snap store is accessible, at the same time calculate the
        # extra size needed by to-be-installed snaps.  This also prepares
        # the snaps-to-install list for the actual upgrade.
        if self._snapstore_reachable:
            self._calculateSnapSizeRequirements()

    def PostUpgrade(self):
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        logging.debug("running Quirks.PostUpgrade")
        cache = self.controller.cache
        if 'snapd' not in cache:
            logging.debug("package required for Quirk not in cache")
            return
        if cache['snapd'].is_installed and \
                self._snap_list:
            self._replaceDebsAndSnaps()
        if 'ubuntu-desktop-raspi' in cache:
            if cache['ubuntu-desktop-raspi'].is_installed:
                self._replace_fkms_overlay()
                self._remove_z3fold()
        if 'ubuntu-server-raspi' in cache:
            if cache['ubuntu-server-raspi'].is_installed:
                self._add_kms_overlay()

    # individual quirks handler when the dpkg run is finished ---------
    def PostCleanup(self):
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        " run after cleanup "
        logging.debug("running Quirks.PostCleanup")
        self._remove_apport_ignore_list()

        # Try to refresh snaps, but ignore errors.
        try:
            subprocess.check_call(['snap', 'refresh'])
        except Exception as e:
            logging.debug(f'Failed to refresh snaps : {e}')

    # run right before the first packages get installed
    def StartUpgrade(self):
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        logging.debug("running Quirks.StartUpgrade")
        cache = self.controller.cache
        self._removeOldApportCrashes()
        self._killUpdateNotifier()
        self._pokeScreensaver()
        self._set_generic_font()
        self._disable_kdump_tools_on_install(cache)

    # individual quirks handler that run *right before* the dist-upgrade
    # is calculated in the cache
    def PreDistUpgradeCache(self):
        """ run right before calculating the dist-upgrade """
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        logging.debug("running Quirks.PreDistUpgradeCache")
        self._maybe_remove_gpg_wks_server()
        self._install_linux_sysctl_defaults()
        self._fix_lintian_resolver_deadlock()

    # individual quirks handler that run *after* the dist-upgrade was
    # calculated in the cache
    def PostDistUpgradeCache(self):
        """ run after calculating the dist-upgrade """
        # we do not run any quirks in partialUpgrade mode
        if self.controller._partialUpgrade:
            logging.info("not running quirks in partialUpgrade mode")
            return

        logging.debug("running Quirks.PostDistUpgradeCache")
        self._install_linux_metapackage()
        self._switch_to_systemd_coredump_for_kde_flavors()
        self._force_piboot_try_install()
        self._force_dracut_install()

    def _test_and_warn_if_ros_installed(self, cache):
        """
        Test and warn if ROS is installed. A given ROS release only
        supports specific Ubuntu releases, and can cause the upgrade
        to fail in an overly-cryptic manner.
        """

        # These are the root ROS 1 and 2 dependencies as of 07/27/2020
        ros_package_patterns = set()
        for package_name in (
                "catkin",
                "rosboost-cfg",
                "rosclean",
                "ros-environment",
                "ros-workspace"):
            ros_package_patterns.add(
                re.compile(r"ros-[^\-]+-%s" % package_name))

        ros_is_installed = False
        for pkg in cache:
            if ros_is_installed:
                break

            for pattern in ros_package_patterns:
                if pattern.match(pkg.name):
                    if pkg.is_installed or pkg.marked_install:
                        ros_is_installed = True
                    break

        if ros_is_installed:
            res = self._view.askYesNoQuestion(
                _("The Robot Operating System (ROS) is installed"),
                _("It appears that ROS is currently installed. Each ROS "
                  "release is very strict about the versions of Ubuntu "
                  "it supports, and Ubuntu upgrades can fail if that "
                  "guidance isn't followed. Before continuing, please "
                  "either uninstall ROS, or ensure the ROS release you "
                  "have installed supports the version of Ubuntu to "
                  "which you're upgrading.\n\n"
                  "For ROS 1 releases, refer to REP 3:\n"
                  "https://www.ros.org/reps/rep-0003.html\n\n"
                  "For ROS 2 releases, refer to REP 2000:\n"
                  "https://www.ros.org/reps/rep-2000.html\n\n"
                  "Are you sure you want to continue?"))
            if not res:
                self.controller.abort()

    def _maybe_prevent_flatpak_auto_removal(self):
        """
        If flatpak is installed, and there are either active remotes, or
        flatpak apps installed, prevent flatpak's auto-removal on upgrade.
        """
        prevent_auto_removal = False

        if "flatpak" not in self.controller.cache:
            return

        if not self.controller.cache["flatpak"].is_installed:
            return

        if not os.path.exists("/usr/bin/flatpak"):
            return

        for subcmd in ["remotes", "list"]:
            r = subprocess.run(
                    ["/usr/bin/flatpak", subcmd],
                    stdout=subprocess.PIPE
            )
            if r.stdout.decode("utf-8").strip():
                prevent_auto_removal = True
                break

        logging.debug("flatpak will{}be marked as manually installed"
                      .format(" " if prevent_auto_removal else " NOT "))

        if not prevent_auto_removal:
            return

        self.controller.cache["flatpak"].mark_auto(auto=False)

        for pkg in ("plasma-discover-backend-flatpak",
                    "gnome-software-plugin-flatpak"):
            if pkg not in self.controller.cache:
                continue

            if not self.controller.cache[pkg].is_installed:
                continue

            logging.debug("{} will be marked as manually installed"
                          .format(pkg))
            self.controller.cache[pkg].mark_auto(auto=False)

        self.controller.cache.commit(
            self._view.getAcquireProgress(),
            self._view.getInstallProgress(self.controller.cache)
        )

    def _fix_lintian_resolver_deadlock(self):
        """
        Fix an issue on Noble where the resolver can get stuck in a deadlock
        due to lintian being broken by a newer version of libyaml-libyaml-perl
        and the resolver refusing to upgrade lintian due to having to install
        libfile-libmagic-perl.

        Fixes LP: #2150319
        """

        if self.controller.fromDist != "noble":
            return

        if not ("lintian" in self.controller.cache and
                self.controller.cache["lintian"].is_installed):
            return

        # nudge the resolver to install libfile-libmagic-perl
        pkg_name = "libfile-libmagic-perl"
        logging.info(
            f"Quirk: Marking '{pkg_name}' for install to prevent dependency "
            "deadlock."
        )
        try:
            self.controller.cache[pkg_name].mark_install(auto_fix=False)
        except Exception as e:
            logging.error(
                f"Quirk: Failed to mark '{pkg_name}' for install: {e}"
            )

    def _add_apport_ignore_list(self):
        ignore_list = [
            '/usr/libexec/tracker-extract-3',  # LP: #2012638
            '/usr/sbin/update-apt-xapian-index',  # LP: #2058227
        ]

        path = '/etc/apport/blacklist.d/upgrade-quirks-ignore-list'

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                for bin in ignore_list:
                    f.write(f'{bin}\n')

        except Exception as e:
            logging.debug(f'Failed to create {path}: {e}')

    def _remove_apport_ignore_list(self):
        path = '/etc/apport/blacklist.d/upgrade-quirks-ignore-list'

        try:
            os.remove(path)
        except Exception as e:
            logging.debug(f'Failed to remove {path}: {e}')

    def _killUpdateNotifier(self):
        "kill update-notifier"
        # kill update-notifier now to suppress reboot required
        if os.path.exists("/usr/bin/killall"):
            logging.debug("killing update-notifier")
            subprocess.call(["killall", "-q", "update-notifier"])

    def _pokeScreensaver(self):
        if (os.path.exists("/usr/bin/xdg-screensaver") and
                os.environ.get('DISPLAY')):
            logging.debug("setup poke timer for the screensaver")
            cmd = "while true;"
            cmd += " do /usr/bin/xdg-screensaver reset >/dev/null 2>&1;"
            cmd += " sleep 30; done"
            try:
                self._poke = subprocess.Popen(cmd, shell=True)
                atexit.register(self._stopPokeScreensaver)
            except (OSError, ValueError):
                logging.exception("failed to setup screensaver poke")

    def _stopPokeScreensaver(self):
        res = False
        if self._poke is not None:
            try:
                self._poke.terminate()
                res = self._poke.wait()
            except OSError:
                logging.exception("failed to stop screensaver poke")
            self._poke = None
        return res

    def _removeOldApportCrashes(self):
        " remove old apport crash files and whoopsie control files "
        try:
            for ext in ['.crash', '.upload', '.uploaded']:
                for f in glob.glob("/var/crash/*%s" % ext):
                    logging.debug("removing old %s file '%s'" % (ext, f))
                    os.unlink(f)
        except Exception as e:
            logging.warning("error during unlink of old crash files (%s)" % e)

    def _checkStoreConnectivity(self):
        """ check for connectivity to the snap store to install snaps"""
        res = False
        snap_env = os.environ.copy()
        snap_env["LANG"] = "C.UTF-8"
        try:
            connected = Popen(["snap", "debug", "connectivity"], stdout=PIPE,
                              stderr=PIPE, env=snap_env,
                              universal_newlines=True).communicate()
        except Exception as e:
            logging.debug(
                f'Failed to check snap store connectivity, assuming none: {e}'
            )
            self._snapstore_reachable = False
            return

        if re.search(r"^ \* PASS", connected[0], re.MULTILINE):
            self._snapstore_reachable = True
            return
        # can't connect
        elif re.search(r"^ \*.*unreachable", connected[0], re.MULTILINE):
            logging.error("No snap store connectivity")
            old_lxd_deb_installed = False
            cache = self.controller.cache
            if 'lxd' in cache:
                # epoch 1 is the transitional deb
                if cache['lxd'].is_installed and not \
                        cache['lxd'].candidate.version.startswith("1:"):
                    logging.error("lxd is installed")
                    old_lxd_deb_installed = True
            if old_lxd_deb_installed:
                summary = _("Connection to the Snap Store failed")
                msg = _("You have the package lxd installed but your "
                        "system is unable to reach the Snap Store. "
                        "lxd is now provided via a snap and the release "
                        "upgrade will fail if snapd is not functional. "
                        "Please make sure you're connected to the "
                        "Internet and update any firewall or proxy "
                        "settings as needed so that you can reach "
                        "api.snapcraft.io. If you are an enterprise "
                        "with a firewall setup you may want to configure "
                        "a Snap Store proxy."
                        )
                self._view.error(summary, msg)
                self.controller.abort()
            else:
                res = self._view.askYesNoQuestion(
                    _("Connection to Snap Store failed"),
                    _("Your system does not have a connection to the Snap "
                      "Store. For the best upgrade experience make sure "
                      "that your system can connect to api.snapcraft.io.\n"
                      "Do you still want to continue with the upgrade?")
                )
        # debug command not available
        elif 'error: unknown command' in connected[1]:
            logging.error("snap debug command not available")
            res = self._view.askYesNoQuestion(
                _("Outdated snapd package"),
                _("Your system does not have the latest version of snapd. "
                  "Please update the version of snapd on your system to "
                  "improve the upgrade experience.\n"
                  "Do you still want to continue with the upgrade?")
            )
        # not running as root
        elif 'error: access denied' in connected[1]:
            res = False
            logging.error("Not running as root!")
        else:
            logging.error("Unhandled error connecting to the snap store.")
        if not res:
            self.controller.abort()

    def _calculateSnapSizeRequirements(self):
        import json
        import urllib.request
        from urllib.error import URLError

        # first fetch the list of snap-deb replacements that will be needed
        # and store them for future reference, along with other data we'll
        # need in the process
        self._prepare_snap_replacement_data()
        # now perform direct API calls to the store, requesting size
        # information for each of the snaps needing installation
        self._view.updateStatus(_("Calculating snap size requirements"))
        for snap, snap_object in self._snap_list.items():
            if snap_object['command'] != 'install':
                continue
            action = {
                "instance-key": "upgrade-size-check",
                "action": "download",
                "snap-id": snap_object['snap-id'],
                "channel": snap_object['channel'],
            }
            data = {
                "context": [],
                "actions": [action],
            }
            req = urllib.request.Request(
                url='https://api.snapcraft.io/v2/snaps/refresh',
                data=bytes(json.dumps(data), encoding='utf-8'))
            req.add_header('Snap-Device-Series', '16')
            req.add_header('Content-type', 'application/json')
            req.add_header('Snap-Device-Architecture', self.controller.arch)
            try:
                response = urllib.request.urlopen(req).read()
                info = json.loads(response)
                size = int(info['results'][0]['snap']['download']['size'])
            except (KeyError, URLError, ValueError):
                logging.debug("Failed fetching size of snap %s" % snap)
                continue
            self.extra_snap_space += size

    def _replaceDebsAndSnaps(self):
        """ install a snap and mark its corresponding package for removal """
        self._view.updateStatus(_("Processing snap replacements"))
        # _snap_list should be populated by the earlier
        # _calculateSnapSizeRequirements call.
        for snap, snap_object in self._snap_list.items():
            command = snap_object['command']
            if command == 'switch':
                channel = snap_object['channel']
                self._view.updateStatus(
                    _("switching channel for snap %s" % snap)
                )
                popenargs = ["snap", command, "--channel", channel, snap]

            elif command == 'remove':
                self._view.updateStatus(_("removing snap %s" % snap))
                popenargs = ["snap", command, snap]
            else:
                self._view.updateStatus(_("installing snap %s" % snap))
                popenargs = ["snap", command,
                             "--channel", snap_object['channel'], snap]
            try:
                self._view.processEvents()
                proc = subprocess.run(
                    popenargs,
                    stdout=subprocess.PIPE,
                    check=True)
                self._view.processEvents()
            except subprocess.CalledProcessError:
                logging.debug("%s of snap %s failed" % (command, snap))
                continue
            if proc.returncode == 0:
                logging.debug("%s of snap %s succeeded" % (command, snap))
            if command == 'install' and snap_object['deb']:
                self.controller.forced_obsoletes.append(snap_object['deb'])

    def _is_greater_than(self, term1, term2):
        """ copied from ubuntu-drivers common """
        # We don't want to take into account
        # the flavour
        pattern = re.compile('(.+)-([0-9]+)-(.+)')
        match1 = pattern.match(term1)
        match2 = pattern.match(term2)
        if match1 and match2:
            term1 = '%s-%s' % (match1.group(1),
                               match1.group(2))
            term2 = '%s-%s' % (match2.group(1),
                               match2.group(2))

        logging.debug('Comparing %s with %s' % (term1, term2))
        return apt.apt_pkg.version_compare(term1, term2) > 0

    def _get_linux_metapackage(self, cache, headers):
        """ Get the linux headers or linux metapackage
            copied from ubuntu-drivers-common
        """
        suffix = headers and '-headers' or ''
        pattern = re.compile('linux-image-(.+)-([0-9]+)-(.+)')
        source_pattern = re.compile('linux-(.+)')

        metapackage = ''
        version = ''
        for pkg in cache:
            if ('linux-image' in pkg.name and 'extra' not in pkg.name and
                    (pkg.is_installed or pkg.marked_install)):
                match = pattern.match(pkg.name)
                # Here we filter out packages such as
                # linux-generic-lts-quantal
                if match:
                    source = pkg.candidate.record['Source']
                    current_version = '%s-%s' % (match.group(1),
                                                 match.group(2))
                    # See if the current version is greater than
                    # the greatest that we've found so far
                    if self._is_greater_than(current_version,
                                             version):
                        version = current_version
                        match_source = source_pattern.match(source)
                        # Set the linux-headers metapackage
                        if '-lts-' in source and match_source:
                            # This is the case of packages such as
                            # linux-image-3.5.0-18-generic which
                            # comes from linux-lts-quantal.
                            # Therefore the linux-headers-generic
                            # metapackage would be wrong here and
                            # we should use
                            # linux-headers-generic-lts-quantal
                            # instead
                            metapackage = 'linux%s-%s-%s' % (
                                           suffix,
                                           match.group(3),
                                           match_source.group(1))
                        else:
                            # The scheme linux-headers-$flavour works
                            # well here
                            metapackage = 'linux%s-%s' % (
                                           suffix,
                                           match.group(3))
        return metapackage

    def _install_linux_metapackage(self):
        """ Ensure the linux metapackage is installed for the newest_kernel
            installed. (LP: #1509305)
        """
        cache = self.controller.cache
        linux_metapackage = self._get_linux_metapackage(cache, False)
        # Seen on errors.u.c with linux-rpi2 metapackage
        # https://errors.ubuntu.com/problem/994bf05fae85fbcd44f721495db6518f2d5a126d
        if linux_metapackage not in cache:
            logging.info("linux metapackage (%s) not available" %
                         linux_metapackage)
            return
        # install the package if it isn't installed
        if not cache[linux_metapackage].is_installed:
            logging.info("installing linux metapackage: %s" %
                         linux_metapackage)
            reason = "linux metapackage may have been accidentally uninstalled"
            cache.mark_install(linux_metapackage, reason)

    def ensure_recommends_are_installed_on_desktops(self):
        """ ensure that on a desktop install recommends are installed
            (LP: #759262)
        """
        if not self.controller.serverMode:
            if not apt.apt_pkg.config.find_b("Apt::Install-Recommends"):
                msg = "Apt::Install-Recommends was disabled,"
                msg += " enabling it just for the upgrade"
                logging.warning(msg)
                apt.apt_pkg.config.set("Apt::Install-Recommends", "1")

    def _is_deb2snap_metapkg_installed(self, deb2snap_entry):
        """ Helper function that checks if the given deb2snap entry
            has at least one metapkg which is installed on the system.
        """
        metapkg_list = deb2snap_entry.get("metapkg", None)
        if not isinstance(metapkg_list, list):
            metapkg_list = [metapkg_list]

        for metapkg in metapkg_list:
            if metapkg not in self.controller.cache:
                continue
            if metapkg and \
                    self.controller.cache[metapkg].is_installed is False:
                continue

            return True

        return False

    def _parse_deb2snap_json(self):
        import json
        seeded_snaps = {}
        unseeded_snaps = {}

        try:
            deb2snap_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'deb2snap.json'
            )
            with open(deb2snap_path, 'r') as f:
                d2s = json.loads(f.read())

            for snap in d2s["seeded"]:
                seed = d2s["seeded"][snap]
                if not self._is_deb2snap_metapkg_installed(seed):
                    continue
                deb = seed.get("deb", None)
                # Support strings like stable/ubuntu-{FROM_VERSION} in
                # deb2snap.json so that (a) we don't need to update the file
                # for every release, and (b) so that from_channel is not bound
                # to only one release.
                from_chan = seed.get(
                    'from_channel',
                    'stable/ubuntu-{FROM_VERSION}'
                ).format(
                    FROM_VERSION=self.controller.fromVersion
                )
                to_chan = seed.get(
                    'to_channel',
                    'stable/ubuntu-{TO_VERSION}'
                ).format(
                    TO_VERSION=self.controller.toVersion
                )
                force_switch = seed.get("force_switch", False)
                seeded_snaps[snap] = (deb, from_chan, to_chan, force_switch)

            for snap in d2s["unseeded"]:
                unseed = d2s["unseeded"][snap]
                deb = unseed.get("deb", None)
                if not self._is_deb2snap_metapkg_installed(unseed):
                    continue
                from_chan = seed.get(
                    'from_channel',
                    'stable/ubuntu-{FROM_VERSION}'
                ).format(
                    FROM_VERSION=self.controller.fromVersion
                )
                unseeded_snaps[snap] = (deb, from_chan)
        except Exception as e:
            logging.warning("error reading deb2snap.json file (%s)" % e)

        return seeded_snaps, unseeded_snaps

    def _prepare_snap_replacement_data(self):
        """ Helper function fetching all required info for the deb-to-snap
            migration: version strings for upgrade (from and to) and the list
            of snaps (with actions).
        """
        self._snap_list = {}

        seeded_snaps, unseeded_snaps = self._parse_deb2snap_json()

        snap_list = ''
        # list the installed snaps and add them to seeded ones
        snap_list = subprocess.Popen(["snap", "list"],
                                     universal_newlines=True,
                                     stdout=subprocess.PIPE).communicate()
        if snap_list:
            # first line of output is a header and the last line is empty
            snaps_installed = [line.split()[0]
                               for line in snap_list[0].split('\n')[1:-1]]

            for snap in snaps_installed:
                if snap in seeded_snaps or snap in unseeded_snaps:
                    continue
                else:
                    seeded_snaps[snap] = (
                        None,
                        f'stable/ubuntu-{self.controller.fromVersion}',
                        f'stable/ubuntu-{self.controller.toVersion}',
                        False
                    )

        self._view.updateStatus(_("Checking for installed snaps"))
        for snap, props in seeded_snaps.items():
            (deb, from_channel, to_channel, force_switch) = props
            snap_object = {}
            # check to see if the snap is already installed
            snap_info = subprocess.Popen(["snap", "info", snap],
                                         universal_newlines=True,
                                         stdout=subprocess.PIPE).communicate()
            self._view.processEvents()
            if re.search(r"^installed: ", snap_info[0], re.MULTILINE):
                logging.debug("Snap %s is installed" % snap)

                if not re.search(r"^tracking:.*%s" % from_channel,
                                 snap_info[0], re.MULTILINE):
                    logging.debug("Snap %s is not tracking the release channel"
                                  % snap)

                    if not force_switch:
                        # It is not tracking the release channel, and we were
                        # not told to force so don't switch.
                        continue

                snap_object['command'] = 'switch'
            else:
                # Do not replace packages not installed
                cache = self.controller.cache
                if (deb and (deb not in cache or not cache[deb].is_installed)):
                    logging.debug("Deb package %s is not installed. Skipping "
                                  "snap package %s installation" % (deb, snap))
                    continue

                match = re.search(r"snap-id:\s*(\w*)", snap_info[0])
                if not match:
                    logging.debug("Could not parse snap-id for the %s snap"
                                  % snap)
                    continue
                snap_object['command'] = 'install'
                snap_object['deb'] = deb
                snap_object['snap-id'] = match[1]
            snap_object['channel'] = to_channel
            self._snap_list[snap] = snap_object
        for snap, (deb, from_channel) in unseeded_snaps.items():
            snap_object = {}
            # check to see if the snap is already installed
            snap_info = subprocess.Popen(["snap", "info", snap],
                                         universal_newlines=True,
                                         stdout=subprocess.PIPE).communicate()
            self._view.processEvents()
            if re.search(r"^installed: ", snap_info[0], re.MULTILINE):
                logging.debug("Snap %s is installed" % snap)
                # its not tracking the release channel so don't remove
                if not re.search(r"^tracking:.*%s" % from_channel,
                                 snap_info[0], re.MULTILINE):
                    logging.debug("Snap %s is not tracking the release channel"
                                  % snap)
                    continue

                snap_object['command'] = 'remove'

                # check if this snap is being used by any other snaps
                conns = subprocess.Popen(["snap", "connections", snap],
                                         universal_newlines=True,
                                         stdout=subprocess.PIPE).communicate()
                self._view.processEvents()

                for conn in conns[0].split('\n'):
                    conn_cols = conn.split()
                    if len(conn_cols) != 4:
                        continue
                    plug = conn_cols[1]
                    slot = conn_cols[2]

                    if slot.startswith(snap + ':'):
                        plug_snap = plug.split(':')[0]
                        if plug_snap != '-' and \
                           plug_snap not in unseeded_snaps:
                            logging.debug("Snap %s is being used by %s. "
                                          "Switching it to stable track"
                                          % (snap, plug_snap))
                            snap_object['command'] = 'switch'
                            snap_object['channel'] = 'stable'
                            break

                self._snap_list[snap] = snap_object
        return self._snap_list

    def _remove_z3fold(self, boot_dir='/boot/firmware'):
        failure_action = (
            "You may need to remove zswap.zpool=z3fold from cmdline.txt "
            "on your boot partition")

        # Find cmdline.txt (the kernel command line) in one of the following
        # sub-directories of *boot_dir*: "new" (if it exists, which will hold
        # to-be-tested boot assets), "current" (if new does not exist, this
        # will be the current boot assets), or "" (the root of the boot
        # partition to cover the edge case of people not using the piboot-try
        # layout)
        boot_root = pathlib.Path(boot_dir)
        for boot_path in (boot_root / 'new', boot_root / 'current', boot_root):
            try:
                cmdline_path = boot_path / 'cmdline.txt'
                old_content = cmdline_path.read_bytes()
                # Only the first line is valid; all other lines are ignored
                old_params = (
                    old_content.decode('utf-8', errors='replace')
                    .splitlines()[0].split())
                # NOTE: we can't add the customary comment line indicating a
                # change made by u-r-u as the file can only contain one line
                new_params = [
                    param
                    for param in old_params
                    if param and param != 'zswap.zpool=z3fold'
                ]
                if old_params == new_params:
                    logging.warning(
                        "no z3fold usage found in %s", cmdline_path)
                else:
                    backup_path = cmdline_path.with_suffix('.txt.distUpgrade')
                    backup_path.write_bytes(old_content)
                    cmdline_path.write_bytes(
                        ' '.join(new_params).encode('utf-8'))
                return
            except FileNotFoundError:
                continue
            except OSError as exc:
                logging.error("failed to update kernel command line in "
                              "%s: %s; %s", cmdline_path, exc, failure_action)
                return
        logging.error("failed to locate kernel command line; %s",
                      failure_action)

    def _replace_pi_boot_config(self, old_config, new_config,
                                boot_config_filename, failure_action):
        try:
            boot_backup_filename = boot_config_filename + '.distUpgrade'
            with open(boot_backup_filename, 'w', encoding='utf-8') as f:
                f.write(old_config)
        except IOError as exc:
            logging.error("unable to write boot config backup to %s: %s; %s",
                          boot_backup_filename, exc, failure_action)
            return
        try:
            with open(boot_config_filename, 'w', encoding='utf-8') as f:
                f.write(new_config)
        except IOError as exc:
            logging.error("unable to write new boot config to %s: %s; %s",
                          boot_config_filename, exc, failure_action)

    def _replace_fkms_overlay(self, boot_dir='/boot/firmware'):
        failure_action = (
            "You may need to replace the vc4-fkms-v3d overlay with "
            "vc4-kms-v3d in config.txt on your boot partition")

        try:
            boot_config_filename = os.path.join(boot_dir, 'config.txt')
            with open(boot_config_filename, 'r', encoding='utf-8') as f:
                boot_config = f.read()
        except FileNotFoundError:
            logging.error("failed to open boot configuration in %s; %s",
                          boot_config_filename, failure_action)
            return

        new_config = ''.join(
            # startswith and replace used to cope with (and preserve) any
            # trailing d-t parameters, and any use of the -pi4 suffix
            '# changed by do-release-upgrade (LP: #1923673)\n#' + line +
            line.replace('dtoverlay=vc4-fkms-v3d', 'dtoverlay=vc4-kms-v3d')
            if line.startswith('dtoverlay=vc4-fkms-v3d') else
            # camera firmware disabled due to incompatibility with "full" kms
            # overlay; without the camera firmware active it's also better to
            # disable gpu_mem leaving the default (64MB) to allow as much as
            # possible for the KMS driver
            '# disabled by do-release-upgrade (LP: #1923673)\n#' + line
            if line.startswith('gpu_mem=') or line.rstrip() == 'start_x=1' else
            line
            for line in boot_config.splitlines(keepends=True)
        )

        if new_config == boot_config:
            logging.warning("no fkms overlay or camera firmware line found "
                            "in %s", boot_config_filename)
            return
        self._replace_pi_boot_config(
            boot_config, new_config, boot_config_filename, failure_action)

    def _add_kms_overlay(self, boot_dir='/boot/firmware'):
        failure_action = (
            "You may need to add dtoverlay=vc4-kms-v3d to an [all] section "
            "in config.txt on your boot partition")
        added_lines = [
            '# added by do-release-upgrade (LP: #2065051)',
            'dtoverlay=vc4-kms-v3d',
            'disable_fw_kms_setup=1',
            '',
            '[pi3+]',
            'dtoverlay=vc4-kms-v3d,cma-128',
            '',
            '[pi02]',
            'dtoverlay=vc4-kms-v3d,cma-128',
            '',
            '[all]',
        ]
        try:
            boot_config_filename = os.path.join(boot_dir, 'config.txt')
            with open(boot_config_filename, 'r', encoding='utf-8') as f:
                boot_config = f.read()
        except FileNotFoundError:
            logging.error("failed to open boot configuration in %s; %s",
                          boot_config_filename, failure_action)
            return

        def find_insertion_point(lines):
            # Returns the zero-based index of the dtoverlay=vc4-kms-v3d line in
            # an [all] section, if one exists, or the last line of the last
            # [all] section of the file, if one does not exist
            in_all = True
            last = 0
            for index, line in enumerate(lines):
                line = line.rstrip()
                if in_all:
                    last = index
                    # startswith used to cope with any trailing dtparams
                    if line.startswith('dtoverlay=vc4-kms-v3d'):
                        return last
                    elif line.startswith('[') and line.endswith(']'):
                        in_all = line == '[all]'
                    elif line.startswith('include '):
                        # [sections] are included from includes verbatim, hence
                        # (without reading the included file) we must assume
                        # we're no longer in an [all] section
                        in_all = False
                else:
                    in_all = line == '[all]'
            return last

        def add_kms_overlay(lines):
            insert_point = find_insertion_point(lines)
            try:
                if lines[insert_point].startswith('dtoverlay=vc4-kms-v3d'):
                    return lines
            except IndexError:
                # Empty config, apparently!
                pass
            lines[insert_point:insert_point] = added_lines
            return lines

        lines = [line.rstrip() for line in boot_config.splitlines()]
        lines = add_kms_overlay(lines)
        new_config = ''.join(line + '\n' for line in lines)

        if new_config == boot_config:
            logging.warning("no addition of KMS overlay required in %s",
                            boot_config_filename)
            return
        self._replace_pi_boot_config(
            boot_config, new_config, boot_config_filename, failure_action)

    def _force_dracut_install(self):
        """
        Force installation of dracut over initramfs-tools.

        At present this is only used on the Raspberry Pi images. See
        LP: #2148475 for further details.
        """
        cache = self.controller.cache

        raspi_seeds = ('ubuntu-server-raspi', 'ubuntu-desktop-raspi')
        meta_pkg = None
        for pkg in raspi_seeds:
            if pkg in cache and cache[pkg].is_installed:
                meta_pkg = pkg
                break

        if meta_pkg is None:
            return

        logging.debug(
            'Raspberry Pi seed detected (%s), switching to dracut', meta_pkg)
        if 'dracut' in cache and not cache['dracut'].is_installed:
            logging.debug('Marking dracut for installation')
            cache['dracut'].mark_install()

    def _force_piboot_try_install(self):
        """
        Force installation of piboot-try over flash-kernel.

        This is required in the resolute upgrade.
        """
        cache = self.controller.cache

        raspi_seeds = ('ubuntu-server-raspi', 'ubuntu-desktop-raspi')
        meta_pkg = None
        for pkg in raspi_seeds:
            if pkg in cache and cache[pkg].is_installed:
                meta_pkg = pkg
                break

        if meta_pkg is None:
            return

        logging.debug(
            'Raspberry Pi seed detected (%s), switching flash-kernel to '
            'piboot-try', meta_pkg)
        if 'piboot-try' in cache and not cache['piboot-try'].is_installed:
            logging.debug('Marking piboot-try for installation')
            cache['piboot-try'].mark_install()

    def _set_generic_font(self):
        """ Due to changes to the Ubuntu font we enable a generic font
            (in practice DejaVu or Noto) during the upgrade.
            See https://launchpad.net/bugs/2034986
        """
        temp_font = 'Sans'

        if self._did_change_font:
            return

        if self.controller.get_user_env('XDG_SESSION_TYPE', '') in ('', 'tty'):
            # Avoid running this on server systems or when the upgrade
            # is done over ssh.
            return

        if self.controller.get_user_uid() is None:
            logging.debug(
                'Cannot determine non-root UID, will not change font'
            )
            return

        schema = 'org.gnome.desktop.interface'

        desktops = self.controller.get_user_env(
            'XDG_CURRENT_DESKTOP', ''
        ).split(':')

        # Some flavors use other schemas for the desktop font.
        if 'MATE' in desktops or 'UKUI' in desktops:
            schema = 'org.mate.interface'
        elif 'X-Cinnamon' in desktops:
            schema = 'org.cinnamon.desktop.interface'

        # Some flavors lack the systemd integration needed for a
        # user service, so we create an autostart file instead.
        use_autostart = bool(
            set(['Budgie', 'LXQt', 'MATE', 'UKUI', 'X-Cinnamon', 'XFCE'])
            & set(desktops)
        )

        r = self.controller.run_as_user(
            ['/usr/bin/gsettings', 'get',
             f'{schema}', 'font-name'],
            stdout=subprocess.PIPE,
            encoding='utf-8',
        )

        (font, _, size) = r.stdout.strip('\'\n').rpartition(' ')
        font = font or 'Ubuntu'
        try:
            int(size)
        except ValueError:
            size = '11'

        logging.debug(f'Setting generic font {temp_font} {size} during the '
                      f'upgrade. Original font is {font} {size}.')

        r = self.controller.run_as_user([
            '/usr/bin/gsettings', 'set', f'{schema}',
            'font-name', f'"{temp_font} {size}"'
        ])
        if r.returncode != 0:
            logging.debug(f'Failed to change font to {temp_font} {size}')
            return

        self._did_change_font = True

        # Touch a file to indiate that the font should be restored on the next
        # boot.
        need_font_restore_file = os.path.join(
            self.controller.get_user_home(),
            '.config/upgrade-need-font-restore'
        )
        os.makedirs(os.path.dirname(need_font_restore_file), exist_ok=True)
        pathlib.Path(need_font_restore_file).touch(mode=0o666)
        os.chown(
            need_font_restore_file,
            self.controller.get_user_uid(),
            self.controller.get_user_gid(),
        )

        if use_autostart:
            autostart_file = '/etc/xdg/autostart/upgrade-restore-font.desktop'
            os.makedirs(os.path.dirname(autostart_file), exist_ok=True)
            flag = '$HOME/.config/upgrade-need-font-restore'
            with open(autostart_file, 'w') as f:
                f.write(
                    '[Desktop Entry]\n'
                    'Name=Restore font after upgrade\n'
                    'Comment=Auto-generated by ubuntu-release-upgrader\n'
                    'Type=Application\n'
                    f'Exec=sh -c \'if [ -e "{flag}" ]; then gsettings set '
                    f'{schema} font-name "{font} {size}";'
                    f'rm -f "{flag}"; fi\'\n'
                    'NoDisplay=true\n'
                )
            return

        # If we set the font back to normal before a reboot, the font will
        # still get all messed up. To allow normal usage whether the user
        # reboots immediately or not, create a service that will run only if a
        # ~/.config/upgrade-need-font-restore exists, and then remove that file
        # in ExecStart. This has the effect of creating a one-time service on
        # the next boot.
        unit_file = '/usr/lib/systemd/user/upgrade-restore-font.service'
        os.makedirs(os.path.dirname(unit_file), exist_ok=True)

        with open(unit_file, 'w') as f:
            f.write(
                '# Auto-generated by ubuntu-release-upgrader\n'
                '[Unit]\n'
                'Description=Restore font after upgrade\n'
                'After=graphical-session.target dconf.service\n'
                'ConditionPathExists=%h/.config/upgrade-need-font-restore\n'
                '\n'
                '[Service]\n'
                'Type=oneshot\n'
                'ExecStart=/usr/bin/gsettings set '
                f'{schema} font-name \'{font} {size}\'\n'
                'ExecStart=/usr/bin/rm -f '
                '%h/.config/upgrade-need-font-restore\n'
                '\n'
                '[Install]\n'
                'WantedBy=graphical-session.target\n'
            )

        self.controller.systemctl_as_user(['daemon-reload'])
        r = self.controller.systemctl_as_user(
            ['enable', os.path.basename(unit_file)]
        )

        if r.returncode != 0:
            logging.debug(f'Failed to enable {os.path.basename(unit_file)}. '
                          'Font will not be restored on reboot')

    def _maybe_remove_gpg_wks_server(self):
        """
        Prevent postfix from being unnecessarily installed, and leading to a
        debconf prompt (LP: #2060578).
        """
        # We want to use attributes of the cache that are only exposed in
        # apt_pkg.Cache, not the higher level apt.Cache. Hence we operate on
        # apt.Cache._cache.
        cache = self.controller.cache._cache

        try:
            if not cache['gpg-wks-server'].current_ver:
                # Not installed, nothing to do.
                return

            provides_mta = cache['mail-transport-agent'].provides_list
            installed_mta = [
                ver for _, _, ver in provides_mta
                if ver.parent_pkg.current_ver
            ]
        except KeyError:
            # Something wasn't in the cache, ignore.
            return

        if not any(installed_mta):
            logging.info(
                'No mail-transport-agent installed, '
                'marking gpg-wks-server for removal'
            )

            self.controller.cache['gpg-wks-server'].mark_delete(auto_fix=False)
            apt.ProblemResolver(self.controller.cache).protect(
                self.controller.cache['gpg-wks-server']
            )

    def _test_and_fail_on_rva23(self):
        """
        With release Ubuntu 25.10 we have raised the ISA profile requirement
        on RISC-V to RVA23U64. Prevent systems that don't implement RVA23U64
        from upgrading beyond Ubuntu 24.04 LTS.
        """

        di = distro_info.UbuntuDistroInfo()
        version = di.version(self.controller.toDist) or 'next release'

        try:
            cpuinfo = RiscvProfile.read_cpuinfo()
        except RiscvProfileException as ex:
            # Either /proc/cpuinfo cannot be read or this not a RISC-V system
            logging.debug(f'RVA23 check: {ex}')
            return

        try:
            cpuinfo.assert_rva23_ready()
            return
        except RiscvProfileException as ex:
            logging.error(f'RVA23 check: {ex}')
            self._view.error(
                _(
                    f'Sorry, cannot upgrade this system to {version}'
                ),
                _(
                    'On Ubuntu 25.10 and later, RISC-V systems are required '
                    'to support the RVA23U64 profile, but your system does '
                    'not. Please, see https://discourse.ubuntu.com/t/'
                    'questing-quokka-release-notes for more information.'
                ),
            )
            self.controller.abort()

    def _test_and_fail_on_z13(self):
        """
        With release Ubuntu 26.04 we have raised the ISA generation
        requirement on s390x to z15. Prevent systems that are below z15
        from upgrading beyond Ubuntu 25.10.
        """

        if self.controller.arch != 's390x':
            return

        generation: S390xGeneration | None = get_system_s390x_generation()
        if generation is None:
            logging.debug(
                's390x generation check: cannot determine generation'
            )
            return

        if generation >= S390xGeneration.Z15:
            logging.debug(
                's390x generation check: generation is z15 or newer'
            )
            return

        self._view.error(
            _(
                'Sorry, cannot upgrade this system to Ubuntu 26.04 LTS'
            ),
            _(
                'On Ubuntu 26.04 and later, s390x systems are required '
                'to be z15 or newer, but your system is not. Please, '
                'see https://discourse.ubuntu.com/t/'
                'resolute-raccoon-release-notes for more information.'
            ),
        )
        self.controller.abort()

    def _test_and_fail_on_pi_old_eeprom(self, dt_dir='/proc/device-tree'):
        """
        Ubuntu 26.04 has minimum EEPROM requirements, partly for the "tryboot"
        facility of the bootloader (for the Pi 4) and partly for kernel version
        7 compatibility (for the Pi 5).

        LP: #2130734
        LP: #2146383
        """
        if self.controller.arch not in ('armhf', 'arm64'):
            return

        # Are we running on a Raspberry Pi 4/400/CM4? Check the NUL-separated
        # strings in /proc/device-tree/compatible for any beginning with
        # "raspberrypi," and "brcm,brcm2711" (latter indicates 4 series)
        dt = pathlib.Path(dt_dir)
        try:
            compatible = set((
                dt / 'compatible').read_bytes().rstrip(b'\0').split(b'\0'))
        except FileNotFoundError:
            return
        else:
            if not any(s.startswith(b'raspberrypi,') for s in compatible):
                return
            if b'brcm,bcm2711' in compatible:  # Pi 4
                minimum_built, bug = 1669373653, 2130734
            elif b'brcm,bcm2712' in compatible:  # Pi 5
                minimum_built, bug = 1739293519, 2146383
            else:
                return
            minimum_dt = datetime.fromtimestamp(minimum_built, tz=timezone.utc)

        # Check the bootloader build timestamp; this does not exist on *really*
        # ancient bootloaders, so take non-existence as failure too
        import struct
        try:
            timestamp_node = (dt / 'chosen' / 'bootloader' / 'build-timestamp')
            built = struct.unpack('>I', timestamp_node.read_bytes())[0]
        except FileNotFoundError:
            pass
        else:
            if built >= minimum_built:
                return

        self._view.error(
            _(
                'Newer Raspberry Pi boot EEPROM required'
            ),
            _(
                'For Ubuntu 26.04, this Raspberry Pi requires the boot '
                'EEPROM to be dated at least {minimum_dt:%c %Z} or later. '
                'If you wish to proceed with the upgrade, once this '
                'upgrader exits, run "sudo rpi-eeprom-update -a" and '
                'reboot. Afterwards, you should be able to proceed with '
                'this upgrade. Please see '
                'https://launchpad.net/bugs/{bug} for more information.'
            ).format(minimum_dt=minimum_dt, bug=bug),
        )
        self.controller.abort()

    def _test_and_fail_on_tpm_fde(self):
        """
        LP: #2065229
        """
        if (
            os.path.exists('/snap/pc-kernel') and
            'ubuntu-desktop-minimal' in self.controller.cache and
            self.controller.cache['ubuntu-desktop-minimal'].is_installed
        ):
            logging.debug('Detected TPM FDE system')

            di = distro_info.UbuntuDistroInfo()
            version = di.version(self.controller.toDist) or 'next release'

            self._view.error(
                _(
                    f'Sorry, cannot upgrade this system to {version}'
                ),
                _(
                    'Upgrades for desktop systems running TPM FDE are not '
                    'currently supported. '
                    'Please see https://launchpad.net/bugs/2065229 '
                    'for more information.'
                ),
            )
            self.controller.abort()

    def _disable_kdump_tools_on_install(self, cache):
        """Disable kdump-tools if installed during upgrade."""
        if 'kdump-tools' not in cache:
            # Not installed or requested, nothing to do.
            return

        pkg = cache['kdump-tools']

        if pkg.is_installed:
            logging.info("kdump-tools already installed. Not disabling.")
            return
        elif pkg.marked_install:
            logging.info("installing kdump-tools due to upgrade. Disabling.")
            proc = subprocess.run(
                (
                    'echo "kdump-tools kdump-tools/use_kdump boolean false"'
                    ' | debconf-set-selections'
                ),
                shell=True,
            )
            ret_code = proc.returncode
            if ret_code != 0:
                logging.debug(
                    (
                         "kdump-tools debconf-set-selections "
                         f"returned: {ret_code}"
                    )
                )

    def _install_linux_sysctl_defaults(self):
        """ LP: #2089759 """

        if self.controller.fromDist != 'oracular':
            return

        if (
            'linux-sysctl-defaults' in self.controller.cache and
            not self.controller.cache['linux-sysctl-defaults'].is_installed
        ):
            logging.debug('Installing linux-sysctl-defaults')

            self.controller.cache['linux-sysctl-defaults'].mark_install(
                auto_fix=False
            )

    def _switch_to_systemd_coredump_for_kde_flavors(self):
        """
        For Kubuntu and Ubuntu Studio, switch from apport-core-dump-handler
        to systemd-coredump. These flavors use DrKonqi for crash handling
        which requires systemd-coredump.
        """
        cache = self.controller.cache

        # Check if this is a Kubuntu or Ubuntu Studio system
        kde_flavor_pkgs = (
            'kubuntu-desktop',
            'ubuntustudio-desktop-core',
        )
        meta_pkg = None
        for pkg in kde_flavor_pkgs:
            if pkg in cache and cache[pkg].is_installed:
                meta_pkg = pkg
                break

        if meta_pkg is None:
            return

        logging.debug(
            'KDE flavor detected (%s), switching to systemd-coredump',
            meta_pkg,
        )

        # Remove apport-core-dump-handler if installed
        if (
            'apport-core-dump-handler' in cache and
            cache['apport-core-dump-handler'].is_installed
        ):
            logging.debug('Marking apport-core-dump-handler for removal')
            cache['apport-core-dump-handler'].mark_delete(auto_fix=False)

        # Install systemd-coredump
        if (
            'systemd-coredump' in cache and
            not cache['systemd-coredump'].is_installed
        ):
            logging.debug('Marking systemd-coredump for installation')
            cache['systemd-coredump'].mark_install(auto_fix=False)

        # Ensure the KDE metapackage is marked for upgrade, since the
        # resolver may have held it back due to the coredump conflict
        if not cache[meta_pkg].marked_upgrade:
            logging.debug(
                'Re-marking %s for upgrade after coredump switch', meta_pkg
            )
            cache[meta_pkg].mark_upgrade()

    def _test_and_fail_without_cgroupv2(self):
        """
        Starting in 26.04 LTS, systemd requires cgroupv2 unified hierarchy,
        and will refuse to start under other configurations which were
        previously allowed.
        """
        with open('/proc/mounts') as f:
            mounts = f.readlines()

        for line in mounts:
            try:
                (what, where, fs, opts, a, b) = line.strip().split()
            except ValueError:
                logging.warning(
                    f'could not parse {line} from /proc/mounts, ignoring'
                )
                continue

            if (fs, where) == ('cgroup2', '/sys/fs/cgroup'):
                # We have unified cgroupv2 hierarchy, good.
                return

        # We did not find a unified cgroupv2 hierarchy, refuse to upgrade.
        self._view.error(
            _(
                'Cannot upgrade without unified cgroupv2 hierarchy'
            ),
            _(
                'Beginning with Ubuntu 26.04 LTS, it is required that the '
                'system is booted with a unified cgroupv2 hierarchy, but '
                'this system is not.\n\nSee '
                'https://discourse.ubuntu.com/t/resolute-raccoon-release-notes'
                ' for more information.'
            )
        )
        self.controller.abort()

    def _test_and_fail_rabbitmq_server_installed_and_not_upgradable(self):
        """
        RabbitMQ can only be upgraded to 4.X (the version in resolute) if a set
        of feature flags is enabled.
        """
        import json

        if self.controller.toDist != "resolute":
            return

        if not (
            'rabbitmq-server' in self.controller.cache and
            self.controller.cache['rabbitmq-server'].is_installed
        ):
            return

        try:
            result = subprocess.run(
                [
                    '/usr/sbin/rabbitmqctl',
                    '--formatter',
                    'json',
                    'list_feature_flags',
                ],
                check=True,
                timeout=30,
                stdout=subprocess.PIPE,
            )
            raw_flags = json.loads(result.stdout.decode('utf-8'))
        except (
            OSError,
            subprocess.SubprocessError,
            UnicodeDecodeError,
            json.JSONDecodeError
        ):
            logging.exception('Failed to query RabbitMQ feature flags')
            summary = _('Unable to upgrade RabbitMQ')
            message = _(
                'The RabbitMQ feature flags could not be detected.\n\n'
                'Please follow the instructions at '
                'https://discourse.ubuntu.com/t/77271 to prepare RabbitMQ '
                'for the upgrade, then retry.'
            )
            self._view.error(summary, message)
            self.controller.abort()

        feature_flags = {
            flag['name']: (flag['state'] == 'enabled')
            for flag in raw_flags
        }
        enabled_flags = {
            flag
            for flag, enabled in feature_flags.items()
            if enabled
        }

        # List of feature flags that must be enabled in order to upgrade to 4.0
        # https://www.rabbitmq.com/docs/feature-flags#list-of-feature-flags
        core_required_flags = {
            'stream_filtering',
            'stream_update_config_command',
            'restart_streams',
            'stream_sac_coordinator_unblock_group',
        }

        # Extra feature flags needed if the mqtt plugin is used.
        mqtt_required_flags = {
            'mqtt_v5',
            'delete_ra_cluster_mqtt_node',
            'rabbit_mqtt_qos0_queue',
        }
        has_mqtt = bool(mqtt_required_flags & feature_flags.keys())

        if (
            (not core_required_flags.issubset(enabled_flags)) or
            (has_mqtt and not mqtt_required_flags.issubset(enabled_flags))
        ):
            summary = _('Unable to upgrade RabbitMQ')
            message = _(
                'Your RabbitMQ server installation requires manual '
                'preparation before it can be upgraded to the newer '
                'version.\n\n Please follow the instructions at '
                'https://discourse.ubuntu.com/t/77271 to prepare RabbitMQ '
                'for the upgrade, then retry.'
            )
            self._view.error(summary, message)
            self.controller.abort()
