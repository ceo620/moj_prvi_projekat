# QUrlOpener.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2014-2018 Harald Sitter <apachelogger@kubuntu.org>
#  Copyright (c) 2024 Simon Quigley <tsimonq2@ubuntu.com>
#  Copyright (c) 2026 Erich Eickmeyer <eeickmeyer@ubuntu.com>
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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .PyQtCompat import (
    QObject, QCoreApplication, pyqtSlot, QUrl, QDesktopServices,
)

import os
import subprocess


def singleton(class_):
    instances = {}

    def instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return instance


@singleton
class QUrlOpener(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.setParent(QCoreApplication.instance())

    def setupUrlHandles(self):
        # Make sure we don't run a root browser.
        # NOTE: Qt native API can set an openUrl handler from a QObject
        # function, pyqt in theory also allows an arbitrary callable. Latter
        # has been observed to be non-functional so rely on the native handling
        QDesktopServices.setUrlHandler('http', self, 'openUrl')
        QDesktopServices.setUrlHandler('https', self, 'openUrl')

    def teardownUrlHandles(self):
        # Unset the URL handlers to avoid the warning
        QDesktopServices.unsetUrlHandler('http')
        QDesktopServices.unsetUrlHandler('https')

    # NOTE: largely code copy from ReleaseNotesViewer which imports GTK.
    @pyqtSlot(QUrl)
    def openUrl(self, url):
        url = url.toString()
        """Open the specified URL in a browser"""
        # Find an appropiate browser
        if os.path.exists("/usr/bin/xdg-open"):
            command = ["xdg-open", url]
        elif os.path.exists("/usr/bin/kde-open"):
            command = ["kde-open", url]
        elif os.path.exists("/usr/bin/exo-open"):
            command = ["exo-open", url]
        elif os.path.exists('/usr/bin/gnome-open'):
            command = ['gnome-open', url]
        else:
            command = ['x-www-browser', url]
        # Avoid to run the browser as user root
        if os.getuid() == 0 and 'SUDO_USER' in os.environ:
            command = ['sudo',
                       '--set-home',
                       '-u', os.environ['SUDO_USER']] + command
        subprocess.Popen(command)
