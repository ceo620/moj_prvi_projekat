from aptsources.sourceslist import (SourceEntry, Deb822SourceEntry)

def copy_source_entry(orig):
    """ Return a shallow copy of the source entry. """
    if isinstance(orig, Deb822SourceEntry):
        return Deb822SourceEntry(str(orig), file=orig.file)

    return SourceEntry(str(orig), file=orig.file)

def replace_source_entry(orig, **kwargs):
    """Return a copy of the given source entry with replaced field(s)."""
    entry = copy_source_entry(orig)
    for (k, v) in kwargs.items():
        setattr(entry, k, v)
    return entry

def get_source_entry_pocket(source_entry):
    """
    Return the pocket, or if unset return 'release'.

    This always returns the pocket in lowercase.
    """
    parts = source_entry.dist.partition('-')
    return (parts[2] or 'release').lower()

def get_source_entry_suite(source_entry):
    """
    Return the suite, without pocket.

    This always returns the suite in lowercase.
    """
    return source_entry.dist.partition('-')[0]

def get_source_entry_from_list(entries, entry):
    """
    Return the source entry from entries that matches entry, if found.
    Otherwise return None.

    This function uses a modified equality check, i.e. it considers components
    as a set rather than a list so that different ordering does not affect the
    comparison.
    """
    target = replace_source_entry(entry, comps=set(entry.comps))

    for e in entries:
        if replace_source_entry(e, comps=set(e.comps)) == target:
            return e

    return None

def deb822_source_entry_contains(a, b):
    """
    Return True if the source defined by b is already satisfied
    by the source defined by a.

    For example, if source a is:

    Types: deb
    URIs: http://archive.ubuntu.com/ubuntu
    Suites: jammy
    Components: main universe

    and source b is:

    Types: deb
    URIs: http://archive.ubuntu.com/ubuntu
    Suites: jammy
    Components: universe

    Then source a contains source b.

    But if source b was:

    Types: deb-src
    URIs: http://archive.ubuntu.com/ubuntu
    Suites: jammy
    Components: universe

    Then a does not contain b because it does not include deb-src.
    """
    if a.disabled != b.disabled:
        return False

    for attr in ['types', 'comps', 'suites', 'uris']:
        if set(getattr(b, attr)) - set(getattr(a, attr)):
            return False

    return True
