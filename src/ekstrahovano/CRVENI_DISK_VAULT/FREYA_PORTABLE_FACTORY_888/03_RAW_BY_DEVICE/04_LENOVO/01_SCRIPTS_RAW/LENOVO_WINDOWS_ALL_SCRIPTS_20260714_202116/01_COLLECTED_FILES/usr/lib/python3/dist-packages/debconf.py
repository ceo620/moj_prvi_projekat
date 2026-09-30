# Copyright:
#   Moshe Zadka (c) 2002
#   Canonical Ltd. (c) 2005 (DebconfCommunicator)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY AUTHORS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from __future__ import annotations

import errno
import fcntl
import os
import re
import subprocess
import sys
from types import TracebackType
from typing import IO, Protocol


class Command(Protocol):
    def __call__(self, *params: str | int) -> str: ...


class DebconfError(Exception):
    pass


LOW, MEDIUM, HIGH, CRITICAL = "low", "medium", "high", "critical"


class Debconf:
    """A class that speaks the debconf protocol.

    The simplest way to use this is as a context manager:

        import debconf

        with debconf.Debconf(run_frontend=True) as db:
            print(db.get('debconf/frontend'))

    Note that this will send the STOP command on exiting the context
    manager, so you shouldn't expect to be able to use the same frontend
    again after this.  If you need to do that, then you should instantiate
    the class directly instead:

        import debconf

        db = debconf.Debconf(run_frontend=True)
        print(db.get('debconf/frontend'))
    """

    beginblock: Command
    capb: Command
    endblock: Command
    exist: Command
    fset: Command
    get: Command
    go: Command
    info: Command
    input: Command
    progress: Command
    purge: Command
    register: Command
    reset: Command
    set: Command
    settitle: Command
    subst: Command
    title: Command
    unregister: Command
    version_: Command
    visible: Command

    def __init__(
        self,
        title: str | None = None,
        read: IO[str] | None = None,
        write: IO[str] | None = None,
        run_frontend: bool = False,
    ) -> None:
        for command in (
            "capb set reset title input beginblock endblock go get"
            " register unregister subst fset fget"
            " visible purge metaget exist version_ settitle"
            " info progress data"
        ).split():
            self.setCommand(command)
        self.read = read or sys.stdin
        self.write = write or sys.stdout
        sys.stdout = sys.stderr
        if run_frontend:
            runFrontEnd()
        self.setUp(title)

    def setUp(self, title: str | None) -> None:
        self.version = self.version_(2)
        if self.version[:2] != "2.":
            raise DebconfError(256, "wrong version: %s" % self.version)
        self.capabilities = self.capb().split()
        if title:
            self.title(title)

    def setCommand(self, command: str) -> None:
        setattr(
            self,
            command,
            lambda *args, **kw: self.command(command, *args, **kw),
        )

    def command(self, command: str, *params: str | int) -> str:
        if command == "version_":
            command = "version"
        command = command.upper()
        self.write.write("{} {}\n".format(command, " ".join(map(str, params))))
        self.write.flush()

        while True:
            try:
                resp = self.read.readline().rstrip("\n")
                break
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise

        if " " in resp:
            status_, data = resp.split(" ", 1)
        else:
            status_, data = resp, ""
        status = int(status_)
        if status == 0:
            return data
        elif status == 1:  # unescaped data
            unescaped = ""
            for chunk in re.split(r"(\\.)", data):
                if chunk.startswith("\\") and len(chunk) == 2:
                    if chunk[1] == "n":
                        unescaped += "\n"
                    else:
                        unescaped += chunk[1]
                else:
                    unescaped += chunk
            return unescaped
        else:
            raise DebconfError(status, data)

    def stop(self) -> None:
        self.write.write("STOP\n")
        self.write.flush()

    def forceInput(self, priority: str, question: str) -> int:
        try:
            self.input(priority, question)
            return 1
        except DebconfError as e:
            if e.args[0] != 30:
                raise
        return 0

    def getBoolean(self, question: str) -> bool:
        result = self.get(question)
        return result == "true"

    def getString(self, question: str) -> str:
        return self.get(question)

    def __enter__(self) -> Debconf:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()


class DebconfCommunicator(Debconf):
    def __init__(
        self, owner: str, title: str | None = None, cloexec: bool = False
    ) -> None:
        args = ["debconf-communicate", "-fnoninteractive", owner]
        self.dccomm: subprocess.Popen[str] | None = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            close_fds=True,
            universal_newlines=True,
        )
        super().__init__(
            title=title, read=self.dccomm.stdout, write=self.dccomm.stdin
        )
        if cloexec:
            fcntl.fcntl(self.read.fileno(), fcntl.F_SETFD, fcntl.FD_CLOEXEC)
            fcntl.fcntl(self.write.fileno(), fcntl.F_SETFD, fcntl.FD_CLOEXEC)

    def shutdown(self) -> None:
        if self.dccomm is not None:
            assert self.dccomm.stdin is not None
            assert self.dccomm.stdout is not None
            self.dccomm.stdin.close()
            self.dccomm.stdout.close()
            self.dccomm.wait()
            self.dccomm = None

    # Don't rely on this; call .shutdown() explicitly.
    def __del__(self) -> None:
        try:
            self.shutdown()
        except AttributeError:
            pass


if (
    "DEBCONF_USE_CDEBCONF" in os.environ
    and os.environ["DEBCONF_USE_CDEBCONF"] != ""
):
    _frontEndProgram = "/usr/lib/cdebconf/debconf"
else:
    _frontEndProgram = "/usr/share/debconf/frontend"


def runFrontEnd(*, pass_sys_executable: bool = False) -> None:
    if "DEBIAN_HAS_FRONTEND" not in os.environ:
        os.environ["PERL_DL_NONLAZY"] = "1"
        args = [_frontEndProgram]
        if pass_sys_executable:
            args.append(sys.executable)
        args.extend(sys.argv)
        os.execv(_frontEndProgram, args)


if __name__ == "__main__":
    runFrontEnd(pass_sys_executable=True)
    db = Debconf()
    db.forceInput(CRITICAL, "bsdmainutils/calendar_lib_is_not_empty")
    db.go()
    less = db.getBoolean("less/add_mime_handler")
    aptlc = db.getString("apt-listchanges/email-address")
    db.stop()
    print(db.version)
    print(db.capabilities)
    print(less)
    print(aptlc)
