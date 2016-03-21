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
    ('"""This is a\nmultiline\nstring"""', 'This is a\nmultiline\nstring'),
])
def test_clean_value(conf, val):
    assert mod.parse_value(conf) == val


@pytest.mark.parametrize('section,key,comp', [
    ('global', 'foo', 'foo'),
    ('global', 'bar', 'bar'),
    ('database', 'foo', 'database.foo'),
    ('database', 'bar', 'database.bar'),
])
def test_get_compound_key(section, key, comp):
    assert mod.get_compound_key(section, key) == comp


@pytest.mark.parametrize('section,key,key_ext', [
    ('global', 'foo', ('foo', False)),
    ('database', 'foo', ('database.foo', False)),
    ('database', '+foo', ('database.foo', True)),
])
def test_parse_key(section, key, key_ext):
    assert mod.parse_key(section, key) == key_ext


@pytest.mark.parametrize('val,ret', [
    ('foo', ['foo']),
    (1, [1]),
    (True, [True]),
    (False, [False]),
    (None, [None]),
    ('', ['']),
    (['foo', 'bar'], ['foo', 'bar']),
    (('foo', 'bar'), ['foo', 'bar']),
])
def test_make_list(val, ret):
    assert mod.make_list(val) == ret


def test_extend_key():
    d = {'foo': [1, 2, 3], 'bar': 'test'}
    mod.extend_key(d, 'foo', [4, 5, 6])
    assert d['foo'] == [1, 2, 3, 4, 5, 6]
    mod.extend_key(d, 'bar', ['more'])
    assert d['bar'] == ['test', 'more']
    mod.extend_key(d, 'baz', [1, 2, 3])
    assert d['baz'] == [1, 2, 3]


def test_extend_noniterable_raises():
    d = {'foo': [1, 2, 3], 'bar': 'test'}
    with pytest.raises(TypeError):
        mod.extend_key(d, 'foo', 12)


def get_mock_conf():
    mock_parser = mock.Mock(specs=mod.ConfigParser)
    conf = mod.ConfDict()
    conf.parser = mock_parser
    return conf


def test_get_option():
    conf = get_mock_conf()
    ret = conf.get_option('foo', 'bar')
    conf.parser.get.assert_called_once_with('foo', 'bar')
    assert ret == conf.parser.get.return_value


@mock.patch.object(mod, 'NoOptionError', Exception)
def test_get_option_none():
    conf = get_mock_conf()
    conf.parser.get.side_effect = mod.NoOptionError
    ret = conf.get_option('foo', 'bar')
    assert ret is None


@mock.patch.object(mod, 'NoOptionError', Exception)
def test_get_option_default():
    conf = get_mock_conf()
    conf.parser.get.side_effect = mod.NoOptionError
    ret = conf.get_option('foo', 'bar', 'default')
    assert ret == 'default'


@mock.patch.object(mod.ConfDict, 'get_section')
def test_parse_section(get_section):
    conf = mod.ConfDict()
    get_section.return_value = [('foo', 'bar'), ('bar', '1')]
    ret = conf._parse_section('foo')
    get_section.assert_called_once_with('foo')
    assert conf['foo.foo'] == 'bar'
    assert conf['foo.bar'] == 1
    assert ret == []


@mock.patch.object(mod.ConfDict, 'get_section')
def test_parse_section_extend(get_section):
    conf = mod.ConfDict()
    get_section.return_value = [('foo', 'bar'), ('bar', '1'), ('+baz', '\n12')]
    ret = conf._parse_section('foo')
    assert ret == [('foo.baz', [12])]


@mock.patch.object(mod.ConfDict, 'get_section')
def test_parse_section_no_clean(get_section):
    conf = mod.ConfDict()
    conf.skip_clean = True
    get_section.return_value = [('foo', 'bar'), ('bar', '1'), ('+baz', '\n12')]
    ret = conf._parse_section('foo')
    assert conf['foo.bar'] == '1'
    assert ret == [('foo.baz', '\n12')]


@mock.patch.object(mod.ConfDict, 'get_option')
def test_get_config_paths(get_option):
    conf = mod.ConfDict()
    get_option.return_value = '\nfoo/bar/baz.ini\nbaz/bar/foo.ini'
    ret = conf._get_config_paths('defaults')
    get_option.assert_called_once_with('config', 'defaults', '\n')
    assert ret == ['foo/bar/baz.ini', 'baz/bar/foo.ini']


@mock.patch.object(mod.ConfDict, 'get_option')
def test_get_config_paths_single_string(get_option):
    conf = mod.ConfDict()
    get_option.return_value = 'foo/bar/baz.ini'
    ret = conf._get_config_paths('defaults')
    get_option.assert_called_once_with('config', 'defaults', '\n')
    assert ret == ['foo/bar/baz.ini']


@mock.patch.object(mod.ConfDict, '_get_config_paths')
@mock.patch.object(mod.ConfDict, 'from_file')
@mock.patch.object(mod.ConfDict, 'setdefaults')
def test_preprocess(setdefaults, from_file, get_config_paths):
    conf = get_mock_conf()
    conf.base_path = 'test'
    get_config_paths.side_effect = [['foo/bar/baz.ini'], ['baz/bar/foo.ini']]
    conf._preprocess()
    # The defaults and includes are set so they can be accessed later
    assert conf.defaults == ['foo/bar/baz.ini']
    assert conf.include == ['baz/bar/foo.ini']
    # The one file listed in defaults, should be made relative to current
    # config's base path (directory) and loaded
    from_file.assert_called_once_with('test/foo/bar/baz.ini', conf.skip_clean)
    setdefaults.assert_called_once_with(from_file.return_value)


@mock.patch.object(mod.ConfDict, 'setdefaults')
def test_preprocess_no_config_section(setdefaults):
    conf = get_mock_conf()
    # Config does not have 'config' section at all
    conf.parser.has_section.return_value = False
    conf._preprocess()
    assert conf.defaults == []
    assert conf.include == []
    assert setdefaults.call_count == 0


@mock.patch.object(mod.ConfDict, '_get_config_paths')
@mock.patch.object(mod.ConfDict, 'from_file')
@mock.patch.object(mod.ConfDict, 'setdefaults')
def test_preprocess_no_keys(setdefaults, file_from, get_config_paths):
    conf = get_mock_conf()
    # Only includes are provided in config
    get_config_paths.side_effect = [[], ['baz/bar/foo.ini']]
    conf._preprocess()
    assert conf.defaults == []
    assert conf.include == ['baz/bar/foo.ini']
    # Only defaults are provided in config
    get_config_paths.side_effect = [['foo/bar/baz.ini'], []]
    conf._preprocess()
    assert conf.defaults == ['foo/bar/baz.ini']
    assert conf.include == []


@mock.patch.object(mod.ConfDict, '_parse_section')
@mock.patch.object(mod.ConfDict, 'sections', new_callable=mock.PropertyMock)
def test_process(sections, parse_section):
    conf = mod.ConfDict()
    sections.return_value = ['foo', 'bar', 'baz']
    parse_section.return_value = []
    conf._process()
    parse_section.assert_has_calls([
        mock.call('foo'),
        mock.call('bar'),
        mock.call('baz')
    ])


@mock.patch.object(mod.ConfDict, '_parse_section')
@mock.patch.object(mod.ConfDict, 'sections', new_callable=mock.PropertyMock)
def test_process_extension(sections, parse_sections):
    conf = mod.ConfDict()
    sections.return_value = ['foo', 'bar', 'baz']
    parse_sections.side_effect = [[('foo', [1, 2]), ('bar', [2, 3])], [], []]
    conf._process()
    assert conf._extensions == [
        ('foo', [1, 2]),
        ('bar', [2, 3]),
    ]


@mock.patch.object(mod.ConfDict, '_parse_section')
@mock.patch.object(mod.ConfDict, 'sections', new_callable=mock.PropertyMock)
def test_process_resets_extensions(sections, parse_sections):
    conf = mod.ConfDict()
    conf._extensions = [('test', None)]
    sections.return_value = ['foo', 'bar', 'baz']
    parse_sections.side_effect = [[('foo', [1, 2]), ('bar', [2, 3])], [], []]
    conf._process()
    assert conf._extensions == [
        ('foo', [1, 2]),
        ('bar', [2, 3]),
    ]


def test_postprocess_extensions():
    conf = mod.ConfDict()
    conf['foo'] = [1, 2, 3]
    conf['bar'] = ['a', 'b', 'c']
    conf._extensions = [
        ('foo', [4, 5, 6]),
        ('bar', ['d', 'e', 'f']),
    ]
    conf._postprocess()
    assert conf['foo'] == [1, 2, 3, 4, 5, 6]
    assert conf['bar'] == ['a', 'b', 'c', 'd', 'e', 'f']


def test_postprocess_extensions_no_clean():
    conf = mod.ConfDict()
    conf['foo'] = '123'
    conf['bar'] = 'abc'
    conf._extensions = [
        ('foo', '456'),
        ('bar', 'def'),
    ]
    conf.skip_clean = True
    conf._postprocess()
    assert conf['foo'] == '123456'
    assert conf['bar'] == 'abcdef'


@mock.patch.object(mod.ConfDict, 'update')
@mock.patch.object(mod.ConfDict, 'from_file')
def test_postprocess_include(from_file, update):
    conf = mod.ConfDict()
    conf.base_path = 'test'
    conf.include = ['foo/bar/baz.ini']
    conf._postprocess()
    from_file.assert_called_once_with('test/foo/bar/baz.ini', conf.skip_clean)
    update.assert_called_once_with(from_file.return_value)


@mock.patch(MOD + '.ConfigParser', specs=mod.ConfigParser)
def test_init_parser(ConfigParser):
    mock_parser = ConfigParser.return_value
    conf = mod.ConfDict()
    conf.path = 'foo/bar/baz.ini'
    assert conf.parser is None
    conf._init_parser()
    assert conf.parser == mock_parser
    mock_parser.read.assert_called_once_with('foo/bar/baz.ini')


@mock.patch(MOD + '.ConfigParser', specs=mod.ConfigParser)
def test_init_parser_with_fd(ConfigParser):
    from StringIO import StringIO
    mock_parser = ConfigParser.return_value
    conf = mod.ConfDict()
    buff = StringIO()
    conf.path = buff
    assert conf.parser is None
    conf._init_parser()
    assert conf.parser == mock_parser
    mock_parser.readfp.assert_called_once_with(buff)


@mock.patch.object(mod.ConfDict, '_init_parser')
@mock.patch.object(mod.ConfDict, '_check_conf')
@mock.patch.object(mod.ConfDict, '_preprocess')
@mock.patch.object(mod.ConfDict, '_process')
@mock.patch.object(mod.ConfDict, '_postprocess')
def test_load(postprocess, process, preprocess, check, init):
    conf = mod.ConfDict()
    conf.load()
    # Load is just a wrapper that calls all these methods
    for meth in postprocess, process, preprocess, check, init:
        meth.assert_called_once_with()


def test_configure():
    conf = mod.ConfDict()
    conf.configure('foo/bar/baz.ini', True)
    assert conf.path == 'foo/bar/baz.ini'
    assert conf.base_path == 'foo/bar'
    assert conf.skip_clean is True


@mock.patch.object(mod.ConfDict, 'load')
@mock.patch.object(mod.ConfDict, 'configure')
def test_from_file(configure, load):
    ret = mod.ConfDict.from_file('foo/bar/baz.ini', False, foo='bar')
    assert ret['foo'] == 'bar'
    configure.assert_called_once_with('foo/bar/baz.ini', False)
    load.assert_called_once_with()


def test_setdefaults():
    conf = mod.ConfDict()
    conf['foo'] = 'bar'
    conf.setdefaults({
        'foo': 1,
        'bar': 2
    })
    assert conf['foo'] == 'bar'
    assert conf['bar'] == 2
