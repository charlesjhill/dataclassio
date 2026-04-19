import pytest

from dataclass_io.functional import EFS

from . import _example_schemas as _sch


def test_extra_exclude():
    kls = _sch.CocoCategory
    dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

    inst = kls.from_dict(dikt, extra_field_strategy=EFS.IGNORE)
    assert not inst.extra_fields, "expected extra_fields to be empty"


def test_extra_strict():
    kls = _sch.CocoCategory
    dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

    with pytest.raises(ValueError, match="extra fields.*bonus"):
        kls.from_dict(dikt, extra_field_strategy=EFS.STRICT)


def test_extra_capture():
    kls = _sch.CocoCategory
    dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

    inst = kls.from_dict(dikt, extra_field_strategy=EFS.CAPTURE)
    assert inst.extra_fields == {"bonus": "bonus"}
