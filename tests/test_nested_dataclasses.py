from dataclassio import _example_schemas as sch


class TestDictNestedDataclasses:
    def test_optional_nested_dataclass(self):
        ex_user = {"id": 1, "name": "username"}

        actual = sch.User.from_dict(ex_user)
        assert actual.address is None
        assert actual.to_dict(skip_defaults=True) == ex_user

    def test_optional_non_default_dataclass(self):
        ex_data = {"metric": None}

        actual = sch.MaybeMetric.from_dict(ex_data)
        assert actual.metric is None
        assert actual.to_dict() == ex_data

    def test_simple_nested_dataclass(self):
        ex_user = {"id": 1, "name": "username", "address": {"city": "Anytown"}}

        actual = sch.User.from_dict(ex_user)
        assert isinstance(actual.address, sch.Address)
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

        actual = sch.TinyTable.from_dict(ex_data)
        assert isinstance(actual.rows, list)
        assert len(actual.rows) == 2
        assert all(isinstance(r, sch.TinyRow) for r in actual.rows)
        assert actual.rows[1].name == "b"
        assert actual.to_dict(skip_defaults=True) == ex_data

    def test_dict_of_list_of_dataclass(self):
        ex_data = {
            "title": "System Health",
            "data_points": {
                "cpu_usage": [
                    {"value": 12.5, "unit": "percent"},
                    None,
                    {"value": 45.0, "unit": "percent"},
                ],
                "memory": [
                    {"value": 1.2, "unit": "GB"},
                ],
            },
        }

        actual = sch.Dashboard.from_dict(ex_data)
        assert len(actual.data_points) == 2
        assert isinstance(actual.data_points["cpu_usage"][0], sch.Metric)
        assert actual.data_points["cpu_usage"][1] is None

    def test_dataclass_dict_value(self):
        data = {
            "id": 1,
            "name": "Alice",
            "named_addresses": {"home": {"city": "Anytown"}, "work": {"city": "Coolsville"}},
        }

        actual = sch.User.from_dict(data)
        assert isinstance(actual.named_addresses, dict)
        assert len(actual.named_addresses) == 2
        assert isinstance(actual.named_addresses["home"], sch.Address)
        assert isinstance(actual.named_addresses["work"], sch.Address)
        assert actual.named_addresses["work"].city == "Coolsville"
        assert actual.to_dict(skip_defaults=True) == data
