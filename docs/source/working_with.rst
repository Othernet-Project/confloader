Working with configuration files
================================

This section gives you a quick overview of Confloader library usage.

Loading configuration files
---------------------------

Configuration files can be loaded from files or file descrptors and objects
that support file-descriptor-like API (e.g., ``StringIO``). To load a
configuration file, you can use the ``from_file()`` method on the
``confloader.ConfDict`` class::

    from confloader import ConfDict

    conf = ConfDict.from_file('config.ini')

If the configuration file is blank, missing, contains no section, or has
options that are dangling outside sections, or otherwise malformed, you will
get a ``ConfigurationError`` exception. This exception is available as an
attribute on the ``ConfDict`` class as convenience::

    try:
        conf = ConfDict.from_file('nonexistent.ini')
    except ConfDict.ConfigError:
        print('Oh noes!')

Application may specify its own defaults when loading configuration files. This
is done by using the ``defaults`` argument which must be a dictionary::

    conf = ConfDict.from_file('config.ini', defaults={
        'myoption1': 12,
        'myoption2': no
    })

If, for some reason, you don't like type conversions, you can omit type
conversion by passing the ``skip_clean`` flag::

    conf = ConfDict.from_file('config.ini', skip_clean=True)

List extension can be suppressed by using ``noextend`` parameter::

    conf = ConfDict.from_file('config.ini', noextend=True)

Adding options from configuration files at runtime
--------------------------------------------------

The confiuration object, once instantiated, can be further manipulated by
calling the ``import_from_file`` method on the ``ConfigDict`` objects. For
example::

    conf = ConfDict.from_file('config.ini')
    conf.import_from_file('fragment.ini')

This method has two modes. The first mode is the include mode, which overwrites
existing options using the options from the specified file. The other mode is
the defaults mode which only fills in the blank while leaving existing options
intact. The defaults mode is enabled by supplying ``as_defaults=True``
argument.

By default, calling ``import_from_file`` on a non-existent configuration file
will raise the ``ConfigError`` exception. This exception can be suppressed by
passing the ``ignore_missing=True`` argument.

Accessing options
-----------------

Options are accessed via keys that are a combination of the section name and
option name. ::

    [foo]

    bar = 1

The ``bar`` option from the above example is accessed as ``config['foo.bar']``.

There is a special section named ``[global]``. Options that appear in this
section are unprefixed. ::

    [global]

    foo = yes

The ``foo`` option from the above example is acessed as ``conf['foo']``.
