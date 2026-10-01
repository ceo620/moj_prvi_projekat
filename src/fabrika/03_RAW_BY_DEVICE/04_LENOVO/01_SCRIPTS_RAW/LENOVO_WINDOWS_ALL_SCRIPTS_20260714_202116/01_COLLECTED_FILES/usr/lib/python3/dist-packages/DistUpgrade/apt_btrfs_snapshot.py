# Copyright (C) 2011 Canonical
#
# Author:
#  Michael Vogt
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from __future__ import print_function, unicode_literals

import apt_pkg
import collections
import datetime
import itertools
import os
import subprocess
import sys
import time

from distutils.spawn import find_executable

from gettext import gettext as _


class AptBtrfsSnapshotError(Exception):
    pass


class AptBtrfsNotSupportedError(AptBtrfsSnapshotError):
    pass


class AptBtrfsRootWithNoatimeError(AptBtrfsSnapshotError):
    pass


class FstabEntry(object):
    """ a single fstab entry line """
    @classmethod
    def from_line(cls, line):
        # split up
        args = line.partition("#")[0].split()
        # use only the first 7 args and ignore anything after them, mount
        # seems to do the same, see bug #873411 comment #7
        return FstabEntry(*args[0:6])

    def __init__(self, fs_spec, mountpoint, fstype, options, dump=0, passno=0):
        # uuid or device
        self.fs_spec = fs_spec
        self.mountpoint = mountpoint
        self.fstype = fstype
        self.options = options
        self.dump = dump
        self.passno = passno

    def __repr__(self):
        return "<FstabEntry '%s' '%s' '%s' '%s' '%s' '%s'>" % (
            self.fs_spec, self.mountpoint, self.fstype,
            self.options, self.dump, self.passno)


class Fstab(list):
    """ a list of FstabEntry items """
    def __init__(self, fstab="/etc/fstab"):
        super(Fstab, self).__init__()

        with open(fstab) as fstab_file:
            for stripped_line in (line.strip() for line in fstab_file):
                if stripped_line == "" or stripped_line.startswith("#"):
                    continue
                try:
                    entry = FstabEntry.from_line(stripped_line)
                except ValueError:
                    continue
                self.append(entry)


class LowLevelCommands(object):
    """ lowlevel commands invoked to perform various tasks like
        interact with mount and btrfs tools
    """
    def mount(self, fs_spec, mountpoint):
        ret = subprocess.call(["mount", fs_spec, mountpoint])
        return ret == 0

    def umount(self, mountpoint):
        ret = subprocess.call(["umount", mountpoint])
        return ret == 0

    def btrfs_subvolume_snapshot(self, source, dest):
        ret = subprocess.call(["btrfs", "subvolume", "snapshot",
                               source, dest])
        return ret == 0

    def btrfs_delete_snapshot(self, snapshot):
        ret = subprocess.call(["btrfs", "subvolume", "delete", snapshot])
        return ret == 0


class AptBtrfsSnapshot(object):
    """ the high level object that interacts with the snapshot system """

    # normal snapshot
    SNAP_PREFIX = "@apt-snapshot-"
    # backname when changing
    BACKUP_PREFIX = SNAP_PREFIX + "old-root-"
    # Mount point to mount to
    MOUNTPOINT = "/run/apt-btrfs-snapshot/root"

    def __init__(self, fstab="/etc/fstab"):
        self.fstab = Fstab(fstab)
        self.commands = LowLevelCommands()
        self._btrfs_root_mountpoint = None
        self.mounted = None

    def snapshots_supported(self):
        """ verify that the system supports apt btrfs snapshots
            by checking if the right fs layout is used etc
        """
        if not (find_executable("btrfs")):
            return False
        # check the fstab
        entry = self._get_supported_btrfs_root_fstab_entry()
        return entry is not None

    def _get_supported_btrfs_root_fstab_entry(self):
        """ return the supported btrfs root FstabEntry or None """
        for entry in self.fstab:
            if (
                    entry.mountpoint == "/" and
                    entry.fstype == "btrfs" and
                    "subvol=@" in entry.options):
                return entry
        return None

    def _uuid_for_mountpoint(self, mountpoint, fstab="/etc/fstab"):
        """ return the device or UUID for the given mountpoint """
        for entry in self.fstab:
            if entry.mountpoint == mountpoint:
                return entry.fs_spec
        return None

    def __enter__(self):
        """ mount the mount point and return it (or None)"""
        if self.mounted:
            self.mounted += 1
            return self._btrfs_root_mountpoint
        uuid = self._uuid_for_mountpoint("/")
        os.makedirs(self.MOUNTPOINT, exist_ok=True)
        if not os.path.ismount(self.MOUNTPOINT):
            if not self.commands.mount(uuid, self.MOUNTPOINT):
                return None
        self.mounted = 1
        self._btrfs_root_mountpoint = self.MOUNTPOINT
        return self._btrfs_root_mountpoint

    def __exit__(self, *args):
        if not self.mounted:
            return
        self.mounted -= 1
        if self.mounted:
            return  # Nothing to do
        self.commands.umount(self._btrfs_root_mountpoint)
        os.rmdir(self._btrfs_root_mountpoint)
        self._btrfs_root_mountpoint = None

    def _get_now_str(self):
        return datetime.datetime.now().replace(microsecond=0).isoformat(
            str('_'))

    def create_btrfs_root_snapshot(self, additional_prefix="", prune=False):
        with self as mp:
            snap_id = self._get_now_str()
            source = os.path.join(mp, "@")
            target = os.path.join(mp, self.SNAP_PREFIX + additional_prefix +
                                  snap_id)

            if os.path.exists(target):
                print(_("INFO: snapshot directory '%s' already exists, "
                        "not creating duplicate") % (target,))
                return True
            else:
                res = self.commands.btrfs_subvolume_snapshot(source, target)
                if prune:
                    if apt_pkg.config.find_i("APT::Snapshots::MaxAge"):
                        print(_("INFO: Not pruning automatically as "
                                "APT::Snapshots::MaxAge is set, consider "
                                "using APT::Snapshots::Retain instead"))
                    else:
                        self.clean_btrfs_root_snapshots_by_policy()

                return res

    def get_btrfs_root_snapshots_list(self, older_than=0):
        """ get the list of available snapshot
            If "older_then" is given (in unixtime format) it will only include
            snapshots that are older then the given date)
        """
        result = []
        # if older_than is used, ensure that the rootfs does not use
        # "noatime"
        if older_than != 0:
            entry = self._get_supported_btrfs_root_fstab_entry()
            if not entry:
                raise AptBtrfsNotSupportedError()
            if "noatime" in entry.options:
                raise AptBtrfsRootWithNoatimeError()
        # if there is no older than, interpret that as "now"
        if older_than == 0:
            older_than = time.time()
        with self as mp:
            for e in os.listdir(mp):
                if e.startswith(self.SNAP_PREFIX):
                    # fstab is read when it was booted and when a snapshot is
                    # created (to check if there is support for btrfs)
                    atime = os.path.getatime(os.path.join(mp, e,
                                                          "etc", "fstab"))
                    if atime < older_than:
                        result.append(e)
        return result

    def print_btrfs_root_snapshots(self):
        print("Available snapshots:")
        print("  \n".join(self.get_btrfs_root_snapshots_list()))
        return True

    def _parse_older_than_to_unixtime(self, timefmt):
        now = time.time()
        if not timefmt.endswith("d"):
            raise Exception("Please specify time in days (e.g. 10d)")
        days = int(timefmt[:-1])
        return now - (days * 24 * 60 * 60)

    def print_btrfs_root_snapshots_older_than(self, timefmt):
        older_than_unixtime = self._parse_older_than_to_unixtime(timefmt)
        try:
            print("Available snapshots older than '%s':" % timefmt)
            print("  \n".join(self.get_btrfs_root_snapshots_list(
                older_than=older_than_unixtime)))
        except AptBtrfsRootWithNoatimeError:
            sys.stderr.write("Error: fstab option 'noatime' incompatible "
                             "with option")
            return False
        return True

    def clean_btrfs_root_snapshots_by_policy(self, verbose=False):
        keep = {
                "latest": ("%Y-%m-%d %H:%M:%S", 0),
                "minutely": ("%Y-%m-%d %H:%M:%S", 0),
                "hourly": ("%Y-%m-%d %H", 8),
                "daily": ("%Y-%m-%d", 7),
                "weekly": ("%Y-week%V", 2),
                "monthly": ("%Y-%m", 0),
                "yearly": ("%Y", 0),
        }

        snaps = []
        for snap in self.get_btrfs_root_snapshots_list():
            try:
                dt = datetime.datetime.strptime(snap,
                                                "@apt-snapshot-"
                                                "%Y-%m-%d_%H:%M:%S")
            except Exception:
                continue
            snaps.append((snap, dt))

        snaps.sort(key=lambda k: k[1], reverse=True)
        to_keep = collections.defaultdict(list)
        for name, (fmt, count) in keep.items():
            count = apt_pkg.config.find_i(f"APT::Snapshot::Retain::{name}",
                                          count)
            # Group our snapshots by periods and for each period,
            # keep the configured number of latest ones. We simply
            # format the time using the strftime expression that just
            # refers to the period.
            group_by_period = itertools.groupby(snaps,
                                                lambda k: k[1].strftime(fmt))

            # Iterate over the snapshots and see
            for index, (_group, items) in enumerate(group_by_period):
                if index >= count:
                    break
                try:
                    i = next(items)
                    to_keep[i].append(name)
                except StopIteration:
                    pass

        res = True
        for name, _dt in snaps:
            if (name, _dt) in to_keep:
                if verbose:
                    print("Keeping", "snapshot", name,
                          "due to", ", ".join(to_keep[(name, _dt)]))
            else:
                print("Deleting", "expired snapshot", name)
                res &= self.delete_snapshot(name)

        return res

    def clean_btrfs_root_snapshots_older_than(self, timefmt):
        res = True
        older_than_unixtime = self._parse_older_than_to_unixtime(timefmt)
        try:
            for snap in self.get_btrfs_root_snapshots_list(
                    older_than=older_than_unixtime):
                res &= self.delete_snapshot(snap)
        except AptBtrfsRootWithNoatimeError:
            sys.stderr.write("Error: fstab option 'noatime' incompatible with "
                             "option")
            return False
        return res

    def command_set_default(self, snapshot_name):
        res = self.set_default(snapshot_name)
        return res

    def set_default(self, snapshot_name, backup=True):
        """ set new default """
        with self as mp:
            new_root = os.path.join(mp, snapshot_name)
            if (
                    os.path.isdir(new_root) and
                    snapshot_name.startswith("@") and
                    snapshot_name != "@"):
                default_root = os.path.join(mp, "@")
                backup = os.path.join(mp, self.BACKUP_PREFIX
                                      + self._get_now_str())
                os.rename(default_root, backup)
                os.rename(new_root, default_root)
                print("Default changed to %s, please reboot for "
                      "changes to take effect." % snapshot_name)
            else:
                print("You have selected an invalid snapshot. "
                      "Please make sure that it exists, "
                      "and that it is not \"@\".")
        return True

    def delete_snapshot(self, snapshot_name):
        with self as mp:
            res = self.commands.btrfs_delete_snapshot(
                os.path.join(mp, snapshot_name))
        return res
