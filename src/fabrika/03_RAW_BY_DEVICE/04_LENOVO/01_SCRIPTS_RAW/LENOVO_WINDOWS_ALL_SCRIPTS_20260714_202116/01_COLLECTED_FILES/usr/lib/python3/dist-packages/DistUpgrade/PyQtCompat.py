# PyQtCompat.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
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
#
# Compatibility shim to support both PyQt5 (Ubuntu 24.04) and PyQt6.
# Import Qt modules from here instead of directly from PyQt5/PyQt6.

try:
    from PyQt6 import uic
    from PyQt6.QtCore import (
        Qt, QLocale, QTranslator, QTimer, QEventLoop,
        QObject, QCoreApplication, QUrl, pyqtSlot,
    )
    from PyQt6.QtWidgets import (
        QTextEdit, QApplication, QDialog, QMessageBox,
        QDialogButtonBox, QTreeWidgetItem, QPushButton,
        QWidget, QHBoxLayout, QLabel,
    )
    from PyQt6.QtGui import (
        QTextOption, QPixmap, QIcon, QTextCursor,
        QDesktopServices,
    )
except ImportError:
    from PyQt5 import uic
    from PyQt5.QtCore import (
        Qt, QLocale, QTranslator, QTimer, QEventLoop,
        QObject, QCoreApplication, QUrl, pyqtSlot,
    )
    from PyQt5.QtWidgets import (
        QTextEdit, QApplication, QDialog, QMessageBox,
        QDialogButtonBox, QTreeWidgetItem, QPushButton,
        QWidget, QHBoxLayout, QLabel,
    )
    from PyQt5.QtGui import (
        QTextOption, QPixmap, QIcon, QTextCursor,
        QDesktopServices,
    )
