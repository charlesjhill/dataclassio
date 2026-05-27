import pytest

from dataclassio import EFS
from dataclassio import _example_schemas as _sch


class TestDictExtras:
    def test_ignore(self):
        kls = _sch.CocoCategory
        dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

        inst = kls.from_dict(dikt, extra_field_strategy=EFS.IGNORE)
        assert not inst.extra_fields, "expected extra_fields to be empty"

        # And skipping extras works as expected
        dikt.pop("bonus")
        assert inst.to_dict(skip_extras=True) == dikt

    def test_strict(self):
        kls = _sch.CocoCategory
        dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

        with pytest.raises(ValueError, match="extra fields.*bonus"):
            kls.from_dict(dikt, extra_field_strategy=EFS.STRICT)

        # Removing the extra field fixes the issue.
        dikt.pop("bonus")
        inst = kls.from_dict(dikt)

        # And dumping w/o the extras has no issue, of course.
        assert inst == _sch.CocoCategory(1, "person", "person")
        assert inst.to_dict(skip_extras=True) == dikt

    def test_capture(self):
        kls = _sch.CocoCategory
        dikt = {"id": 1, "name": "person", "supercategory": "person", "bonus": "bonus"}

        inst = kls.from_dict(dikt, extra_field_strategy=EFS.CAPTURE)
        assert inst.extra_fields == {"bonus": "bonus"}
        assert inst.to_dict() == dikt

        # Check that we can disable dumping extras
        assert inst.to_dict(skip_extras=True) == {
            "id": 1,
            "name": "person",
            "supercategory": "person",
        }

        # And toggle it back on with the next call
        assert inst.to_dict() == dikt
