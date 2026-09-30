# DistUpgradeFetcherCore.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2006 Canonical
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

import os
import apt_pkg
import logging
import tarfile
import tempfile
import shutil
import socket
import sys
import subprocess
from gettext import gettext as _
from urllib.request import urlopen
from urllib.error import HTTPError

from .utils import get_dist
from .DistUpgradeViewText import readline


class DistUpgradeFetcherCore(object):
    " base class (without GUI) for the upgrade fetcher "

    DEFAULT_MIRROR = "http://archive.ubuntu.com/ubuntu"
    DEFAULT_COMPONENT = "main"
    DEBUG = "DEBUG_UPDATE_MANAGER" in os.environ

    def __init__(self, new_dist, progress):
        self.new_dist = new_dist
        self.current_dist_name = get_dist()
        self._progress = progress
        # options to pass to the release upgrader when it is run
        self.run_options = []

    def _debug(self, msg):
        " helper to show debug information "
        if self.DEBUG:
            sys.stderr.write(msg + "\n")

    def showReleaseNotes(self):
        if '--frontend=DistUpgradeViewNonInteractive' in self.run_options:
            return True
        if self.new_dist.releaseNotesURI is not None:
            uri = self.new_dist.releaseNotesURI
            timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(5)
                release_notes = urlopen(uri)
                notes = release_notes.read().decode("UTF-8", "replace")
            except HTTPError:
                self.error(_("Could not find the release announcement"),
                           _("The server may be overloaded."))
                return False
            except IOError:
                self.error(_("Could not download the release announcement"),
                           _("Please check your internet connection."))
                return False
            socket.setdefaulttimeout(timeout)
        print()
        print(notes)
        print(_("Continue [yN] "), end="")
        res = readline()
        if res.strip().lower().startswith(_("y")):
            return True
        return False

    def error(self, summary, message):
        """ minimal implementation for error display, should be overwriten
            by subclasses that want to more fancy method
        """
        print(summary)
        print(message)
        return False

    def authenticate(self):
        if self.new_dist.upgradeToolSig:
            f = self.tmpdir + "/" + os.path.basename(self.new_dist.upgradeTool)
            sig = self.tmpdir + "/" + os.path.basename(
                self.new_dist.upgradeToolSig)
            print(_("authenticate '%(file)s' against '%(signature)s' ") % {
                'file': os.path.basename(f),
                'signature': os.path.basename(sig)})
            if self.gpgauthenticate(f, sig):
                return True
        return False

    def gpgauthenticate(self, file, signature):
        """ authenticate a file against a given signature """
        gpg = [
            '/usr/bin/gpgv',
            '--keyring', '/usr/share/keyrings/ubuntu-archive-keyring.gpg',
            signature,
            file,
        ]

        ret = subprocess.call(gpg, stderr=subprocess.PIPE)
        return ret == 0

    def extractDistUpgrader(self):
        # extract the tarball
        fname = os.path.join(self.tmpdir, os.path.basename(self.uri))
        print(_("extracting '%s'") % os.path.basename(fname))
        if not os.path.exists(fname):
            return False
        try:
            tar = tarfile.open(self.tmpdir + "/" +
                               os.path.basename(self.uri), "r")
            for tarinfo in tar:
                tar.extract(tarinfo)
            tar.close()
        except tarfile.ReadError as e:
            logging.error("failed to open tarfile (%s)" % e)
            return False
        return True

    def verifyDistUpgrader(self):
        # FIXME: check an internal dependency file to make sure
        #        that the script will run correctly

        # see if we have a script file that we can run
        self.script = script = "%s/%s" % (self.tmpdir, self.new_dist.name)
        if not os.path.exists(script):
            return self.error(_("Could not run the upgrade tool"),
                              _("Could not run the upgrade tool") + ".  " +
                              _("This is most likely a bug in the upgrade "
                                "tool. Please report it as a bug using the "
                                "command 'ubuntu-bug "
                                "ubuntu-release-upgrader-core'."))
        return True

    def fetchDistUpgrader(self):
        " download the tarball with the upgrade script "
        tmpdir = tempfile.mkdtemp(prefix="ubuntu-release-upgrader-")
        self.tmpdir = tmpdir
        os.chdir(tmpdir)
        logging.debug("using tmpdir: '%s'" % tmpdir)
        # turn debugging on here (if required)
        if self.DEBUG > 0:
            apt_pkg.config.set("Debug::Acquire::http", "1")
            apt_pkg.config.set("Debug::Acquire::ftp", "1")
        #os.listdir(tmpdir)
        fetcher = apt_pkg.Acquire(self._progress)
        if self.new_dist.upgradeToolSig is not None:
            uri = self.new_dist.upgradeToolSig
            af1 = apt_pkg.AcquireFile(fetcher,
                                      uri,
                                      descr=_("Upgrade tool signature"))
            # reference it here to shut pyflakes up
            af1
        if self.new_dist.upgradeTool is not None:
            self.uri = self.new_dist.upgradeTool
            af2 = apt_pkg.AcquireFile(fetcher,
                                      self.uri,
                                      descr=_("Upgrade tool"))
            # reference it here to shut pyflakes up
            af2
            result = fetcher.run()
            if result != fetcher.RESULT_CONTINUE:
                logging.warning("fetch result != continue (%s)" % result)
                return False
            # check that both files are really there and non-null
            for f in [os.path.basename(self.new_dist.upgradeToolSig),
                      os.path.basename(self.new_dist.upgradeTool)]:
                if not (os.path.exists(f) and os.path.getsize(f) > 0):
                    logging.warning("file '%s' missing" % f)
                    return False
            return True
        return False

    def runDistUpgrader(self):
        args = [self.script] + self.run_options
        if os.getuid() != 0:
            os.execv("/usr/bin/sudo", ["sudo", "-E"] + args)
        else:
            os.execv(self.script, args)

    def cleanup(self):
        # cleanup
        os.chdir("..")
        # del tmpdir
        shutil.rmtree(self.tmpdir)

    def run(self):
        # see if we have release notes
        if not self.showReleaseNotes():
            return
        if not self.fetchDistUpgrader():
            self.error(_("Failed to fetch"),
                       _("Fetching the upgrade failed. There may be a network "
                         "problem. "))
            return
        if not self.authenticate():
            self.error(_("Authentication failed"),
                       _("Authenticating the upgrade failed. There may be a "
                         "problem with the network or with the server. "))
            self.cleanup()
            return
        if not self.extractDistUpgrader():
            self.error(_("Failed to extract"),
                       _("Extracting the upgrade failed. There may be a "
                         "problem with the network or with the server. "))

            return
        if not self.verifyDistUpgrader():
            self.error(_("Verification failed"),
                       _("Verifying the upgrade failed.  There may be a "
                         "problem with the network or with the server. "))
            self.cleanup()
            return
        try:
            # check if we can execute, if we run it via sudo we will
            # not know otherwise, pkexec will not raise a exception
            if not os.access(self.script, os.X_OK):
                ex = OSError("Can not execute '%s'" % self.script)
                ex.errno = 13
                raise ex
            self.runDistUpgrader()
        except OSError as e:
            if e.errno == 13:
                self.error(_("Can not run the upgrade"),
                           _("This usually is caused by a system where /tmp "
                             "is mounted noexec. Please remount without "
                             "noexec and run the upgrade again."))
                return False
            else:
                self.error(_("Can not run the upgrade"),
                           _("The error message is '%s'.") % e.strerror)
        return True
