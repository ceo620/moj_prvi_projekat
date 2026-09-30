#  Copyright (c) 2019 Canonical Ltd.
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

import apt_pkg
import os
import re
import subprocess
import tempfile

from aptsources.distro import get_distro
from aptsources.sourceslist import (SourceEntry, SourcesList, Deb822SourceEntry)

from contextlib import suppress

from gettext import gettext as _

from urllib.parse import urlparse

from softwareproperties.sourceutils import (get_source_entry_from_list,
                                            copy_source_entry,
                                            deb822_source_entry_contains)


apt_pkg.init()

GPG_KEYRING_CMD = 'gpg -q --no-options --no-default-keyring --batch --keyring %s'


class ShortcutHandler(object):
    '''Superclass for shortcut handler implementations.

    This provides a way to take a apt repository reference, in various forms,
    and write the specific apt configuration to local files.  This also can
    remove previously written configuration from local files.

    This class and any subclasses should never modify any main apt configuration
    files, only specifically named files in '.d' subdirs (e.g. sources.list.d, etc)
    should be modified.  The only exception to that rule is adding or removing
    sourceslist lines or components of existing source entries.
    '''
    def __init__(self, shortcut, components=None, enable_source=False,
                 codename=None, pocket=None, dry_run=False, deb822=False, **kwargs):
        self.shortcut = shortcut
        self.components = components or []
        self.enable_source = enable_source
        self.distro = get_distro()
        self.codename = codename or self.distro.codename
        self.pocket = pocket
        self.dry_run = dry_run
        self.deb822 = deb822

        # Subclasses should not directly reference _source_entry,
        # use _set_source_entry() and SourceEntry()
        self._source_entry = None

        # Subclasses should directly set these fields, if appropriate
        self._filebase = None
        self._username = None
        self._password = None

    @classmethod
    def is_valid_uri(cls, uri):
        '''Return if the uri is in valid uri format'''
        parsed = urlparse(uri)
        return parsed.scheme and parsed.netloc

    @classmethod
    def uri_strip_auth(cls, uri):
        '''Return the uri with the username and password stripped'''
        parsed = urlparse(uri)
        # urlparse doesn't have any great way to simply remove the auth data,
        # so let's just strip everything to the left of '@'
        return parsed._replace(netloc=parsed.netloc.rpartition('@')[2]).geturl()

    @classmethod
    def uri_insert_auth(cls, uri, username, password):
        '''Return the uri with the username and password included'''
        parsed = urlparse(cls.uri_strip_auth(uri))
        netloc='%s:%s@%s' % (username, password, parsed.netloc)
        return parsed._replace(netloc=netloc).geturl()

    @classmethod
    def fingerprints(cls, keys):
        '''Return an array of fingerprint(s) for provided key(s).

        The 'keys' parameter should be in text (str) or binary (bytes) format;
        it is converted to bytes if needed, and then passed to the 'gpg' program.
        '''
        cmd = 'gpg --show-keys -q --no-options --no-keyring --batch --with-colons'
        # yes, --with-fingerprint twice, to print subkey fingerprints
        cmd += ' --with-fingerprint' * 2
        try:
            with tempfile.TemporaryDirectory() as homedir:
                cmd += f' --homedir {homedir}'
                if not isinstance(keys, bytes):
                    keys = keys.encode()
                stdout = subprocess.run(cmd.split(), check=True, input=keys,
                                        stdout=subprocess.PIPE).stdout.decode()
        except subprocess.CalledProcessError as e:
            print(_("Warning: gpg error while processing keys:\n%s") % e)
            return []

        try:
            # gpg --with-colons fpr field puts fingerprint into (1-based) field 10
            return [l.split(':')[9] for l in stdout.splitlines() if l.startswith('fpr')]
        except KeyError:
            print(_("Warning: invalid gpg output:\n%s") % stdout)
            return []

    @property
    def description(self):
        return (_("Archive for codename: %s components: %s" %
                  (self.SourceEntry().dist,
                   ','.join(self.SourceEntry().comps))))

    @property
    def web_link(self):
        return self.archive_link

    @property
    def archive_link(self):
        return self.SourceEntry().uri

    @property
    def dist(self):
        if self.pocket:
            return '%s-%s' % (self.codename, self.pocket)
        return self.codename

    @property
    def binary_type(self):
        '''Text indicating a binary-type SourceEntry.'''
        return self.distro.binary_type

    @property
    def source_type(self):
        '''Text indicating a source-type SourceEntry.'''
        return self.distro.source_type

    def SourceEntry(self, pkgtype=None):
        '''Get the SourceEntry representing this archive/shortcut.

        This should never include any authentication data; if required,
        the username and password should only be available from the
        username and password properties, as well as from the
        netrcparts_content property.

        If pkgtype is provided, it must be either binary_type or source_type,
        in which case this returns a SourceEntry with the requested type.
        If pkgtype is not specified, this returns a SourceEntry with an
        implementation-dependent type (in most cases, implementations should
        default to binary_type).

        Note that the default SourceEntry will be returned without modification,
        and the implementation will determine if it is enabled or disabled;
        while the source-type SourceEntry will be enabled or disabled based on
        self.enable_source.  The binary-type SourceEntry will always be enabled.

        The SourceEntry 'file' field should always be set to the value of
        sourceparts_file.
        '''
        if not self._source_entry:
            raise NotImplementedError('Implementation class did not set self._source_entry')
        e = copy_source_entry(self._source_entry)
        if not pkgtype:
            return e
        if pkgtype == self.binary_type:
            e.set_enabled(True)
        elif pkgtype == self.source_type:
            e.set_enabled(self.enable_source)
        else:
            raise ValueError('Invalid pkgtype: %s' % pkgtype)

        if isinstance(e, Deb822SourceEntry):
            e.types = [pkgtype]
        else:
            e.type = pkgtype

        return copy_source_entry(e)

    @property
    def username(self):
        '''Return the username used for authentication

        If authentication is used, return the username; otherwise return None.

        By default, this returns the private variable self._username, which
        defaults to None.  Subclasses should override this method and/or
        set self._username if they have authentication data.
        '''
        return self._username

    @property
    def password(self):
        '''Return the password used for authentication

        If authentication is used, return the password; otherwise return None.

        By default, this returns the private variable self._password, which
        defaults to None.  Subclasses should override this method and/or
        set self._password if they have authentication data.
        '''
        return self._password

    def add(self):
        '''Save all data for this shortcut to file(s).

        This writes everything to the relevant files.  By default, it
        calls add_source(), add_key(), and add_login().  Subclasses
        should override it if other actions are required.
        '''
        self.add_source()
        self.add_key()
        self.add_login()

    def remove(self):
        '''Remove all data for this shortcut from file(s).

        This removes everything from the relevant files.  By default, it
        only calls remove_source() and remove_login().  Subclasses
        should override it if other actions are required.  Note that by
        default is does not call remove_key().
        '''
        self.remove_source()
        self.remove_login()

    def _add_deb822_source(self):
        sourceslist = SourcesList(deb822=True)

        newentry = None
        binentry = self.SourceEntry(self.binary_type)
        for s in sourceslist:
            if not isinstance(s, Deb822SourceEntry):
                continue

            if deb822_source_entry_contains(s, binentry):
                newentry = s
                break

        if newentry is not None:
            print(_("Found existing %s entry in %s") % (self.binary_type,
                                                        newentry.file))
        else:
            newentry = sourceslist.add('', '', '', [],
                                       file=self.sourceparts_file)
            newentry.types = binentry.types
            newentry.uris = binentry.uris
            newentry.suites = binentry.suites
            newentry.comps = binentry.comps

            if self.trustedparts_content:
                lines = self.trustedparts_content.splitlines()
                lines = [' ' + (l if l.strip() else '.') for l in lines]
                newentry.section['Signed-By'] = '\n' + '\n'.join(lines)

        binentry = newentry

        if self.enable_source and self.source_type not in set(binentry.types):
            newentry = None
            srcentry = self.SourceEntry(self.source_type)

            for s in sourceslist:
                if not isinstance(s, Deb822SourceEntry):
                    continue

                if deb822_source_entry_contains(s, srcentry):
                    newentry = s
                    break

            if newentry is not None:
                print(_("Found existing %s entry in %s") % (self.source_type,
                                                            newentry.file))
            else:
                binentry.types = [self.binary_type, self.source_type]

        if not self.dry_run:
            if not os.path.exists(binentry.file):
                # Create the dir if needed
                if (binentry.file.startswith(self.sourceparts_path)
                    and not os.path.exists(self.sourceparts_path)):
                    os.mkdir(self.sourceparts_path, 0o755)
                with open(binentry.file, 'w'):
                    os.chmod(binentry.file, self.sourceparts_mode)
            sourceslist.save()

    def add_source(self):
        '''Add the apt SourceEntries.

        This uses SourcesList to add the binary-type and source-type
        SourceEntries.

        If the SourceEntry matches a known apt template, this will ignore
        the sourceparts_file and instead place the SourceEntries into
        the main/default sources.list file.  Otherwise, this will add
        the SourceEntries into the sourceparts_file.

        If either the binary-type or source-type entry exist in the current
        SourcesList, the existing entries are updated instead of placing
        the entries in the sourceparts_file.
        '''
        if self.deb822:
            self._add_deb822_source()
            return

        binentry = self.SourceEntry(self.binary_type)
        srcentry = self.SourceEntry(self.source_type)
        mode = self.sourceparts_mode

        sourceslist = SourcesList()

        newentry = get_source_entry_from_list(sourceslist, binentry)
        if newentry is not None:
            print(_("Found existing %s entry in %s") % (newentry.type, newentry.file))
        else:
            newentry = sourceslist.add(
                uri=binentry.uri,
                dist=binentry.dist,
                file=binentry.file,
                type=binentry.type,
                orig_comps=binentry.comps
            )
            newentry.disabled = binentry.disabled

        if binentry.file != newentry.file:
            # existing binentry, but not in file we were expecting, just update it
            print(_("Updating existing entry instead of using %s") % binentry.file)
        elif newentry.template:
            # our SourceEntry matches a template; use default sources.list file
            newentry.file = SourceEntry('').file
            print(_("Archive has template, updating %s") % newentry.file)
        elif binentry.disabled:
            print(_("Adding disabled %s entry to %s") % (newentry.type, newentry.file))
        else:
            print(_("Adding %s entry to %s") % (newentry.type, newentry.file))

        binentry = newentry

        # Unless it already exists somewhere, add the srcentry right after the binentry
        srcentry.file = binentry.file

        newentry = get_source_entry_from_list(sourceslist, srcentry)
        if newentry is not None:
            print(_("Found existing %s entry in %s") % (newentry.type, newentry.file))
        else:
            newentry = sourceslist.add(
                uri=srcentry.uri,
                dist=srcentry.dist,
                file=srcentry.file,
                type=srcentry.type,
                orig_comps=srcentry.comps
            )
            newentry.disabled = srcentry.disabled

        if srcentry.file != newentry.file:
            # existing srcentry, but not in file we were expecting, just update it
            print(_("Updating existing entry instead of using %s") % srcentry.file)
        elif srcentry.disabled:
            print(_("Adding disabled %s entry to %s") % (newentry.type, newentry.file))
        else:
            print(_("Adding %s entry to %s") % (newentry.type, newentry.file))

        srcentry = newentry

        if not self.dry_run:
            # If the file doesn't exist, create it so we can set the mode
            for entryfile in set([binentry.file, srcentry.file]):
                if not os.path.exists(entryfile):
                    # Create the dir if needed
                    if (entryfile.startswith(self.sourceparts_path)
                        and not os.path.exists(self.sourceparts_path)):
                        os.mkdir(self.sourceparts_path, 0o755)
                    with open(entryfile, 'w'):
                        os.chmod(entryfile, mode)
            sourceslist.save()

    def _remove_deb822_source(self):
        sourceslist = SourcesList(deb822=True)
        binentry = self.SourceEntry(self.binary_type)

        for s in sourceslist:
            if not isinstance(s, Deb822SourceEntry):
                continue

            if deb822_source_entry_contains(s, binentry):
                print(_("Removing entry from %s") % (s.file))
                binentry = s
                sourceslist.remove(binentry)
                break

        if not self.dry_run:
            sourceslist.save()
            if not [s for s in sourceslist if s.file == binentry.file]:
                try:
                    os.remove(binentry.file)
                except (OSError, IOError):
                    pass

    def remove_source(self):
        '''Remove the apt SourceEntries.

        This uses SourcesList to remove the binary-type and source-type
        SourceEntries.

        This must disable the corresponding SourceEntries, from whatever file(s)
        they are located in.  This must not disable more than matches, e.g.
        if the existing SourceEntry line contains more components this must
        edit the existing line to remove this SourceEntry's component(s).

        After disabling all matching SourceEntries, if the sourceparts_file is
        empty or contains only invalid and/or disabled SourceEntries, this
        may remove the sourceparts_file.
        '''
        if self.deb822:
            self._remove_deb822_source()
            return

        sourceslist = SourcesList()
        orig_files = set([e.file for e in sourceslist])

        binentry = self.SourceEntry(self.binary_type)
        srcentry = self.SourceEntry(self.source_type)

        binentry.disabled = False
        srcentry.disabled = False

        for s in sourceslist:
            if get_source_entry_from_list([binentry,srcentry], s) is not None:
                print(_("Disabling %s entry in %s") % (s.type, s.file))
                s.disabled = True

        file_entries = [s for s in sourceslist if s.file == self.sourceparts_file]
        if not [e for e in file_entries if not e.invalid and not e.disabled]:
            # no more valid/enabled entries in our file, remove them
            for e in file_entries:
                if not e.invalid:
                    print(_("Removing disabled %s entry from %s") % (e.type, e.file))
                sourceslist.remove(e)

        if not self.dry_run:
            sourceslist.save()
            for file in orig_files - set([e.file for e in sourceslist]):
                try:
                    os.remove(file)
                except (OSError, IOError):
                    pass

    @property
    def sourceparts_path(self):
        '''Return result of apt_pkg.config.find_dir("Dir::Etc::sourceparts")'''
        return apt_pkg.config.find_dir("Dir::Etc::sourceparts")

    @property
    def sourceparts_filename(self):
        '''Get the sources.list.d filename, without the leading path.

        By default, this combines the filebase with the codename, and uses a
        extension of 'list' if deb822 is not enabled, and 'sources' if deb822
        is enabled.  This is different than the trustedparts or
        netrcparts filenames, which use only the filebase plus extension.
        '''
        ext = 'sources' if self.deb822 else 'list'
        return self._filebase_to_filename(ext, suffix=self.codename)

    @property
    def sourceparts_file(self):
        '''Get the sources.list.d absolute-path filename.

        Note that the add_source() function will not use this file if this shortcut's
        SourceEntry matches a known apt template; instead the entries will be placed
        in the main sources.list file.  Also, if the SourceEntry already exists in
        the SourcesList, it will be edited in place, instead of using this file.
        See add_source() for more details.
        '''
        return self._filename_to_file(self.sourceparts_path, self.sourceparts_filename)

    @property
    def sourceparts_mode(self):
        '''Mode of sourceparts file.

        Note that add_source() will only use this mode if it creates a new file
        for sourceparts_file; if the file already exists or if the SourceEntry is
        saved in a different file, this mode is not used.
        '''
        return 0o644

    def add_key(self):
        '''Add the GPG key(s) corresponding to this repo.

        By default, if self.trustedparts_content contains content,
        and self.trustedparts_file points to a file, the key(s) will
        be added to the file.

        If the file does not yet exist, and self.trustedparts_mode is set,
        the file will be created with that mode.
        '''
        if self.deb822:
            # The key is embedded into the file when the source is added.
            return

        if not all((self.trustedparts_file, self.trustedparts_content)):
            return

        dest = self.trustedparts_file
        keys = self.trustedparts_content
        if not isinstance(keys, bytes):
            keys = keys.encode()
        fp = self.fingerprints(keys)

        print(_("Adding key to %s with fingerprint %s") % (dest, ','.join(fp)))

        cmd = GPG_KEYRING_CMD % dest
        action = "--import"
        if not self.dry_run:
            if not os.path.exists(dest):
                # Create the dir if needed
                if (dest.startswith(self.trustedparts_path)
                    and not os.path.exists(self.trustedparts_path)):
                    os.mkdir(self.trustedparts_path, mode=0o755)
                if self.trustedparts_mode:
                    with open(dest, 'wb'):
                        os.chmod(dest, self.trustedparts_mode)
            try:
                with tempfile.TemporaryDirectory() as homedir:
                    cmd += f" --homedir {homedir} {action}"
                    subprocess.run(cmd.split(), check=True, input=keys)
            except subprocess.CalledProcessError as e:
                raise ShortcutException(e)

    def remove_key(self):
        '''Remove the GPG key(s) corresponding to this repo.

        By default, if self.trustedparts_content contains content,
        and self.trustedparts_file points to a file, the key(s) will
        be removed from the file.

        If the file contains no more keys after removal, the file will
        be removed.

        This does not consider other files; multiple repositories may
        use the same signing key.  This only modifies/removes
        self.trustedparts_file.
        '''
        if not all((self.trustedparts_file, self.trustedparts_content)):
            return

        dest = self.trustedparts_file
        fp = self.fingerprints(self.trustedparts_content)

        if not os.path.exists(dest):
            return

        print(_("Removing key from %s with fingerprint %s") % (dest, ','.join(fp)))

        cmd = GPG_KEYRING_CMD % dest
        action = "--delete-keys %s" % ' '.join(fp)
        if not self.dry_run:
            try:
                with tempfile.TemporaryDirectory() as homedir:
                    cmd += f" --homedir {homedir} {action}"
                    subprocess.run(cmd.split(), check=True)
            except subprocess.CalledProcessError as e:
                raise ShortcutException(e)

            with open(dest, 'rb') as f:
                empty = not self.fingerprints(f.read())
            if empty:
                os.remove(dest)

    @property
    def trustedparts_path(self):
        '''Return result of apt_pkg.config.find_dir("Dir::Etc::trustedparts")'''
        return apt_pkg.config.find_dir("Dir::Etc::trustedparts")

    @property
    def trustedparts_filename(self):
        '''Get the trusted.gpg.d filename, without the leading path.'''
        return self._filebase_to_filename('gpg')

    @property
    def trustedparts_file(self):
        '''Get the trusted.gpg.d absolute-path filename.'''
        return self._filename_to_file(self.trustedparts_path, self.trustedparts_filename)

    @property
    def trustedparts_content(self):
        '''Content to put into trusted.gpg.d file'''
        return None

    @property
    def trustedparts_mode(self):
        '''Mode of trustedparts file'''
        return 0o644

    def add_login(self):
        '''Add the login credentials corresponding to this repo.

        By default, if self.netrcparts_content contains content,
        and self.netrcparts_file points to a file, the file will be
        created and content placed into it.
        '''
        if not all((self.netrcparts_file, self.netrcparts_content)):
            return

        dest = self.netrcparts_file
        content = self.netrcparts_content

        newfile = not os.path.exists(dest)
        finalchar = '\n'
        if not newfile:
            with open(dest, 'r') as f:
                lines = [l.strip() for l in f.readlines()]
            with suppress(KeyError):
                finalchar = lines[-1][-1]
            if all([l.strip() in lines for l in content.splitlines()]):
                print(_("Authentication data already in %s") % dest)
                return

        print(_("Adding authentication data to %s") % dest)
        if not self.dry_run:
            if newfile:
                # Create the dir if needed
                if (dest.startswith(self.netrcparts_path)
                    and not os.path.exists(self.netrcparts_path)):
                    os.mkdir(self.netrcparts_path, mode=0o755)
                if self.netrcparts_mode:
                    with open(dest, 'w'):
                        os.chmod(dest, self.netrcparts_mode)
            with open(dest, 'a') as f:
                # we're appending; if the file doesn't end in \n, throw one in
                if finalchar != '\n':
                    f.write('\n')
                f.write(self.netrcparts_content)

    def remove_login(self):
        '''Remove the login credentials corresponding to this repo.

        By default, if self.netrcparts_content contains content,
        and self.netrcparts_file points to a file, the content will
        be removed from the file.

        If the file is empty (other than whitespace) after removal, the file
        will be removed.

        This does not consider other files; this only modifies/removes
        self.netrcparts_file.
        '''
        if not all((self.netrcparts_file, self.netrcparts_content)):
            return

        dest = self.netrcparts_file
        content = set([l.strip() for l in self.netrcparts_content.splitlines()])

        if not os.path.exists(dest):
            return

        with open(dest, 'r') as f:
            filecontent = set([l.strip() for l in f.readlines()])
        if not filecontent & content:
            print(_("Authentication data not contained in %s") % dest)
        else:
            print(_("Removing authentication data from %s") % dest)
            if not self.dry_run:
                with open(dest, 'w') as f:
                    f.write('\n'.join(filecontent - content))

        if not self.dry_run:
            with open(dest, 'r') as f:
                empty = not f.read().strip()
            if empty:
                os.remove(dest)

    @property
    def netrcparts_path(self):
        '''Return result of apt_pkg.config.find_dir("Dir::Etc::netrcparts")'''
        return apt_pkg.config.find_dir("Dir::Etc::netrcparts")

    @property
    def netrcparts_filename(self):
        '''Get the auth.conf.d filename, without the leading path.'''
        return self._filebase_to_filename('conf')

    @property
    def netrcparts_file(self):
        '''Get the auth.conf.d absolute-path filename.'''
        return self._filename_to_file(self.netrcparts_path, self.netrcparts_filename)

    @property
    def netrcparts_content(self):
        '''Content to put into auth.conf.d file

        By default, if both username and password are set, this will return a proper
        netrc-formatted line with the authentication information, including the
        hostname and path.
        '''
        if not all((self.username, self.password)):
            return None

        hostname = urlparse(self.SourceEntry().uri).hostname
        path = urlparse(self.SourceEntry().uri).path
        return f'machine {hostname}{path} login {self.username} password {self.password}'

    @property
    def netrcparts_mode(self):
        '''Mode of netrcparts file'''
        return 0o600

    def _set_source_entry(self, line):
        '''Set the SourceEntry.

        This should be called from subclasses to set the SourceEntry.
        The SourceEntry file will be set to the sourceparts_file value.

        The self.components, if any, will be added to the line's component(s).
        '''
        if self.deb822:
            e = Deb822SourceEntry(line, file=self.sourceparts_file)
        else:
            e = SourceEntry(line, file=self.sourceparts_file)

        e.comps = list(set(e.comps) | set(self.components))
        self._source_entry = copy_source_entry(e)

    def _encode_filebase(self, suffix=None):
        base = self._filebase
        if not base:
            return None
        if suffix:
            base += '-%s' % suffix
        return re.sub("[^a-z0-9_-]+", "_", base.lower())

    def _filebase_to_filename(self, ext, suffix=None):
        base = self._encode_filebase(suffix=suffix)
        if not base:
            return None
        return '%s.%s' % (base, ext)

    def _filename_to_file(self, path, name):
        if not name:
            return None
        return os.path.join(path, name)


class ShortcutException(Exception):
    '''General Exception during shortcut processing.'''
    pass


class InvalidShortcutException(ShortcutException):
    '''Invalid shortcut.

    This should only be thrown from the constructor of a ShortcutHandler
    subclass, and only to indicate that the provided shortcut is invalid
    for that ShortcutHandler class.
    '''
    pass


# vi: ts=4 expandtab
