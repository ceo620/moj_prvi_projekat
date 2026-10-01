# DistUpgradeController.py
#
#  Copyright (c) 2004-2022 Canonical Ltd.
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
import apt_pkg
import base64
import distro_info
import glob
import sys
import os
import subprocess
import locale
import logging
import tempfile
import time
import copy
import platform
import pwd
import errno

from configparser import NoOptionError
from configparser import ConfigParser as SafeConfigParser
from .telemetry import get as get_telemetry
from .utils import (url_downloadable,
                    check_and_fix_xbit,
                    iptables_active,
                    inside_chroot,
                    get_string_with_no_auth_from_source_entry,
                    is_child_of_process_name,
                    inhibit_sleep)
from urllib.parse import urlsplit
from .DistUpgradeView import Step
from .DistUpgradeCache import MyCache
from .DistUpgradeConfigParser import DistUpgradeConfig
from .DistUpgradeQuirks import DistUpgradeQuirks

# workaround broken relative import in python-apt (LP: #871007), we
# want the local version of distinfo.py from oneiric, but because of
# a bug in python-apt we will get the natty version that does not
# know about "Component.parent_component" leading to a crash
from aptsources import distinfo
from aptsources import sourceslist
sourceslist.DistInfo = distinfo.DistInfo

from aptsources.sourceslist import (SourcesList,
                                    SourceEntry,
                                    Deb822SourceEntry,
                                    is_mirror)

from .DistUpgradeGettext import gettext as _
from .DistUpgradeGettext import ngettext
import gettext

from .DistUpgradeCache import (CacheExceptionDpkgInterrupted,
                               CacheExceptionLockingFailed,
                               NotEnoughFreeSpaceError)
from .DistUpgradeApport import run_apport

REBOOT_REQUIRED_FILE = "/var/run/reboot-required"


def component_ordering_key(a):
    """ key() function for sorted to ensure "correct" component ordering """
    ordering = ["main", "restricted", "universe", "multiverse"]
    try:
        return ordering.index(a)
    except ValueError:
        # ensure to sort behind the "official" components, order is not
        # really important for those
        return len(ordering)+1

def suite_ordering_key(a):
    """ key() function for sorted to ensure "correct" suite ordering """
    ordering = ["", "updates", "security", "backports", "proposed"]
    pocket = a.partition("-")[2]

    try:
        return ordering.index(pocket)
    except ValueError:
        return len(ordering)+1

def gpg_keyring_to_ascii(keyring_path):
    out = []

    out.append('-----BEGIN PGP PUBLIC KEY BLOCK-----')
    out.append('')

    with open(keyring_path, 'rb') as f:
        data = base64.b64encode(f.read())

    out += [data[i:i+64].decode('us-ascii') for i in range(0, len(data), 64)]
    out.append('-----END PGP PUBLIC KEY BLOCK-----')

    return out


class DistUpgradeController(object):
    """ this is the controller that does most of the work """

    def __init__(self, distUpgradeView, options=None, datadir=None):
        # setup the paths
        localedir = "/usr/share/locale/"
        if datadir == None or datadir == '.':
            datadir = os.getcwd()
            localedir = os.path.join(datadir,"mo")
        self.datadir = datadir
        self.options = options

        try:
            self._invoking_user_pwd = pwd.getpwuid(
                int(os.getenv('SUDO_UID', os.getenv('PKEXEC_UID')))
            )
        except TypeError:
            logging.debug(
                'Failed to determine invoking user, '
                'environment variables may be incomplete.'
            )
            self._invoking_user_pwd = None

        # init gettext
        gettext.bindtextdomain("ubuntu-release-upgrader",localedir)
        gettext.textdomain("ubuntu-release-upgrader")

        # setup the view
        logging.debug("Using '%s' view" % distUpgradeView.__class__.__name__)
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self.cache = None
        self.fetcher = None

        # the configuration
        self.config = DistUpgradeConfig(datadir)
        self.sources_backup_ext = "."+self.config.get("Files","BackupExt")

        # move some of the options stuff into the self.config,
        # ConfigParser deals only with strings it seems *sigh*
        self.config.add_section("Options")
        self.config.set("Options","devRelease", "False")
        if self.options:
            if self.options.devel_release:
                self.config.set("Options","devRelease", "True")

        # Add context about the versions we are upgrading from/to.
        os_release = platform.freedesktop_os_release()
        self.fromDist = os_release.get('VERSION_CODENAME')
        self.fromVersion = os_release.get('VERSION_ID')

        di = distro_info.UbuntuDistroInfo()
        self.toDist = self.config.get('Sources', 'To')
        self.toVersion = (di.version(self.toDist) or '').partition(' ')[0]

        if not di.valid(self.toDist) or not self.toVersion:
            if self.options.devel_release:
                self._view.error(
                    _('Distribution data outdated'),
                    _('An updated distro-info-data package is required '
                      'before upgrading to the development release.\n\n'
                      'Try again after the distro-info-data update is '
                      'available.'),
                )
            else:
                # This really should not happen once upgrades are supported.
                self._view.error(
                    _('Distribution data outdated'),
                    _('Please ensure all package updates are installed, '
                      'and then try again.')
                )

            # Too early to call abort().
            sys.exit(1)

        self.isFromDistEOL = self.fromDist not in di.supported()
        self.supportedFromDists = self.config.getlist('Sources', 'From')

        # Defaults for deb sources
        self.default_sources_filepath = os.path.join(
            apt_pkg.config.find_dir("Dir::Etc::sourceparts"),
            "ubuntu.sources"
        )

        self.arch = apt_pkg.config.find("APT::Architecture")
        if self.arch in ("amd64", "arm64", "i386"):
            self.default_source_uri = "http://archive.ubuntu.com/ubuntu"
            self.security_source_uri = "http://security.ubuntu.com/ubuntu"
        else:
            self.default_source_uri = "http://ports.ubuntu.com/ubuntu-ports"
            self.security_source_uri = "http://ports.ubuntu.com/ubuntu-ports"

        # we run with --force-overwrite by default
        if "RELEASE_UPGRADE_NO_FORCE_OVERWRITE" not in os.environ:
            logging.debug("enable dpkg --force-overwrite")
            apt_pkg.config.set("DPkg::Options::","--force-overwrite")

        # we run in full upgrade mode by default
        self._partialUpgrade = False

        # install the quirks handler
        self.quirks = DistUpgradeQuirks(self, self.config)

        # install a logind sleep inhibitor
        self.inhibitor_fd = inhibit_sleep()

        # setup env var
        os.environ["RELEASE_UPGRADE_IN_PROGRESS"] = "1"
        os.environ["PYCENTRAL_FORCE_OVERWRITE"] = "1"

        # set max retries
        maxRetries = self.config.getint("Network","MaxRetries")
        apt_pkg.config.set("Acquire::Retries", str(maxRetries))
        # max sizes for dpkgpm for large installs (see linux/limits.h and
        #                                          linux/binfmts.h)
        apt_pkg.config.set("Dpkg::MaxArgs", str(64*1024))
        apt_pkg.config.set("Dpkg::MaxArgBytes", str(128*1024))

        # smaller to avoid hangs
        apt_pkg.config.set("Acquire::http::Timeout","20")
        apt_pkg.config.set("Acquire::ftp::Timeout","20")

        # no list cleanup here otherwise a "cancel" in the upgrade
        # will not restore the full state (lists will be missing)
        apt_pkg.config.set("Apt::Get::List-Cleanup", "false")

        # install phased updates during upgrades
        apt_pkg.config.set("APT::Get::Always-Include-Phased-Updates", "yes")

        # forced obsoletes
        self.forced_obsoletes = self.config.getlist("Distro","ForcedObsoletes")
        # list of valid mirrors that we can add
        self.valid_mirrors = self.config.getListFromFile("Sources","ValidMirrors")
        # third party mirrors
        self.valid_3p_mirrors = []
        if self.config.has_section('ThirdPartyMirrors'):
            self.valid_3p_mirrors = [pair[1] for pair in
                                     self.config.items('ThirdPartyMirrors')]

        # for inhibiting idle
        self._session_bus = None

        # Sources files that we generated during deb822 migration. Used restore
        # to original state on abort.
        self._generated_sources_files = set()

        # Keep track of foreign packages before and after re-writing sources.
        # This helps track down upgrade calculation errors related to PPAs etc.
        self._foreign_packages_pre_rewrite = dict()
        self._foreign_packages_post_rewrite = dict()

    def openCache(self, lock=True, restore_sources_list_on_fail=False):
        logging.debug("openCache()")
        if self.cache is None:
            self.quirks.PreCacheOpen()
        else:
            self.cache.release_lock()
            self.cache.unlock_lists_dir()
        # this loop will try getting the lock a couple of times
        MAX_LOCK_RETRIES = 20
        lock_retry = 0
        while True:
            try:
                # exit here once the cache is ready
                return self._openCache(lock)
            except CacheExceptionLockingFailed as e:
                # wait a bit
                lock_retry += 1
                self._view.processEvents()
                time.sleep(0.1)
                logging.debug(
                    "failed to lock the cache, retrying (%i)" % lock_retry)
                # and give up after some time
                if lock_retry > MAX_LOCK_RETRIES:
                    logging.error("Cache can not be locked (%s)" % e)
                    self._view.error(_("Unable to get exclusive lock"),
                                     _("This usually means that another "
                                       "package management application "
                                       "(like apt-get or aptitude) "
                                       "already running. Please close that "
                                       "application first."));
                    if restore_sources_list_on_fail:
                        self.abort()
                    else:
                        sys.exit(1)

    def _openCache(self, lock):
        try:
            self.cache = MyCache(self.config,
                                 self._view,
                                 self.quirks,
                                 self._view.getOpCacheProgress(),
                                 lock,
                                 from_dist=self.fromDist,
                                 to_dist=self.toDist)
            # alias name for the plugin interface code
            self.apt_cache = self.cache
        # if we get a dpkg error that it was interrupted, just
        # run dpkg --configure -a
        except CacheExceptionDpkgInterrupted:
            logging.warning("dpkg interrupted, calling dpkg --configure -a")
            cmd = ["/usr/bin/dpkg","--configure","-a"]
            if os.environ.get("DEBIAN_FRONTEND") == "noninteractive":
                cmd.append("--force-confold")
            self._view.getTerminal().call(cmd)
            self.cache = MyCache(self.config,
                                 self._view,
                                 self.quirks,
                                 self._view.getOpCacheProgress(),
                                 from_dist=self.fromDist,
                                 to_dist=self.toDist)
        self.cache.partialUpgrade = self._partialUpgrade

        logging.debug("/openCache(), new cache size %i" % len(self.cache))

    def _viewSupportsSSH(self):
      """
      Returns True if this view support upgrades over ssh.
      In theory all views should support it, but for savety
      we do only allow text ssh upgrades (see LP: #322482)
      """
      supported = self.config.getlist("View","SupportSSH")
      if self._view.__class__.__name__ in supported:
          return True
      return False

    def _sshMagic(self):
        """ this will check for server mode and if we run over ssh.
            if this is the case, we will ask and spawn a additional
            daemon (to be sure we have a spare one around in case
            of trouble)
        """
        pidfile = os.path.join("/var/run/release-upgrader-sshd.pid")
        if (not os.path.exists(pidfile) and
            os.path.isdir("/proc") and
            is_child_of_process_name("sshd")):
            # check if the frontend supports ssh upgrades (see lp: #322482)
            if not self._viewSupportsSSH():
                logging.error("upgrade over ssh not allowed")
                self._view.error(_("Upgrading over remote connection not supported"),
                                 _("You are running the upgrade over a "
                                   "remote ssh connection with a frontend "
                                   "that does "
                                   "not support this. Please try a text "
                                   "mode upgrade with 'do-release-upgrade'."
                                   "\n\n"
                                   "The upgrade will "
                                   "abort now. Please try without ssh.")
                                 )
                sys.exit(1)
                return False
            # ask for a spare one to start (and below 1024)
            port = 1022
            res = self._view.askYesNoQuestion(
                _("Continue running under SSH?"),
                _("This session appears to be running under ssh. "
                  "It is not recommended to perform a upgrade "
                  "over ssh currently because in case of failure "
                  "it is harder to recover.\n\n"
                  "If you continue, an additional ssh daemon will be "
                  "started at port '%s'.\n"
                  "Do you want to continue?") % port)
            # abort
            if res == False:
                sys.exit(1)
            res = subprocess.call(["/usr/sbin/sshd",
                                   "-o", "PidFile=%s" % pidfile,
                                   "-p",str(port)])
            if res == 0:
                summary = _("Starting additional sshd")
                descr =  _("To make recovery in case of failure easier, an "
                           "additional sshd will be started on port '%s'. "
                           "If anything goes wrong with the running ssh "
                           "you can still connect to the additional one.\n"
                           ) % port
                if iptables_active():
                    cmd = "iptables -I INPUT -p tcp --dport %s -j ACCEPT" % port
                    descr += _(
                        "If you run a firewall, you may need to "
                        "temporarily open this port. As this is "
                        "potentially dangerous it's not done automatically. "
                        "You can open the port with e.g.:\n'%s'") % cmd
                self._view.information(summary, descr)
        return True

    def _pythonSymlinkCheck(self):
        """ check that /usr/bin/python3 points to the default python version.
            Users tend to modify this symlink, which breaks stuff in obscure
            ways (Ubuntu #75557).
        """
        logging.debug("_pythonSymlinkCheck run")
        binaries_and_dirnames = [("python3", "python3")]
        for binary, dirname in binaries_and_dirnames:
            debian_defaults = '/usr/share/%s/debian_defaults' % dirname
            if os.path.exists(debian_defaults):
                config = SafeConfigParser()
                with open(debian_defaults) as f:
                    config.read_file(f)
                try:
                    expected_default = config.get('DEFAULT', 'default-version')
                except NoOptionError:
                    logging.debug("no default version for %s found in '%s'" %
                                  (binary, config))
                    return False
                try:
                    fs_default_version = os.path.realpath('/usr/bin/%s' % binary)
                except OSError as e:
                    logging.error("os.path.realpath failed (%s)" % e)
                    return False
                if not fs_default_version in (expected_default, os.path.join('/usr/bin', expected_default)):
                    logging.debug("%s symlink points to: '%s', but expected is '%s' or '%s'" %
                                  (binary, fs_default_version, expected_default, os.path.join('/usr/bin', expected_default)))
                    return False
        return True


    def prepare(self):
        """ initial cache opening, coherence checking, network checking """
        # first check if that is a good upgrade
        if not (self.fromDist in self.supportedFromDists or self.fromDist == self.toDist):
            self._view.error(_("Can not upgrade"),
                             _("An upgrade from '%s' to '%s' is not "
                               "supported with this tool." % (self.fromDist, self.toDist)))
            sys.exit(1)

        logging.debug(
            'Upgrading from {} to {}'.format(
                self.fromDist + (' (EOL)' if self.isFromDistEOL else ''),
                self.toDist,
            )
        )

        # do the ssh check and warn if we run under ssh
        self._sshMagic()
        # check python version
        if not self._pythonSymlinkCheck():
            logging.error("pythonSymlinkCheck() failed, aborting")
            self._view.error(_("Can not upgrade"),
                             _("Your python3 install is corrupted. "
                               "Please fix the '/usr/bin/python3' symlink."))
            sys.exit(1)
        # open cache
        try:
            self.openCache()
        except SystemError as e:
            logging.error("openCache() failed: '%s'" % e)
            return False
        if not self.cache.coherence_check(self._view):
            return False

        # now figure out if we need to go into desktop or
        # server mode - we use a heuristic for this
        self.serverMode = self.cache.need_server_mode()
        if self.serverMode:
            os.environ["RELEASE_UPGRADE_MODE"] = "server"
        else:
            os.environ["RELEASE_UPGRADE_MODE"] = "desktop"

        if not self.checkViewDepends():
            logging.error("checkViewDepends() failed")
            return False

        from .DistUpgradeMain import SYSTEM_DIRS
        for systemdir in SYSTEM_DIRS:
            if os.path.exists(systemdir) and not os.access(systemdir, os.W_OK):
                logging.error("%s not writable" % systemdir)
                self._view.error(
                    _("Can not write to '%s'") % systemdir,
                    _("Its not possible to write to the system directory "
                      "'%s' on your system. The upgrade can not "
                      "continue.\n"
                      "Please make sure that the system directory is "
                      "writable.") % systemdir)
                self.abort()

        return True

    def _deb822SourceEntryDownloadable(self, entry):
        """
        Check if deb822 source points to downloadable archive(s).
        Returns a tuple (bool, list).

        The bool is True if any combination of URI and suite was downloadable,
        or False if no combination was.

        The list contains tuples of URI and suite that were not downloadable
        together.
        """
        logging.debug("verifySourcesListEntry: %s" % entry)

        failed = []
        downloadable = False

        for uri in entry.uris:
            for suite in entry.suites:
                release_file = "{}/dists/{}/Release".format(uri, suite)
                if url_downloadable(release_file, logging.debug):
                    downloadable = True
                else:
                    failed.append((uri,suite))

        return (downloadable, failed)

    def migratedToDeb822(self):
        """
        Return an integer indicating if sources are migrated to deb822.
        Possible return values are:

            -1: not migrated to deb822 sources
             0: partially migrated to deb822 sources
             1: fully migrated to deb822 sources
        """
        sources = SourcesList(matcherPath=self.datadir, deb822=True)
        deb822 = [s for s in sources if isinstance(s, Deb822SourceEntry)]
        nondeb822 = [s for s in sources if not isinstance(s, Deb822SourceEntry)]

        # On migration, we leave behind an empty (i.e. invalid)
        # /etc/apt/sources.list to explain the migration. Ignore this file.
        sourcelist_file = os.path.join(
            apt_pkg.config.find_dir("Dir::Etc"),
            apt_pkg.config.find("Dir::Etc::sourcelist")
        )
        nondeb822 = [s for s in nondeb822 \
                     if not (s.file == sourcelist_file and s.invalid)]

        if deb822 and not nondeb822:
            # Fully migrated to deb822 sources.
            return 1
        elif deb822 and nondeb822:
            # Partially migrated. A mix of .list and .sources are configured.
            return 0
        else:
            # Either no deb822 sources, or no sources at all.
            return -1

    def migrateToDeb822Sources(self):
        """
        Migrate .list files to corresponding .sources files.
        """
        logging.debug("migrateToDeb822Sources()")

        sourcelist_file = os.path.join(
            apt_pkg.config.find_dir("Dir::Etc"),
            apt_pkg.config.find("Dir::Etc::sourcelist")
        )
        sourceparts_dir = apt_pkg.config.find_dir('Dir::Etc::sourceparts')
        trustedparts_dir = apt_pkg.config.find_dir('Dir::Etc::trustedparts')
        migrated_sources_list = False
        cannot_migrate = {}

        self.sources = SourcesList(matcherPath=self.datadir)
        self.sources.backup('.migrate')

        index = {}
        for entry in self.sources:
            if not isinstance(entry, SourceEntry):
                continue

            if entry.invalid:
                logging.debug(
                    f'Could not migrate {str(entry)} from {entry.file}'
                    ', disabling instead.'
                )

                # It's possible that the source is considered invalid because python-apt
                # does not support [signed-by=] or something. For anything that we
                # cannot migrate, move it instead to <filename>.disabled. These will not
                # be cleaned up at the end of the upgrade.
                #
                # NB: Unfortunately, we cannot just do entry.disabled = True and let
                # sources.save() write disabled entries, because SourceEntry.str will
                # return the raw line when entry.invalid == True. So, the line will not
                # actually be commented out.
                try:
                    cannot_migrate[entry.file].append(str(entry))
                except KeyError:
                    cannot_migrate[entry.file] = [str(entry)]

                continue

            # Remove disabled deb-src entries, because stylistically it makes
            # more sense to add/remove deb-src in the Types: field, rather than
            # having a deb-src entry with Enabled: no.
            if entry.type == 'deb-src' and entry.disabled:
                continue

            # Figure out where this new entry is going.
            if entry.file == sourcelist_file:
                migrated_sources_list = True

                if self.isMirror(entry.uri):
                    # sources.list -> sources.list.d/ubuntu.sources
                    new_filepath = os.path.join(sourceparts_dir, 'ubuntu.sources')
                else:
                    # sources.list -> sources.list.d/third-party.sources
                    new_filepath = os.path.join(sourceparts_dir, 'third-party.sources')
            else:
                # sources.list.d/foo.list -> sources.list.d/foo.sources
                new_filepath = os.path.splitext(entry.file)[0] + '.sources'

            # Start by making the existing sources as "flat" as possible. Later
            # we can consolidate by suite and type if possible.
            key = (new_filepath, entry.disabled, entry.type, entry.uri, entry.dist)
            try:
                e = index[key]
                e['comps'] = list(set(e['comps'] + entry.comps))
                e['comps'].sort(key=component_ordering_key)
            except KeyError:
                e = {}
                e['filepath'] = new_filepath
                e['disabled'] = entry.disabled
                e['types'] = [entry.type]
                e['uris'] = [entry.uri]
                e['suites'] = [entry.dist]
                e['comps'] = list(set(entry.comps))
                e['comps'].sort(key=component_ordering_key)
                index[key] = e

        for suite in [k[-1] for k in index.keys()]:
            for k in [k for k in index.keys() if k[-1] != suite]:
                try:
                    e = index[(*k[:-1], suite)]

                    if e['comps'] == index[k]['comps']:
                        e['suites'] += index[k]['suites']
                        e['suites'].sort(key=suite_ordering_key)

                        del index[k]
                except KeyError:
                    continue

        for (ks, se) in [(k,e) for (k,e) in index.items() if k[2] == 'deb-src']:
            for (kb, be) in [(k,e) for (k,e) in index.items() if k[2] == 'deb']:
                can_combine = True
                can_combine &= se['filepath'] == be['filepath']
                can_combine &= se['disabled'] == be['disabled']
                can_combine &= se['uris'] == be['uris']
                can_combine &= se['suites'] == be['suites']
                can_combine &= se['comps'] == be['comps']

                if can_combine:
                    be['types'] = ['deb', 'deb-src']
                    del index[ks]

        # Consolidate GPG keys from trusted.gpg.d into their respective .sources files.
        for entry in index.values():
            filepath = entry['filepath']

            if filepath == os.path.join(sourceparts_dir, 'ubuntu.sources'):
                entry['signed-by'] = ' /usr/share/keyrings/ubuntu-archive-keyring.gpg'
            else:
                # Check if there is a ppa.gpg corresponding to ppa.list.
                keyring = os.path.basename(os.path.splitext(filepath)[0])
                keyring = os.path.join(trustedparts_dir, keyring + '.gpg')

                if not os.path.exists(keyring):
                    # apt-add-repository names the list files as $user-ubuntu-$ppa-$release.list,
                    # but the .gpg files are named $user-ubuntu-$ppa.gpg.
                    keyring = os.path.basename(os.path.splitext(filepath)[0])
                    keyring = keyring.rsplit('-', 1)[0] + '.gpg'
                    keyring = os.path.join(trustedparts_dir, keyring)

                if os.path.exists(keyring) and not entry.get('signed-by'):
                    lines = gpg_keyring_to_ascii(keyring)
                    lines = [' ' + (l if l.strip() else '.') for l in lines]

                    entry['signed-by'] = '\n' + '\n'.join(lines)

        # Generate the new .sources files. We write the files manually rather
        # than using python-apt because the currently loaded version of
        # aptsources.sourceslist might not have Deb822SourceEntry yet.
        for path in set([e['filepath'] for e in index.values()]):
            stanzas = []

            for e in [e for e in index.values() if e['filepath'] == path]:
                stanza = ''
                if e['disabled']:
                    stanza += 'Enabled: no\n'

                stanza += 'Types: {}\n'.format(' '.join(e['types']))
                stanza += 'URIs: {}\n'.format(' '.join(e['uris']))
                stanza += 'Suites: {}\n'.format(' '.join(e['suites']))
                stanza += 'Components: {}\n'.format(' '.join(e['comps']))

                if e.get('signed-by'):
                    stanza += 'Signed-By:{}\n'.format(e['signed-by'])

                stanzas.append(stanza)

            with open(path, 'w') as f:
                f.write('\n'.join(stanzas))

            self._generated_sources_files.add(path)

        # Remove the old .list files.
        for entry in [e for e in self.sources if isinstance(e, SourceEntry)]:
            if entry.file == sourcelist_file and not migrated_sources_list:
                # If we didn't migrate sources.list, then it's because it's not
                # valid. Probably because it already contains just a comment
                # about the move to ubuntu.sources. Leave it alone.
                continue

            if os.path.exists(entry.file):
                os.remove(entry.file)

            self.sources.remove(entry)

        self.sources.save()

        if migrated_sources_list:
            # Finally, leave a comment in the old sources.list file explaining
            # the migration.
            with open(sourcelist_file, 'w') as f:
                f.write('# Ubuntu sources have moved to {}\n'
                        .format(os.path.join(sourceparts_dir, 'ubuntu.sources')))

        for (file, entries) in cannot_migrate.items():
            with open(f'{file}.disabled', 'w') as f:
                f.write(
                    '# This file could not be automatically migrated '
                    'to a .sources file during the upgrade.\n'
                    '# Please see sources.list(5) (or '
                    'https://manpages.ubuntu.com/manpages/man5/sources.list.5.html'
                    ')\n# for details on how to migrate manually.\n\n'
                )
                for entry in entries:
                    f.write(f'# {entry}\n')


    def restoreMigratedSources(self):
        if not self._generated_sources_files:
            return

        sourcelist_file = os.path.join(
            apt_pkg.config.find_dir("Dir::Etc"),
            apt_pkg.config.find("Dir::Etc::sourcelist")
        )
        sourceparts_dir = apt_pkg.config.find_dir('Dir::Etc::sourceparts')

        for path in glob.glob(f'{sourceparts_dir}/*.migrate'):
            try:
                os.rename(path, path.removesuffix('.migrate'))
            except OSError as e:
                logging.debug(f'Failed to restore {path}: {e}')

        try:
            os.rename(
                f'{sourcelist_file}.migrate',
                sourcelist_file
            )
        except FileNotFoundError:
            pass
        except OSError as e:
            logging.debug(f'Failed to restore {sourcelist_file}: {e}')

        for path in self._generated_sources_files:
            try:
                os.remove(path)
            except OSError as e:
                logging.debug(f'Failed to remove {path}: {e}')

    def cleanBackupSources(self):
        sourcelist_file = os.path.join(
            apt_pkg.config.find_dir("Dir::Etc"),
            apt_pkg.config.find("Dir::Etc::sourcelist")
        )
        sourceparts_dir = apt_pkg.config.find_dir('Dir::Etc::sourceparts')

        paths = [
            f'{sourcelist_file}{self.sources_backup_ext}',
            f'{sourcelist_file}.migrate',
        ]
        paths += glob.glob(f'{sourceparts_dir}/*{self.sources_backup_ext}')
        paths += glob.glob(f'{sourceparts_dir}/*.migrate')

        for path in paths:
            try:
                os.remove(path)
            except OSError:
                pass

    def _addDefaultSources(self):
        e = self.sources.add(
            file=self.default_sources_filepath,
            type='deb',
            uri=self.default_source_uri,
            dist=self.toDist,
            orig_comps=['main', 'restricted', 'universe', 'multiverse']
        )
        e.suites = sorted([self.toDist, self.toDist + '-updates'],
                          key=suite_ordering_key)
        e.section['Signed-By'] = '/usr/share/keyrings/ubuntu-archive-keyring.gpg'

    def _addSecuritySources(self):
        e = self.sources.add(
            file=self.default_sources_filepath,
            type='deb',
            uri=self.security_source_uri,
            dist=self.toDist + '-security',
            orig_comps=['main', 'restricted', 'universe', 'multiverse']
        )
        e.section['Signed-By'] = '/usr/share/keyrings/ubuntu-archive-keyring.gpg'

    def _allowThirdParty(self):
        return any((
            self.config.getWithDefault("Sources","AllowThirdParty",False),
            "RELEASE_UPGRADER_ALLOW_THIRD_PARTY" in os.environ,
        ))

    def _mirrorCheck(self):
        # skip mirror check if special environment is set
        # (useful for server admins with internal repos)
        if self._allowThirdParty():
            logging.warning("mirror check skipped, *overriden* via config")
            return True

        # check if we need to enable main
        # now check if the base-meta pkgs are available in
        # the archive or only available as "now"
        # -> if not that means that "main" is missing and we
        #    need to enable it
        logging.debug(self.config.getlist("Distro", "BaseMetaPkgs"))
        for pkgname in self.config.getlist("Distro", "BaseMetaPkgs"):
            logging.debug("Checking pkg: %s" % pkgname)
            if ((not pkgname in self.cache or
                 not self.cache[pkgname].candidate or
                 len(self.cache[pkgname].candidate.origins) == 0)
                or
                (self.cache[pkgname].candidate and
                 len(self.cache[pkgname].candidate.origins) == 1 and
                 self.cache[pkgname].candidate.origins[0].archive == "now")
               ):
                logging.debug("BaseMetaPkg '%s' has no candidate.origins" % pkgname)
                return False

        return True

    def rewriteDeb822Sources(self):
        """
        deb822-aware version of rewriteSourcesList()

        Return True if we found a valid dist to ugprade to, and return False
        otherwise.
        """
        found_components = {}
        disabled_unknown_mirror = []
        disabled_no_release_file = []
        disabled_unknown_dist = []

        # Map suites from current release to next release.
        suite_mapping = {self.fromDist: self.toDist}
        for pocket in self.config.getlist("Sources", "Pockets"):
            f = '{}-{}'.format(self.fromDist, pocket)
            t = '{}-{}'.format(self.toDist, pocket)
            suite_mapping[f] = t

        sources = [
            e for e in self.sources
            if not any((
                e.invalid,
                e.disabled,
                not isinstance(e, Deb822SourceEntry),
            ))
        ]

        for entry in sources:
            # Disable -proposed when upgrading to -devel release.
            if self.options and self.options.devel_release:
                logging.debug("upgrade to development release, disabling proposed")
                no_proposed = set(entry.suites) - set([self.fromDist + "-proposed"])
                if not no_proposed:
                    # -proposed is the only pocket for this source, so just
                    # disable it.
                    entry.disabled = True
                    continue
                else:
                    # If there are other suites, just remove -proposed.
                    entry.suites = no_proposed

            # Remove/replace old-releases.ubuntu.com sources as needed.
            entry.uris = set([u for u in entry.uris \
                              if "old-releases.ubuntu.com/" not in u])
            if not entry.uris:
                if [s for s in entry.suites if s.endswith("-security")]:
                    entry.uris = [self.security_source_uri]
                else:
                    entry.uris = [self.default_source_uri]

            # Rewrite ports.ubuntu.com -> archive.ubuntu.com for arm64.
            # arm64 packages moved to the primary archive as of Resolute
            # (LP: #2147101). Also covers systems that were already on
            # Resolute (fromDist) and are upgrading onward.
            #
            # arm64 sources historically use a single consolidated stanza
            # covering all pockets including -security. For stanzas that
            # have only -security suites we use security_source_uri; for
            # all others (including mixed stanzas) we use default_source_uri,
            # which also serves the security pocket.
            if self.arch == "arm64" and (
                self.toDist == "resolute" or self.fromDist == "resolute"
            ):
                security_only = all(
                    s.endswith("-security") for s in entry.suites
                )
                new_uri = (
                    self.security_source_uri
                    if security_only
                    else self.default_source_uri
                )
                entry.uris = set(
                    u.replace(
                        "ports.ubuntu.com/ubuntu-ports",
                        new_uri.split("://", 1)[1],
                    )
                    for u in entry.uris
                )

            logging.debug("examining: '%s'" %
                          get_string_with_no_auth_from_source_entry(copy.deepcopy(entry)))

            # Disable sources that do not contain valid mirrors.
            known_mirrors = [
                u for u in entry.uris
                if any((
                    self.isMirror(u),
                    self.isThirdPartyMirror(u),
                    self._allowThirdParty(),
                ))
            ]
            if not known_mirrors:
                entry.disabled = True
                disabled_unknown_mirror.append(entry)
                logging.debug("entry '%s' was disabled (unknown mirror)"
                              % get_string_with_no_auth_from_source_entry(copy.deepcopy(entry)))
                continue

            # Move suites to the next release.
            new_suites = []
            for s in entry.suites:
                try:
                    new_suites.append(suite_mapping[s])
                except KeyError:
                    if s in suite_mapping.values():
                        new_suites.append(s)

            # If this did not yield any suites, disable this source.
            if not new_suites:
                entry.disabled = True
                disabled_unknown_dist.append(entry)

                logging.debug("entry '%s' was disabled (unknown dist)"
                              % get_string_with_no_auth_from_source_entry(copy.deepcopy(entry)))
                continue
            else:
                entry.suites = sorted(list(set(new_suites)), key=suite_ordering_key)

            # deb-src entries, security archive URIs, and sources without only
            # -security or -backports enabled are not valid "to" sources.
            valid_uris = [u for u in entry.uris \
                          if "/security.ubuntu.com" not in u]
            valid_suites = [s for s in entry.suites \
                            if s.rsplit('-', 1)[-1] not in ["backports", "security"]]
            valid_to = "deb" in entry.types and valid_uris and valid_suites
            if not valid_to:
                continue

            # Finally, test the archive to make sure it provides the new dist.
            (downloadable, failed) = self._deb822SourceEntryDownloadable(entry)
            if not downloadable:
                entry.disabled = True
                disabled_no_release_file.append(entry)
                logging.debug("entry '%s' was disabled (no Release file)"
                              % get_string_with_no_auth_from_source_entry(copy.deepcopy(entry)))
                continue
            elif failed:
                logging.debug("some Release files were not downloadable for '%s"
                              % get_string_with_no_auth_from_source_entry(copy.deepcopy(entry)))
            else:
                # We can upgrade using this source.
                for suite in entry.suites:
                    try:
                        found_components[suite] |= set(entry.comps)
                    except KeyError:
                        found_components[suite] = set(entry.comps)

        if 'main' not in found_components.get(self.toDist, set()):
            if disabled_no_release_file:
                details = _(
                    'This is probably because one or more of the following '
                    'mirrors are out-of-date or unreachable:\n\n'
                )
                details += '\n'.join(
                    sorted(e.uri for e in disabled_no_release_file)
                )

            elif disabled_unknown_mirror:
                details = _(
                    'This is probably because of one or more of the following '
                    'unsupported mirrors was disabled:\n\n'
                )
                details += '\n'.join(
                    sorted(e.uri for e in disabled_unknown_mirror)
                )

            else:
                details = _(
                    'This is probably because the current apt sources '
                    'configuration is unsupported.'
                )

                if disabled_unknown_dist:
                    details += _(
                        '\n\nThe following suites were disabled because they are '
                        'out-of-date or unknown:\n\n'
                    )
                    details += '\n'.join(sorted(
                        set().union(*[e.uri for e in disabled_unknown_dist])
                    ))

            details += _(
                '\n\nWould you like to continue the upgrade using default '
                'sources? If you select \'No\', the upgrade will be aborted.'
            )

            res = self._view.askYesNoQuestion(
                _('Required apt sources are missing'),
                details,
            )

            if not res:
                return False

            self._addDefaultSources()
            self._addSecuritySources()

        return True

    def updateDeb822Sources(self):
        """
        deb822-aware version of updateSourcesList()
        """
        logging.debug("updateDeb822Sources()")
        self.sources = SourcesList(matcherPath=self.datadir, deb822=True)
        self.sources.backup(self.sources_backup_ext)

        if not self.rewriteDeb822Sources():
            self.abort()

        # Ensure suites and components are sorted.
        for entry in self.sources:
            if entry.disabled or entry.invalid:
                continue

            entry.comps = sorted(entry.comps, key=component_ordering_key)
            entry.suites = sorted(entry.suites, key=suite_ordering_key)

        self.sources.save()

        return True

    def _logChanges(self):
        # debugging output
        logging.debug("About to apply the following changes")
        inst = []
        up = []
        rm = []
        held = []
        keep = []
        for pkg in self.cache:
            if pkg.marked_install: inst.append(pkg.name)
            elif pkg.marked_upgrade: up.append(pkg.name)
            elif pkg.marked_delete: rm.append(pkg.name)
            elif (pkg.is_installed and pkg.is_upgradable): held.append(pkg.name)
            elif pkg.is_installed and pkg.marked_keep: keep.append(pkg.name)
        logging.debug("Keep at same version: %s" % " ".join(keep))
        logging.debug("Upgradable, but held- back: %s" % " ".join(held))
        logging.debug("Remove: %s" % " ".join(rm))
        logging.debug("Install: %s" % " ".join(inst))
        logging.debug("Upgrade: %s" % " ".join(up))

    def doPostInitialUpdate(self):
        # check if we have packages in ReqReinst state that are not
        # downloadable
        logging.debug("doPostInitialUpdate")
        self.quirks.PostInitialUpdate()
        if not self.cache:
            return False

        # Check foreign packages before we rewrite sources. This will give us a
        # better chance of tracking the source of foreign packages, i.e. which
        # PPA they come from.
        self._foreign_packages_pre_rewrite = self.cache.foreign_packages()

        if len(self.cache.req_reinstall_pkgs) > 0:
            logging.warning("packages in reqReinstall state, trying to fix")
            self.cache.fix_req_reinst(self._view)
            self.openCache()
        if len(self.cache.req_reinstall_pkgs) > 0:
            reqreinst = self.cache.req_reinstall_pkgs
            header = ngettext("Package in inconsistent state",
                              "Packages in inconsistent state",
                              len(reqreinst))
            summary = ngettext("The package '%s' is in an inconsistent "
                               "state and needs to be reinstalled, but "
                               "no archive can be found for it. "
                               "Please reinstall the package manually "
                               "or remove it from the system.",
                               "The packages '%s' are in an inconsistent "
                               "state and need to be reinstalled, but "
                               "no archive can be found for them. "
                               "Please reinstall the packages manually "
                               "or remove them from the system.",
                               len(reqreinst)) % ", ".join(reqreinst)
            self._view.error(header, summary)
            return False
        # Log MetaPkgs installed to see if there is more than one.
        meta_pkgs = []
        for pkg in self.config.getlist("Distro","MetaPkgs"):
            if pkg in self.cache and self.cache[pkg].is_installed:
                meta_pkgs.append(pkg)
        logging.debug("MetaPkgs: %s" % " ".join(sorted(meta_pkgs)))
        # FIXME: check out what packages are downloadable etc to
        # compare the list after the update again
        self.obsolete_pkgs = self.cache._getObsoletesPkgs()
        logging.debug("Obsolete: %s" % " ".join(sorted(self.obsolete_pkgs)))
        return True

    def doUpdate(self, showErrors=True, forceRetries=None):
        logging.debug("running doUpdate() (showErrors=%s)" % showErrors)
        self.cache._list.read_main_list()
        progress = self._view.getAcquireProgress()
        # FIXME: also remove all files from the lists partial dir!
        currentRetry = 0
        if forceRetries is not None:
            maxRetries=forceRetries
        else:
            maxRetries = self.config.getint("Network","MaxRetries")
        # LP: #1321959
        error_msg = ""
        while currentRetry < maxRetries:
            try:
                self.cache.update(progress)
            except (SystemError, IOError) as e:
                error_msg = str(e)
                logging.error("IOError/SystemError in cache.update(): '%s'. Retrying (currentRetry: %s)" % (e,currentRetry))
                currentRetry += 1
                continue
            # no exception, so all was fine, we are done
            return True

        logging.error("doUpdate() failed completely")
        if showErrors:
            self._view.error(_("Error during update"),
                             _("A problem occurred during the update. "
                               "This is usually some sort of network "
                               "problem, please check your network "
                               "connection and retry."), "%s" % error_msg)
        return False


    def _checkBootEfi(self):
        " check that /boot/efi is a mounted partition on an EFI system"

        # Not an UEFI system
        if not os.path.exists("/sys/firmware/efi"):
            logging.debug("Not an UEFI system")
            return True

        # Stuff we know about that would write to the ESP
        bootloaders = ["shim-signed", "grub-efi-amd64", "grub-efi-ia32", "grub-efi-arm", "grub-efi-arm64", "sicherboot"]

        if not any(bl in self.cache and self.cache[bl].is_installed for bl in bootloaders):
            logging.debug("UEFI system, but no UEFI grub installed")
            return True

        mounted=False

        with open("/proc/mounts") as mounts:
            for line in mounts:
                line=line.strip()
                try:
                    (what, where, fs, options, a, b) = line.split()
                except ValueError as e:
                    logging.debug("line '%s' in /proc/mounts not understood (%s)" % (line, e))
                    continue

                if where != "/boot/efi":
                    continue

                mounted=True

                if "rw" in options.split(","):
                    logging.debug("Found writable ESP %s", line)
                    return True

        if not mounted:
            self._view.error(_("EFI System Partition (ESP) not usable"),
                             _("Your EFI System Partition (ESP) is not "
                               "mounted at /boot/efi. Please ensure that "
                               "it is properly configured and try again."))
        else:
            self._view.error(_("EFI System Partition (ESP) not usable"),
                             _("The EFI System Partition (ESP) mounted at "
                               "/boot/efi is not writable. Please mount "
                               "this partition read-write and try again."))
        return False

    def _checkFreeSpace(self):
        " this checks if we have enough free space on /var and /usr"
        err_sum = _("Not enough free disk space")
        # TRANSLATORS: you can change the order of the sentence,
        # make sure to keep all {str_*} string untranslated.
        err_msg = _("The upgrade has aborted. "
                    "The upgrade needs a total of {str_total} free space on disk '{str_dir}'. "
                    "Please free at least an additional {str_needed} of disk "
                    "space on '{str_dir}'. {str_remedy}")
        # specific ways to resolve lack of free space
        remedy_archivedir = _("Remove temporary packages of former "
                              "installations using 'sudo apt clean'.")
        remedy_boot = _("You can remove old kernels using "
                        "'sudo apt autoremove' and you could also "
                        "set COMPRESS=xz in "
                        "/etc/initramfs-tools/initramfs.conf to "
                        "reduce the size of your initramfs.")
        remedy_root = _("Empty your trash and remove temporary "
                        "packages of former installations using "
                        "'sudo apt-get clean'.")
        remedy_tmp = _("Reboot to clean up files in /tmp.")
        remedy_usr = _("")
        # allow override
        if self.config.getWithDefault("FreeSpace","SkipCheck",False):
            logging.warning("free space check skipped via config override")
            return True
        # do the check
        with_snapshots = self._is_apt_btrfs_snapshot_supported()
        try:
            self.cache.checkFreeSpace(with_snapshots)
        except NotEnoughFreeSpaceError as e:
            # ok, showing multiple error dialog sucks from the UI
            # perspective, but it means we do not need to break the
            # string freeze
            archivedir = apt_pkg.config.find_dir("Dir::Cache::archives")
            err_long = ""
            remedy = {archivedir: remedy_archivedir,
                      '/var': remedy_archivedir,
                      '/boot': remedy_boot,
                      '/': remedy_root,
                      '/tmp': remedy_tmp,
                      '/usr': remedy_usr}
            for req in e.free_space_required_list:
                if err_long != "":
                     err_long += " "
                if req.dir in remedy:
                    err_long += err_msg.format(str_total=req.size_total, str_dir=req.dir,
                                               str_needed=req.size_needed,
                                               str_remedy=remedy[req.dir])
                else:
                    err_long += err_msg.format(str_total=req.size_total, str_dir=req.dir,
                                               str_needed=req.size_needed,
                                               str_remedy='')
            self._view.error(err_sum, err_long)
            return False
        return True


    def calcDistUpgrade(self):
        self._view.updateStatus(_("Calculating the changes"))
        if not self.cache.distUpgrade(self._view, self.serverMode, self._partialUpgrade):
            return False

        if self.serverMode:
            if not self.cache.installTasks(self.cache.installedTasks):
                return False

        # show changes and confirm
        changes = self.cache.get_changes()
        self._view.processEvents()

        # log the changes for debugging
        self._logChanges()
        self._view.processEvents()

        # check if we have enough free space
        if not self._checkFreeSpace():
            return False

        # check that ESP is sane
        if not self._checkBootEfi():
            return False

        self._view.processEvents()

        # flush UI
        self._view.processEvents()
        return changes

    def askDistUpgrade(self):
        changes = self.calcDistUpgrade()

        if not changes:
            return False

        # ask the user
        res = self._view.confirmChanges(_("Do you want to start the upgrade?"),
                                        changes,
                                        self.cache.required_download)
        return res

    def _isLivepatchEnabled(self):
        di = distro_info.UbuntuDistroInfo()
        return di.is_lts(self.fromDist) and os.path.isfile('/var/snap/canonical-livepatch/common/machine-token')

    def askLivepatch(self):
        di = distro_info.UbuntuDistroInfo()

        if not self._isLivepatchEnabled() or di.is_lts(self.toDist):
            return True

        version = next((r.version for r in di.get_all("object") if r.series == self.toDist), self.toDist)

        res = self._view.askCancelContinueQuestion(None,
            _("Livepatch security updates are not available for Ubuntu %s. "
              "If you upgrade, Livepatch will turn off.") % version)
        return res

    def doDistUpgradeFetching(self):
        # get the upgrade
        currentRetry = 0
        fprogress = self._view.getAcquireProgress()
        #iprogress = self._view.getInstallProgress(self.cache)
        # start slideshow
        url = self.config.getWithDefault("Distro","SlideshowUrl",None)
        if url:
            try:
                lang = locale.getdefaultlocale()[0].split('_')[0]
            except:
                logging.exception("getdefaultlocale")
                lang = "en"
            self._view.getHtmlView().open("%s#locale=%s" % (url, lang))
        # retry the fetching in case of errors
        maxRetries = self.config.getint("Network","MaxRetries")
        # FIXME: we get errors like
        #   "I wasn't able to locate file for the %s package"
        #  here sometimes. its unclear why and not reproducible, the
        #  current theory is that for some reason the file is not
        #  considered trusted at the moment
        #  pkgAcquireArchive::QueueNext() runs debReleaseIndex::IsTrused()
        #  (the later just checks for the existence of the .gpg file)
        #  OR
        #  the fact that we get a pm and fetcher here confuses something
        #  in libapt?
        # POSSIBLE workaround: keep the list-dir locked so that
        #          no apt-get update can run outside from the release
        #          upgrader
        user_canceled = False
        # LP: #1102593 - In Python 3, the targets of except clauses get `del`d
        # from the current namespace after the exception is handled, so we
        # must assign it to a different variable in order to use it after
        # the while loop.
        exception = None
        while currentRetry < maxRetries:
            try:
                pm = apt_pkg.PackageManager(self.cache._depcache)
                self.fetcher = apt_pkg.Acquire(fprogress)
                self.cache._fetch_archives(self.fetcher, pm)
            except apt.cache.FetchCancelledException as e:
                logging.info("user canceled")
                user_canceled = True
                exception = e
                break
            except IOError as e:
                # fetch failed, will be retried
                logging.error("IOError in cache.commit(): '%s'. Retrying (currentTry: %s)" % (e,currentRetry))
                currentRetry += 1
                exception = e
                continue
            return True

        # maximum fetch-retries reached without a successful commit
        if user_canceled:
            self._view.information(_("Upgrade canceled"),
                                   _("The upgrade will cancel now and the "
                                     "original system state will be restored. "
                                     "You can resume the upgrade at a later "
                                     "time."))
        else:
            logging.error("giving up on fetching after maximum retries")
            self._view.error(_("Could not download the upgrades"),
                             _("The upgrade has aborted. Please check your "
                               "Internet connection or "
                               "installation media and try again. All files "
                               "downloaded so far have been kept."),
                             "%s" % exception)
        # abort here because we want our sources.list back
        self.abort()

    def _is_apt_btrfs_snapshot_supported(self):
        """ check if apt-btrfs-snapshot is usable """
        try:
            import apt_btrfs_snapshot
        except ImportError:
            return
        try:
            apt_btrfs = apt_btrfs_snapshot.AptBtrfsSnapshot()
            res = apt_btrfs.snapshots_supported()
        except:
            logging.exception("failed to check btrfs support")
            return False
        logging.debug("apt btrfs snapshots supported: %s" % res)
        return res

    def _maybe_create_apt_btrfs_snapshot(self):
        """ create btrfs snapshot (if btrfs layout is there) """
        if not self._is_apt_btrfs_snapshot_supported():
            return
        import apt_btrfs_snapshot
        apt_btrfs = apt_btrfs_snapshot.AptBtrfsSnapshot()
        prefix = "release-upgrade-%s-" % self.toDist
        res = apt_btrfs.create_btrfs_root_snapshot(prefix)
        logging.info("creating snapshot '%s' (success=%s)" % (prefix, res))

    def doDistUpgradeSimulation(self):
        backups = {}
        backups["dir::bin::dpkg"] = [apt_pkg.config["dir::bin::dpkg"]]
        apt_pkg.config["dir::bin::dpkg"] = "/bin/true"

        # If we remove automatically installed packages in the upgrade, we'd lose their auto bit
        # here in the simulation as we'd write the simulated end result to the file, so let's
        # not write the file for the simulation.
        backups["Dir::State::extended_states"] = [apt_pkg.config["Dir::State::extended_states"]]

        with tempfile.NamedTemporaryFile(prefix='apt_extended_states_') as f:
            apt_pkg.config["Dir::State::extended_states"] = f.name

            for lst in "dpkg::pre-invoke", "dpkg::pre-install-pkgs", "dpkg::post-invoke", "dpkg::post-install-pkgs":
                backups[lst + "::"] = apt_pkg.config.value_list(lst)
                apt_pkg.config.clear(lst)

            try:
                return self.doDistUpgrade()
            finally:
                for lst in backups:
                    for item in backups[lst]:
                        apt_pkg.config.set(lst, item)

    def doDistUpgrade(self):
        # add debug code only here
        #apt_pkg.config.set("Debug::pkgDpkgPM", "1")
        #apt_pkg.config.set("Debug::pkgOrderList", "1")
        #apt_pkg.config.set("Debug::pkgPackageManager", "1")

        # get the upgrade
        currentRetry = 0
        fprogress = self._view.getAcquireProgress()
        iprogress = self._view.getInstallProgress(self.cache)
        # retry the fetching in case of errors
        maxRetries = self.config.getint("Network","MaxRetries")
        if not self._partialUpgrade:
            self.quirks.StartUpgrade()
            # FIXME: take this into account for diskspace calculation
            self._maybe_create_apt_btrfs_snapshot()
        res = False
        exception = None
        while currentRetry < maxRetries:
            try:
                res = self.cache.commit(fprogress,iprogress)
                logging.debug("cache.commit() returned %s" % res)
            except SystemError as e:
                logging.error("SystemError from cache.commit(): %s" % e)
                exception = e
                # if its a ordering bug we can cleanly revert to
                # the previous release, no packages have been installed
                # yet (LP: #328655, #356781)
                if os.path.exists("/var/run/ubuntu-release-upgrader-apt-exception"):
                    with open("/var/run/ubuntu-release-upgrader-apt-exception") as f:
                        e = f.read()
                    logging.error("found exception: '%s'" % e)
                    # if its a ordering bug we can cleanly revert but we need to write
                    # a marker for the parent process to know its this kind of error
                    pre_configure_errors = [
                        "E:Internal Error, Could not perform immediate configuration",
                        "E:Couldn't configure pre-depend "]
                    for preconf_error in pre_configure_errors:
                        if str(e).startswith(preconf_error):
                            logging.debug("detected preconfigure error, restorting state")
                            # FIXME: strings are not good, but we are in string freeze
                            # currently
                            msg = _("Error during commit")
                            msg += "\n'%s'\n" % str(e)
                            msg += _("Restoring original system state")
                            self._view.error(_("Could not install the upgrades"), msg)
                            # abort() exits cleanly
                            self.abort()

                # invoke the frontend now and show a error message
                msg = _("The upgrade has aborted. Your system "
                        "could be in an unusable state. A recovery "
                        "will run now (dpkg --configure -a).")
                if not self._partialUpgrade:
                    if not run_apport():
                        msg += _("\n\nPlease report this bug in a browser at "
                                 "http://bugs.launchpad.net/ubuntu/+source/ubuntu-release-upgrader/+filebug "
                                 "and attach the files in /var/log/dist-upgrade/ "
                                 "to the bug report.\n"
                                 "%s" % e)
                self._view.error(_("Could not install the upgrades"), msg)
                # installing the packages failed, can't be retried
                cmd = ["/usr/bin/dpkg","--configure","-a"]
                if os.environ.get("DEBIAN_FRONTEND") == "noninteractive":
                    cmd.append("--force-confold")
                self._view.getTerminal().call(cmd)
                return False
            except IOError as e:
                # fetch failed, will be retried
                logging.error("IOError in cache.commit(): '%s'. Retrying (currentTry: %s)" % (e,currentRetry))
                currentRetry += 1
                exception = e
                continue
            except OSError as e:
                logging.exception("cache.commit()")
                # deal gracefully with:
                #  OSError: [Errno 12] Cannot allocate memory
                exception = e
                if e.errno == 12:
                    msg = _("Error during commit")
                    msg += "\n'%s'\n" % str(e)
                    msg += _("Restoring original system state")
                    self._view.error(_("Could not install the upgrades"), msg)
                    # abort() exits cleanly
                    self.abort()
            # no exception, so all was fine, we are done
            return True

        # maximum fetch-retries reached without a successful commit
        logging.error("giving up on fetching after maximum retries")
        self._view.error(_("Could not download the upgrades"),
                         _("The upgrade has aborted. Please check your "\
                           "Internet connection or "\
                           "installation media and try again. "),
                           "%s" % exception)
        # abort here because we want our sources.list back
        self.abort()

    def doPostUpgrade(self):
        get_telemetry().add_stage('POSTUPGRADE')
        # clean up downloaded packages
        archivedir = os.path.dirname(
            apt_pkg.config.find_dir("Dir::Cache::archives"))
        for item in self.fetcher.items:
            if os.path.dirname(os.path.abspath(item.destfile)) == archivedir:
                try:
                    os.unlink(item.destfile)
                except OSError:
                    pass

        # reopen cache
        self.openCache()
        # run the quirks handler that does does like things adding
        # missing groups or similar work arounds, only do it on real
        # upgrades
        self.quirks.PostUpgrade()
        # check out what packages are cruft now
        self._view.setStep(Step.CLEANUP)
        self._view.updateStatus(_("Searching for obsolete software"))
        now_obsolete = self.cache._getObsoletesPkgs()
        logging.debug("Obsolete: %s" % " ".join(sorted(now_obsolete)))
        # now coherence check - if a base meta package is in the obsolete list
        # now, that means that something went wrong (see #335154) badly with
        # the network. this should never happen, but it did happen at least
        # once so we add extra paranoia here
        for pkg in self.config.getlist("Distro","BaseMetaPkgs"):
            if pkg in now_obsolete:
                logging.error("the BaseMetaPkg '%s' is in the obsolete list, something is wrong, ignoring the obsoletes" % pkg)
                now_obsolete = set()
                break
        # check if we actually want obsolete removal
        if not self.config.getWithDefault("Distro","RemoveObsoletes", True):
            logging.debug("Skipping obsolete Removal")
            return True

        # now get the meta-pkg specific obsoletes and purges
        for pkg in self.config.getlist("Distro","MetaPkgs"):
            if pkg in self.cache and self.cache[pkg].is_installed:
                self.forced_obsoletes.extend(self.config.getlist(pkg,"ForcedObsoletes"))
        logging.debug("forced_obsoletes: %s" % self.forced_obsoletes)

        # mark packages that are now obsolete (and were not obsolete
        # before) to be deleted.
        remove_candidates = now_obsolete - self.obsolete_pkgs
        remove_candidates |= set(self.forced_obsoletes)

        # now go for the unused dependencies
        unused_dependencies = self.cache._getUnusedDependencies()
        logging.debug("Unused dependencies: %s" %" ".join(unused_dependencies))
        remove_candidates |= set(unused_dependencies)

        # see if we actually have to do anything here
        if not self.config.getWithDefault("Distro","RemoveObsoletes", True):
            logging.debug("Skipping RemoveObsoletes as stated in the config")
            remove_candidates = set()
        logging.debug("remove_candidates: '%s'" % remove_candidates)
        logging.debug("Start checking for obsolete pkgs")
        progress = self._view.getOpCacheProgress()
        scheduled_remove = set()

        # Remove all remove candidates that should not actually be ones from the list
        for pkgname in list(remove_candidates):
            if not self.cache.isRemoveCandidate(pkgname, self._foreign_packages_pre_rewrite):
                remove_candidates.remove(pkgname)

        with self.cache.actiongroup():
            # Forced obsoletes we remove, removing any of their dependencies, hence do a first loop with auto_fix=True
            for (i, pkgname) in enumerate(remove_candidates):
                progress.update((i/float(len(remove_candidates)))*100.0 / 2)
                if pkgname in self.forced_obsoletes:
                    self._view.processEvents()
                    if not self.cache.tryMarkObsoleteForRemoval(pkgname, remove_candidates, self.forced_obsoletes, auto_fix=True):
                        logging.debug("'%s' scheduled for remove but not safe to remove, skipping", pkgname)
                    else:
                        scheduled_remove.add(pkgname)

            # Now let's try to remove other packages
            for (i, pkgname) in enumerate(remove_candidates):
                progress.update((i/float(len(remove_candidates)))*100.0 / 2 + 50)
                self._view.processEvents()
                if not self.cache.tryMarkObsoleteForRemoval(pkgname, remove_candidates, self.forced_obsoletes, auto_fix=False):
                    logging.debug("'%s' scheduled for remove but not safe to remove, skipping", pkgname)
                else:
                    scheduled_remove.add(pkgname)

            # We have scheduled their removals, but not any reverse-dependencies. If anything is broken now,
            # resolve them by keeping back the obsolete packages.
            self.cache._startAptResolverLog()
            pr = apt.ProblemResolver(self.cache)
            try:
                pr.resolve_by_keep()
            except Exception:
                pass
            self.cache._stopAptResolverLog()

            if self.cache.broken_count > 0:
                logging.debug("resolve_by_keep() failed to resolve conflicts from removing obsolete packages, falling back to slower implementation.")
                self.cache.clear()
                scheduled_remove = set()
                with self.cache.actiongroup():
                    for (i, pkgname) in enumerate(remove_candidates):
                        progress.update((i/float(len(remove_candidates)))*100.0)
                        self._view.processEvents()
                        if not self.cache.tryMarkObsoleteForRemoval(pkgname, remove_candidates, self.forced_obsoletes, auto_fix=True):
                            logging.debug("'%s' scheduled for remove but not safe to remove, skipping", pkgname)
                        else:
                            scheduled_remove.add(pkgname)

            # resolve_by_keep() will revert any unsafe removals, so we need to list them here again.
            for pkgname in scheduled_remove:
                if (
                    pkgname in self.cache and
                    not self.cache[pkgname].marked_delete
                ):
                    logging.debug("obsolete package '%s' could not be removed", pkgname)

        logging.debug("Finish checking for obsolete pkgs")
        progress.done()

        # get changes
        changes = self.cache.get_changes()
        logging.debug("The following packages are marked for removal: %s" % " ".join([pkg.name for pkg in changes]))
        summary = _("Remove obsolete packages?")
        actions = [_("_Keep"), _("_Remove")]
        # FIXME Add an explanation about what obsolete packages are
        #explanation = _("")
        if (len(changes) > 0 and
            self._view.confirmChanges(summary, changes, 0, actions, False)):
            fprogress = self._view.getAcquireProgress()
            iprogress = self._view.getInstallProgress(self.cache)
            try:
                self.cache.commit(fprogress,iprogress)
            except (SystemError, IOError) as e:
                logging.error("cache.commit() in doPostUpgrade() failed: %s" % e)
                self._view.error(_("Error during commit"),
                                 _("A problem occurred during the clean-up. "
                                   "Please see the below message for more "
                                   "information. "),
                                   "%s" % e)

        self.cleanBackupSources()

        # run stuff after cleanup
        self.quirks.PostCleanup()
        # run the post upgrade scripts that can do fixup like xorg.conf
        # fixes etc - only do on real upgrades
        if not self._partialUpgrade:
            self.runPostInstallScripts()

        return True

    def runPostInstallScripts(self):
        """
        scripts that are run in any case after the distupgrade finished
        whether or not it was successful

        Cache lock is released during script runs in the event that the
        PostInstallScripts require apt or dpkg changes.
        """
        if self.cache:
            self.cache.release_lock()
            self.cache.unlock_lists_dir()
        # now run the post-upgrade fixup scripts (if any)
        for script in self.config.getlist("Distro","PostInstallScripts"):
            if not os.path.exists(script):
                logging.warning("PostInstallScript: '%s' not found" % script)
                continue
            logging.debug("Running PostInstallScript: '%s'" % script)
            try:
                # work around kde tmpfile problem where it eats permissions
                check_and_fix_xbit(script)
                self._view.getTerminal().call([script], hidden=True)
            except Exception as e:
                logging.error("got error from PostInstallScript %s (%s)" % (script, e))
        if self.cache:
            self.cache.get_lock()

    def abort(self):
        """ abort the upgrade, cleanup (as much as possible) """
        logging.debug("abort called")
        if hasattr(self, "sources"):
            self.sources.restore_backup(self.sources_backup_ext)
            self.restoreMigratedSources()
            self.cleanBackupSources()

        # generate a new cache
        self._view.updateStatus(_("Restoring original system state"))
        self._view.abort()
        self.openCache()
        sys.exit(1)

    def _checkDep(self, depstr):
        " check if a given depends can be satisfied "
        for or_group in apt_pkg.parse_depends(depstr):
            logging.debug("checking: '%s' " % or_group)
            for dep in or_group:
                depname = dep[0]
                ver = dep[1]
                oper = dep[2]
                if depname not in self.cache:
                    logging.error("_checkDep: '%s' not in cache" % depname)
                    return False
                inst = self.cache[depname]
                instver = getattr(inst.installed, "version", None)
                if (instver != None and
                    apt_pkg.check_dep(instver,oper,ver) == True):
                    return True
        logging.error("depends '%s' is not satisfied" % depstr)
        return False

    def checkViewDepends(self):
        " check if depends are satisfied "
        logging.debug("checkViewDepends()")
        res = True
        # now check if anything from $foo-updates is required
        depends = self.config.getlist("View","Depends")
        depends.extend(self.config.getlist(self._view.__class__.__name__,
                                           "Depends"))
        for dep in depends:
            logging.debug("depends: '%s'", dep)
            res &= self._checkDep(dep)
            if not res:
                # FIXME: instead of error out, fetch and install it
                #        here
                self._view.error(_("Required depends is not installed"),
                                 _("The required dependency '%s' is not "
                                   "installed. " % dep))
                sys.exit(1)
        return res

    def isMirror(self, uri):
        """ check if uri is a known mirror """
        # deal with username:password in a netloc
        raw_uri = uri.rstrip("/")
        scheme, netloc, path, query, fragment = urlsplit(raw_uri)
        if "@" in netloc:
            netloc = netloc.split("@")[1]
        # construct new mirror url without the username/pw
        uri = "%s://%s%s" % (scheme, netloc, path)
        for mirror in self.valid_mirrors:
            mirror = mirror.rstrip("/")
            if is_mirror(mirror, uri):
                return True
            # deal with mirrors like
            #    deb http://localhost:9977/security.ubuntu.com/ubuntu intrepid-security main restricted
            # both apt-debtorrent and apt-cacher use this (LP: #365537)
            mirror_host_part = mirror.split("//")[1]
            if uri.endswith(mirror_host_part):
                logging.debug("found apt-cacher/apt-torrent style uri %s" % uri)
                return True
        return False

    def isThirdPartyMirror(self, uri):
        " check if uri is an allowed third-party mirror "
        uri = uri.rstrip("/")
        for mirror in self.valid_3p_mirrors:
            mirror = mirror.rstrip("/")
            if is_mirror(mirror, uri):
                return True
        return False

    # this is the core
    def fullUpgrade(self):
        # coherence check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking package manager"))
        self._view.setStep(Step.PREPARE)

        if not self.prepare():
            logging.error("self.prepare() failed")
            if os.path.exists("/usr/bin/apport-bug"):
                self._view.error(_("Preparing the upgrade failed"),
                                 _("Preparing the system for the upgrade "
                                   "failed so a bug reporting process is "
                                   "being started."))
                subprocess.Popen(["apport-bug", "ubuntu-release-upgrader-core"])
            else:
                self._view.error(_("Preparing the upgrade failed"),
                                 _("Preparing the system for the upgrade "
                                   "failed. To report a bug install apport "
                                   "and then execute 'apport-bug "
                                   "ubuntu-release-upgrader'."))
                logging.error("Missing apport-bug, bug report not "
                              "autocreated")
            self.abort()

        if not self.askLivepatch():
            self.abort()

        # run a "apt-get update" now, its ok to ignore errors,
        # because
        # a) we disable any third party sources later
        # b) we check if we have valid ubuntu sources later
        #    after we rewrite the sources.list and do a
        #    apt-get update there too
        # because the (unmodified) sources.list of the user
        # may contain bad/unreachable entries we run only
        # with a single retry
        self.doUpdate(showErrors=False, forceRetries=1)
        self.openCache()

        # do pre-upgrade stuff (calc list of obsolete pkgs etc)
        if not self.doPostInitialUpdate():
            self.abort()

        try:
            # update sources.list
            self._view.setStep(Step.MODIFY_SOURCES)
            self._view.updateStatus(_("Updating repository information"))

            # Deb822 sources are the default on Ubuntu, and we don't want to
            # maintain two ways to re-write sources. Migrate any .list sources
            # to .sources before the re-write.
            if self.migratedToDeb822() <= 0:
                self.migrateToDeb822Sources()

            if not self.updateDeb822Sources():
                self.abort()

            # then update the package index files
            if not self.doUpdate():
                self.abort()

            # then open the cache (again)
            self._view.updateStatus(_("Checking package manager"))
            # if something fails here (e.g. locking the cache) we need to
            # restore the system state (LP: #1052605)
            self.openCache(restore_sources_list_on_fail=True)

            # Check foreign packages now, and abort the upgrade if there are
            # any left. If third-party sources are allowed, issue a warning
            # instead.
            self._foreign_packages_post_rewrite = self.cache.foreign_packages()
            self._warn_about_foreign_packages()

            # re-check server mode because we got new packages (it may happen
            # that the system had no sources.list entries and therefore no
            # desktop file information)
            # switch from server to desktop but not the other way
            if self.serverMode:
                self.serverMode = self.cache.need_server_mode()
            # do it here as we need to know if we are in server or client mode
            self.quirks.ensure_recommends_are_installed_on_desktops()
            # now check if we still have some key packages available/downloadable
            # after the update - if not something went seriously wrong
            # (this happend e.g. during the intrepid->jaunty upgrade for some
            #  users when de.archive.ubuntu.com was overloaded)
            for pkg in self.config.getlist("Distro","BaseMetaPkgs"):
                if (pkg not in self.cache or
                    not self.cache.anyVersionDownloadable(self.cache[pkg])):
                    # FIXME: we could offer to add default source entries here,
                    #        but we need to be careful to not duplicate them
                    #        (i.e. the error here could be something else than
                    #        missing sources entries but network errors etc)
                    logging.error("No '%s' available/downloadable after sources.list rewrite+update" % pkg)
                    if pkg not in self.cache:
                        logging.error("'%s' was not in the cache" % pkg)
                    elif not self.cache.anyVersionDownloadable(self.cache[pkg]):
                        logging.error("'%s' was not downloadable" % pkg)
                    self._view.error(_("Invalid package information"),
                                     _("After updating your package "
                                       "information, the essential package '%s' "
                                       "could not be located. This may be "
                                       "because you have no official mirrors "
                                       "listed in your software sources, or "
                                       "because of excessive load on the mirror "
                                       "you are using. See /etc/apt/sources.list "
                                       "for the current list of configured "
                                       "software sources."
                                       "\n"
                                       "In the case of an overloaded mirror, you "
                                       "may want to try the upgrade again later.")
                                       % pkg)
                    if os.path.exists("/usr/bin/apport-bug"):
                        subprocess.Popen(["apport-bug", "ubuntu-release-upgrader-core"])
                    else:
                        logging.error("Missing apport-bug, bug report not "
                                      "autocreated")
                    self.abort()

            # calc the dist-upgrade and see if the removals are ok/expected
            # do the dist-upgrade
            self._view.updateStatus(_("Calculating the changes"))
            if not self.askDistUpgrade():
                self.abort()
            self._inhibitIdle()

            # fetch the stuff
            self._view.setStep(Step.FETCH)
            self._view.updateStatus(_("Fetching"))
            if not self.doDistUpgradeFetching():
                self.abort()

            # simulate an upgrade
            self._view.setStep(Step.INSTALL)
            self._view.updateStatus(_("Upgrading"))
            if not self.doDistUpgradeSimulation():
                self._view.error(_("Upgrade infeasible"),
                                 _("The upgrade could not be completed, there "
                                   "were errors during the upgrade "
                                   "process."))
                self.abort()

        except KeyboardInterrupt:
            self.abort()

        # Reopen ask above
        self.openCache(restore_sources_list_on_fail=True)
        self.serverMode = self.cache.need_server_mode()
        self.quirks.ensure_recommends_are_installed_on_desktops()

        self._view.updateStatus(_("Calculating the changes"))
        if not self.calcDistUpgrade():
            self.abort()

        # now do the upgrade
        self._view.setStep(Step.INSTALL)
        self._view.updateStatus(_("Upgrading"))
        if not self.doDistUpgrade():
            # run the post install scripts (for stuff like UUID conversion)
            self.runPostInstallScripts()
            # don't abort here, because it would restore the sources.list
            self._view.information(_("Upgrade complete"),
                                   _("The upgrade has completed but there "
                                     "were errors during the upgrade "
                                     "process."))
            # do not abort because we are part of the way through the process
            sys.exit(1)

        # do post-upgrade stuff
        self.doPostUpgrade()

        # remove upgrade-available notice
        if os.path.exists("/var/lib/ubuntu-release-upgrader/release-upgrade-available"):
            os.unlink("/var/lib/ubuntu-release-upgrader/release-upgrade-available")

        # done, ask for reboot
        self._view.setStep(Step.REBOOT)
        self._view.updateStatus(_("System upgrade is complete."))
        get_telemetry().done()
        # FIXME should we look into /var/run/reboot-required here?
        if not inside_chroot():
            if self._inside_WSL():
                self._view.adviseExitOtherWSL()
                with open("/run/launcher-command", "w+", encoding="utf-8") as f:
                    f.write("action: reboot\n")
                self._view.adviseRestartWSL()
            elif self._view.confirmRestart():
                subprocess.Popen(["/usr/bin/systemctl", "reboot", "--check-inhibitors=no"])
            sys.exit(0)
        return True

    def run(self):
        self._view.processEvents()
        return self.fullUpgrade()

    def doPartialUpgrade(self):
        " partial upgrade mode, useful for repairing "
        self._view.setStep(Step.PREPARE)
        self._view.hideStep(Step.MODIFY_SOURCES)
        self._view.hideStep(Step.REBOOT)
        self._partialUpgrade = True
        self.prepare()
        if not self.doPostInitialUpdate():
            return False
        if not self.askDistUpgrade():
            return False
        self._view.setStep(Step.FETCH)
        self._view.updateStatus(_("Fetching"))
        if not self.doDistUpgradeFetching():
            return False
        self._view.setStep(Step.INSTALL)
        self._view.updateStatus(_("Upgrading"))
        if not self.doDistUpgrade():
            self._view.information(_("Upgrade complete"),
                                   _("The upgrade has completed but there "
                                     "were errors during the upgrade "
                                     "process."))
            return False
        if not self.doPostUpgrade():
            self._view.information(_("Upgrade complete"),
                                   _("The upgrade has completed but there "
                                     "were errors during the upgrade "
                                     "process."))
            return False

        if os.path.exists(REBOOT_REQUIRED_FILE):
            # we can not talk to session management here, we run as root
            if self._view.confirmRestart():
                subprocess.Popen(["/usr/bin/systemctl", "reboot", "--check-inhibitors=no"])
        else:
            self._view.information(_("Upgrade complete"),
                                   _("The partial upgrade was completed."))
        return True

    def _inhibitIdle(self):
        logging.debug('inhibit screensaver')

        try:
            import dbus

            # Temporarily override DBUS_SESSION_BUS_ADDRESS so that we get the
            # invoking user's session bus.
            bus_address_copy = os.getenv('DBUS_SESSION_BUS_ADDRESS', '')
            bus_address_user = self.get_user_env(
                'DBUS_SESSION_BUS_ADDRESS',
                bus_address_copy,
            )
            os.environ['DBUS_SESSION_BUS_ADDRESS'] = bus_address_user

            xdg_session_type = self.get_user_env('XDG_SESSION_TYPE', '')

            if (
                os.getuid() == 0 and
                (uid := self.get_user_uid()) is not None
            ):
                os.seteuid(uid)

            # The org.freedesktop.ScreenSaver.Inhibit effect lasts only
            # as long as the dbus connection remains open. Once u-r-u
            # exits, the connection will be closed and screen inhibition
            # will be removed.
            self._session_bus = dbus.SessionBus()
            proxy = self._session_bus.get_object('org.freedesktop.ScreenSaver',
                                                 '/org/freedesktop/ScreenSaver')
            screensaver = dbus.Interface(proxy, dbus_interface='org.freedesktop.ScreenSaver')
            screensaver.Inhibit('ubuntu-release-upgrader', 'Upgrading Ubuntu')

            summary = _("Lock screen disabled")
            message = _("Your lock screen has been "
                        "disabled and will remain "
                        "disabled during the upgrade.")
        except Exception as e:
            if xdg_session_type in ('', 'tty'):
                return

            logging.debug('failed to inhibit screensaver: ' + str(e))
            summary = _("Unable to disable lock screen")
            message = _("It is highly recommended that the "
                        "lock screen be disabled during the "
                        "upgrade to prevent later issues. "
                        "Please ensure your screen lock is "
                        "disabled before continuing.")
        finally:
            os.environ['DBUS_SESSION_BUS_ADDRESS'] = bus_address_copy
            os.seteuid(os.getuid())

        self._view.information(summary, message)

    def _inside_WSL(self):
        return os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")

    def _warn_about_foreign_packages(self):
        logging.debug(
            'Foreign (before rewriting sources): {}'
            .format(' '.join(self._foreign_packages_pre_rewrite))
        )
        logging.debug(
            'Foreign (after rewriting sources): {}'
            .format(' '.join(self._foreign_packages_post_rewrite))
        )

        if not self._foreign_packages_post_rewrite:
            return

        header = _('Foreign Packages Installed')
        body = _(
            'The following unofficial packages are currently installed:\n\n'
        )

        for (name, pkg_file) in self._foreign_packages_post_rewrite.items():
            # The "before" dict may contain a package file for the sources,
            # while the "after" dict probably won't, unless --allow-third-party
            # is set.
            if pkg_file is None:
                pkg_file = self._foreign_packages_pre_rewrite.get(name)

            if pkg_file is not None:
                origin = pkg_file.origin
            else:
                origin = _('unknown origin')

            body += _(f'{name:.<25}Installed from: {origin}\n')

        body += _(
            '\n\nIt is recommended to install supported versions from '
            'the Ubuntu archive, and try the upgrade again.\n\n'
            'Do you want to continue the upgrade anyways?'
        )

        if self._view.askYesNoQuestion(header, body):
            return
        else:
            self.abort()

    def get_user_uid(self):
        if self._invoking_user_pwd is None:
            return None

        return self._invoking_user_pwd.pw_uid

    def get_user_gid(self):
        if self._invoking_user_pwd is None:
            return None

        return self._invoking_user_pwd.pw_gid

    def get_user_name(self):
        if self._invoking_user_pwd is None:
            return None

        return self._invoking_user_pwd.pw_name

    def get_user_home(self):
        if self._invoking_user_pwd is None:
            return None

        return self._invoking_user_pwd.pw_dir

    def run_as_user(self, args, **kwargs):
        user = self.get_user_name()
        if user is None:
            raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))

        return subprocess.run(
            [
                'systemd-run',
                '--user',
                '-M', f'{user}@.host',
                '--wait',
                '--pipe',
                '-q',
                '--',
                *args,
            ],
            **kwargs,
        )

    def get_user_env(self, key, default=None):
        """
        Helper to access variables from the invoking user's environment.
        """
        try:
            v = self.run_as_user(
                ['echo', f'${key}'],
                stdout=subprocess.PIPE,
            ).stdout.decode().strip()
            if not v:
                return default

            return v

        except OSError:
            return default

    def systemctl_as_user(self, args):
        user = self.get_user_name()
        if user is None:
            raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))

        return subprocess.run(
            [
                'systemctl',
                '--user',
                '-M', f'{user}@.host',
                *args,
            ]
        )
