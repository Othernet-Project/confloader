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
