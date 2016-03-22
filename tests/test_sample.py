import os

import confloader as mod


sample_file = os.path.join(os.path.dirname(__file__), 'sample.ini')
include2 = os.path.join(os.path.dirname(__file__), 'include2.ini')


def test_sample():
    conf = mod.ConfDict.from_file(sample_file)
    assert conf['blank'] == ''
    assert conf['string'] == 'foo'
    assert conf['int'] == 12
    assert conf['float'] == 2.1
    assert conf['bytes'] == 204800
    assert conf['bool_true'] is True
    assert conf['bool_false'] is False
    assert conf['null'] is None
    assert conf['list'] == ['foo', 'bar', 'baz']
    assert conf['int_list'] == [1, 2, 3]
    assert conf['float_list'] == [0.4, 2.3, 5.4]
    assert conf['bytes_list'] == [10240, 12582912, 5368709120]
    assert conf['bool_list'] == [True, False, True, False]
    assert conf['mixed_list'] == ['foo', 12]
    assert conf['multiline_string'] == ('This is a multiline string,\n'
                                        'and it has two lines')
    assert conf['section.abc'] == 12


def test_sample_related():
    conf = mod.ConfDict.from_file(sample_file)
    assert conf['foo'] == 'bar'
    assert conf['other_section.abc'] == 12
    assert conf['other_section.bcd'] == 2
    assert conf['extended_list'] == ['a', 'b', 'c', 'd', 'e', 'f']
    assert conf['extend_me'] == ['foo', 'bar', 'baz']


def test_sample_with_defaults():
    conf = mod.ConfDict.from_file(sample_file, defaults=dict(excellent=True))
    assert conf['excellent'] is True


def test_sample_without_cleaning():
    conf = mod.ConfDict.from_file(sample_file, skip_clean=True)
    assert conf['blank'] == ''
    assert conf['string'] == 'foo'
    assert conf['int'] == '12'
    assert conf['float'] == '2.1'
    assert conf['bytes'] == '200 KB'
    assert conf['bool_true'] == 'yes'
    assert conf['bool_false'] == 'no'
    assert conf['null'] == 'null'
    assert conf['list'] == '\nfoo\nbar\nbaz'
    assert conf['int_list'] == '\n1\n2\n3'
    assert conf['float_list'] == '\n0.4\n2.3\n5.4'
    assert conf['bytes_list'] == '\n10KB\n12 mB\n5 gb'
    assert conf['bool_list'] == '\nyes\nNO\ntrue\nFalse'
    assert conf['mixed_list'] == '\nfoo\n12'
    assert conf['multiline_string'] == ('"""\nThis is a multiline string,\n'
                                        'and it has two lines\n"""')
    assert conf['section.abc'] == '12'


def test_import():
    conf = mod.ConfDict.from_file(sample_file)
    conf.import_from_file(include2)
    # Extension still works as expected:
    assert conf['extend_me'] == ['foo', 'bar', 'baz', 1, 2, 3]
    # New key is successfully added
    assert conf['other_section.cde'] == 3
    # Pre-existing keys are overwritten
    assert conf['other_section.bcd'] == 11
    # New section is added
    assert conf['new_section.awesome'] is True


def test_import_without_overwrite():
    conf = mod.ConfDict.from_file(sample_file)
    ret = conf.import_from_file(include2, as_defaults=True)
    # Extension still works as expected:
    assert conf['extend_me'] == ['foo', 'bar', 'baz', 1, 2, 3]
    # Pre-existing keys are *not* overwritten
    assert conf['other_section.bcd'] == 2
    # But they are still avalable as return value
    assert ret['other_section.bcd'] == 11
