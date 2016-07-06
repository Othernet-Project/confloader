import os
import re
import sys
import glob

try:
    from configparser import RawConfigParser as ConfigParser, NoOptionError
except ImportError:
    from ConfigParser import RawConfigParser as ConfigParser, NoOptionError


__version__ = '1.1'
__author__ = 'Outernet Inc <apps@outernet.is>'


DEFAULT_SECTIONS = ('global')
FLOAT_RE = re.compile(r'^-?\d+\.\d+$')
INT_RE = re.compile(r'^-?\d+$')
SIZE_RE = re.compile(r'^-?\d+(\.\d{1,3})? ?[KMG]B$', re.I)
FACTORS = {
    'b': 1,
    'k': 1024,
    'm': 1024 * 1024,
    'g': 1024 * 1024 * 1024,
}


def get_config_path(default=None):
    """
    Attempt to obtain and return a path to configuration file specified by
    ``--conf`` command line argument, and fall back on specified default path.
    Default value is ``None``.
    """
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
    if val == '':
        return []
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
    """
    Parses size with B, KB, MB, or GB suffix and returns in size bytes. The
    suffix is not metric but based on powers of 1024. The suffix is also
    case-insensitive.
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
    """
    Detect value type and coerce to appropriate Python type. The input must be
    a string and the value's type is derived based on it's formatting. The
    following types are supported:

    - boolean ('yes', 'no', 'true', 'false', case-insensitive)
    - None ('null', 'none', case-insensitive)
    - integer (any number of digits, optionally prefixed with minus sign)
    - float (digits with floating point, optionally prefix with minus sign)
    - byte sizes (same as float, but with KB, MB, or GB suffix)
    - lists (any value that sarts with a newline)

    Other values are returned as is.
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

    # Everything else is returned as is
    return val


def get_compound_key(section, key):
    """
    Return the key that will be used to look up configuration options.  Except
    for the global keys, the compoint key is in ``<section>.<option>`` format.
    """
    if section in DEFAULT_SECTIONS:
        return key
    return '{}.{}'.format(section, key)


def parse_key(section, key):
    """
    Given section name and option name (key), return a compound key and a flag
    that is ``True`` if the option marks an extension.
    """
    is_ext = key.startswith('+')
    key = key.lstrip('+')
    return get_compound_key(section, key), is_ext


class ConfigurationError(Exception):
    """
    Raised when application is not configured correctly.
    """
    pass


class ConfigurationFormatError(ConfigurationError):
    """
    Raised when configuration file is malformed.
    """
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
    """
    Dictionary subclass that is used to hold the parsed configuration options.

    :py:class:`~ConfDict` is instantiated the same way as dicts. For this
    reason, the paths to configuation files and similar are not passed to the
    constructor. Instead, you should use the :py:meth:`~ConfDict.from_file`
    classmethod.

    Because this class is a dictionary, you can use the standard ``dict`` API
    to access and modify the keys. There is a minor difference when accessing
    key values, though. When using the subscript notation,
    :py:class:`~ConfigurationFormatError` is raised instead of ``KeyError``
    when the key is missing.
    """

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
        self.noextend = False
        super(ConfDict, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return super(ConfDict, self).__getitem__(key)
        except KeyError as err:
            raise ConfigurationFormatError(err)

    def get_section(self, name):
        """
        Returns an iterable containing options for a given section. This method
        does *not* return the dict values, but instead uses the underlying
        parser object to retrieve the values from the parsed configuration
        file.
        """
        return self.parser.items(name)

    def get_option(self, section, name, default=None):
        """
        Returns a single configuration option that matches the given section
        and option names. Optional default value can be specified using the
        ``default`` parameter, and this value is returned when the option is
        not found.

        As with :py:meth:`~ConfDict.get_section` method, this method operates
        on the parsed configuration file rather than dictionary data.
        """
        try:
            return self.parser.get(section, name)
        except NoOptionError:
            return default

    @property
    def sections(self):
        """
        Returns an iterable containing the names of sections. This method uses
        the underlying parser object and does not work with the dict values.
        """
        return self.parser.sections()

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
        paths = []
        parsed_paths = make_list(parse_value(
            self.get_option('config', key, '')))
        for p in parsed_paths:
            path = os.path.normpath(os.path.join(self.base_path, p))
            paths.extend(glob.glob(path))
        return paths

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
        for path in self.defaults:
            defl = self.__class__.from_file(path, self.skip_clean)
            self.setdefaults(defl)

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

    def _extend(self, extensions=None):
        """
        Extends the dictionary data using either the specified iterable
        containing the extensions, or the extensions stored in the
        :py:attr:`~ConfDict._extensions` property.

        The extensions are two-tuples containing the key name and a list of
        values.
        """
        if self.noextend:
            return
        using_self = extensions is None
        if using_self:
            # We're using our own extensions, not the supplied one
            extensions = self._extensions
        for k, v in extensions:
            if self.skip_clean:
                self.setdefault(k, '')
                self[k] += v
            else:
                extend_key(self, k, v)
        # We only clear extensions if we are extending using the internal
        # extensions list.
        if using_self:
            self._extensions = []

    def _postprocess(self):
        """
        Finishes loading proces by processing all extensions and includes.
        """
        self._extend()
        for path in self.include:
            include = self.__class__.from_file(path, self.skip_clean,
                                               noextend=True)
            self.update(include)
            self._extend(include._extensions)

    def _init_parser(self):
        """
        Initialize the ``ConfigParser`` object and read the path or file-like
        object stored in the :py:attr:`~ConfDict.path` property.
        """
        self.parser = ConfigParser()
        if hasattr(self.path, 'read'):
            self.parser.readfp(self.path)
        else:
            self.parser.read(self.path)

    def _check_conf(self):
        """
        Check whether there are any sections, and raise
        :py:class:`~ConfigurationError` excetpion if no sections are found.
        """
        if not self.sections:
            raise ConfigurationError("Missing or empty configuration file at "
                                     "'{}'".format(self.path))

    def load(self):
        """
        Parses and loads the configuration data. This method will trigger a
        sequence of operations:

        - initialize the parser, and load and parse the configuration file
        - check the configuration file
        - perform preprocessing (check for references to other files)
        - process the sections
        - process any includes or extensions

        Any problems with the referenced defaults and includes will propagate
        to this call.

        .. note::
            Using this method for reloading the configuration is not
            recommended. Instead, create a new instance using the
            :py:meth:`~ConfDict.from_file` method.
        """
        self._init_parser()
        self._check_conf()
        self._preprocess()
        self._process()
        self._postprocess()

    def configure(self, path, skip_clean=False, noextend=False):
        """
        Configure the :py:class:`~ConfDict` instance for processing.

        The ``path`` is a path to the configuration file. ``skip_clean``
        parameter is a boolean flag that suppresses type conversion during
        parsing. ``noextend`` flag suppresses list extension.
        """
        self.path = path
        self.base_path = os.path.dirname(os.path.abspath(path))
        self.skip_clean = skip_clean
        self.noextend = noextend

    def setdefaults(self, other):
        """
        This method is a counterpart of the :py:meth:`~dict.update` method and
        works like :py:meth:`~dict.setdefault`. The ``other`` argument is a
        dict or dict-like object, whose key-value pairs are added to the
        :py:class:`~ConfDict` object if the key does not exist already.
        """
        for k in other:
            if k not in self:
                self[k] = other[k]

    def import_from_file(self, path, as_defaults=False, ignore_missing=False):
        """
        Imports additional options from specified file. The ``as_default`` flag
        can be used to cause the options to only be imported if they are not
        already present. The ``ignore_missing`` suppresses the
        :py:class:`~ConfigurationError` exception when the specified file is
        missing.
        """
        try:
            incl = self.__class__.from_file(path, self.skip_clean,
                                            noextend=True)
        except self.ConfigurationError:
            return {}
        if as_defaults:
            self.setdefaults(incl)
        else:
            self.update(incl)
        self._extend(incl._extensions)
        # We have to force extension before returning the incl ConfDict object
        # because otherwise the extension keys will not become available.
        incl.noextend = False
        incl._extend()
        return incl

    @classmethod
    def from_file(cls, path, skip_clean=False, noextend=False, defaults={}):
        """
        Load the values from the specified file. The ``skip_clean`` flag is
        used to suppress type conversion. ``noextend`` flag suppresses list
        extension.

        You may also specify default options using the ``defaults`` argument.
        This argument should be a dict. Values specified in this dict are
        overridden by the values present in the configuration file.
        """
        # Instantiate the ConfDict class and configure it
        self = cls()
        self.update(defaults)
        self.configure(path, skip_clean, noextend)
        self.load()
        return self
