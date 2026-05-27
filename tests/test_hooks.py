from dataclasses import dataclass

import pytest

from dataclassio import IOMixin
from dataclassio import functional as F


@dataclass
class Point(IOMixin):
    x: int
    y: int


# ---------------------------------------------------------------------------
# __pre_to_dict__
# ---------------------------------------------------------------------------
class TestPreToDict:
    def test_invoked_when_overridden(self):
        calls = []

        @dataclass
        class Tracked(Point):
            def __pre_to_dict__(self):
                calls.append(self)

        t = Tracked(1, 2)
        t.to_dict()
        assert calls == [t]

    def test_can_mutate_self_before_serialization(self):
        @dataclass
        class Shifted(Point):
            def __pre_to_dict__(self):
                self.x += 100

        assert Shifted(1, 2).to_dict() == {"x": 101, "y": 2}

    def test_return_value_is_ignored(self):
        @dataclass
        class Bogus(Point):
            def __pre_to_dict__(self):
                return {"not": "used"}

        assert Bogus(1, 2).to_dict() == {"x": 1, "y": 2}


# ---------------------------------------------------------------------------
# __post_to_dict__
# ---------------------------------------------------------------------------
class TestPostToDict:
    def test_invoked_with_serialized_dict(self):
        seen = []

        @dataclass
        class Tracked(Point):
            def __post_to_dict__(self, dikt):
                seen.append(dikt)
                return dikt

        Tracked(1, 2).to_dict()
        assert seen == [{"x": 1, "y": 2}]

    def test_can_mutate_dict_in_place(self):
        @dataclass
        class Tagged(Point):
            def __post_to_dict__(self, dikt):
                dikt["tag"] = "ok"
                return dikt

        assert Tagged(1, 2).to_dict() == {"x": 1, "y": 2, "tag": "ok"}

    def test_can_replace_dict_by_returning_new(self):
        @dataclass
        class Replaced(Point):
            def __post_to_dict__(self, dikt):
                return {"replaced": True}

        assert Replaced(1, 2).to_dict() == {"replaced": True}


# ---------------------------------------------------------------------------
# __pre_from_dict__
# ---------------------------------------------------------------------------
class TestPreFromDict:
    def test_invoked_with_input_dict(self):
        seen = []

        @dataclass
        class Tracked(Point):
            @classmethod
            def __pre_from_dict__(cls, dikt):
                seen.append((cls, dict(dikt)))
                return dikt

        Tracked.from_dict({"x": 1, "y": 2})
        assert seen == [(Tracked, {"x": 1, "y": 2})]

    def test_can_mutate_dict_in_place(self):
        @dataclass
        class Migrating(Point):
            @classmethod
            def __pre_from_dict__(cls, dikt):
                if "X" in dikt:
                    dikt["x"] = dikt.pop("X")
                return dikt

        assert Migrating.from_dict({"X": 1, "y": 2}) == Migrating(1, 2)

    def test_can_replace_dict_by_returning_new(self):
        @dataclass
        class Replacing(Point):
            @classmethod
            def __pre_from_dict__(cls, dikt):
                return {"x": dikt["x"] * 10, "y": dikt["y"] * 10}

        assert Replacing.from_dict({"x": 1, "y": 2}) == Replacing(10, 20)


# ---------------------------------------------------------------------------
# __post_from_dict__
# ---------------------------------------------------------------------------
class TestPostFromDict:
    def test_invoked_on_constructed_instance(self):
        seen = []

        @dataclass
        class Tracked(Point):
            def __post_from_dict__(self, dikt):
                seen.append((self, dikt))

        p = Tracked.from_dict({"x": 1, "y": 2})
        assert seen == [(p, {"x": 1, "y": 2})]

    def test_can_mutate_self_after_deserialization(self):
        @dataclass
        class Finalized(Point):
            def __post_from_dict__(self, dikt):
                self.x *= -1

        assert Finalized.from_dict({"x": 1, "y": 2}) == Finalized(-1, 2)

    def test_return_value_is_ignored(self):
        @dataclass
        class Bogus(Point):
            def __post_from_dict__(self, dikt):
                return Point(999, 999)

        assert Bogus.from_dict({"x": 1, "y": 2}) == Bogus(1, 2)


# ---------------------------------------------------------------------------
# Hook ordering
# ---------------------------------------------------------------------------
class TestHookOrdering:
    def test_to_dict_calls_pre_then_post(self):
        calls = []

        @dataclass
        class Tracked(Point):
            def __pre_to_dict__(self):
                calls.append("pre")

            def __post_to_dict__(self, dikt):
                calls.append("post")
                return dikt

        Tracked(1, 2).to_dict()
        assert calls == ["pre", "post"]

    def test_from_dict_calls_pre_then_post(self):
        calls = []

        @dataclass
        class Tracked(Point):
            @classmethod
            def __pre_from_dict__(cls, dikt):
                calls.append("pre")
                return dikt

            def __post_from_dict__(self, dikt):
                calls.append("post")

        Tracked.from_dict({"x": 1, "y": 2})
        assert calls == ["pre", "post"]


# ---------------------------------------------------------------------------
# Duck-typed hooks on classes that do NOT inherit from IOMixin
# ---------------------------------------------------------------------------


class TestDuckTypedHooks:
    def test_pre_to_dict_on_non_mixin_class(self):
        calls = []

        @dataclass
        class P:
            x: int
            y: int

            def __pre_to_dict__(self):
                calls.append("pre")
                self.x += 100

        assert F.to_dict(P(1, 2)) == {"x": 101, "y": 2}
        assert calls == ["pre"]

    def test_post_to_dict_on_non_mixin_class(self):
        @dataclass
        class P:
            x: int
            y: int

            def __post_to_dict__(self, dikt):
                dikt["tag"] = "ok"
                return dikt

        assert F.to_dict(P(1, 2)) == {"x": 1, "y": 2, "tag": "ok"}

    def test_pre_from_dict_on_non_mixin_class(self):
        @dataclass
        class P:
            x: int
            y: int

            @classmethod
            def __pre_from_dict__(cls, dikt):
                if "X" in dikt:
                    dikt["x"] = dikt.pop("X")
                return dikt

        assert F.from_dict(P, {"X": 1, "y": 2}) == P(1, 2)

    def test_post_from_dict_on_non_mixin_class(self):
        @dataclass
        class P:
            x: int
            y: int

            def __post_from_dict__(self, dikt):
                self.x *= -1

        assert F.from_dict(P, {"x": 1, "y": 2}) == P(-1, 2)


# ---------------------------------------------------------------------------
# Skip hooks
# ---------------------------------------------------------------------------


@dataclass
class Hooked(IOMixin):
    x: int
    y: int

    def __post_init__(self):
        self.calls = []
        super().__post_init__()

    def __pre_to_dict__(self) -> None:
        self.calls.append("pre_to_dict")

    def __post_to_dict__(self, dikt: dict) -> dict:
        dikt["post_to_dict"] = True
        return dikt

    @classmethod
    def __pre_from_dict__(cls, dikt: dict) -> dict:
        dikt = dict(dikt)
        dikt.setdefault("x", 0)
        dikt["_pre_from_dict"] = True  # Will be ignored.
        return dikt

    def __post_from_dict__(self, dikt: dict) -> None:
        self.calls.append("post_from_dict")


class TestCallLevelSkipHooks:
    def test_to_dict_runs_hooks_by_default(self):
        h = Hooked(1, 2)
        d = h.to_dict()

        assert "pre_to_dict" in h.calls
        assert d.get("post_to_dict") is True

    def test_to_dict_skips_hooks_when_requested(self):
        h = Hooked(1, 2)
        d = h.to_dict(skip_hooks=True)
        assert h.calls == []
        assert "post_to_dict" not in d

    def test_from_dict_runs_hooks_by_default(self):
        h = Hooked.from_dict({"x": 1, "y": 2})
        assert "post_from_dict" in h.calls

    def test_from_dict_skips_hooks_when_requested(self):
        # __pre_from_dict__ would inject a default for x; skipping should
        # mean the missing key causes the usual error path.
        with pytest.raises(KeyError):
            Hooked.from_dict({"y": 2}, skip_hooks=True)

        h = Hooked.from_dict({"x": 1, "y": 2}, skip_hooks=True)
        assert h.calls == []
