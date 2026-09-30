# DistUpgradeFetcherKDE.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2008 Canonical Ltd
#  Copyright (c) 2014-2018 Harald Sitter <sitter@kde.org>
#  Copyright (c) 2024 Simon Quigley <tsimonq2@ubuntu.com>
#  Copyright (c) 2026 Erich Eickmeyer <eeickmeyer@ubuntu.com>
#
#  Author: Jonathan Riddell <jriddell@ubuntu.com>
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
    uic, QTranslator, QLocale, QIcon,
    QDialog, QDialogButtonBox, QMessageBox, QApplication,
)

import apt_pkg

from DistUpgrade.DistUpgradeFetcherCore import DistUpgradeFetcherCore
from gettext import gettext as _
from urllib.request import urlopen
from urllib.error import HTTPError
import os

import apt

from .QUrlOpener import QUrlOpener


# TODO: uifile resolution is an utter mess and should be revised globally for
#       both the fetcher and the upgrader GUI.

# TODO: make this a singleton
# We have no globally constructed QApplication available so we need to
# make sure that one is created when needed. Since from a module POV
# this can be happening in any order of the two classes this function takes
# care of it for the classes, the classes only hold a ref to the qapp returned
# to prevent it from getting GC'd, so in essence this is a singleton scoped to
# the longest lifetime of an instance from the Qt GUI. Since the lifetime is
# pretty much equal to the process' one we might as well singleton up.
def _ensureQApplication():
    if not QApplication.instance():
        # Force environment to make sure Qt uses suitable theming and UX.
        os.environ["QT_PLATFORM_PLUGIN"] = "kde"
        # For above settings to apply automatically we need to indicate that we
        # are inside a full KDE session.
        os.environ["KDE_FULL_SESSION"] = "TRUE"
        # We also need to indicate version as otherwise KDElibs3 compatibility
        # might kick in such as in QIconLoader.cpp:QString fallbackTheme.
        os.environ["KDE_SESSION_VERSION"] = "6"
        # Pretty much all of the above but for Qt6
        os.environ["QT_QPA_PLATFORMTHEME"] = "kde"

        app = QApplication(["ubuntu-release-upgrader"])

        # Try to load default Qt translations so we don't have to worry about
        # QStandardButton translations.
        # FIXME: make sure we dep on l10n
        translator = QTranslator(app)
        translator.load(QLocale.system(), 'qt', '_',
                        '/usr/share/qt6/translations')
        app.installTranslator(translator)
        return app
    return QApplication.instance()


def _warning(text):
    QMessageBox.warning(None, "", text)


def _icon(name):
    return QIcon.fromTheme(name)


class DistUpgradeFetcherKDE(DistUpgradeFetcherCore):

    def __init__(self, new_dist, progress, parent, datadir):
        DistUpgradeFetcherCore.__init__(self, new_dist, progress)

        self.app = _ensureQApplication()
        self.app.setWindowIcon(_icon("system-software-update"))

        self.datadir = datadir

        QUrlOpener().setupUrlHandles()
        self.app.aboutToQuit.connect(QUrlOpener().teardownUrlHandles)

        QApplication.processEvents()

    def error(self, summary, message):
        QMessageBox.critical(None, summary, message)

    def runDistUpgrader(self):
        # now run it with sudo
        if os.getuid() != 0:
            os.execv("/usr/bin/pkexec",
                     ["pkexec",
                      self.script + " --frontend=DistUpgradeViewKDE"])
        else:
            os.execv(self.script,
                     [self.script, "--frontend=DistUpgradeViewKDE"] +
                     self.run_options)

    def showReleaseNotes(self):
        # FIXME: care about i18n! (append -$lang or something)
        # TODO:  ^ what is this supposed to mean?
        self.dialog = QDialog()
        uic.loadUi(self.datadir + "/dialog_release_notes.ui", self.dialog)
        upgradeButton = self.dialog.buttonBox.button(
            QDialogButtonBox.StandardButton.Ok
        )
        upgradeButton.setText(_("&Upgrade"))
        upgradeButton.setIcon(_icon("dialog-ok"))
        cancelButton = self.dialog.buttonBox.button(
            QDialogButtonBox.StandardButton.Cancel
        )
        cancelButton.setText(_("&Cancel"))
        cancelButton.setIcon(_icon("dialog-cancel"))
        self.dialog.setWindowTitle(_("Release Notes"))
        self.dialog.show()
        if self.new_dist.releaseNotesHtmlUri is not None:
            uri = self.new_dist.releaseNotesURI
            # download/display the release notes
            # TODO: add some progress reporting here
            result = None
            try:
                release_notes = urlopen(uri)
                notes = release_notes.read().decode("UTF-8", "replace")
                self.dialog.scrolled_notes.setText(notes)
                result = self.dialog.exec()
            except HTTPError:
                primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                          _("Could not find the release notes")
                secondary = _("The server may be overloaded. ")
                _warning(primary + "<br />" + secondary)
            except IOError:
                primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                          _("Could not download the release notes")
                secondary = _("Please check your internet connection.")
                _warning(primary + "<br />" + secondary)
            # user clicked cancel
            if result == QDialog.DialogCode.Accepted:
                return True
        return False


class KDEAcquireProgressAdapter(apt.progress.base.AcquireProgress):
    def __init__(self, parent, datadir, label):
        self.app = _ensureQApplication()
        self.dialog = QDialog()

        uiFile = os.path.join(datadir, "fetch-progress.ui")
        uic.loadUi(uiFile, self.dialog)
        self.dialog.setWindowTitle(_("Upgrade"))
        self.dialog.installingLabel.setText(label)
        self.dialog.buttonBox.rejected.connect(self.abort)

        # This variable is used as return value for AcquireProgress pulses.
        # Setting it to False will abort the Acquire and consequently the
        # entire fetcher.
        self._continue = True

        QApplication.processEvents()

    def abort(self):
        self._continue = False

    def start(self):
        self.dialog.installingLabel.setText(
            _("Downloading additional package files..."))
        self.dialog.installationProgress.setValue(0)
        self.dialog.show()

    def stop(self):
        self.dialog.hide()

    def pulse(self, owner):
        apt.progress.base.AcquireProgress.pulse(self, owner)
        self.dialog.installationProgress.setValue(int(
            (self.current_bytes + self.current_items) /
            float(self.total_bytes + self.total_items) * 100))
        current_item = self.current_items + 1
        if current_item > self.total_items:
            current_item = self.total_items
        label_text = _("Downloading additional package files...")
        if self.current_cps > 0:
            label_text += _("File %s of %s at %sB/s") % (
                self.current_items, self.total_items,
                apt_pkg.size_to_str(self.current_cps))
        else:
            label_text += _("File %s of %s") % (
                self.current_items, self.total_items)
        self.dialog.installingLabel.setText(label_text)
        QApplication.processEvents()
        return self._continue

    def mediaChange(self, medium, drive):
        msg = _("Please insert '%s' into the drive '%s'") % (medium, drive)
        change = QMessageBox.question(None, _("Media Change"), msg,
                                      QMessageBox.StandardButton.Ok,
                                      QMessageBox.StandardButton.Cancel)
        if change == QMessageBox.StandardButton.Ok:
            return True
        return False
