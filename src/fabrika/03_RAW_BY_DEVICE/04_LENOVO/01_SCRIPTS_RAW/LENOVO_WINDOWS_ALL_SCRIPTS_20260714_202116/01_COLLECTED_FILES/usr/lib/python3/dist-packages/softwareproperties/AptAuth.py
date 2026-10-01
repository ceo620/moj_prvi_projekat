# dialog_apt_key.py.in - edit the apt keys
#
#  Copyright (c) 2004 Canonical
#
#  Author: Michael Vogt <mvo@debian.org>
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

import gettext
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from subprocess import PIPE

# gettext convenient
_ = gettext.gettext
N_ = lambda e: e

# some known keys
N_("Ubuntu Archive Automatic Signing Key <ftpmaster@ubuntu.com>")
N_("Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>")
N_("Ubuntu Archive Automatic Signing Key (2012) <ftpmaster@ubuntu.com>")
N_("Ubuntu CD Image Automatic Signing Key (2012) <cdimage@ubuntu.com>")
N_("Ubuntu Extras Archive Automatic Signing Key <ftpmaster@ubuntu.com>")
PARTS=pathlib.Path("etc/apt/trusted.gpg.d")

class AptAuth:

    def __init__(self, rootdir="/"):
        self.rootdir = pathlib.Path(rootdir)

    def run_gpg(self, *args):
        return subprocess.run(["gpg",
                               "--homedir", self.home,
                               "--no-options",
                               "--no-default-keyring",
                               "--no-auto-check-trustdb",
                               "--trust-model", "always",
                               "--with-colons",
                               "--batch",
                               "--fixed-list-mode",
                               ] + list(args), stdout=PIPE, text=True)

    def list(self):
        res = []
        for filename in os.listdir(self.rootdir / PARTS):
            if not any(filename.endswith(x) for x in (".asc", ".gpg")):
                continue
            filepath = self.rootdir / PARTS / filename
            try:
                process = subprocess.run(["sq", "--cert-store=none", "--key-store=none",
                                          "keyring", "list", str(filepath)], stdout=PIPE, text=True)
                res.append("%s\n  %s" % (filepath, "\n  ".join(process.stdout.strip().split("\n"))))
            except OSError:
                # We can only hope and pray gpg spawns no daemons that take over the home dir
                with tempfile.TemporaryDirectory() as self.home:
                    keyring = filepath
                    if keyring.suffix == ".asc":
                        keyring = pathlib.Path(self.home) / "dearmored-key.gpg"
                        self.run_gpg("-o", keyring, "--dearmor", filepath)
                    process = self.run_gpg("--keyring", keyring, "--list-keys")
                lines = []
                for line in process.stdout.splitlines():
                    fields = line.split(":")
                    if fields[0] == "fpr":
                        fpr = fields[9]
                    if fields[0] == "uid":
                        uid = fields[9]

                        lines.append(f"{fpr} {uid}")
                res.append("%s\n  %s" % (filepath, "\n  ".join(lines)))

        return res

    def add(self, filename):
        out = self.rootdir / PARTS / os.path.basename(filename)
        print("Add", filename, out, file=sys.stderr)
        if not os.path.exists(out):
            print("Copy", filename, out, file=sys.stderr)
            try:
                shutil.copyfile(filename, out)
            except Exception as e:
                print(e)
            return True
        return False

    def rm(self, key):
        print("Removing", key)
        try:
            os.unlink(key)
        except OSError:
            return True
