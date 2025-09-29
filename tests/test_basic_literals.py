import copy

import pytest

from dataclass_io import _test_schema as _schemas
from dataclass_io.io_mixin import _DICT_DESERIALIZER_NAME


@pytest.fixture
def example_category():
    dikt = {"name": "Example", "id": 1, "supercategory": ""}
    return dikt, _schemas.CocoCategory(**dikt)


def test_required_literals(example_category):
    dikt, expected = example_category
    assert not hasattr(_schemas.CocoCategory, _DICT_DESERIALIZER_NAME)

    original_dikt = copy.deepcopy(dikt)

    actual = _schemas.CocoCategory.from_dict(dikt)
    assert actual == expected
    assert hasattr(_schemas.CocoCategory, _DICT_DESERIALIZER_NAME)

    # Constructing doesn't mutate.
    assert original_dikt == dikt


def test_optional_literals():
    dikt = {"city": "Anytown"}
    dikt2 = {"city": "Anytown", "zip_code": "12345"}

    assert _schemas.Address.from_dict(dikt2) == _schemas.Address("Anytown", "12345")
    assert _schemas.Address.from_dict(dikt) == _schemas.Address("Anytown")
