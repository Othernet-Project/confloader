Writing .ini files
==================

The .ini format that is used by Confloader is more or less the same as the one
used by Python's standard library `ConfigParser
<https://docs.python.org/2/library/configparser.html>`_ module. 

Sections
--------

The configuration file consists of sections which start with the section header
in ``[name]`` format. Section naming is arbitrary and completely up to the
user, but there are two special sections, ``[global]`` and ``[config]`` which
have special handling in Confloader.

Options
-------

The configuration options are specified using ``key=value`` format. Leading
whitespace, whitespace around the equals sign, and whitespace around the value
are ignored. A simple value may look like this::

    foo = bar

Values can span multiple lines. Unlike ``ConfigParser``, multi-line values have
special meaning to Confloader, which we will discuss later. At it's simplest,
multiline value may look like this::

    foo = Long value that 
          spans multiple lines.

Note that leading whitespace in the second line is completely ignored.

Data types
----------

Values that *appear* to be of some type will be coerced to that type.
Currently, coercion is supported for the following types:

- integer
- float
- byte size
- boolean
- null/None
- list

Numeric values
~~~~~~~~~~~~~~

If the value is strictly numeric, it will be treated as an integer or a float.
Presence of the decimal dot determines the actual type used. For instance::

    foo = 12   # becomes int(12)
    bar = 1.2  # becomes float(1.2)

Negative numbers are also supported with a ``-`` prefix. There cannot be any
whitespace between the prefix and the digits, however.

Byte size values
~~~~~~~~~~~~~~~~

Byte size values are similar to numeric values but they have 'KB', 'MB', or
'GB' suffix. The suffix may be separated from the digits by a blank, and is
case-insensitive (e.g., 'KB' is the same as 'kb' and same as 'Kb').

These values translate to integers in bytes, where the prefixes are not metric
but powers of 1024 as per JEDEC. Here is an example::

    foo = 2MB  # becomes int(2 * 1024 * 1024) == int(2097152)


Boolean and null values
~~~~~~~~~~~~~~~~~~~~~~~

Boolean and null values are words with special meaning. These words are:

- yes (``True``)
- no (``False``)
- true (``True``)
- false (``False``)
- null (``None``)
- none (``None``)

These words are case-insensitive, so 'Yes' is the same as 'yes', and 'NULL' is
the same as 'nuLL'.

Here are a few examples::

    foo = yes
    bar = False
    baz = none

Lists
~~~~~

Lists are a special form of multi-line values. Lists are specified by starting
the value with a newline and listing list items one item per line. For
example::

    foo =
        foo
        bar
        baz

The above value will be translated to a list of strings: ``['foo', 'bar',
'baz']``.

All other types except multiline values and lists themselves can be used in
lists. This inclues integers, floats, booleans, and bytes.

Referencing other configuration files
-------------------------------------

Configuration files can be made modular by cross-referencing other
configuration file fragments. This is done by two list keys in a special
``[config]`` section. Here is an example::

    [config]

    defaults =
        networking.ini
        visuals.ini

    include =
        /etc/myapp.d/networking.ini
        /etc/myapp.d/visuals.ini
        /etc/myapp.d/overrides.ini

The above example references two configuration files as defaults, and three
files as includes. The primary difference between defaults and includes is in
how they affect the configuration file in which they appear. Defaults serve as
a base, which teh current configuration file overrides, while include override
the current configuration.

The paths are evaluated relative to the configuration files. In the above
example, the default configuration files are all assumed to reside in the same
location as the configuation file in which they are referenced. Absolute paths
are unaffected by this.

Paths may include glob patterns supported by Python's ``glob`` module. The
above example for the ``include`` key can be rewritten as::

    include =
        /etc/myapp.d/*.ini

All of the paths referenced by the ``[config]`` section are optional, in the
sense that missing paths will not cause failure.

Extending lists
---------------

Lists can be extended between two configuration files. This is best described
through an example::

    # default.ini
    [foo]

    bar =
       1
       2
       3

    # master.ini
    [config]

    defaults =
        default.ini

    [foo]

    +bar =
        4
        5
        6

By prefixing a key with a plus sign (``+``), the ``bar`` list in ``master.ini``
will be used to extend the ``bar`` list in ``default.ini``. The resulting value
will be ``[1, 2, 3, 4, 5, 6]``.

This also applies to extensions defined in an include, which do not replace the
original keys found in the configuration file in which it is referenced, but
extends it instead.

When Confloads encounters an extend key, but there is nothing to extend, it
will simply create an empty list and extend it. For example, if the
``default.ini`` in the above example did not contain any ``bar`` key, the
result would be a list that contains only the elements from ``master.ini``'s
``bar`` list: ``[4, 5, 6]``.
