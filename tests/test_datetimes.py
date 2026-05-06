import dataclasses as dcs
from datetime import datetime, timezone

import pytest

from dataclassio import IOMixin


@dcs.dataclass
class TimestampModel(IOMixin):
    event_name: str
    ts: datetime
    # Testing optionality in the recursive parser
    updated_at: datetime | None = None


@dcs.dataclass
class NestedLog(IOMixin):
    log_id: int
    entries: list[TimestampModel]


class TestDatetimeParsing:
    """
    Validates ISO-8601 datetime handling for DataclassIO.
    Ensures generated code accurately converts between string literals
    and datetime objects.
    """

    def test_basic_iso_parsing(self):
        """Test from_dict with standard ISO strings."""
        data = {
            "event_name": "startup",
            "ts": "2026-05-05T20:00:00Z",
            "updated_at": "2026-05-06T12:00:00+00:00",
        }
        obj = TimestampModel.from_dict(data)

        assert isinstance(obj.ts, datetime)
        assert obj.ts.year == 2026
        assert obj.updated_at.day == 6

    def test_iso_serialization(self):
        """Test to_dict converts datetime to ISO format strings."""
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        obj = TimestampModel(event_name="login", ts=ts)

        result = obj.to_dict()
        # Verify it exports the string representation for JSON compatibility
        assert isinstance(result["ts"], str)
        assert "2026-01-01T12:00:00+00:00" in result["ts"]

    def test_optional_datetime_none(self):
        """Ensure the parser handles None without attempting to parse it."""
        data = {"event_name": "background_sync", "ts": "2026-05-05T20:00:00Z", "updated_at": None}
        obj = TimestampModel.from_dict(data)
        assert obj.updated_at is None

    def test_nested_datetime_collection(self):
        """Test recursive parsing of datetimes inside a list."""
        data = {
            "log_id": 101,
            "entries": [
                {"event_name": "a", "ts": "2026-01-01T00:00:00Z"},
                {"event_name": "b", "ts": "2026-01-02T00:00:00Z"},
            ],
        }
        obj = NestedLog.from_dict(data)

        assert len(obj.entries) == 2
        assert all(isinstance(e.ts, datetime) for e in obj.entries)
        assert obj.entries[1].ts.day == 2

    def test_invalid_iso_format_raises(self):
        """Verify that malformed strings raise ValueErrors, maintaining integrity."""
        data = {"event_name": "fail", "ts": "not-a-date"}
        with pytest.raises(ValueError):
            TimestampModel.from_dict(data)
