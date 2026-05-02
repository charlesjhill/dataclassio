import filecmp
import io
import json
from pathlib import Path

import pytest

from dataclassio import _example_schemas as sch


@pytest.fixture
def example_dashboard_data():
    return {
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


@pytest.fixture
def example_dashboard(example_dashboard_data):
    return sch.Dashboard.from_dict(example_dashboard_data)


class TestJSONIO:
    def test_to_json_stringio(
        self, example_dashboard: sch.Dashboard, example_dashboard_data: dict
    ):
        buffer = io.StringIO()
        buffer2 = io.StringIO()

        example_dashboard.to_json_file(buffer)
        json.dump(example_dashboard_data, buffer2)

        assert buffer.getvalue() == buffer2.getvalue()

    def test_to_json_file(
        self, example_dashboard: sch.Dashboard, example_dashboard_data: dict, tmp_path: Path
    ):
        mixin_path = tmp_path / "mixin.json"
        man_path = tmp_path / "manual.json"

        example_dashboard.to_json_file(mixin_path)

        with man_path.open("w") as f:
            json.dump(example_dashboard_data, f)

        assert filecmp.cmp(mixin_path, man_path)

    def test_from_json_stringio(
        self, example_dashboard: sch.Dashboard, example_dashboard_data: dict
    ):
        buffer = io.StringIO()
        json.dump(example_dashboard_data, buffer)
        buffer.seek(0)

        assert example_dashboard == sch.Dashboard.from_json_file(buffer)

    def test_from_json_file(
        self, example_dashboard: sch.Dashboard, example_dashboard_data: dict, tmp_path: Path
    ):
        man_path = tmp_path / "manual.json"
        with man_path.open("w") as f:
            json.dump(example_dashboard_data, f)

        assert example_dashboard == sch.Dashboard.from_json_file(man_path)
