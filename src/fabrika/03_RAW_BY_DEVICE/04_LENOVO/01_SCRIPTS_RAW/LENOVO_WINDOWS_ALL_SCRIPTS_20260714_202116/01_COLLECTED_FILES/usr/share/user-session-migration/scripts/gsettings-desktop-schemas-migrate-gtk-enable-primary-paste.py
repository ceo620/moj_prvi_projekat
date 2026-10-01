#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Canonical Ltd.
# SPDX-FileContributor: Alessandro Astone <alessandro.astone@canonical.com>

import sys
import re
from pathlib import Path

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio

MEDIA_INFO_PATH = Path('/var/log/installer/media-info')
TARGET_VERSION = (26, 4)

SCHEMA_ID = 'org.gnome.desktop.interface'
KEY_NAME = 'gtk-enable-primary-paste'
NEW_VALUE = True

if not MEDIA_INFO_PATH.exists():
    sys.exit(0)

media_info = MEDIA_INFO_PATH.read_text(errors='ignore')
version = re.search(r'\b(\d{2})\.(\d{2})\b', media_info)
if not version:
    sys.exit(0)

major, minor = int(version.group(1)), int(version.group(2))
if (major, minor) >= TARGET_VERSION:
    sys.exit(0)

settings = Gio.Settings.new(SCHEMA_ID)
user_val = settings.get_user_value(KEY_NAME)
if user_val is None:
    settings.set_boolean(KEY_NAME, NEW_VALUE)
    Gio.Settings.sync()
