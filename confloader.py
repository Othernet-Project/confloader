"""
confloader.py: Application configuration loader

Copyright 2014-2016, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import re
import sys

try:
    from configparser import RawConfigParser as ConfigParser, NoOptionError
except ImportError:
    from ConfigParser import RawConfigParser as ConfigParser, NoOptionError


__version__ = '1.0'
__author__ = 'Outernet Inc <apps@outernet.is>'


DEFAULT_SECTIONS = ('DEFAULT', 'bottle')
FLOAT_RE = re.compile(r'^\d+\.\d+$')
INT_RE = re.compile(r'^\d+$')
SIZE_RE = re.compile(r'^\d+(\.\d{1,3})? ?[KMG]B$', re.I)
FACTORS = {
    'b': 1,
    'k': 1024,
    'm': 1024 * 1024,
    'g': 1024 * 1024 * 1024,
}


def get_config_path(default=None):
    regex = r'--conf[=\s]{1}((["\']{1}(.+)["\']{1})|([^\s]+))\s*'
    arg_str = ' '.join(sys.argv[1:])
    result = re.search(regex, arg_str)
    return result.group(1).strip(' \'"') if result else default


def make_list(val):
    """
    If the value is not a list, it is converted to a list. Iterables like tuple
    and list itself are converted to lists, whereas strings, integers, and
    other values are converted to a list whose sole item is the original value.
    """
    if type(val) in [list, tuple]:
        return list(val)
    return [val]


def extend_key(d, key, val):
    """
    Extends a dictionary key with a specified iterable. If the key does not
    exist, it is assigned a list before extending. If the key exists, but maps
    to a non-list value, the key value is convereted to a list before being
    extended.
    """
    d.setdefault(key, [])
    d[key] = make_list(d[key])
    d[key].extend(val)


def parse_size(size):
    """ Parses size with B, K, M, or G suffix and returns in size bytes

    :param size:    human-readable size with suffix
    :returns:       size in bytes or 0 if source string is using invalid
                    notation
    """
    size = size.lower()[:-1]
    if size[-1] not in 'bkmg':
        suffix = 'b'
    else:
        suffix = size[-1]
        size = size[:-1]
    try:
        size = float(size)
    except ValueError:
        return 0
    return size * FACTORS[suffix]


def parse_value(val):
    """ Detect value type and coerce to appropriate Python type

    :param val:     value in configuration format
    :returns:       python value
    """
    # True values: 'yes', 'Yes', 'true', 'True'
    if val.lower() in ('yes', 'true'):
        return True

    # False values: 'no', 'No', 'false', 'False'
    if val.lower() in ('no', 'false'):
        return False

    # Null values: 'null', 'NULL', 'none', 'None'
    if val.lower() in ('null', 'none'):
        return None

    # Floating point numbers: 1.0, 12.443, 1002.3
    if FLOAT_RE.match(val):
        return float(val)

    # Integer values: 1, 30, 445
    if INT_RE.match(val):
        return int(val)

    # Data sizes: 10B, 12.3MB, 5.6 GB
    if SIZE_RE.match(val):
        return parse_size(val)

    # Lists: one item per line, indented
    if val.startswith('\n'):
        return [parse_value(v) for v in val[1:].split('\n')]

    # Multi-line string: same as python with triple-doublequotes
    if val.startswith('"""'):
        return val.strip('"""').strip()

    # Everything else is returned as is
    return val


def get_compound_key(section, key):
    if section in DEFAULT_SECTIONS:
        return key
    return '{}.{}'.format(section, key)


def parse_key(section, key):
    is_ext = key.startswith('+')
    key = key.lstrip('+')
    return get_compound_key(section, key), is_ext


class ConfigurationError(Exception):
    """ Raised when application is not configured correctly """
    pass


class ConfigurationFormatError(ConfigurationError):
    """ Raised when configuration file is malformed """
    def __init__(self, keyerr):
        key = keyerr.args[0]
        if '.' in key:
            self.section, self.subsection = key.split('.')
        else:
            self.section = 'GLOBAL'
            self.subsection = key
        super(ConfigurationFormatError, self).__init__(
            "Configuration error in section [{}]: missing '{}' setting".format(
                self.section, self.subsection))


class ConfDict(dict):
    ConfigurationError = ConfigurationError
    ConfigurationFormatError = ConfigurationFormatError

    def __init__(self, *args, **kwargs):
        self.path = None
        self.parser = None
        self.base_path = '.'
        self.defaults = []
        self.include = []
        self._extensions = []
        self.skip_clean = False
        super(ConfDict, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return super(ConfDict, self).__getitem__(key)
        except KeyError as err:
            raise ConfigurationFormatError(err)

    def get_section(self, name):
        return self.parser.items(name)

    def get_option(self, section, name, default=None):
        try:
            return self.parser.get(section, name)
        except NoOptionError:
            return default

    def _parse_section(self, section):
        """
        Given a section name, parses the section and returns a list of
        extension keys (keys prefixed with '+' character) with their values.
        """
        extensions = []
        for key, value in self.get_section(section):
            compound_key, extends = parse_key(section, key)
            if not self.skip_clean:
                value = parse_value(value)
            if extends:
                extensions.append((compound_key, value))
                continue
            self[compound_key] = value
        return extensions

    def _get_config_paths(self, key):
        """
        Return a list of paths in the special config keys.
        """
        paths = parse_value(self.get_option('config', key, '\n'))
        return make_list(paths)

    def _preprocess(self):
        """
        Prepares for config loading by parsing the special config section and
        setting up defaults and include lists. The defaults are also loaded
        immediately to ensure they are successfully overwritten during
        subsequent parsing.
        """
        if not self.parser.has_section('config'):
            return
        self.defaults = self._get_config_paths('defaults')
        self.include = self._get_config_paths('include')
        for p in self.defaults:
            path = os.path.normpath(os.path.join(self.base_path, p))
            self.setdefaults(self.__class__.from_file(path, self.skip_clean))

    def _process(self):
        """
        Processes all sections one by one. The special section named 'config'
        is skipped'.

        While the sections are parsed, the extensions dictionary is updated.
        """
        self._extensions = []
        for section in self.sections:
            exts = self._parse_section(section)
            self._extensions.extend(exts)

    def _postprocess(self):
        """
        Finishes loading proces by processing all extensions and includes.
        """
        for k, v in self._extensions:
            if self.skip_clean:
                self.setdefault(k, '')
                self[k] += v
            else:
                extend_key(self, k, v)
        for p in self.include:
            path = os.path.normpath(os.path.join(self.base_path, p))
            self.update(self.__class__.from_file(path, self.skip_clean))

    def _init_parser(self):
        self.parser = ConfigParser()
        if hasattr(self.path, 'read'):
            self.parser.readfp(self.path)
        else:
            self.parser.read(self.path)

    def _check_conf(self):
        if not self.sections:
            raise ConfigurationError("Missing or empty configuration file at"
                                     "'{}'".format(self.path))

    def load(self):
        self._init_parser()
        self._check_conf()
        self._preprocess()
        self._process()
        self._postprocess()

    def configure(self, path, skip_clean=False):
        self.path = path
        self.base_path = os.path.dirname(path)
        self.skip_clean = skip_clean

    @property
    def sections(self):
        return self.parser.sections()

    @classmethod
    def from_file(cls, path, skip_clean=False, **defaults):
        # Instantiate the ConfDict class and configure it
        self = cls()
        self.update(defaults)
        self.configure(path, skip_clean)
        self.load()
        return self

    def setdefaults(self, other):
        for k in other:
            if k not in self:
                self[k] = other[k]
