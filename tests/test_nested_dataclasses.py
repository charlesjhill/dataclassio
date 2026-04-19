from dataclassio._example_schemas import Address, TinyRow, TinyTable, User


class TestDictNestedDataclasses:
    def test_optional_nested_dataclass(self):
        ex_user = {"id": 1, "name": "username"}

        actual = User.from_dict(ex_user)
        assert actual.address is None
        assert actual.to_dict(skip_defaults=True) == ex_user

    def test_simple_nested_dataclass(self):
        ex_user = {"id": 1, "name": "username", "address": {"city": "Anytown"}}

        actual = User.from_dict(ex_user)
        assert isinstance(actual.address, Address)
        assert actual.address.city == "Anytown"
        assert actual.to_dict(skip_defaults=True) == ex_user

    def test_simple_list_dataclass(self):
        ex_data = {
            "id": 1,
            "rows": [
                {
                    "id": 1,
                    "name": "a",
                },
                {"id": 2, "name": "b"},
            ],
        }

        actual = TinyTable.from_dict(ex_data)
        assert isinstance(actual.rows, list)
        assert len(actual.rows) == 2
        assert all(isinstance(r, TinyRow) for r in actual.rows)
        assert actual.rows[1].name == "b"
        assert actual.to_dict(skip_defaults=True) == ex_data

    def test_dataclass_dict_value(self):
        data = {
            "id": 1,
            "name": "Alice",
            "named_addresses": {"home": {"city": "Anytown"}, "work": {"city": "Coolsville"}},
        }

        actual = User.from_dict(data)
        assert isinstance(actual.named_addresses, dict)
        assert len(actual.named_addresses) == 2
        assert isinstance(actual.named_addresses["home"], Address)
        assert isinstance(actual.named_addresses["work"], Address)
        assert actual.named_addresses["work"].city == "Coolsville"
        assert actual.to_dict(skip_defaults=True) == data
