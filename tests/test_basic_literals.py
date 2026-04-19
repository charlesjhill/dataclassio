import copy

import pytest

from dataclassio import _example_schemas as _schemas


class TestDictLiterals:
    def test_required_literals(self):
        dikt = {"name": "Example", "id": 1, "supercategory": ""}
        expected = _schemas.CocoCategory.manual_from_dict(dikt)

        original_dikt = copy.deepcopy(dikt)

        actual = _schemas.CocoCategory.from_dict(dikt)
        assert actual == expected

        # Constructing doesn't mutate.
        assert original_dikt == dikt

        # Test round trip
        new_dict = actual.to_dict()
        assert original_dikt == new_dict

    def test_optional_literals(self):
        dikt = {"city": "Anytown"}
        dikt2 = {"city": "Anytown", "zip_code": "12345"}

        addr1 = _schemas.Address.from_dict(dikt)
        addr2 = _schemas.Address.from_dict(dikt2)

        assert addr1 == _schemas.Address("Anytown")
        assert addr2 == _schemas.Address("Anytown", "12345")

        # Test round trip
        assert addr2.to_dict() == dikt2

        rt_dikt1 = addr1.to_dict()
        assert rt_dikt1 == {**dikt, "zip_code": None}

        assert addr1.to_dict(skip_defaults=True) == dikt

    def test_useful_message_for_missing_value(self):
        with pytest.raises(KeyError, match="required attribute.*zip_code"):
            _schemas.Address.from_dict({"zip_code": "12345"})

    def test_default_uses_dataclass_default(self):
        dikt = {"id": 1, "name": "Alice"}
        actual = _schemas.User.from_dict(dikt)
        expected = _schemas.User(1, "Alice", False)
        assert actual == expected
        assert actual.to_dict(skip_defaults=True) == dikt

        dikt_with_admin = {"id": 2, "name": "Bob", "is_admin": True}
        actual = _schemas.User.from_dict(dikt_with_admin)
        expected = _schemas.User(2, "Bob", True)
        assert actual == expected
        assert actual.to_dict(True) == dikt_with_admin

    def test_plain_containers(self):
        dikt = {"id": 1, "name": "Alice", "metadata": {"k1": "k2"}, "data": [1, 2, 3]}
        actual = _schemas.TinyRow.from_dict(dikt)
        expected = _schemas.TinyRow(**dikt)

        assert actual == expected
        assert actual.to_dict() == dikt
