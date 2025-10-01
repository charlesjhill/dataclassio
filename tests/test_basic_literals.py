import copy

import pytest

from . import _example_schemas as _schemas


def test_required_literals():
    dikt = {"name": "Example", "id": 1, "supercategory": ""}
    expected = _schemas.CocoCategory(**dikt)

    original_dikt = copy.deepcopy(dikt)

    actual = _schemas.CocoCategory.from_dict(dikt)
    assert actual == expected

    # Constructing doesn't mutate.
    assert original_dikt == dikt


def test_optional_literals():
    dikt = {"city": "Anytown"}
    dikt2 = {"city": "Anytown", "zip_code": "12345"}

    assert _schemas.Address.from_dict(dikt2) == _schemas.Address("Anytown", "12345")
    assert _schemas.Address.from_dict(dikt) == _schemas.Address("Anytown")


def test_useful_message_for_missing_value():
    with pytest.raises(KeyError, match="required attribute.*zip_code"):
        _schemas.Address.from_dict({"zip_code": "12345"})


def test_default_uses_dataclass_default():
    dikt = {"id": 1, "name": "Alice"}
    dikt_with_admin = {"id": 2, "name": "Bob", "is_admin": True}

    assert _schemas.User.from_dict(dikt) == _schemas.User(1, "Alice", False)
    assert _schemas.User.from_dict(dikt_with_admin) == _schemas.User(2, "Bob", True)
