import pytest

from dataclassio import EFS
from dataclassio import _example_schemas as _sch


class TestInitFalseFields:
    def test_init_false_field_from_dict(self):
        data = {"a": 1.0, "b": 2.0}
        inst = _sch.InitFalseDC.from_dict(data)

        assert inst.a == 1.0
        assert inst.b == 2.0
        assert inst.c == (1.0 + 2.0)

    def test_init_false_field_to_dict(self):
        inst = _sch.InitFalseDC(1.0, 2.0)
        data = inst.to_dict()

        assert data == {"a": 1.0, "b": 2.0, "c": 1.0 + 2.0}

    def test_init_false_round_trip(self):
        inst = _sch.InitFalseDC(1.0, 2.0)
        data = inst.to_dict()
        inst2 = _sch.InitFalseDC.from_dict(data)

        assert inst == inst2

    def test_init_false_efs(self):
        data = {"a": 1.0, "b": 2.0, "c": "ignored"}
        expected = _sch.InitFalseDC(1.0, 2.0)

        # Business as usual
        new_inst = _sch.InitFalseDC.from_dict(data, EFS.IGNORE)
        assert expected == new_inst

        # No exception despite the "extra" field
        new_inst = _sch.InitFalseDC.from_dict(data, EFS.STRICT)
        assert expected == new_inst

        # 'c' is not captured.
        new_inst = _sch.InitFalseDC.from_dict(data, extra_field_strategy=EFS.CAPTURE)
        assert expected == new_inst
        assert new_inst.extra_fields == {}


class TestInitOnlyFields:
    def test_init_only_from_dict_all_fields(self):
        data = {"value": 10.0, "unit": "seconds"}

        actual = _sch.ImputedMetric.from_dict(data)
        expected = _sch.ImputedMetric(**data)

        assert actual == expected

    def test_init_only_from_dict_excl_optional_fields(self):
        data = {"unit": "seconds"}

        actual = _sch.ImputedMetric.from_dict(data)
        expected = _sch.ImputedMetric(**data)

        assert actual == expected

    def test_init_only_from_dict_missing_fields(self):
        data = {"value": 10.0}

        with pytest.raises(KeyError):
            _sch.ImputedMetric.from_dict(data)
