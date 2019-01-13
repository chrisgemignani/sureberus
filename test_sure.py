import pytest

from sureberus import normalize_dict, normalize_schema
from sureberus import schema as S
from sureberus import errors as E

id_int = {'id': S.Integer()}
nested_num_int = {'nested': S.Dict(schema={'num': S.Integer()})}
default_num = {'num': S.Integer(default=0)}


def test_sure():
    sample = {'id': 3}
    assert normalize_dict(id_int, sample) == sample

def test_bad_type():
    sample = {'id': '3'}
    with pytest.raises(E.BadType) as ei:
        normalize_dict(id_int, sample)
    assert ei.value.value == '3'
    assert ei.value.type_ == 'integer'
    assert ei.value.stack == ('id',)

def test_field_not_found():
    with pytest.raises(E.DictFieldNotFound) as ei:
        normalize_dict(id_int, {'foo': 'bar'})
    assert ei.value.key == 'id'
    assert ei.value.value == {'foo': 'bar'}
    assert ei.value.stack == ()

def test_nested_error():
    with pytest.raises(E.BadType) as ei:
        normalize_dict(nested_num_int, {'nested': {'num': 'three!'}})
    assert ei.value.value == 'three!'
    assert ei.value.type_ == 'integer'
    assert ei.value.stack == ('nested', 'num')

def test_default():
    old_dict = {}
    new_dict = normalize_dict(default_num, old_dict)
    assert old_dict == {}
    assert new_dict == {'num': 0}

def test_normalize_schema():
    assert normalize_schema(S.Integer(), 3)

def test_anyof():
    anyof = {'anyof': [S.Integer(), S.String()]}
    assert normalize_schema(anyof, 3) == 3
    assert normalize_schema(anyof, 'three') == 'three'
    with pytest.raises(E.NoneMatched) as ei:
        normalize_schema(anyof, object())

def test_anyof_with_normalization():
    """THIS IS THE WHOLE REASON FOR SUREBERUS TO EXIST"""
    # We want to support
    # ANY OF:
    # - {'image': str, 'opacity': {'type': 'integer', 'default': 100}}
    # - {'gradient': ...}
    anyof = S.Dict(
        anyof=[
            S.SubSchema(gradient=S.String()),
            S.SubSchema(image=S.String(), opacity=S.Integer(default=100))
        ]
    )

    gfoo = {'gradient': 'foo'}
    assert normalize_schema(anyof, gfoo) == gfoo
    ifoo_with_opacity = {'image': 'foo', 'opacity': 99}
    assert normalize_schema(anyof, ifoo_with_opacity) == ifoo_with_opacity
    ifoo_with_default = {'image': 'foo'}
    assert normalize_schema(anyof, ifoo_with_default) == {'image': 'foo', 'opacity': 100}


def test_nullable_with_anyof():
    """This is the second reason that sureberus exists."""
    anyof = {
        'nullable': True,
        'anyof': [S.Integer(), S.String()],
    }
    assert normalize_schema(anyof, None) == None
