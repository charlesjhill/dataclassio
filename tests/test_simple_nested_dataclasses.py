from ._example_schemas import Address, User


def test_optional_nested_dataclass():
    ex_user = {"id": 1, "name": "username"}

    actual = User.from_dict(ex_user)
    assert actual.address is None


def test_simple_nested_dataclass():
    ex_user = {"id": 1, "name": "username", "address": {"city": "Anytown"}}

    actual = User.from_dict(ex_user)
    assert isinstance(actual.address, Address)
