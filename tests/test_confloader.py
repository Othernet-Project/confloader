try:
    from unittest import mock
except ImportError:
    import mock

import pytest

import confloader as mod


MOD = mod.__name__


@pytest.mark.parametrize('arg,path', [
    ('--conf=test.ini', 'test.ini'),
    ("--conf='test.ini'", 'test.ini'),
    ('--conf="test.ini"', 'test.ini'),
    ('--conf test.ini', 'test.ini'),
    ('--conf /path/to/file-test.ini', '/path/to/file-test.ini'),
    ('--conf=/path/to/file-test.ini', '/path/to/file-test.ini'),
    ("--conf='/path/to/file-test.ini'", '/path/to/file-test.ini'),
    ('--conf="/path/to/file-test.ini"', '/path/to/file-test.ini'),
    ('--conf c,\path\\to\mis leading', 'c,\path\\to\mis'),
])
@mock.patch.object(mod, 'sys')
def test_get_config_path(sys, arg, path):
    sys.argv = ['cmd', '-t', '--flag', '--var="te st"', arg, '--var2=3']
    result = mod.get_config_path()
    assert result == path


@pytest.mark.parametrize('conf,val', [
    ('2B', 2.0),
    ('2b', 2.0),
    ('2 b', 2.0),
    ('200B', 200.0),
    ('1KB', 1024.0),
    ('1kb', 1024.0),
    ('22kb', 22528.0),
    ('5MB', 5242880.0),
    ('5mb', 5242880.0),
    ('5 mb', 5242880.0),
    ('10GB', 10737418240.0),
    ('0.3GB', 322122547.2),
])
def test_parse_size(conf, val):
    assert mod.parse_size(conf) == val


@pytest.mark.parametrize('conf,val', [
    ('', ''),
    ('foo', 'foo'),
    ('bar', 'bar'),
    ('yes', True),
    ('true', True),
    ('no', False),
    ('false', False),
    ('YES', True),
    ('TRUE', True),
    ('NO', False),
    ('FALSE', False),
    ('Yes', True),
    ('True', True),
    ('No', False),
    ('False', False),
    ('none', None),
    ('null', None),
    ('NONE', None),
    ('NULL', None),
    ('None', None),
    ('Null', None),
    ('0.3', 0.3),
    ('12.2', 12.2),
    ('2', 2),
    ('0', 0),
    ('1KB', 1024.0),
    ('1 kb', 1024.0),
    ('22kb', 22528.0),
    ('5MB', 5242880.0),
    ('5mb', 5242880.0),
    ('5 mb', 5242880.0),
    ('10GB', 10737418240.0),
    ('0.3GB', 322122547.2),
    ('\nfoo\nbar', ['foo', 'bar']),
    ('\n1\n2', [1, 2]),
    ('\nyes\nno', [True, False]),
])
def test_clean_value(conf, val):
    assert mod.parse_value(conf) == val
