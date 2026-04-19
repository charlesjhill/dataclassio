import pytest

from dataclassio import EFS
from dataclassio import _example_schemas as _sch


class TestDictExtras:
    def test_ignore(self):
        kls = _sch.CocoCategory
        dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

        inst = kls.from_dict(dikt, extra_field_strategy=EFS.IGNORE)
        assert not inst.extra_fields, "expected extra_fields to be empty"

    def test_strict(self):
        kls = _sch.CocoCategory
        dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

        with pytest.raises(ValueError, match="extra fields.*bonus"):
            kls.from_dict(dikt, extra_field_strategy=EFS.STRICT)

    def test_capture(self):
        kls = _sch.CocoCategory
        dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

        inst = kls.from_dict(dikt, extra_field_strategy=EFS.CAPTURE)
        assert inst.extra_fields == {"bonus": "bonus"}
        assert inst.to_dict() == dikt
